/**
 * Smoke endpoint for Phase 1 (DB connectivity). Returns a JSON object that
 * reports whether DATABASE_URL is wired and — once Phase 1 lands — the
 * count of rows in `dilemmas`.
 *
 * Public on purpose for local dev; before going live behind research.values.md
 * either gate behind X-API-Key or delete.
 */
import type { APIRoute } from 'astro';
import { env } from 'cloudflare:workers';

export const GET: APIRoute = async () => {
  const haveUrl = Boolean(env?.DATABASE_URL);

  const body = {
    ok: true,
    phase: 0,
    database_url_present: haveUrl,
    // Phase 1 will add: dilemmas_count, judgements_count, latency_ms
    note: 'Connect Drizzle + neon-http in Phase 1.',
  };

  return new Response(JSON.stringify(body, null, 2), {
    status: 200,
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'no-store',
    },
  });
};
