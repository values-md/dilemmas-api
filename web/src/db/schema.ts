/**
 * Drizzle schema for the Cloudflare D1 (SQLite) database.
 *
 * History: originally generated from Neon Postgres by `drizzle-kit pull`,
 * then ported to sqlite-core when the data moved to D1 (2026-08 — the
 * project is an archive; a serverless Postgres was overkill and expensive).
 * Data model mirrors the Python SQLModel side in src/dilemmas/models/db.py,
 * which was itself born on SQLite (data/dilemmas.db), so this is a
 * homecoming: JSON-in-TEXT columns, indexed scalar fields.
 *
 * Timestamps are stored as INTEGER epoch milliseconds (UTC) and surface as
 * JS Date objects, so existing `.toISOString()` call sites are unchanged.
 */
import { sqliteTable, text, integer, real, index } from 'drizzle-orm/sqlite-core';
import { jsonText } from './json-text';
import type { DilemmaData, JudgementData, ValuesMarkdownData } from './types';

const timestamp = (name: string) => integer(name, { mode: 'timestamp_ms' });

// ---------------------------------------------------------------------------
// Dilemmas
// ---------------------------------------------------------------------------
export const dilemmas = sqliteTable(
  'dilemmas',
  {
    id: text().primaryKey().notNull(),
    data: jsonText<DilemmaData>('data').notNull(),
    title: text().notNull(),
    difficultyIntended: integer('difficulty_intended').notNull(),
    createdBy: text('created_by').notNull(),
    createdAt: timestamp('created_at').notNull(),
    tagsJson: jsonText<string[]>('tags_json').notNull(),
    version: integer().notNull(),
    parentId: text('parent_id'),
    collection: text(),
    batchId: text('batch_id'),
  },
  (table) => [
    index('ix_dilemmas_batch_id').on(table.batchId),
    index('ix_dilemmas_collection').on(table.collection),
    index('ix_dilemmas_created_at').on(table.createdAt),
    index('ix_dilemmas_created_by').on(table.createdBy),
    index('ix_dilemmas_difficulty_intended').on(table.difficultyIntended),
    index('ix_dilemmas_parent_id').on(table.parentId),
    index('ix_dilemmas_title').on(table.title),
  ],
);

// ---------------------------------------------------------------------------
// Judgements
// ---------------------------------------------------------------------------
export const judgements = sqliteTable(
  'judgements',
  {
    id: text().primaryKey().notNull(),
    dilemmaId: text('dilemma_id').notNull(),
    data: jsonText<JudgementData>('data').notNull(),
    judgeType: text('judge_type').notNull(),
    judgeId: text('judge_id').notNull(),
    mode: text().notNull(),
    choiceId: text('choice_id'),
    createdAt: timestamp('created_at').notNull(),
    variationKey: text('variation_key'),
    experimentId: text('experiment_id'),
    temperature: real(),
    systemPromptType: text('system_prompt_type'),
    valuesFileName: text('values_file_name'),
    repetitionNumber: integer('repetition_number'),
  },
  (table) => [
    index('ix_judgements_created_at').on(table.createdAt),
    index('ix_judgements_dilemma_id').on(table.dilemmaId),
    index('ix_judgements_experiment_id').on(table.experimentId),
    index('ix_judgements_judge_id').on(table.judgeId),
    index('ix_judgements_judge_type').on(table.judgeType),
    index('ix_judgements_mode').on(table.mode),
    index('ix_judgements_repetition_number').on(table.repetitionNumber),
    index('ix_judgements_system_prompt_type').on(table.systemPromptType),
    index('ix_judgements_temperature').on(table.temperature),
    index('ix_judgements_values_file_name').on(table.valuesFileName),
    index('ix_judgements_variation_key').on(table.variationKey),
  ],
);

// ---------------------------------------------------------------------------
// VALUES.md (cache + history)
// ---------------------------------------------------------------------------
export const valuesMd = sqliteTable('values_md', {
  participantId: text('participant_id').primaryKey().notNull(),
  markdownText: text('markdown_text').notNull(),
  structuredJson: jsonText<ValuesMarkdownData>('structured_json').notNull(),
  generatedAt: timestamp('generated_at').notNull(),
  modelId: text('model_id').notNull(),
  judgementCount: integer('judgement_count').notNull(),
  version: integer().notNull(),
  lastChangeType: text('last_change_type').default('ai_generated').notNull(),
});

export const valuesMdHistory = sqliteTable(
  'values_md_history',
  {
    id: text().primaryKey().notNull(),
    participantId: text('participant_id').notNull(),
    markdownText: text('markdown_text').notNull(),
    structuredJson: jsonText<ValuesMarkdownData>('structured_json').notNull(),
    version: integer().notNull(),
    changeType: text('change_type').notNull(),
    generatedAt: timestamp('generated_at').notNull(),
    modelId: text('model_id').notNull(),
    judgementCount: integer('judgement_count').notNull(),
    changedAt: timestamp('changed_at').notNull(),
  },
  (table) => [
    index('ix_values_md_history_change_type').on(table.changeType),
    index('ix_values_md_history_changed_at').on(table.changedAt),
    index('ix_values_md_history_participant_id').on(table.participantId),
  ],
);
