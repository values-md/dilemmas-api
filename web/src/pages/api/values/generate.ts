/**
 * POST /api/values/generate
 *
 * Generate a VALUES.md for a participant by feeding their judgements + the
 * referenced dilemmas to an LLM. Mirrors src/dilemmas/api/app.py:generate_values_md
 * + src/dilemmas/services/values_generator.py:ValuesGenerator.generate.
 *
 * Honors `force_regenerate` (default false) and `from_cache` semantics:
 *  - cached row exists + !force → return with from_cache=true (no LLM call)
 *  - else call LLM, upsert values_md, append values_md_history row,
 *    return from_cache=false
 *  - <5 judgements → success=false, error=...
 */
import type { APIRoute } from 'astro';
import { z } from 'zod';
import { env } from 'cloudflare:workers';
import { randomUUID } from 'node:crypto';
import { and, eq, inArray } from 'drizzle-orm';
import { getDb } from '@/db/client';
import { dilemmas, judgements, valuesMd, valuesMdHistory } from '@/db/schema';
import { requireApiKey } from '@/lib/auth';
import { jsonNoStore } from '@/lib/json-response';
import { chatText } from '@/lib/openrouter';
import { formatJudgements } from '@/lib/format-judgements-for-values';
import generateValuesMdPrompt from '@/prompts/values/generate_values_md.md?raw';

const MIN_JUDGEMENTS = 5;
const DEFAULT_MODEL = 'google/gemini-2.5-flash';
const TEMPERATURE = 0.7;
const MAX_TOKENS = 16000;

const Schema = z.object({
  participant_id: z.string(),
  model_id: z.string().optional(),
  force_regenerate: z.boolean().optional(),
});

export const POST: APIRoute = async ({ request }) => {
  const denied = requireApiKey(request);
  if (denied) return denied;

  let body: z.infer<typeof Schema>;
  try {
    body = Schema.parse(await request.json());
  } catch (err) {
    const msg = err instanceof z.ZodError ? z.prettifyError(err) : 'Invalid JSON';
    return jsonNoStore({ detail: msg }, 400);
  }

  const modelId = body.model_id ?? DEFAULT_MODEL;
  const db = getDb(env.DATABASE_URL);

  // ---- Cache check ------------------------------------------------------
  if (!body.force_regenerate) {
    const cached = await db
      .select()
      .from(valuesMd)
      .where(eq(valuesMd.participantId, body.participant_id))
      .limit(1);
    if (cached.length > 0) {
      const row = cached[0]!;
      return jsonNoStore({
        success: true,
        participant_id: body.participant_id,
        values_md: row.markdownText,
        from_cache: true,
        judgement_count: row.judgementCount,
        generated_at: row.generatedAt.toISOString(),
        model_id: row.modelId,
      });
    }
  }

  // ---- Generate ---------------------------------------------------------
  try {
    const judgementRows = await db
      .select()
      .from(judgements)
      .where(and(eq(judgements.judgeType, 'human'), eq(judgements.judgeId, body.participant_id)));

    if (judgementRows.length < MIN_JUDGEMENTS) {
      return jsonNoStore({
        success: false,
        participant_id: body.participant_id,
        error: `Insufficient judgements for VALUES.md generation. Found ${judgementRows.length}, minimum ${MIN_JUDGEMENTS} required.`,
      });
    }

    const judgementData = judgementRows.map((r) => r.data);
    const dilemmaIds = Array.from(new Set(judgementRows.map((j) => j.dilemmaId)));
    const dilemmaRows = await db
      .select({ id: dilemmas.id, data: dilemmas.data })
      .from(dilemmas)
      .where(inArray(dilemmas.id, dilemmaIds));
    const dilemmaMap = new Map(dilemmaRows.map((d) => [d.id, d.data]));

    const judgementsBlock = formatJudgements(judgementData, dilemmaMap);
    const today = new Date().toISOString().slice(0, 10); // YYYY-MM-DD

    const markdownText = await chatText({
      model: modelId,
      system: generateValuesMdPrompt,
      user: `Analyze these ethical judgements and generate a VALUES.md file.

IMPORTANT: Today's date is ${today}. Use this exact date for the "Last updated" field.

${judgementsBlock}

Extract patterns, formulate actionable decision rules, and create a framework that AI agents can use to make decisions on behalf of this person.

Remember: Be specific, provide concrete hypothetical examples (NOT references to judgements), keep it under 3000 words, and acknowledge limitations.

Output ONLY the markdown content, nothing else.`,
      temperature: TEMPERATURE,
      maxTokens: MAX_TOKENS,
    });

    // ---- Persist ---------------------------------------------------------
    const existing = await db
      .select()
      .from(valuesMd)
      .where(eq(valuesMd.participantId, body.participant_id))
      .limit(1);
    const newVersion = existing[0] ? existing[0].version + 1 : 1;
    const changeType = existing[0] ? 'regeneration' : 'ai_generated';
    const now = new Date();
    const judgementCount = judgementRows.length;

    if (existing[0]) {
      await db
        .update(valuesMd)
        .set({
          markdownText,
          structuredJson: {},
          generatedAt: now,
          modelId,
          judgementCount,
          version: newVersion,
          lastChangeType: changeType,
        })
        .where(eq(valuesMd.participantId, body.participant_id));
    } else {
      await db.insert(valuesMd).values({
        participantId: body.participant_id,
        markdownText,
        structuredJson: {},
        generatedAt: now,
        modelId,
        judgementCount,
        version: newVersion,
        lastChangeType: changeType,
      });
    }

    await db.insert(valuesMdHistory).values({
      id: randomUUID(),
      participantId: body.participant_id,
      markdownText,
      structuredJson: {},
      version: newVersion,
      changeType,
      generatedAt: now,
      modelId,
      judgementCount,
      changedAt: now,
    });

    return jsonNoStore({
      success: true,
      participant_id: body.participant_id,
      values_md: markdownText,
      from_cache: false,
      judgement_count: judgementCount,
      generated_at: now.toISOString(),
      model_id: modelId,
    });
  } catch (err) {
    console.error('[values/generate]', err);
    return jsonNoStore({
      success: false,
      participant_id: body.participant_id,
      error: 'Failed to generate VALUES.md. Please try again.',
    });
  }
};
