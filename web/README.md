# web/ — research.values.md (Cloudflare Worker)

Astro 6 SSR app that replaces the Python FastAPI at `research.values.md`. See
[`../docs/CLOUDFLARE_MIGRATION_PLAN.md`](../docs/CLOUDFLARE_MIGRATION_PLAN.md)
for the full plan and rationale.

## Stack

- **Astro 6** SSR (`output: 'server'`) via `@astrojs/cloudflare`
- **Cloudflare Workers** runtime (Workers Assets for static)
- **Drizzle ORM** (`drizzle-orm/neon-http`) against the existing **Neon Postgres**
- **Zod 4** for input/output contracts (with native `z.toJSONSchema()` for LLM structured output)
- **pnpm** for package management

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
wrangler secret put DATABASE_URL
wrangler secret put OPENROUTER_API_KEY
wrangler secret put INTERNAL_API_KEY
```

The custom domain (`research-next.values.md` initially, then `research.values.md`)
is configured in `wrangler.jsonc` — uncomment the `routes` block once ready.

## Database

We **do not** own the schema initially — it's defined by the Python side at
`../src/dilemmas/models/db.py` and managed by Alembic until cutover. To
introspect the existing tables into a Drizzle schema:

```bash
# DATABASE_URL must be set in your shell or in .dev.vars
pnpm db:pull
```

After cutover, schema changes go through Drizzle:

```bash
# edit src/db/schema.ts, then:
pnpm db:generate                  # produces SQL under drizzle/
pnpm db:migrate                   # applies pending migrations
```

## What lives where

- `src/pages/`        — Astro pages (HTML) + API routes (JSON)
- `src/layouts/`      — Page layouts (Base.astro = port of Jinja base.html)
- `src/db/`           — Drizzle schema + per-request client
- `src/lib/`          — OpenRouter client, auth middleware, cache helpers
- `src/content.config.ts` — Astro content collection for `../research/*/findings.md`
- `public/`           — Static assets bundled with the Worker
- `scripts/`          — Build-time helpers (research figure copy)
