# Cloudflare Migration Plan: research.values.md

**Status:** Draft — pending approval
**Author:** Claude + gs
**Date:** 2026-05-20
**Scope:** Migrate the FastAPI app served at `research.values.md` from Fly.io to Cloudflare Workers. Keep the existing Neon Postgres database. Keep the Python research/experiment code as-is.

---

## TL;DR

- **Frontend + API:** Rewrite the web layer in **Astro 6 (SSR-only) with `@astrojs/cloudflare`**, deployed as a Cloudflare Worker. Astro 6's content collections fit the `research/` markdown folder almost 1:1, and Astro layouts replace Jinja inheritance directly. Cloudflare acquired Astro in Jan 2026 and Astro 6 (Feb 2026) treats Workers as a first-class target.
- **Database:** Keep Neon Postgres. No data migration. Access from the Worker via **Drizzle ORM + `drizzle-orm/neon-http`**. Introspect existing schema with `drizzle-kit pull`. Graduate to Hyperdrive + `postgres-js` only if latency/transaction needs demand it later.
- **Migrations:** Replace Alembic with `drizzle-kit generate` + `drizzle-kit migrate`, run from GitHub Actions before `wrangler deploy`. Freeze Alembic at the cutover commit.
- **Static assets:** Workers Assets binding (favicons, logo, research figures bundled into `public/`).
- **LLM endpoints:** Drop pydantic-ai; talk to OpenRouter via bare `fetch` with Zod schemas for structured output. Workers paid plan ($5/mo) supports 5-min CPU and unbounded `fetch` wait — fine for 20-40s generation calls.
- **Repo layout:** Add `web/` directory to this repo. Single source of truth for the schema; Python and TS coexist against the same Neon DB.
- **Cutover:** Deploy the new app to `research-next.values.md` first. Side-by-side soak. Flip the `research.values.md` Custom Domain when stable. Decommission Fly app + image.
- **Compatibility constraint:** The Next.js app at `~/dev/values.md/next/` (deployed to `values.md`) is the primary API consumer — already on CF (OpenNext + D1), calls server-to-server with `X-API-Key`. The migration must preserve byte-level response shapes for ~10 endpoints; if done correctly the Next.js codebase needs **zero changes**. See [Appendix C](#appendix-c--compatibility-with-the-valuesmd-nextjs-client).
- **Effort:** 5–7 focused days. The site has ~25 routes; most are CRUD-ish. The non-trivial pieces are the research-folder pipeline, the dilemma generator (one LLM call w/ structured output), and the VALUES.md generator.

---

## Table of Contents

1. [Decisions & Rationale](#1-decisions--rationale)
2. [Target Architecture](#2-target-architecture)
3. [Repo Layout](#3-repo-layout)
4. [Phased Migration](#4-phased-migration)
5. [Database Migration Details](#5-database-migration-details)
6. [Research Folder Pipeline](#6-research-folder-pipeline)
7. [Caching Strategy](#7-caching-strategy)
8. [LLM Endpoints — Porting Notes](#8-llm-endpoints--porting-notes)
9. [Template / Page Port Map](#9-template--page-port-map)
10. [Auth, Secrets, Env Vars](#10-auth-secrets-env-vars)
11. [Local Dev Workflow](#11-local-dev-workflow)
12. [CI / Deployment](#12-ci--deployment)
13. [Cutover Plan](#13-cutover-plan)
14. [What We Do NOT Migrate](#14-what-we-do-not-migrate)
15. [Risks & Mitigations](#15-risks--mitigations)
16. [Rollback Plan](#16-rollback-plan)
17. [Out-of-Scope / Follow-ups](#17-out-of-scope--follow-ups)
18. [Effort Estimate](#18-effort-estimate)

---

## 1. Decisions & Rationale

### 1.1 Framework: Astro 6 SSR, not plain Hono

| Concern | Astro 6 | Hono + JSX | Plain Worker |
|---|---|---|---|
| Research markdown folder | Content Collections with Zod-validated frontmatter, dynamic routes, image pipeline — fits like a glove | Hand-rolled (glob + gray-matter + remark + router) | Hand-rolled, much more |
| Jinja `base.html` inheritance | Astro layouts map 1:1 | Hono `jsxRenderer` w/ `_renderer.tsx` — workable but more setup | DIY |
| JSON API routes | `src/pages/api/*.ts` — standard `Request`/`Response` | Native, slightly nicer ergonomics | Verbose |
| CF integration | First-party (CF acquired Astro Jan 2026); `astro dev` runs on `workerd` for prod parity | Mature | Mature |
| Bundle / cold start | ~50ms SSR cold start; small bundle if no React islands | Smallest | Smallest |
| Known issues | One real one: [#15237](https://github.com/withastro/astro/issues/15237) — hybrid prerender+SSR with `cloudflare:` imports breaks the build. **Mitigation:** force SSR-only (`output: 'server'`). All our routes are dynamic anyway. | None blocking | N/A |

The site is 50% long-form research content and 50% DB-backed app routes. Astro is built for that mix. Hono would be the right call if it were 90% JSON API — it isn't.

**Do not add React islands.** A couple of open Astro+Cloudflare issues (#16387, #16529) involve React hydration; if we keep everything as plain `.astro` components we avoid them entirely. Interactive bits, if any, can be done with vanilla TS in a `<script>` tag or Astro's `client:*` directives with a small framework (Solid / Preact) chosen only if needed.

### 1.2 ORM / driver: Drizzle + neon-http first

| Driver | When | Verdict |
|---|---|---|
| `drizzle-orm/neon-http` + `@neondatabase/serverless` | Simple HTTP per query, no pool to manage. Best cold start. No interactive transactions. | **Start here.** |
| `drizzle-orm/postgres-js` over **Hyperdrive** | Real connection pooling, prepared-statement caching, lower steady-state latency, real `BEGIN…COMMIT`. | Graduate if metrics demand. Driver swap is small. |
| `drizzle-orm/neon-serverless` (WebSocket) | Worst option in Workers — WS can't outlive a request. | Skip. |

Our query patterns are simple reads and short writes. No long interactive transactions in the existing code. `neon-http` is the right starting point.

### 1.3 Database & migration tool

- **Keep Neon Postgres.** Same connection, no data migration.
- **Replace Alembic with Drizzle migrations** going forward. Freeze the Alembic head at cutover.
- Introspect existing schema with `drizzle-kit pull`; expect hand-edits for the `data TEXT` JSON columns (introspects as plain text, we wrap with a `jsonText<T>()` custom type).

### 1.4 Static assets

Workers Assets binding (`assets` block in `wrangler.jsonc`). Pages-style deployment is being absorbed into Workers; Assets is the recommended path. Per-file 25 MiB, 100k files on Paid — our ~10 MB of research images is trivial.

### 1.5 LLM library: none

Drop pydantic-ai. The Worker just makes `fetch` calls to OpenRouter's OpenAI-compatible endpoint with a JSON body and a `response_format: { type: 'json_schema', json_schema: { ... } }` derived from Zod via `zod-to-json-schema`. Three endpoints use LLM calls — that's a few hundred lines of TS total.

---

## 2. Target Architecture

```
                          ┌────────────────────────────────┐
                          │  research.values.md            │
                          │  (Cloudflare Custom Domain)    │
                          └──────────────┬─────────────────┘
                                         │
                                         ▼
                          ┌────────────────────────────────┐
                          │  Cloudflare Worker              │
                          │  ─ Astro 6 SSR-only adapter     │
                          │  ─ Workers Assets binding       │
                          │  ─ Compatibility: nodejs_compat │
                          └───┬──────────────┬──────────────┘
                              │              │
                              ▼              ▼
                ┌──────────────────┐  ┌──────────────────┐
                │  Neon Postgres    │  │  OpenRouter API  │
                │  (existing DB)    │  │  (LLM calls)     │
                │  via neon-http    │  │                  │
                └──────────────────┘  └──────────────────┘

Bundled into the Worker at build time:
   src/content/research/ ← symlink/copy of ../research/*/findings.md
   public/research-static/{slug}/figures/...
   public/static/{favicons, logo.svg}
```

Local Python (unchanged) writes to the same Neon DB for experiment generation and analysis.

---

## 3. Repo Layout

Single-repo layout. The Python project stays where it is; add a `web/` directory.

```
dilemmas/
├── src/dilemmas/             # Python: models, services, scripts target — UNCHANGED
├── scripts/                  # Python: experiment runners, sync_to_prod, generators — UNCHANGED
├── research/                 # markdown findings — canonical, shared between Python + Astro
├── prompts/                  # LLM prompts — used by both Python (live) and TS (the 3 ported endpoints)
├── alembic/                  # FROZEN at cutover commit — keep for history; no new revisions
├── data/                     # local SQLite + outputs — UNCHANGED
├── docs/
│   └── CLOUDFLARE_MIGRATION_PLAN.md    ← this doc
├── pyproject.toml, uv.lock, etc.       # UNCHANGED
│
└── web/                                # NEW — Astro Worker
    ├── astro.config.mjs
    ├── wrangler.jsonc
    ├── package.json
    ├── tsconfig.json
    ├── drizzle.config.ts
    ├── .dev.vars                        # gitignored
    ├── .gitignore
    ├── public/                          # bundled static
    │   ├── static/                      # favicons, logo (copied from src/dilemmas/api/static/)
    │   └── research-static/             # populated by prebuild from ../research/*/figures
    ├── drizzle/                         # generated migration SQL files
    ├── scripts/
    │   └── copy-research-figures.ts     # prebuild step
    ├── src/
    │   ├── env.d.ts                     # Cloudflare bindings types
    │   ├── content.config.ts            # Astro 6 collection definitions
    │   ├── db/
    │   │   ├── schema.ts                # Drizzle schema (matches DilemmaDB / JudgementDB / ValuesMdDB)
    │   │   ├── json-text.ts             # customType<T>() for JSON-in-TEXT columns
    │   │   ├── client.ts                # drizzle(neon(env.DATABASE_URL)) per-request
    │   │   └── queries.ts               # high-level query helpers
    │   ├── lib/
    │   │   ├── openrouter.ts            # bare fetch client
    │   │   ├── auth.ts                  # X-API-Key check
    │   │   ├── markdown.ts              # remark pipeline for rendering loaded markdown
    │   │   ├── cache.ts                 # tiny in-isolate TTL cache (parity with current API)
    │   │   └── og.ts                    # OG image helpers
    │   ├── prompts/                     # imported via Vite ?raw — copied from ../prompts at build
    │   ├── layouts/
    │   │   └── Base.astro               # port of base.html
    │   ├── components/
    │   │   ├── Dilemma.astro
    │   │   ├── Judgement.astro
    │   │   ├── Badge.astro
    │   │   └── ResearchCard.astro
    │   └── pages/
    │       ├── index.astro              # /
    │       ├── dilemmas/
    │       │   ├── index.astro          # /dilemmas (note: existing is /dilemmas — already plural)
    │       │   └── [id].astro           # /dilemma/{id} — keep singular at /dilemma/[id].astro
    │       ├── dilemma/
    │       │   └── [id].astro
    │       ├── judgements/
    │       │   └── index.astro
    │       ├── judgement/
    │       │   └── [id].astro
    │       ├── research/
    │       │   ├── index.astro          # /research
    │       │   ├── guide.astro          # /research/guide
    │       │   ├── [slug].astro         # /research/{slug}
    │       │   └── [slug]/download.ts   # /research/{slug}/download
    │       └── api/
    │           ├── dilemmas.ts                  # GET protected + GET public variant
    │           ├── dilemma/[id].ts
    │           ├── collections/[name]/dilemmas.ts
    │           ├── stats.ts
    │           ├── generate.ts                  # POST — LLM
    │           ├── judgements.ts                # POST submit human judgements
    │           ├── judgements/[participantId].ts # GET
    │           ├── participants/[pid]/demographics.ts # POST
    │           ├── values/
    │           │   ├── generate.ts              # POST — LLM
    │           │   ├── [pid].ts                 # GET
    │           │   ├── [pid]/history.ts         # GET
    │           │   ├── update.ts                # POST
    │           │   └── restore.ts               # POST
    │           └── alignment/
    │               ├── test.ts                  # POST — LLM
    │               └── [pid].ts                 # GET
    └── README.md
```

### Why a single repo

- Schema lives in one place. The Python `DilemmaDB`/`JudgementDB` SQLModels and the TS Drizzle schema must agree. Catching drift via a single repo (CI runs `drizzle-kit pull` against a shadow DB and diffs) is much easier than coordinating two repos.
- `research/` and `prompts/` are referenced by both halves; no cross-repo symlinks or submodules.
- Deploys stay independent: `wrangler deploy` only fires when `web/**` changes (CI path filter).

---

## 4. Phased Migration

We work bottom-up. Every phase ends in a runnable state on `research-next.values.md`.

### Phase 0 — Scaffold (0.5 day)

- [ ] `cd web && npm create astro@latest -- --template minimal --typescript strict --no-git --no-install` then `npm install`
- [ ] Add `@astrojs/cloudflare`, `astro` (v6+), `drizzle-orm`, `drizzle-kit`, `@neondatabase/serverless`, `zod`, `zod-to-json-schema`, `marked` (or `remark` pipeline)
- [ ] `wrangler.jsonc` with `assets.binding = "ASSETS"`, `compatibility_date`, `compatibility_flags: ["nodejs_compat"]`, `limits.cpu_ms = 300000`, `routes` left empty for now
- [ ] `astro.config.mjs`: `output: 'server'`, `adapter: cloudflare({ imageService: 'compile' })`
- [ ] Reserve `research-next.values.md` as Custom Domain via `wrangler deploy` of a hello-world Worker
- [ ] Wire `wrangler secret put` for `OPENROUTER_API_KEY`, `DATABASE_URL`, `INTERNAL_API_KEY` (the latter == current Fly `API_KEY`)
- [ ] `.dev.vars` populated for local dev (gitignored)

**Exit:** `https://research-next.values.md/` returns "hello world" from the Worker.

### Phase 1 — Drizzle schema + DB connectivity (0.5 day)

- [ ] `drizzle.config.ts` targets `process.env.DATABASE_URL` and writes to `web/src/db/schema.ts`
- [ ] `npx drizzle-kit pull` against the existing Neon DB
- [ ] Hand-edit `schema.ts` to swap `text('data')`, `text('tags_json')`, `text('structured_json')` for `jsonText<T>('...')` (custom type — see §5.3)
- [ ] Diff resulting schema against `src/dilemmas/models/db.py` — confirm fields, types, indexes match
- [ ] `web/src/db/client.ts` exports a `getDb(env)` factory that constructs Drizzle per-request
- [ ] One-shot smoke API route `GET /api/_dbping` that runs `SELECT count(*) FROM dilemmas` and returns JSON

**Exit:** `curl https://research-next.values.md/api/_dbping` returns `{"dilemmas_count": N}` matching production.

### Phase 2 — Base layout + research site (1 day)

This is the highest-value, lowest-risk part to land first because the research pages get the most external linking.

- [ ] Port `base.html` → `src/layouts/Base.astro` (the CSS goes inline in the layout, like today). Slot for `<title>`, OG meta, page content.
- [ ] Copy `src/dilemmas/api/static/*` → `web/public/static/` (favicons, logo).
- [ ] `prebuild` script: copy `../research/*/figures/` → `public/research-static/{slug}/figures/` and `../research/*/*.png` similarly. Idempotent.
- [ ] `src/content.config.ts`: define `research` collection via `glob({ pattern: '*/findings.md', base: '../../research' })` with a Zod schema for the frontmatter (title, date, status, summary, key_finding, research_question, models, tags, abstract, og_image, og_image_alt, experiment_id, data: { dilemmas, judgements, conditions }, ...).
- [ ] `src/pages/research/index.astro` — list all entries sorted by date desc. Replaces `research_index.html`. **`export const prerender = true`**.
- [ ] `src/pages/research/[slug].astro` — render via `render(entry)`. Replaces `research_detail.html`. **`export const prerender = true`** + `getStaticPaths()`. Must not import `cloudflare:*` modules (see §7.2).
- [ ] `src/pages/research/guide.astro` — port of `research_guide.html`. Loads `research/GUIDE.md` similarly (separate collection or single-file load). **`export const prerender = true`**.
- [ ] Markdown image-path rewrite: a small remark plugin (or `astro:content`'s `transform`) that rewrites `figures/x.png` → `/research-static/{slug}/figures/x.png` so existing markdown stays GitHub-readable.
- [ ] `/research/{slug}/download` — endpoint that streams a zip of the experiment folder. See §6.3.

**Exit:** All research pages render at `https://research-next.values.md/research/...` with images, identical look to production.

### Phase 3 — DB-backed read pages (0.5 day)

- [ ] `/` index page (`index.astro`) — homepage; what's currently at root in the FastAPI app
- [ ] `/dilemmas` list page with filter UI — port of `index.html` template
- [ ] `/dilemma/[id]` — port of `dilemma.html`
- [ ] `/judgements` list — port of `judgements.html`
- [ ] `/judgement/[id]` — port of `judgement.html`
- [ ] Query helpers in `web/src/db/queries.ts` with Drizzle queries matching the FastAPI ones (filtering by difficulty, tags, collection, batch_id, search)
- [ ] **Per-page `Cache-Control` headers** following the TTL table in §7.4. `/dilemma/[id]` and `/judgement/[id]` get 24h cache (append-only). List pages get 1–5 min.

**Exit:** Lists and detail pages render with real data and match the production look. Hitting the same URL twice in quick succession shows cache HIT on the second request (visible in `wrangler tail` / browser dev tools `cf-cache-status`).

### Phase 4 — JSON read API (0.5 day)

Port these as plain Astro endpoint files in `src/pages/api/*`:

- [ ] `GET /api/dilemmas` (protected — needs API key)
- [ ] `GET /api/dilemma/[id]` (public)
- [ ] `GET /api/collections/[name]/dilemmas` (cached)
- [ ] `GET /api/stats` (protected)
- [ ] `GET /api/judgements/[participantId]` (protected)
- [ ] `GET /api/values/[pid]` (protected)
- [ ] `GET /api/values/[pid]/history` (protected)
- [ ] `GET /api/alignment/[pid]` (protected)

All return the same JSON shapes as today (Zod schemas in `web/src/lib/contracts.ts` mirror existing Pydantic response models so consumers don't break). Apply the `Cache-Control` TTLs from §7.4 — read endpoints get 5-min to 24-h edge caching depending on volatility.

**Exit:** Snapshot tests: hit the new endpoint and the old prod endpoint for the same inputs; diff. Expected drift only on timestamps. `cf-cache-status: HIT` on warm requests to read endpoints.

### Phase 5 — JSON write API (1 day)

- [ ] `POST /api/judgements` (submit batch of human judgements; computes `variation_key` via MD5 to match Python)
- [ ] `POST /api/participants/[pid]/demographics`
- [ ] `POST /api/values/update`
- [ ] `POST /api/values/restore`

All protected with `X-API-Key` middleware. Validate input with Zod; write with Drizzle. Mirror the existing JSON storage format exactly — store `data` as `JSON.stringify(domainObject)` so Python can still read it through `Dilemma.model_validate_json` / `Judgement.model_validate_json`. Set `Cache-Control: no-store` on all write responses; trigger any necessary cache purges per §7.6 (e.g., `POST /api/generate` purges `/api/dilemmas` and `/api/stats`).

**Exit:** End-to-end test: from a test client, submit a judgement batch via the new endpoint, then read it back from the FastAPI prod endpoint. Should be byte-identical.

### Phase 6 — LLM API (1.5 days)

The three live LLM endpoints:

1. `POST /api/generate` — generate a new dilemma. Single OpenRouter call with structured output (the Dilemma schema). Save to DB.
2. `POST /api/values/generate` — generate a VALUES.md for a participant from their judgements. Single OpenRouter call with **plain string** output (no JSON wrapper; matches existing implementation in `services/values_generator.py`). Save markdown to `values_md` table + append history entry to `values_md_history`.
3. `POST /api/alignment/test` — test an AI judge against a participant's values. Possibly multiple LLM calls. See `services/alignment.py`.

For each:
- Bundle the relevant prompt(s) from `prompts/` via Vite `?raw` imports (compile time) — they get inlined into the Worker bundle.
- Use `zod-to-json-schema` to derive the OpenAI/OpenRouter JSON-schema response format from a Zod definition.
- Bare `fetch` to OpenRouter's `/v1/chat/completions`. No SDK.
- Set `limits.cpu_ms = 300000` in `wrangler.jsonc` to allow long calls. `fetch()` wait doesn't count toward CPU time; we mainly need this for streaming/parsing safety margin.

**Special case — `/api/generate` uses two-step generation** (concrete → variable extraction, see CLAUDE.md §11). That's two LLM calls, the second of which is on Gemini 2.5 Flash. Need to faithfully port the `variablize_dilemma()` flow.

**Exit:** Each LLM endpoint returns successfully and writes the same DB rows the Python version would.

### Phase 7 — Cutover (0.5 day)

See §13. DNS flip + Fly decommission.

---

## 5. Database Migration Details

### 5.1 Driver choice

Start with `drizzle-orm/neon-http`:

```ts
// web/src/db/client.ts
import { drizzle } from 'drizzle-orm/neon-http';
import { neon } from '@neondatabase/serverless';
import * as schema from './schema';

export function getDb(env: { DATABASE_URL: string }) {
  return drizzle(neon(env.DATABASE_URL), { schema });
}
```

The existing Neon URL (`postgresql://...?sslmode=require&channel_binding=require`) works as-is for `@neondatabase/serverless`. No URL rewriting needed (unlike the asyncpg dance in `src/dilemmas/db/database.py`).

### 5.2 Schema introspection

```bash
cd web
# put DATABASE_URL in .env (or .dev.vars + shell export)
npx drizzle-kit pull
```

Output: `web/src/db/schema.ts`. Expect to hand-edit:
- `data TEXT` columns → swap `text('data')` for `jsonText<DilemmaData>('data')`
- `tags_json TEXT` → `jsonText<string[]>('tags_json')`
- `structured_json TEXT` → `jsonText<ValuesMarkdown>('structured_json')`
- Verify `timestamp(..., { withTimezone: false })` matches the existing TIMESTAMP WITHOUT TIME ZONE columns (it should after introspection — confirm)
- Check `version` column doesn't get treated as SQL keyword `VERSION`

Diff the result against `src/dilemmas/models/db.py`:

```bash
# from repo root
diff <(uv run python -c "from dilemmas.models.db import *; import json; print(json.dumps({t.name: {c.name: str(c.type) for c in t.columns} for t in [DilemmaDB.__table__, JudgementDB.__table__, ValuesMdDB.__table__, ValuesMdHistoryDB.__table__]}, indent=2))") \
     <(grep -E "pgTable|\\.\\w+\\('" web/src/db/schema.ts)
```

### 5.3 The `jsonText` custom type

The Python side stores JSON as `TEXT` (not `JSONB`). We must preserve this — both for compat with the existing rows and so Python's `Dilemma.model_validate_json(row.data)` keeps working.

```ts
// web/src/db/json-text.ts
import { customType } from 'drizzle-orm/pg-core';

export const jsonText = <T>(name: string) =>
  customType<{ data: T; driverData: string }>({
    dataType() { return 'text'; },
    toDriver(value: T): string { return JSON.stringify(value); },
    fromDriver(value: string): T { return JSON.parse(value) as T; },
  })(name);
```

**Caveats** (per Drizzle docs / issue #818):
- Don't use `.default(...)` on customType columns — set defaults in app code.
- `JSON.stringify` emits raw UTF-8; Python's `json.dumps(..., ensure_ascii=True)` (default) emits `\uXXXX`. Both round-trip, but byte-equal comparisons across the two languages will differ. Never use raw `=` on the `data` column for dedup — always parse first. (We don't do this today; just flag it.)

### 5.4 Migration handover

One-time, at cutover:

1. The existing `__drizzle_migrations` table doesn't exist yet. `drizzle-kit migrate` will create it on first run.
2. Generate a baseline migration from current schema:
   ```bash
   cd web && npx drizzle-kit generate --name=baseline
   ```
3. Mark the baseline as applied without running it (DB is already in that state):
   ```sql
   -- run against Neon (psql or Neon SQL editor)
   CREATE TABLE IF NOT EXISTS __drizzle_migrations (
     id SERIAL PRIMARY KEY,
     hash TEXT NOT NULL,
     created_at BIGINT
   );
   -- look up the baseline hash from drizzle/meta/_journal.json
   INSERT INTO __drizzle_migrations (hash, created_at) VALUES ('<HASH>', <UNIX_MS>);
   ```
4. Freeze Alembic: don't add new revisions. Keep `alembic/versions/` for historical reference. Add a note in `alembic/README` pointing to this doc.

Future schema changes:
```bash
cd web
# edit src/db/schema.ts
npx drizzle-kit generate --name=add_foo_column
# review the SQL under drizzle/
npx drizzle-kit migrate   # local apply
git commit ...
# CI runs migrate against PROD_DATABASE_URL before wrangler deploy
```

Python code that reads new columns: update `models/db.py` by hand. Python won't generate migrations anymore.

### 5.5 Schema-drift CI guard

A nightly GitHub Action runs `drizzle-kit pull` against a Neon branch (or against prod read-only) and diffs the result against the committed `schema.ts`. Fail loudly if they diverge — catches anyone running raw SQL on the DB.

---

## 6. Research Folder Pipeline

The most subtle piece. Goal: keep `research/` exactly as it is today (the canonical location, edited as-is, used by Python analysis scripts), and have Astro render it.

### 6.1 Loading

Astro 6 content collections support `glob({ base: '...' })` with a path outside the project root.

```ts
// web/src/content.config.ts
import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const research = defineCollection({
  loader: glob({ pattern: '*/findings.md', base: '../research' }),
  schema: z.object({
    title: z.string(),
    date: z.string(),                       // ISO YYYY-MM-DD
    status: z.enum(['completed', 'in_progress']),
    experiment_id: z.string().optional(),
    version: z.string().optional(),
    og_image: z.string().optional(),
    og_image_alt: z.string().optional(),
    abstract: z.string().optional(),
    key_finding: z.string().optional(),
    research_question: z.string().optional(),
    hypothesis: z.string().optional(),
    models: z.array(z.string()).default([]),
    tags: z.array(z.string()).default([]),
    data: z.object({
      dilemmas: z.number().optional(),
      judgements: z.number().optional(),
      conditions: z.number().optional(),
    }).partial().optional(),
  }),
});

export const collections = { research };
```

Slug derivation: Astro uses the directory name from the glob match (`2025-11-27-when-agents-act`), which matches `research_parser.py`'s `slug` exactly.

### 6.2 Image handling

Markdown bodies reference `figures/x.png` (works on GitHub). For the web, we need them served from `/research-static/{slug}/figures/x.png` — same convention as today.

Two-prong approach:

**(a) Copy figures to `public/` at build time.** A `prebuild` script:

```ts
// web/scripts/copy-research-figures.ts
import { cp, readdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join } from 'node:path';

const SRC = '../research';
const DST = 'public/research-static';

for (const entry of await readdir(SRC, { withFileTypes: true })) {
  if (!entry.isDirectory()) continue;
  if (!/^\d{4}-\d{2}-\d{2}-/.test(entry.name)) continue;
  const figures = join(SRC, entry.name, 'figures');
  if (existsSync(figures)) {
    await cp(figures, join(DST, entry.name, 'figures'), { recursive: true });
  }
  // Also copy top-level images at research/{slug}/*.png if any
}
```

Wire `"prebuild": "tsx scripts/copy-research-figures.ts"` in `package.json` so it runs before `astro build` and before `astro dev`.

**(b) Rewrite markdown image paths at render time.** A tiny remark plugin (or just string-replace in a content `transform`) that, for each entry, rewrites `![alt](figures/foo.png)` → `![alt](/research-static/{id}/figures/foo.png)`. Mirrors the existing `render_markdown(experiment_slug=...)` logic.

### 6.3 The `/download` endpoint

`/research/{slug}/download` currently builds a zip of the experiment folder on the fly. In a Worker, we can either:
- **Pre-build zips** at deploy time (one per experiment), drop them in `public/research-static/{slug}.zip`, redirect to that URL.
- **Build at request time** using the `fflate` library (works in Workers, no Node deps).

Pre-built zips are simpler and free to serve. Recommend that.

### 6.4 Build-time vs runtime

The existing Python `research_parser.py` does TTL caching of folder scans + rendered HTML. Astro's content collections do better than that: content is parsed and indexed **at build time**, once per deploy. SSR pages call `getEntry()` which is in-process and microsecond-fast. We can do even better by **prerendering** the research pages outright — see §7.2.

---

## 7. Caching Strategy

The site has a lot of long-tail content (past research write-ups) that essentially never changes after publication, and a moderate amount of DB-backed pages where the data is append-only (a dilemma or judgement, once created, never mutates). The strategy is layered, from cheapest to most-expensive:

1. **Prerender at build time (SSG)** — no DB hit, no Worker invocation cost. Served as a static asset from the edge.
2. **Edge cache (Cloudflare Cache API + `Cache-Control` headers)** — Worker runs once per cache-miss, response is cached at each PoP for the TTL.
3. **In-isolate memory cache** — for very hot paths within a single isolate's lifetime, microsecond hits.
4. **Bypass cache for writes and live LLM calls.**

### 7.1 What hits Neon (and what doesn't)

Reading the route list with caching in mind:

| Route | Hits Neon today? | Hits Neon in TS port? | Caching tier |
|---|---|---|---|
| `/research`, `/research/[slug]`, `/research/guide` | No (markdown only) | **No** | **Prerender (SSG)** |
| `/research/[slug]/download` | No (zip of files) | No | Prerender zip artifacts at build time |
| `/` (homepage) | Maybe (stats?) | Same — if it shows live stats, edge-cache; else prerender | Prerender or 5-min edge cache |
| `/dilemmas` list | Yes | Yes | Edge cache, 5-min |
| `/dilemma/[id]` | Yes | Yes | Edge cache, 24-h (append-only) |
| `/judgements` list | Yes | Yes | Edge cache, 1-min |
| `/judgement/[id]` | Yes | Yes | Edge cache, 24-h (append-only) |
| `GET /api/dilemmas`, `/api/dilemma/[id]`, `/api/collections/[name]/dilemmas` | Yes | Yes | Edge cache, 5-min / 24-h / 1-h |
| `GET /api/stats` | Yes | Yes | Edge cache, 5-min |
| `GET /api/judgements/[pid]`, `/api/values/[pid]`, etc. | Yes | Yes | Edge cache, 60s (per-participant) |
| `POST /api/judgements` etc. | Yes (write) | Yes (write) | **No cache.** Issue targeted purges. |
| `POST /api/generate`, `/values/generate`, `/alignment/test` | Yes + LLM | Yes + LLM | **Never cache.** |

The headline: with this strategy, **the entire research site (the bulk of long-tail traffic) hits Neon zero times**.

### 7.2 Prerendering research pages

Even with `output: 'server'` set globally, Astro lets individual pages opt into prerendering:

```astro
---
// src/pages/research/[slug].astro
export const prerender = true;

export async function getStaticPaths() {
  const all = await getCollection('research');
  return all.map(entry => ({ params: { slug: entry.id }, props: { entry } }));
}

const { entry } = Astro.props;
const { Content } = await render(entry);
---
<Base title={entry.data.title} ogImage={entry.data.og_image}>
  <Content />
</Base>
```

Astro builds one static HTML file per research entry. The Worker handler is never invoked for these URLs — Cloudflare's edge serves them directly from the Workers Assets layer.

**Important constraint** (already mentioned in §1.1): prerendered files must not import from `cloudflare:` modules ([issue #15237](https://github.com/withastro/astro/issues/15237)). Keep research pages free of any DB or env-binding imports — they only use content collections and the markdown renderer, which is fine.

Rebuilding to reflect new research content is a normal deploy. Add a "publish research" workflow: edit `research/2025-XX-YY-foo/findings.md`, commit, push → CI redeploys → new entry appears. Old entries stay byte-identical.

### 7.3 Edge cache for DB-backed pages

For pages that need real-time data but tolerate brief staleness, set `Cache-Control` headers and rely on Cloudflare's edge cache. The Cache API gives finer control when needed.

**Pattern A — `Cache-Control` only** (simplest, works for both HTML pages and API endpoints):

```astro
---
// src/pages/dilemma/[id].astro
const { id } = Astro.params;
const db = getDb(Astro.locals.runtime.env);
const dilemma = await db.query.dilemmas.findFirst({ where: eq(dilemmas.id, id) });
if (!dilemma) return new Response('Not found', { status: 404 });

Astro.response.headers.set(
  'Cache-Control',
  'public, s-maxage=86400, stale-while-revalidate=604800'
);
---
<Base title={dilemma.title}> ... </Base>
```

CF's edge automatically caches the response. `s-maxage` is the shared-cache TTL; `stale-while-revalidate` lets the edge serve a stale copy while it fetches a fresh one in the background.

**Pattern B — explicit Cache API** (when you want to cache more aggressively than the default Vary or skip cookies/headers):

```ts
// src/pages/api/stats.ts
export const GET: APIRoute = async ({ request, locals }) => {
  const cache = caches.default;
  const cacheKey = new Request(new URL(request.url).toString(), request);
  const hit = await cache.match(cacheKey);
  if (hit) return hit;

  const db = getDb(locals.runtime.env);
  const stats = await computeStats(db);
  const res = new Response(JSON.stringify(stats), {
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'public, s-maxage=300, stale-while-revalidate=3600',
    },
  });
  // fire-and-forget cache write
  Astro.locals.runtime.ctx.waitUntil(cache.put(cacheKey, res.clone()));
  return res;
};
```

### 7.4 Recommended TTLs

| Resource class | `s-maxage` | `stale-while-revalidate` | Rationale |
|---|---|---|---|
| Individual immutable record (`/dilemma/[id]`, `/judgement/[id]`) | 86400 (24h) | 604800 (7d) | Append-only; will only change if we explicitly republish |
| Long lists that grow append-only (`/dilemmas`, `/api/dilemmas`) | 300 (5min) | 3600 (1h) | New entries appear gradually; 5-min freshness is fine |
| `/judgements` (humans submit during sessions) | 60 (1min) | 600 (10m) | More write-active than dilemmas |
| `/api/stats` | 300 | 3600 | Counts change slowly |
| Per-participant data (`/api/judgements/[pid]`, `/api/values/[pid]`, `/api/values/[pid]/history`, `/api/alignment/[pid]`) | **0 (no-store)** | — | Next.js issues read-after-write here (submit → generate → fetch, or edit → fetch). Edge caching causes stale 404 / stale markdown. See Appendix C.4. |
| `/api/collections/[name]/dilemmas` (test set fetch) | 3600 (1h) | 86400 (1d) | Test collections are essentially frozen |
| `/research/*` | n/a — **prerendered** | n/a | Served as static assets |
| POST write endpoints | `no-store` | — | Never cache |
| LLM endpoints | `no-store` | — | Never cache |

### 7.5 In-isolate memory cache

For hot paths within a single isolate's lifetime (e.g., the same isolate handling 50 requests in a minute), a small in-memory TTL map avoids even the Cache API round-trip:

```ts
// web/src/lib/cache.ts
type Entry<T> = { expiresAt: number; value: T };
const store = new Map<string, Entry<unknown>>();

export async function memo<T>(key: string, ttlMs: number, loader: () => Promise<T>): Promise<T> {
  const now = Date.now();
  const hit = store.get(key) as Entry<T> | undefined;
  if (hit && hit.expiresAt > now) return hit.value;
  const value = await loader();
  store.set(key, { expiresAt: now + ttlMs, value });
  return value;
}
```

Use sparingly — it's stale on isolate boot, and isolates can be killed any time. Best for things like "the list of collection names" that change at most once per deploy. Always compose *behind* the edge cache: edge cache catches the bulk, in-isolate memoization catches the long tail of cache-miss requests that land on the same isolate.

### 7.6 Cache busting on writes

Write endpoints (`POST /api/judgements`, `POST /api/values/update`, `POST /api/generate`) must invalidate related cached responses. Options, in increasing complexity:

1. **Just wait out the TTL.** With 5-min TTLs on lists and 1-h on collections, fresh data appears within minutes. For most cases this is good enough.
2. **Programmatic purge via Cloudflare API.** From the Worker, call `https://api.cloudflare.com/client/v4/zones/{zone}/purge_cache` with a list of URLs to purge. Needs a `CF_API_TOKEN` secret. Use for cases where stale lists are unacceptable.
3. **Cache by tags.** Cloudflare Enterprise feature; not justified for our scale.

Recommend option 1 by default, option 2 only on `POST /api/generate` (because newly-generated dilemmas should appear in the list within seconds for the admin who triggered the call). Purge `/api/dilemmas` and `/api/stats` after a successful generate.

### 7.7 Cache keys and `Vary`

For protected endpoints (which take an `X-API-Key` header), the default Cache API key is the URL only — which would mean all callers share the cached response. That's fine and even desirable: the response is the same regardless of who made the call. But:

- Do **not** cache 401/403 responses. Set `Cache-Control: no-store` on auth failures.
- For per-participant endpoints (`/api/judgements/[pid]`), the participant ID is in the URL path, so URL-keyed caching is already participant-scoped. Good.
- Avoid putting query strings that shouldn't fragment the cache (e.g., tracking params). Astro/Workers cache by full URL including query string by default; if needed, strip query params before computing the cache key.

### 7.8 What this gets us

A back-of-envelope estimate, assuming modest traffic:

- 1000 page views/day of `/research/*` → **0 DB hits** (SSG)
- 200 page views/day of `/dilemmas` + `/dilemma/*` → ~50 DB hits/day (after edge cache catches most)
- 100 page views/day of `/judgements` + `/judgement/*` → ~30 DB hits/day
- 10 LLM API calls/day → 10 DB writes
- `/api/stats` hit ~once/min by external clients → 12 DB hits/hour (5-min cache)

Comfortably inside Neon's free tier — and inside the Workers free tier on requests (100k/day), though we'll likely be on the $5 Paid plan anyway for the CPU ceiling.

---

## 8. LLM Endpoints — Porting Notes

### 7.1 OpenRouter client

```ts
// web/src/lib/openrouter.ts
import { z } from 'zod';
import { zodToJsonSchema } from 'zod-to-json-schema';

export async function chatJson<T extends z.ZodTypeAny>(opts: {
  apiKey: string;
  model: string;
  system: string;
  user: string;
  schema: T;
  schemaName: string;
  temperature?: number;
  maxTokens?: number;
}): Promise<z.infer<T>> {
  const res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${opts.apiKey}`,
      'Content-Type': 'application/json',
      'HTTP-Referer': 'https://research.values.md',
      'X-Title': 'VALUES.md research',
    },
    body: JSON.stringify({
      model: opts.model,
      messages: [
        { role: 'system', content: opts.system },
        { role: 'user', content: opts.user },
      ],
      temperature: opts.temperature ?? 1.0,
      max_tokens: opts.maxTokens ?? 4000,
      response_format: {
        type: 'json_schema',
        json_schema: {
          name: opts.schemaName,
          strict: true,
          schema: zodToJsonSchema(opts.schema, { target: 'openApi3' }),
        },
      },
    }),
  });
  if (!res.ok) throw new Error(`OpenRouter ${res.status}: ${await res.text()}`);
  const body = await res.json() as { choices: { message: { content: string } }[] };
  const content = body.choices[0].message.content;
  return opts.schema.parse(JSON.parse(content));
}

export async function chatText(opts: {
  apiKey: string;
  model: string;
  system: string;
  user: string;
  temperature?: number;
  maxTokens?: number;
}): Promise<string> {
  // similar, but no response_format; returns body.choices[0].message.content
}
```

### 7.2 `/api/generate`

Pseudocode:
```ts
// web/src/pages/api/generate.ts
import type { APIRoute } from 'astro';
import { DilemmaSchema, VariableExtractionSchema } from '@/lib/contracts';
import { chatJson } from '@/lib/openrouter';
import generationSystemPrompt from '@/prompts/generation/system.md?raw';
import extractionPrompt from '@/prompts/variation/extract_variables.md?raw';
import { getDb } from '@/db/client';
import { dilemmas } from '@/db/schema';

export const POST: APIRoute = async ({ request, locals }) => {
  // 1. verify API key
  // 2. parse + validate body
  // 3. seed selection (port src/dilemmas/services/seeds.py — small, pure logic)
  // 4. chatJson with DilemmaSchema → concrete dilemma
  // 5. if add_variables: chatJson with VariableExtractionSchema → variable-ize
  // 6. assemble final Dilemma, save via Drizzle (jsonText handles serialization)
  // 7. return JSON
};
```

`seeds.py` and the prompt templating logic in `services/generator.py` are pure logic — port directly to TS, ~200 lines.

### 7.3 `/api/values/generate`

Existing Python returns plain markdown (no JSON wrapper). Mirror exactly. Use `chatText`, not `chatJson`. Same min-judgements gate (5). Save to `values_md` and append to `values_md_history`.

### 7.4 `/api/alignment/test`

Larger port. `services/alignment.py` is 225 lines and does multiple LLM calls (running an AI judge against the participant's values). Plan: read the file, port one function at a time, test each independently against fixtures.

### 7.5 Long-running calls

`limits.cpu_ms = 300000` in `wrangler.jsonc` gives 5 minutes. `fetch()` wait doesn't count toward CPU. A 30-40s OpenRouter call is well within bounds. Stream the response if we want progressive output later (Astro endpoints can return `ReadableStream` directly).

### 7.6 Gemini 3 direct API

The Python code routes `google/gemini-3-*` to Google's direct API (for `thought_signature` / function calling). The TS port can route those same model IDs to `https://generativelanguage.googleapis.com/v1beta/...` when needed. Today only the `variablize_dilemma` step uses Gemini and it's Gemini 2.5 Flash via OpenRouter — Gemini 3 routing is a follow-up, not blocking.

---

## 9. Template / Page Port Map

| Current Jinja template | New Astro file | Notes |
|---|---|---|
| `base.html` | `src/layouts/Base.astro` | CSS stays inline. `<slot />` for content. Props for title + OG meta. |
| `index.html` | `src/pages/dilemmas/index.astro` (or root) | Dilemma listing + filters. |
| `dilemma.html` | `src/pages/dilemma/[id].astro` | Single dilemma view. |
| `judgements.html` | `src/pages/judgements/index.astro` | Listing. |
| `judgement.html` | `src/pages/judgement/[id].astro` | Detail. |
| `research_index.html` | `src/pages/research/index.astro` | `getCollection('research')`, sort by date. |
| `research_guide.html` | `src/pages/research/guide.astro` | Static markdown render. |
| `research_detail.html` | `src/pages/research/[slug].astro` | `getEntry('research', slug)` + `render()`. |
| `404.html` | `src/pages/404.astro` | Astro picks this up automatically. |

Confirm by re-reading `src/dilemmas/api/templates/*.html` once before each port — small details (badge classes, print CSS, OG meta blocks) need to come across exactly.

---

## 10. Auth, Secrets, Env Vars

### Secrets (per-Worker)

```bash
cd web
wrangler secret put OPENROUTER_API_KEY
wrangler secret put DATABASE_URL          # full Neon connection string
wrangler secret put INTERNAL_API_KEY      # current Fly API_KEY
# Optional, future:
wrangler secret put GOOGLE_API_KEY        # if we add Gemini 3 routing
```

### Local dev

`web/.dev.vars`:
```
OPENROUTER_API_KEY=sk-or-...
DATABASE_URL=postgresql://...?sslmode=require
INTERNAL_API_KEY=...
```

`wrangler dev` and `astro dev` (which uses workerd under the hood with the CF adapter) both load this automatically.

### Auth middleware

```ts
// web/src/lib/auth.ts
export function requireApiKey(req: Request, env: { INTERNAL_API_KEY: string }) {
  const key = req.headers.get('x-api-key');
  if (!key || key !== env.INTERNAL_API_KEY) {
    return new Response('Unauthorized', { status: 401 });
  }
  return null; // ok
}
```

Wrap each protected endpoint:
```ts
export const GET: APIRoute = async ({ request, locals }) => {
  const env = locals.runtime.env;
  const unauthorized = requireApiKey(request, env);
  if (unauthorized) return unauthorized;
  // ... handler
};
```

(Or write an Astro middleware that runs for `/api/**` and short-circuits.)

---

## 11. Local Dev Workflow

```bash
cd web
npm install
npm run prebuild         # copies research figures into public/
npm run dev              # astro dev on workerd (real CF runtime)
# in another terminal:
npx drizzle-kit studio   # browse DB
```

`npm test` (vitest) runs against a Neon **branch** DB. Each test gets a fresh branch via `neon-branch` (or we use a local Postgres in Docker for unit tests + a real Neon branch for integration tests).

Python side keeps working identically — `uv run python scripts/serve.py` still serves the FastAPI app locally for comparison during the transition.

---

## 12. CI / Deployment

### GitHub Actions: `.github/workflows/web-deploy.yml`

```yaml
name: Deploy web
on:
  push:
    branches: [main]
    paths: ['web/**', '.github/workflows/web-deploy.yml']
  pull_request:
    paths: ['web/**']
jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions: { contents: read, deployments: write }
    defaults: { run: { working-directory: web } }
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-node@v5
        with: { node-version: '22', cache: 'npm', cache-dependency-path: 'web/package-lock.json' }
      - run: npm ci
      - run: npm run prebuild
      - run: npm run typecheck
      - name: Apply DB migrations (prod only)
        if: github.ref == 'refs/heads/main'
        env: { DATABASE_URL: ${{ secrets.PROD_DATABASE_URL }} }
        run: npx drizzle-kit migrate
      - name: Deploy
        uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          workingDirectory: web
          command: ${{ github.ref == 'refs/heads/main' && 'deploy' || 'versions upload' }}
```

- Main pushes deploy to `research-next.values.md` (and later, after cutover, to `research.values.md`).
- PRs run `wrangler versions upload` for a unique preview URL.
- DB migrations run before `wrangler deploy`, so schema is always at-or-ahead of code.
- Repo secrets needed: `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `PROD_DATABASE_URL`.

### Schema-drift nightly

Separate workflow on cron that runs `drizzle-kit pull` against prod (read-only diff) and opens an issue if `web/src/db/schema.ts` differs.

---

## 13. Cutover Plan

### Pre-cutover checklist

- [ ] All 25 routes ported and verified at `research-next.values.md`
- [ ] Snapshot-test the JSON API: hit every GET endpoint on both old and new with the same inputs; diff. Expected drift only on `created_at` formatting.
- [ ] Submit a test batch to `/api/judgements` on the new endpoint, verify it appears via the old endpoint, and via the FastAPI web UI.
- [ ] Generate a test dilemma via `/api/generate`, verify schema matches Python `Dilemma.model_validate_json` round-trip.
- [ ] Hit `/research/2025-11-27-when-agents-act` and other research pages; eyeball-compare against prod.
- [ ] Load test: 100 concurrent requests to read endpoints. Confirm no 5xx, latency p50 < 200ms.
- [ ] Confirm `wrangler tail` log streaming works.
- [ ] **Next.js client contract test:** Point a local Next.js dev server at `RESEARCH_API_URL=https://research-next.values.md`, run the full user flow end-to-end (assessment → submit → values/generate → dashboard → edit → restore → alignment). No 4xx/5xx, no shape errors. See Appendix C.6.

### Flip

1. In Cloudflare dashboard (or via `wrangler.jsonc` + redeploy): change the Custom Domain on the Worker from `research-next.values.md` to `research.values.md`. The old `research-next` domain is also detached.
2. Cloudflare will replace the existing `research.values.md` DNS record (currently pointing to Fly) with the Worker origin. Cert auto-issues.
3. Verify in incognito: `https://research.values.md` is served by the Worker (`server` response header or a temporary `X-Origin: cf-worker` debug header on the new app).
4. Watch logs (`wrangler tail`) and metrics dashboard for 30 minutes.

### Decommission Fly

After 24-48h of stable operation:
- `fly scale count 0 --yes` (stop machines first)
- `fly apps destroy values-md-dilemmas` (irreversible)
- Remove `fly.toml`, `Dockerfile`, `entrypoint.sh` from the repo
- Remove `aiosqlite`/`asyncpg` from `pyproject.toml` only if no Python script still needs them. (Keep them — sync_to_prod.py uses asyncpg.)

### Update external references

- `CLAUDE.md` — update deployment section to reference Cloudflare not Fly
- `DEPLOYMENT.md` — rewrite for Cloudflare
- `README.md` — fix any links to `values-md-dilemmas.fly.dev`

---

## 14. What We Do NOT Migrate

- **Python research scripts (`scripts/*.py`)** — they keep running locally / on a dev box, writing to the same Neon DB. Not on the web path.
- **`src/dilemmas/services/generator.py`, `judge.py`, `validator.py`, `alignment.py` etc.** — they continue to exist for batch generation and experiments. The TS port only covers the 3 *live web* LLM endpoints, not the whole library.
- **Alembic** — frozen. Kept for git history only.
- **`pydantic-ai`** — not used in TS. Python keeps it for batch work.
- **`scripts/serve.py`, `scripts/explore_db.py`** — local-only tools, unchanged.

---

## 15. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Drizzle schema drift from Python `models/db.py` | M | M | Nightly schema-drift CI check; Drizzle is the source of truth post-cutover; Python `from_domain`/`to_domain` stays as the validation layer. |
| Astro adapter bug in hybrid mode | L | H | Already avoided by `output: 'server'` (SSR-only). |
| LLM call exceeds Workers limits | L | M | Already analyzed: paid plan 5min CPU, unbounded fetch wait. Single OpenRouter call is well within. |
| OpenRouter response not strict JSON | M | M | `zod-to-json-schema` + `strict: true`; on parse failure, log + return 502; consider one retry. |
| Markdown rendering differs from `python-markdown` | M | L | Pick `marked` with GFM extensions; visual diff each research page against prod. Manual sign-off per page. |
| Date/time bytes differ between Python and TS JSON | L | L | Both serialize ISO 8601. Pydantic uses `.isoformat()`. Confirm TS uses `toISOString()`. Spot-check during snapshot tests. |
| `json.dumps` vs `JSON.stringify` byte difference | L | L | Both sides round-trip cleanly via parsing; never compare raw strings for dedup. |
| Cold-start latency higher than Fly's always-on | L | L | SSR cold start <50ms on Workers; minimal bundle. Acceptable. |
| External API consumers break on subtle JSON shape changes | L | H | Zod contracts mirror Pydantic response models field-for-field; snapshot-test before cutover. |
| Next.js client (`values.md`) breaks on missing/renamed field | L | **H** | The Next.js app at `~/dev/values.md/next/` calls 10 endpoints with very specific expected fields. See Appendix C for the full contract surface. Pre-cutover: run Next.js test suite against `research-next.values.md`, plus manual end-to-end UX test. |
| Per-participant edge caching causes stale read-after-write | M | M | Set `Cache-Control: private, max-age=0, no-store` on `/api/values/{pid}`, `/api/alignment/{pid}`, `/api/judgements/{pid}` — these endpoints are per-user and Next.js issues read-after-write on them. See §7 / Appendix C.4. |
| Forgot to migrate one route | L | M | Track in §9 table; check that no Fly logs show traffic on unimplemented routes during soak. |

---

## 16. Rollback Plan

For the first 7 days after cutover:

1. Keep the Fly app running (not destroyed) but with `min_machines_running = 0` and `auto_start_machines = true`, so it can come back up on demand without burning $.
2. To roll back: change the `research.values.md` Custom Domain back to point at the Fly origin (DNS-level via Cloudflare dashboard). Propagation is near-instant within Cloudflare.
3. Investigate the issue on the new Worker (`wrangler tail`, version history), redeploy fixed version to `research-next.values.md`, re-verify, re-flip.

After 7 days of stable operation: `fly apps destroy`.

---

## 17. Out-of-Scope / Follow-ups

Things we explicitly do *not* do as part of this migration, even though they'd be nice:

- Swap to Hyperdrive + `postgres-js` — defer; revisit if p95 latency >300ms.
- Move research markdown to a CMS — keep it as Git-versioned markdown.
- Add D1 (CF SQLite) — Neon is fine.
- React/Solid islands for interactivity — only add if a feature demands it.
- Sitemap, RSS, view transitions, image optimization for figures — easy add-ons in Astro; defer until baseline is stable.
- Replace OpenRouter with the Vercel AI SDK or similar — no need.
- Rewrite `services/generator.py` etc. in TS — those are batch tools, leave in Python.
- Server-side analytics (CF Web Analytics is fine for now).

---

## 18. Effort Estimate

| Phase | Estimate |
|---|---|
| 0 — Scaffold | 0.5 day |
| 1 — Drizzle schema + DB ping | 0.5 day |
| 2 — Base layout + research pages | 1.0 day |
| 3 — DB-backed read pages | 0.5 day |
| 4 — JSON read API | 0.5 day |
| 5 — JSON write API | 1.0 day |
| 6 — LLM API endpoints | 1.5 days |
| 7 — Cutover | 0.5 day |
| **Total** | **~6 days focused work** |

Plus 1–2 weeks of low-touch soak time at `research-next.values.md` before the DNS flip.

---

## Appendix A — Key Source Citations

- [Astro Cloudflare adapter](https://docs.astro.build/en/guides/integrations-guide/cloudflare/)
- [Cloudflare Workers framework guide: Astro](https://developers.cloudflare.com/workers/framework-guides/web-apps/astro/)
- [Astro Content Collections](https://docs.astro.build/en/guides/content-collections/)
- [Astro Issue #15237 (hybrid build break)](https://github.com/withastro/astro/issues/15237)
- [Workers Assets binding](https://developers.cloudflare.com/workers/static-assets/binding/)
- [Workers Platform Limits](https://developers.cloudflare.com/workers/platform/limits/)
- [Workers 5-min CPU changelog](https://developers.cloudflare.com/changelog/post/2025-03-25-higher-cpu-limits/)
- [Workers Custom Domains vs Routes](https://developers.cloudflare.com/workers/configuration/routing/)
- [Workers Versions & Deployments](https://developers.cloudflare.com/workers/configuration/versions-and-deployments/)
- [Drizzle — Neon connect](https://orm.drizzle.team/docs/connect-neon)
- [Drizzle — drizzle-kit pull](https://orm.drizzle.team/docs/drizzle-kit-pull)
- [Drizzle — drizzle-kit migrate](https://orm.drizzle.team/docs/drizzle-kit-migrate)
- [Drizzle — Custom types](https://orm.drizzle.team/docs/custom-types)
- [Neon — Use Neon with Cloudflare Workers](https://neon.com/docs/guides/cloudflare-workers)
- [Cloudflare Hyperdrive — Drizzle example](https://developers.cloudflare.com/hyperdrive/examples/connect-to-postgres/postgres-drivers-and-libraries/drizzle-orm/)
- [cloudflare/wrangler-action](https://github.com/cloudflare/wrangler-action)

## Appendix B — Source files to re-read before each phase

- Phase 2 (research site): `src/dilemmas/api/research_parser.py`, `src/dilemmas/api/templates/research_*.html`, `research/*/findings.md` (a couple of representative ones)
- Phase 3 (read pages): `src/dilemmas/api/templates/index.html`, `dilemma.html`, `judgements.html`, `judgement.html`
- Phase 4–5 (API): `src/dilemmas/api/app.py` (lines 657–1700)
- Phase 6 (LLM): `src/dilemmas/services/generator.py`, `services/values_generator.py`, `services/alignment.py`, `llm/openrouter.py`, all of `prompts/`
- Schema mapping: `src/dilemmas/models/db.py`, `models/dilemma.py`, `models/judgement.py`, `models/validation.py`, `models/extraction.py`
- Compatibility contracts (Appendix C): `~/dev/values.md/next/src/lib/research-api.ts`, `~/dev/values.md/next/RESEARCH_API_INTEGRATION.md`, `~/dev/values.md/next/src/app/api/values/{generate,history,update,restore}/route.ts`, `~/dev/values.md/next/src/app/api/alignment/[participant_id]/route.ts`, `~/dev/values.md/next/src/app/api/assessment/submit/route.ts`, `~/dev/values.md/next/src/lib/dilemmas.ts`

---

## Appendix C — Compatibility with the values.md Next.js Client

The Next.js app at `~/dev/values.md/next/` (deployed to `values.md` + `staging.values.md`) is the **primary API consumer** for this service. It's already on Cloudflare (OpenNext on Workers + D1 for user data), and calls the FastAPI server-to-server from Next.js route handlers using `X-API-Key`.

The migration must preserve byte-level response shapes for the endpoints below. If we do that, **the Next.js codebase needs zero changes**.

### C.1 Endpoints the Next.js app calls

| Endpoint | Method | Auth | Caller in `next/` | Body / Response contract |
|---|---|---|---|---|
| `/api/collections/{collection}/dilemmas` | GET | **No** | `src/lib/dilemmas.ts` → `fetchDilemmas('bench-2')` | Returns `Dilemma[]` **directly** (raw array, not wrapped). `cache: 'no-store'` set by client. |
| `/api/judgements` | POST | Yes | `src/lib/research-api.ts` → `submitJudgements()` (used by `app/api/assessment/submit/route.ts`) | Body: `{participant_id, judgements: [{dilemma_id, choice_id, rendered_situation, variable_values, modifier_indices, reasoning?, confidence?, response_time_ms}], demographics?}` |
| `/api/values/generate` | POST | Yes | `generateValuesMd()` (used by `app/api/values/generate/route.ts`) | Body: `{participant_id, model_id?, force_regenerate?}` → Response: `{success, participant_id, values_md?, from_cache, judgement_count, generated_at, model_id, error?}` |
| `/api/values/{participant_id}` | GET | Yes | `getValuesMd()` (used by `dashboard/page.tsx`, `values/[email]/page.tsx`, `auth.ts`, `public/values/[email]/route.ts`) | Returns `{success, participant_id, values_md, generated_at, model_id, judgement_count}` or `404` |
| `/api/values/{participant_id}/history` | GET | Yes | `app/api/values/history/route.ts` (proxy) | Returns version history list (shape: `{participant_id, history: [{id, version, change_type, changed_at, markdown_text, model_id, judgement_count, generated_at}]}` per Python code) |
| `/api/values/update` | POST | Yes | `app/api/values/update/route.ts` (proxy) | Body: `{participant_id, markdown_text}` → Response: `{version, change_type}` |
| `/api/values/restore` | POST | Yes | `app/api/values/restore/route.ts` (proxy) | Body: `{participant_id, version_id}` — note: `version_id` is a STRING (the history row ID), not a version number → Response: `{version, restored_from_version, change_type}` |
| `/api/participants/{participant_id}/demographics` | POST | Yes | `updateParticipantDemographics()` | Body: `{age_range?, gender?, education_level?, country?, professional_background?}` → Response: `{success, participant_id, updated_judgement_count, message?}` |
| `/api/judgements/{participant_id}` | GET | Yes | `app/api/public/values/[email]/route.ts` | Returns `{judgements: [...]}` — wrapped in object, NOT raw array |
| `/api/alignment/{participant_id}` | GET | Yes | `app/api/alignment/[participant_id]/route.ts` (proxy) | Returns `{success, participant_id, alignments: [{model_id, model_name, alignment_score, metrics: {choice_agreement, confidence_similarity, difficulty_similarity, overall_score}, judgements_compared}]}` sorted by `alignment_score` desc |

Other Next.js consumption: `app/page.tsx` has a hard-coded `<a href="https://research.values.md">` link — works post-migration as long as the domain is preserved (it will be).

### C.2 Auth

Single shared secret. Maps:

| Next.js env var (`.dev.vars` / `wrangler secret`) | TS Worker secret |
|---|---|
| `RESEARCH_API_KEY` | `INTERNAL_API_KEY` |
| `RESEARCH_API_URL` (val: `https://research.values.md`) | (the domain itself) |

**Don't rotate the API key during the migration window.** Keep one value across both endpoints (Fly + new Worker) for the entire soak period. Rotate later if needed.

The Worker reads the header `X-API-Key` and compares with constant-time eq (use `crypto.subtle` or a simple length-check + `===` is acceptable here given the entropy of the key).

### C.3 CORS — not a concern

All API calls from `next/` go through Next.js route handlers (server-side, in the Next.js Worker), not directly from the browser. There is no `Origin: values.md` request to the API. Don't add CORS headers unless we later expose the API to browser-direct callers — adding permissive CORS by default is an unnecessary attack surface.

### C.4 Caching constraints driven by Next.js

This is the most subtle compatibility issue. The default cache TTLs in §7.4 must be tightened for per-participant endpoints because Next.js issues **read-after-write** on them within the same user session:

**Flow A (assessment completion):**
1. Browser: `POST /api/assessment/submit` (Next.js side)
2. Next.js → `POST /api/judgements` (Research API)
3. Browser: `POST /api/values/generate` (Next.js side)
4. Next.js → `POST /api/values/generate` (Research API) — LLM call, ~20s
5. Browser: dashboard mounts, calls `GET /api/values/{pid}` and `GET /api/alignment/{pid}`
6. Next.js → `GET /api/values/{pid}` (Research API)

Steps 5–6 happen seconds after step 4. A 60-second edge cache on `GET /api/values/{pid}` would risk returning a stale 404 captured before step 4 completed.

**Flow B (manual edit):**
1. User edits VALUES.md in dashboard, clicks save.
2. Next.js → `POST /api/values/update` (Research API) — writes new version
3. Browser reloads dashboard, calls `GET /api/values/{pid}`
4. Next.js → `GET /api/values/{pid}` — if edge-cached, returns the pre-edit markdown.

**Mitigation:** per-participant endpoints get `Cache-Control: private, max-age=0, no-store`. They will hit Neon per request. Acceptable because:
- One user → low natural cache hit rate anyway.
- Volume is bounded (one logged-in user does at most ~10 calls during one dashboard session).
- Drizzle + neon-http per query is a single HTTPS round-trip with kept-alive connections.

For fleet-wide endpoints (`/api/collections/{name}/dilemmas`, `/api/stats`) keep the longer TTLs from §7.4 — those have high cache hit rates and no read-after-write hazard.

### C.5 `force_regenerate` + `from_cache` semantics (must preserve)

`POST /api/values/generate` behavior, copied from `app.py` lines 1100–1188:

- If `force_regenerate` is falsy AND a row exists in `values_md` for this participant → return cached markdown with `from_cache: true`. **No LLM call.**
- If `force_regenerate` is true OR no cached row exists → call LLM, upsert to `values_md` (incrementing `version`), append new row to `values_md_history` with `change_type='ai_generated'` (or `'regeneration'` if not the first), return with `from_cache: false`.
- If participant has < **5** judgements → return HTTP 400 with `{success: false, error: 'Insufficient judgements for VALUES.md generation. Found N, minimum 5 required.'}`.

The `from_cache` field is currently read by Next.js mostly for telemetry, but the Next.js `/api/values/generate` proxy uses `result.success` to decide whether to send the welcome email — so `success` is the more important field.

### C.6 Pre-cutover contract testing

Add to Phases 4–6 exit criteria. Concrete procedure:

1. In `~/dev/values.md/next/.dev.vars`, set `RESEARCH_API_URL=https://research-next.values.md` and keep `RESEARCH_API_KEY=<same secret>`.
2. `cd ~/dev/values.md/next && pnpm dev` — local Next.js dev server.
3. Walk through the full user flow:
   - Take the assessment at `http://localhost:3000/assessment` (or wherever)
   - Submit (hits `POST /api/judgements` via Next.js → Worker)
   - Wait for VALUES.md generation (hits `POST /api/values/generate`)
   - Land on dashboard (hits `GET /api/values/{pid}` + `GET /api/alignment/{pid}`)
   - Edit VALUES.md → save (hits `POST /api/values/update`)
   - Open version history dialog (hits `GET /api/values/history` → `/api/values/{pid}/history` on the API)
   - Restore previous version (hits `POST /api/values/restore`)
   - Refresh: confirm restored content shows
4. Check Next.js server logs and browser console — no 4xx/5xx, no shape errors, no missing fields.
5. Also exercise `/api/public/values/{email}` (the public profile route) — hits `GET /api/values/{pid}` + `GET /api/judgements/{pid}`.

### C.7 Migration order — API first, Next.js untouched

Dependency direction is one-way: Next.js → Research API. So:

1. Build + deploy TS API to `research-next.values.md`.
2. Run §C.6 contract tests pointing Next.js dev at `research-next`.
3. Soak Fly + new Worker side-by-side (Fly still serving `research.values.md`) for 1–2 weeks.
4. Flip `research.values.md` Custom Domain → new Worker. Next.js needs no deploy.
5. Decommission Fly per §13.

**Confirm with the Next.js codebase owner before the flip** that no API changes are in flight that would coincide with the migration window. Coordinate; don't surprise.

### C.8 Possible Phase-0 micro-optimization

Once the TS Worker is up at `research-next.values.md`, the Next.js *staging* environment can be pointed at it (via `wrangler secret put RESEARCH_API_URL --env staging`) without affecting prod. This gives a real, low-stakes staging-on-staging signal during the soak. Recommend doing this after Phase 5 (write API ported) — by then the contract surface is complete.
