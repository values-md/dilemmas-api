import { pgTable, varchar, index, text, timestamp, doublePrecision, integer } from "drizzle-orm/pg-core"
import { sql } from "drizzle-orm"



export const alembicVersion = pgTable("alembic_version", {
	versionNum: varchar("version_num", { length: 32 }).primaryKey().notNull(),
});

export const judgements = pgTable("judgements", {
	id: varchar().primaryKey().notNull(),
	dilemmaId: varchar("dilemma_id").notNull(),
	data: text().notNull(),
	judgeType: varchar("judge_type").notNull(),
	judgeId: varchar("judge_id").notNull(),
	mode: varchar().notNull(),
	choiceId: varchar("choice_id"),
	createdAt: timestamp("created_at", { mode: 'string' }).notNull(),
	variationKey: varchar("variation_key"),
	experimentId: varchar("experiment_id"),
	temperature: doublePrecision(),
	systemPromptType: varchar("system_prompt_type"),
	valuesFileName: varchar("values_file_name"),
	repetitionNumber: integer("repetition_number"),
}, (table) => [
	index("ix_judgements_created_at").using("btree", table.createdAt.asc().nullsLast().op("timestamp_ops")),
	index("ix_judgements_dilemma_id").using("btree", table.dilemmaId.asc().nullsLast().op("text_ops")),
	index("ix_judgements_experiment_id").using("btree", table.experimentId.asc().nullsLast().op("text_ops")),
	index("ix_judgements_judge_id").using("btree", table.judgeId.asc().nullsLast().op("text_ops")),
	index("ix_judgements_judge_type").using("btree", table.judgeType.asc().nullsLast().op("text_ops")),
	index("ix_judgements_mode").using("btree", table.mode.asc().nullsLast().op("text_ops")),
	index("ix_judgements_repetition_number").using("btree", table.repetitionNumber.asc().nullsLast().op("int4_ops")),
	index("ix_judgements_system_prompt_type").using("btree", table.systemPromptType.asc().nullsLast().op("text_ops")),
	index("ix_judgements_temperature").using("btree", table.temperature.asc().nullsLast().op("float8_ops")),
	index("ix_judgements_values_file_name").using("btree", table.valuesFileName.asc().nullsLast().op("text_ops")),
	index("ix_judgements_variation_key").using("btree", table.variationKey.asc().nullsLast().op("text_ops")),
]);

export const dilemmas = pgTable("dilemmas", {
	id: varchar().primaryKey().notNull(),
	data: text().notNull(),
	title: varchar().notNull(),
	difficultyIntended: integer("difficulty_intended").notNull(),
	createdBy: varchar("created_by").notNull(),
	createdAt: timestamp("created_at", { mode: 'string' }).notNull(),
	tagsJson: text("tags_json").notNull(),
	version: integer().notNull(),
	parentId: varchar("parent_id"),
	collection: varchar(),
	batchId: varchar("batch_id"),
}, (table) => [
	index("ix_dilemmas_batch_id").using("btree", table.batchId.asc().nullsLast().op("text_ops")),
	index("ix_dilemmas_collection").using("btree", table.collection.asc().nullsLast().op("text_ops")),
	index("ix_dilemmas_created_at").using("btree", table.createdAt.asc().nullsLast().op("timestamp_ops")),
	index("ix_dilemmas_created_by").using("btree", table.createdBy.asc().nullsLast().op("text_ops")),
	index("ix_dilemmas_difficulty_intended").using("btree", table.difficultyIntended.asc().nullsLast().op("int4_ops")),
	index("ix_dilemmas_parent_id").using("btree", table.parentId.asc().nullsLast().op("text_ops")),
	index("ix_dilemmas_title").using("btree", table.title.asc().nullsLast().op("text_ops")),
]);

export const valuesMdHistory = pgTable("values_md_history", {
	id: varchar().primaryKey().notNull(),
	participantId: varchar("participant_id").notNull(),
	markdownText: text("markdown_text").notNull(),
	structuredJson: text("structured_json").notNull(),
	version: integer().notNull(),
	changeType: varchar("change_type").notNull(),
	generatedAt: timestamp("generated_at", { mode: 'string' }).notNull(),
	modelId: varchar("model_id").notNull(),
	judgementCount: integer("judgement_count").notNull(),
	changedAt: timestamp("changed_at", { mode: 'string' }).notNull(),
}, (table) => [
	index("ix_values_md_history_change_type").using("btree", table.changeType.asc().nullsLast().op("text_ops")),
	index("ix_values_md_history_changed_at").using("btree", table.changedAt.asc().nullsLast().op("timestamp_ops")),
	index("ix_values_md_history_participant_id").using("btree", table.participantId.asc().nullsLast().op("text_ops")),
]);

export const valuesMd = pgTable("values_md", {
	participantId: varchar("participant_id").primaryKey().notNull(),
	markdownText: text("markdown_text").notNull(),
	structuredJson: text("structured_json").notNull(),
	generatedAt: timestamp("generated_at", { mode: 'string' }).notNull(),
	modelId: varchar("model_id").notNull(),
	judgementCount: integer("judgement_count").notNull(),
	version: integer().notNull(),
	lastChangeType: varchar("last_change_type").default('ai_generated').notNull(),
});
