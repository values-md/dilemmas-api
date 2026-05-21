/**
 * Helpers for consistent JSON responses with the cache controls from
 * docs/CLOUDFLARE_MIGRATION_PLAN.md §7.4.
 */

/** Per-participant or write responses: never cache. */
export function jsonNoStore(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'no-store',
    },
  });
}

/** Public read with edge cache. Defaults to 5-min fresh + 1-h SWR. */
export function jsonCached(
  body: unknown,
  opts: { sMaxAge?: number; swr?: number; status?: number } = {},
): Response {
  const sMaxAge = opts.sMaxAge ?? 300;
  const swr = opts.swr ?? 3600;
  return new Response(JSON.stringify(body), {
    status: opts.status ?? 200,
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': `public, s-maxage=${sMaxAge}, stale-while-revalidate=${swr}`,
    },
  });
}
