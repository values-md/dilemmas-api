/**
 * GET /api/judgements/{participant_id}
 *
 * Returns this participant's human judgements with dilemma context attached,
 * for public profile display. Mirrors src/dilemmas/api/app.py:get_participant_judgements.
 */
import type { APIRoute } from 'astro';
import { env } from 'cloudflare:workers';
import { and, eq, inArray } from 'drizzle-orm';
import { getDb } from '@/db/client';
import { dilemmas, judgements } from '@/db/schema';
import { requireApiKey } from '@/lib/auth';
import { jsonNoStore } from '@/lib/json-response';

export const GET: APIRoute = async ({ request, params }) => {
  const denied = requireApiKey(request);
  if (denied) return denied;

  const participantId = params.participant_id;
  if (!participantId) return jsonNoStore({ detail: 'Missing participant_id' }, 400);

  try {
    const db = getDb(env.DB);

    const judgementRows = await db
      .select()
      .from(judgements)
      .where(and(eq(judgements.judgeType, 'human'), eq(judgements.judgeId, participantId)));

    if (judgementRows.length === 0) {
      return jsonNoStore({
        success: true,
        participant_id: participantId,
        judgements: [],
      });
    }

    const dilemmaIds = Array.from(new Set(judgementRows.map((j) => j.dilemmaId)));
    const dilemmaRows = await db
      .select({ id: dilemmas.id, data: dilemmas.data })
      .from(dilemmas)
      .where(inArray(dilemmas.id, dilemmaIds));
    const dilemmaById = new Map(dilemmaRows.map((d) => [d.id, d.data]));

    const formatted = judgementRows
      .map((row) => {
        const dilemma = dilemmaById.get(row.dilemmaId);
        if (!dilemma) return null;
        const data = row.data;
        const choice = (dilemma.choices ?? []).find((c) => c.id === data.choice_id);
        return {
          dilemma_title: dilemma.title,
          situation: data.rendered_situation || dilemma.situation_template,
          choice_id: data.choice_id,
          choice_description: choice?.description ?? null,
          confidence: data.confidence,
          reasoning: data.reasoning,
          created_at: row.createdAt.toISOString(),
        };
      })
      .filter((x): x is NonNullable<typeof x> => x !== null);

    return jsonNoStore({
      success: true,
      participant_id: participantId,
      judgements: formatted,
    });
  } catch (err) {
    return jsonNoStore({ detail: err instanceof Error ? err.message : 'Internal error' }, 500);
  }
};
