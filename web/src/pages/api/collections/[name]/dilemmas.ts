/**
 * GET /api/collections/{name}/dilemmas
 *
 * Public — no API key. Returns the array of Dilemma objects (full data) in
 * the collection. Mirrors src/dilemmas/api/app.py:get_collection_dilemmas.
 *
 * Caching: 1-h fresh, 24-h SWR (test collections rarely change). The
 * Next.js client sets `cache: 'no-store'` on its end, but that only affects
 * the Next.js Worker's own fetch cache — Cloudflare's edge cache between
 * regions still applies and saves DB hits.
 */
import type { APIRoute } from 'astro';
import { env } from 'cloudflare:workers';
import { eq } from 'drizzle-orm';
import { getDb } from '@/db/client';
import { dilemmas } from '@/db/schema';
import { memo } from '@/lib/cache';
import { jsonCached } from '@/lib/json-response';

export const GET: APIRoute = async ({ params }) => {
  const name = params.name;
  if (!name) {
    return new Response(JSON.stringify({ detail: 'Missing collection name' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  try {
    const rows = await memo(`collection:${name}`, 60 * 60 * 1000, async () => {
      const db = getDb(env.DB);
      return db.select({ data: dilemmas.data }).from(dilemmas).where(eq(dilemmas.collection, name));
    });

    if (rows.length === 0) {
      return new Response(JSON.stringify({ detail: `Collection '${name}' not found` }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // jsonText custom type already parsed each `data` column into an object.
    const payload = rows.map((r) => r.data);
    return jsonCached(payload, { sMaxAge: 3600, swr: 86400 });
  } catch (err) {
    return new Response(
      JSON.stringify({ detail: err instanceof Error ? err.message : 'Internal error' }),
      { status: 500, headers: { 'Content-Type': 'application/json' } },
    );
  }
};
