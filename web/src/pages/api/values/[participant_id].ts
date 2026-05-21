/**
 * GET /api/values/{participant_id}
 *
 * Returns the cached VALUES.md for a participant, or 404. Mirrors
 * src/dilemmas/api/app.py:get_values_md (response shape via
 * GenerateValuesResponse with from_cache=true).
 *
 * Per-participant → no edge caching (Next.js issues read-after-write).
 */
import type { APIRoute } from 'astro';
import { env } from 'cloudflare:workers';
import { eq } from 'drizzle-orm';
import { getDb } from '@/db/client';
import { valuesMd } from '@/db/schema';
import { requireApiKey } from '@/lib/auth';
import { jsonNoStore } from '@/lib/json-response';

export const GET: APIRoute = async ({ request, params }) => {
  const denied = requireApiKey(request);
  if (denied) return denied;

  const participantId = params.participant_id;
  if (!participantId) return jsonNoStore({ detail: 'Missing participant_id' }, 400);

  try {
    const db = getDb(env.DATABASE_URL);
    const rows = await db
      .select()
      .from(valuesMd)
      .where(eq(valuesMd.participantId, participantId))
      .limit(1);

    if (rows.length === 0) {
      return jsonNoStore(
        { detail: `No VALUES.md found for participant '${participantId}'. Generate one first.` },
        404,
      );
    }

    const row = rows[0]!;
    return jsonNoStore({
      success: true,
      participant_id: participantId,
      values_md: row.markdownText,
      from_cache: true,
      judgement_count: row.judgementCount,
      generated_at: row.generatedAt.toISOString(),
      model_id: row.modelId,
    });
  } catch (err) {
    return jsonNoStore({ detail: err instanceof Error ? err.message : 'Internal error' }, 500);
  }
};
