/**
 * POST /api/participants/{participant_id}/demographics
 *
 * Update the embedded HumanJudgeDetails block on every judgement this
 * participant has submitted. Mirrors src/dilemmas/api/app.py:update_participant_demographics.
 *
 * The `data` column is rewritten per row (Python does it the same way) — there's
 * no normalization of the human_judge fields into separate columns, only the
 * embedded JSON.
 */
import type { APIRoute } from 'astro';
import { z } from 'zod';
import { env } from 'cloudflare:workers';
import { and, eq } from 'drizzle-orm';
import { getDb } from '@/db/client';
import { judgements } from '@/db/schema';
import type { JudgementData } from '@/db/types';
import { requireApiKey } from '@/lib/auth';
import { jsonNoStore } from '@/lib/json-response';

const Schema = z.object({
  age_range: z.string().optional().nullable(),
  gender: z.string().optional().nullable(),
  education_level: z.string().optional().nullable(),
  country: z.string().optional().nullable(),
  professional_background: z.string().optional().nullable(),
});

export const POST: APIRoute = async ({ request, params }) => {
  const denied = requireApiKey(request);
  if (denied) return denied;

  const participantId = params.participant_id;
  if (!participantId) return jsonNoStore({ detail: 'Missing participant_id' }, 400);

  let body: z.infer<typeof Schema>;
  try {
    body = Schema.parse(await request.json());
  } catch (err) {
    const msg = err instanceof z.ZodError ? z.prettifyError(err) : 'Invalid JSON';
    return jsonNoStore({ detail: msg }, 400);
  }

  const db = getDb(env.DB);

  const rows = await db
    .select()
    .from(judgements)
    .where(and(eq(judgements.judgeType, 'human'), eq(judgements.judgeId, participantId)));

  if (rows.length === 0) {
    return jsonNoStore({
      success: false,
      participant_id: participantId,
      updated_judgement_count: 0,
      message: `No judgements found for participant ${participantId}`,
    });
  }

  let updated = 0;
  for (const row of rows) {
    const data = row.data as Record<string, unknown>;
    const humanJudge = { ...((data.human_judge as Record<string, unknown>) ?? {}) };
    if (body.age_range != null) humanJudge.age_range = body.age_range;
    if (body.gender != null) humanJudge.gender = body.gender;
    if (body.education_level != null) humanJudge.education_level = body.education_level;
    if (body.country != null) humanJudge.country = body.country;
    if (body.professional_background != null) humanJudge.professional_background = body.professional_background;
    data.human_judge = humanJudge;

    await db.update(judgements).set({ data: data as unknown as JudgementData }).where(eq(judgements.id, row.id));
    updated++;
  }

  return jsonNoStore({
    success: true,
    participant_id: participantId,
    updated_judgement_count: updated,
    message: `Successfully updated ${updated} judgements`,
  });
};
