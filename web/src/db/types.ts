/**
 * Placeholder shapes for the JSON-serialized payloads in `dilemmas.data`,
 * `judgements.data`, etc.
 *
 * Kept loose for now — Phase 4 (when we actually read these in Astro pages
 * and JSON API endpoints) will tighten them to mirror the Pydantic models
 * in src/dilemmas/models/{dilemma,judgement,validation,extraction}.py.
 *
 * Round-trip rule: never compare two JSON strings raw across the Py/TS
 * boundary — always parse, then compare. (Python's json.dumps emits
 * \uXXXX escapes; JS JSON.stringify emits raw UTF-8.)
 */

export type DilemmaData = Record<string, unknown>;
export type JudgementData = Record<string, unknown>;
export type ValuesMarkdownData = Record<string, unknown>;
