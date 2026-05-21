/**
 * Build the JSON payload for a new human Judgement, matching the shape
 * Pydantic produces in src/dilemmas/models/judgement.py:
 *   Judgement.model_dump_json() with judge_type='human', mode='theory'.
 *
 * We need byte-shape parity with the Python side so that:
 *  - existing Python scripts can read these rows via Judgement.model_validate_json
 *  - the JudgementDB indexed columns line up with the embedded JSON
 *
 * Reference sample row (judgements WHERE judge_type='human') verified
 * against Neon prod 2026-05-21.
 */
import { createHash, randomUUID } from 'node:crypto';

export interface HumanJudgeInput {
  participant_id: string;
  age_range?: string | null;
  gender?: string | null;
  education_level?: string | null;
  country?: string | null;
  culture?: string | null;
  professional_background?: string | null;
}

export interface JudgementInput {
  dilemma_id: string;
  rendered_situation: string;
  choice_id: string;
  variable_values?: Record<string, string> | null;
  modifier_indices?: number[] | null;
  reasoning?: string | null;
  confidence?: number | null;
  response_time_ms?: number | null;
}

export interface HumanJudgementBuild {
  id: string;
  createdAt: Date;
  variationKey: string | null;
  data: Record<string, unknown>;
}

/**
 * Compute variation_key: first 16 hex chars of md5("k1=v1|k2=v2|...") with keys
 * sorted alphabetically. Mirrors the Python implementation in
 * src/dilemmas/api/app.py:submit_human_judgements.
 */
export function variationKey(vars: Record<string, string> | null | undefined): string | null {
  if (!vars || Object.keys(vars).length === 0) return null;
  const parts = Object.entries(vars)
    .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))
    .map(([k, v]) => `${k}=${v}`)
    .join('|');
  return createHash('md5').update(parts).digest('hex').slice(0, 16);
}

/**
 * Build the full Judgement JSON payload + indexed-column values for a
 * human submission. Returns the shape Pydantic would produce, with all
 * default-null/empty fields populated identically.
 */
export function buildHumanJudgement(
  item: JudgementInput,
  human: HumanJudgeInput,
): HumanJudgementBuild {
  const id = randomUUID();
  const createdAt = new Date();
  const vk = variationKey(item.variable_values);

  const humanJudge = {
    participant_id: human.participant_id,
    age_range: human.age_range ?? null,
    gender: human.gender ?? null,
    education_level: human.education_level ?? null,
    country: human.country ?? null,
    culture: human.culture ?? null,
    professional_background: human.professional_background ?? null,
    values_scores: null as Record<string, number> | null,
    recruitment_source: null as string | null,
    device_type: null as string | null,
    changed_mind: false,
    revision_history: [] as unknown[],
    time_on_page_ms: null as number | null,
  };

  const data: Record<string, unknown> = {
    id,
    dilemma_id: item.dilemma_id,
    judge_type: 'human',
    ai_judge: null,
    human_judge: humanJudge,
    mode: 'theory',
    rendered_situation: item.rendered_situation,
    variable_values: item.variable_values ?? null,
    modifier_indices: item.modifier_indices ?? [],
    variation_key: vk,
    choice_id: item.choice_id,
    confidence: item.confidence ?? null,
    perceived_difficulty: null,
    reasoning: item.reasoning ?? null,
    reasoning_trace: null,
    response_time_ms: item.response_time_ms ?? null,
    experiment_id: null,
    experiment_metadata: {},
    repetition_number: null,
    time_constraint: null,
    created_at: createdAt.toISOString(),
    error_occurred: false,
    error_message: null,
    refused_to_answer: false,
    notes: null,
  };

  return { id, createdAt, variationKey: vk, data };
}
