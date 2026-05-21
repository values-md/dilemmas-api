/**
 * Shapes of the JSON-serialized payloads in `dilemmas.data`, `judgements.data`,
 * etc. Mirror the Pydantic models in src/dilemmas/models/{dilemma,judgement}.py.
 *
 * These are intentionally permissive — we only declare the fields the TS side
 * actually reads. Other fields ride through as `Record<string, unknown>` via
 * the index signature. Tighten as we add more endpoints.
 *
 * Round-trip rule: never compare two JSON strings raw across the Py/TS
 * boundary — always parse, then compare. (Python's json.dumps emits
 * \uXXXX escapes; JS JSON.stringify emits raw UTF-8.)
 */

export interface DilemmaChoice {
  id: string;
  label: string;
  description: string;
  [k: string]: unknown;
}

export interface DilemmaData {
  id: string;
  title: string;
  situation_template: string;
  question: string;
  choices: DilemmaChoice[];
  variables: Record<string, string[]>;
  modifiers: string[];
  tags: string[];
  difficulty_intended: number | null;
  created_at: string;
  created_by: string;
  collection: string | null;
  [k: string]: unknown;
}

export interface JudgementData {
  id: string;
  dilemma_id: string;
  judge_type: 'human' | 'ai';
  mode: 'theory' | 'action';
  rendered_situation: string;
  choice_id: string | null;
  confidence: number | null;
  reasoning: string | null;
  variable_values?: Record<string, string> | null;
  modifier_indices?: number[] | null;
  variation_key?: string | null;
  response_time_ms?: number | null;
  created_at: string;
  [k: string]: unknown;
}

export type ValuesMarkdownData = Record<string, unknown>;
