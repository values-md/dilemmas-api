/**
 * GET /api/values/{participant_id}/history
 *
 * Returns the full version history for a participant's VALUES.md. Empty
 * `versions` array if none. Mirrors src/dilemmas/api/app.py:get_values_history.
 */
import type { APIRoute } from 'astro';
import { env } from 'cloudflare:workers';
import { desc, eq } from 'drizzle-orm';
import { getDb } from '@/db/client';
import { valuesMdHistory } from '@/db/schema';
import { requireApiKey } from '@/lib/auth';
import { jsonNoStore } from '@/lib/json-response';

export const GET: APIRoute = async ({ request, params }) => {
  const denied = requireApiKey(request);
  if (denied) return denied;

  const participantId = params.participant_id;
  if (!participantId) return jsonNoStore({ detail: 'Missing participant_id' }, 400);

  try {
    const db = getDb(env.DB);
    const rows = await db
      .select()
      .from(valuesMdHistory)
      .where(eq(valuesMdHistory.participantId, participantId))
      .orderBy(desc(valuesMdHistory.version));

    return jsonNoStore({
      success: true,
      participant_id: participantId,
      versions: rows.map((r) => ({
        id: r.id,
        version: r.version,
        change_type: r.changeType,
        changed_at: r.changedAt.toISOString(),
        markdown_text: r.markdownText,
        model_id: r.modelId,
        judgement_count: r.judgementCount,
      })),
    });
  } catch (err) {
    return jsonNoStore({ detail: err instanceof Error ? err.message : 'Internal error' }, 500);
  }
};
