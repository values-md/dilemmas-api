/**
 * Smoke endpoint: counts rows in each table to confirm Drizzle + Neon work
 * from the Worker. Public on purpose during scaffold; remove or gate before
 * going live behind research.values.md.
 */
import type { APIRoute } from 'astro';
import { env } from 'cloudflare:workers';
import { sql } from 'drizzle-orm';
import { getDb } from '@/db/client';
import { dilemmas, judgements, valuesMd, valuesMdHistory } from '@/db/schema';

export const GET: APIRoute = async () => {
  const t0 = Date.now();
  try {
    const db = getDb(env.DB);
    const [d, j, v, h] = await Promise.all([
      db.select({ n: sql<number>`count(*)` }).from(dilemmas),
      db.select({ n: sql<number>`count(*)` }).from(judgements),
      db.select({ n: sql<number>`count(*)` }).from(valuesMd),
      db.select({ n: sql<number>`count(*)` }).from(valuesMdHistory),
    ]);

    const body = {
      ok: true,
      phase: 1,
      counts: {
        dilemmas: d[0]?.n ?? 0,
        judgements: j[0]?.n ?? 0,
        values_md: v[0]?.n ?? 0,
        values_md_history: h[0]?.n ?? 0,
      },
      latency_ms: Date.now() - t0,
    };

    return new Response(JSON.stringify(body, null, 2), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store',
      },
    });
  } catch (err) {
    return new Response(
      JSON.stringify({
        ok: false,
        error: err instanceof Error ? err.message : String(err),
        latency_ms: Date.now() - t0,
      }, null, 2),
      { status: 500, headers: { 'Content-Type': 'application/json' } },
    );
  }
};
