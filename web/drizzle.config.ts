import { defineConfig } from 'drizzle-kit';

// D1 (SQLite) config. The schema is the source of truth; the archive's data
// was imported once from Neon (2026-08) and there are no managed migrations —
// if the schema ever changes, generate SQL with drizzle-kit and apply it via
// `wrangler d1 execute values-md-research-db --remote --file=...`.
export default defineConfig({
  dialect: 'sqlite',
  driver: 'd1-http',
  schema: './src/db/schema.ts',
  out: './drizzle',
  casing: 'snake_case',
});
