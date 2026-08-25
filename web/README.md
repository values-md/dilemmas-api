# web/ — research.values.md (Cloudflare Worker)

Astro 6 SSR app that replaces the Python FastAPI at `research.values.md`. See
[`../docs/CLOUDFLARE_MIGRATION_PLAN.md`](../docs/CLOUDFLARE_MIGRATION_PLAN.md)
for the full plan and rationale.

## Stack

- **Astro 6** SSR (`output: 'server'`) via `@astrojs/cloudflare`
- **Cloudflare Workers** runtime (Workers Assets for static)
- **Drizzle ORM** (`drizzle-orm/d1`) against **Cloudflare D1** (`values-md-research-db`)
- **Zod 4** for input/output contracts (with native `z.toJSONSchema()` for LLM structured output)
- **pnpm** for package management

> **DB history:** originally Neon Postgres (kept from the Fly.io era). Migrated to
> D1 in Aug 2026 — the project is an archive with a frozen 17 MB dataset, and the
> constant bot traffic kept the Neon compute awake ~50% of the time (~370
> CU-hours/month, the single biggest consumer in the org). All data was exported
> with timestamps converted to epoch-ms integers; API response shapes are
> unchanged. The Neon project (`winter-recipe-31937114`) can be deleted once the
> rollback window has passed.

## Local dev

```bash
# one-time
cp .dev.vars.example .dev.vars   # then fill in real values
pnpm install

# every time
pnpm dev                          # astro dev on workerd, http://localhost:4321
```

The `predev` and `prebuild` scripts copy `../research/*/figures/` into
`public/research-static/{slug}/figures/` so the markdown image paths work.

## Build / deploy

```bash
pnpm build                        # astro check + astro build
pnpm deploy                       # build + wrangler deploy
```

For the first deploy you need:

```bash
wrangler login
wrangler secret put OPENROUTER_API_KEY
wrangler secret put INTERNAL_API_KEY
```

The database is the D1 binding `DB` in `wrangler.jsonc` — no connection-string
secret needed.

The custom domain (`research-next.values.md` initially, then `research.values.md`)
is configured in `wrangler.jsonc` — uncomment the `routes` block once ready.

## Database

Cloudflare D1: `values-md-research-db` (id `ec0a8bfb-93d9-4b39-905c-304fa1ec14cc`),
bound as `DB`. `src/db/schema.ts` (drizzle sqlite-core) is the source of truth;
timestamps are INTEGER epoch milliseconds (UTC) surfaced as JS `Date`s.

There are no managed migrations — the archive's data was imported once from
Neon. If the schema ever changes, generate SQL with drizzle-kit and apply it:

```bash
pnpm exec wrangler d1 execute values-md-research-db --remote --file=<migration.sql>
```

For local dev, seed the local D1 the same way with `--local` (ask for the
`d1_import.sql` dump or re-export from the D1 remote with
`wrangler d1 export values-md-research-db --remote --output=dump.sql`).

## What lives where

- `src/pages/`        — Astro pages (HTML) + API routes (JSON)
- `src/layouts/`      — Page layouts (Base.astro = port of Jinja base.html)
- `src/db/`           — Drizzle schema + per-request client
- `src/lib/`          — OpenRouter client, auth middleware, cache helpers
- `src/content.config.ts` — Astro content collection for `../research/*/findings.md`
- `public/`           — Static assets bundled with the Worker
- `scripts/`          — Build-time helpers (research figure copy)
