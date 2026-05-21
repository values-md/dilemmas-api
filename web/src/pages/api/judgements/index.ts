/**
 * POST /api/judgements
 *
 * Batch-submit human judgements. Mirrors src/dilemmas/api/app.py:submit_human_judgements:
 * validates dilemma exists + choice_id is valid per item, computes variation_key,
 * inserts into judgements table with the full Pydantic-equivalent JSON payload.
 *
 * Returns SubmitJudgementsResponse-shaped JSON consumed by the values.md Next.js
 * client (`submitJudgements()` in next/src/lib/research-api.ts).
 */
import type { APIRoute } from 'astro';
import { z } from 'zod';
import { env } from 'cloudflare:workers';
import { inArray } from 'drizzle-orm';
import { getDb } from '@/db/client';
import { dilemmas, judgements } from '@/db/schema';
import { requireApiKey } from '@/lib/auth';
import { jsonNoStore } from '@/lib/json-response';
import { buildHumanJudgement, type HumanJudgeInput } from '@/lib/build-judgement';
import type { JudgementData } from '@/db/types';

const JudgementItemSchema = z.object({
  dilemma_id: z.string(),
  choice_id: z.string(),
  rendered_situation: z.string(),
  variable_values: z.record(z.string(), z.string()).optional().nullable(),
  modifier_indices: z.array(z.number()).optional().nullable(),
  reasoning: z.string().optional().nullable(),
  confidence: z.number().optional().nullable(),
  response_time_ms: z.number().optional().nullable(),
});

const DemographicsSchema = z.object({
  age_range: z.string().optional().nullable(),
  gender: z.string().optional().nullable(),
  education_level: z.string().optional().nullable(),
  country: z.string().optional().nullable(),
  culture: z.string().optional().nullable(),
  professional_background: z.string().optional().nullable(),
});

const SubmitSchema = z.object({
  participant_id: z.string(),
  judgements: z.array(JudgementItemSchema).min(1),
  demographics: DemographicsSchema.optional().nullable(),
});

export const POST: APIRoute = async ({ request }) => {
  const denied = requireApiKey(request);
  if (denied) return denied;

  let body: z.infer<typeof SubmitSchema>;
  try {
    body = SubmitSchema.parse(await request.json());
  } catch (err) {
    const msg = err instanceof z.ZodError ? z.prettifyError(err) : 'Invalid JSON';
    return jsonNoStore({ detail: msg }, 400);
  }

  const db = getDb(env.DATABASE_URL);
  const errors: string[] = [];
  const ids: string[] = [];

  // Bulk-load all referenced dilemmas in one query so we can validate choice_ids
  // without N+1 round trips (the Python version does N+1 — we do better).
  const referencedIds = Array.from(new Set(body.judgements.map((j) => j.dilemma_id)));
  const dilemmaRows = await db
    .select({ id: dilemmas.id, data: dilemmas.data })
    .from(dilemmas)
    .where(inArray(dilemmas.id, referencedIds));
  const validChoiceIdsByDilemma = new Map<string, Set<string>>(
    dilemmaRows.map((r) => [r.id, new Set((r.data.choices ?? []).map((c) => c.id))]),
  );

  const human: HumanJudgeInput = {
    participant_id: body.participant_id,
    ...(body.demographics ?? {}),
  };

  for (const item of body.judgements) {
    const validChoices = validChoiceIdsByDilemma.get(item.dilemma_id);
    if (!validChoices) {
      errors.push(`Dilemma ${item.dilemma_id} not found`);
      continue;
    }
    if (!validChoices.has(item.choice_id)) {
      errors.push(`Invalid choice_id '${item.choice_id}' for dilemma ${item.dilemma_id}`);
      continue;
    }

    const built = buildHumanJudgement(
      {
        dilemma_id: item.dilemma_id,
        choice_id: item.choice_id,
        rendered_situation: item.rendered_situation,
        variable_values: item.variable_values ?? null,
        modifier_indices: item.modifier_indices ?? null,
        reasoning: item.reasoning ?? null,
        confidence: item.confidence ?? null,
        response_time_ms: item.response_time_ms ?? null,
      },
      human,
    );

    try {
      await db.insert(judgements).values({
        id: built.id,
        dilemmaId: item.dilemma_id,
        data: built.data as unknown as JudgementData,
        judgeType: 'human',
        judgeId: body.participant_id,
        mode: 'theory',
        choiceId: item.choice_id,
        createdAt: built.createdAt,
        variationKey: built.variationKey,
        experimentId: null,
        temperature: null,
        systemPromptType: null,
        valuesFileName: null,
        repetitionNumber: null,
      });
      ids.push(built.id);
    } catch (err) {
      errors.push(
        `Error processing judgement for dilemma ${item.dilemma_id}: ${err instanceof Error ? err.message : String(err)}`,
      );
    }
  }

  const message =
    errors.length === 0
      ? `Successfully saved ${ids.length} judgements`
      : `Saved ${ids.length} judgements. Errors: ${errors.join('; ')}`;

  return jsonNoStore({
    success: ids.length > 0,
    judgement_ids: ids,
    message,
  });
};
