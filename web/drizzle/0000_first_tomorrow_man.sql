-- Current sql file was generated after introspecting the database
-- If you want to run this migration please uncomment this code before executing migrations
/*
CREATE TABLE "alembic_version" (
	"version_num" varchar(32) PRIMARY KEY NOT NULL
);
--> statement-breakpoint
CREATE TABLE "judgements" (
	"id" varchar PRIMARY KEY NOT NULL,
	"dilemma_id" varchar NOT NULL,
	"data" text NOT NULL,
	"judge_type" varchar NOT NULL,
	"judge_id" varchar NOT NULL,
	"mode" varchar NOT NULL,
	"choice_id" varchar,
	"created_at" timestamp NOT NULL,
	"variation_key" varchar,
	"experiment_id" varchar,
	"temperature" double precision,
	"system_prompt_type" varchar,
	"values_file_name" varchar,
	"repetition_number" integer
);
--> statement-breakpoint
CREATE TABLE "dilemmas" (
	"id" varchar PRIMARY KEY NOT NULL,
	"data" text NOT NULL,
	"title" varchar NOT NULL,
	"difficulty_intended" integer NOT NULL,
	"created_by" varchar NOT NULL,
	"created_at" timestamp NOT NULL,
	"tags_json" text NOT NULL,
	"version" integer NOT NULL,
	"parent_id" varchar,
	"collection" varchar,
	"batch_id" varchar
);
--> statement-breakpoint
CREATE TABLE "values_md_history" (
	"id" varchar PRIMARY KEY NOT NULL,
	"participant_id" varchar NOT NULL,
	"markdown_text" text NOT NULL,
	"structured_json" text NOT NULL,
	"version" integer NOT NULL,
	"change_type" varchar NOT NULL,
	"generated_at" timestamp NOT NULL,
	"model_id" varchar NOT NULL,
	"judgement_count" integer NOT NULL,
	"changed_at" timestamp NOT NULL
);
--> statement-breakpoint
CREATE TABLE "values_md" (
	"participant_id" varchar PRIMARY KEY NOT NULL,
	"markdown_text" text NOT NULL,
	"structured_json" text NOT NULL,
	"generated_at" timestamp NOT NULL,
	"model_id" varchar NOT NULL,
	"judgement_count" integer NOT NULL,
	"version" integer NOT NULL,
	"last_change_type" varchar DEFAULT 'ai_generated' NOT NULL
);
--> statement-breakpoint
CREATE INDEX "ix_judgements_created_at" ON "judgements" USING btree ("created_at" timestamp_ops);--> statement-breakpoint
CREATE INDEX "ix_judgements_dilemma_id" ON "judgements" USING btree ("dilemma_id" text_ops);--> statement-breakpoint
CREATE INDEX "ix_judgements_experiment_id" ON "judgements" USING btree ("experiment_id" text_ops);--> statement-breakpoint
CREATE INDEX "ix_judgements_judge_id" ON "judgements" USING btree ("judge_id" text_ops);--> statement-breakpoint
CREATE INDEX "ix_judgements_judge_type" ON "judgements" USING btree ("judge_type" text_ops);--> statement-breakpoint
CREATE INDEX "ix_judgements_mode" ON "judgements" USING btree ("mode" text_ops);--> statement-breakpoint
CREATE INDEX "ix_judgements_repetition_number" ON "judgements" USING btree ("repetition_number" int4_ops);--> statement-breakpoint
CREATE INDEX "ix_judgements_system_prompt_type" ON "judgements" USING btree ("system_prompt_type" text_ops);--> statement-breakpoint
CREATE INDEX "ix_judgements_temperature" ON "judgements" USING btree ("temperature" float8_ops);--> statement-breakpoint
CREATE INDEX "ix_judgements_values_file_name" ON "judgements" USING btree ("values_file_name" text_ops);--> statement-breakpoint
CREATE INDEX "ix_judgements_variation_key" ON "judgements" USING btree ("variation_key" text_ops);--> statement-breakpoint
CREATE INDEX "ix_dilemmas_batch_id" ON "dilemmas" USING btree ("batch_id" text_ops);--> statement-breakpoint
CREATE INDEX "ix_dilemmas_collection" ON "dilemmas" USING btree ("collection" text_ops);--> statement-breakpoint
CREATE INDEX "ix_dilemmas_created_at" ON "dilemmas" USING btree ("created_at" timestamp_ops);--> statement-breakpoint
CREATE INDEX "ix_dilemmas_created_by" ON "dilemmas" USING btree ("created_by" text_ops);--> statement-breakpoint
CREATE INDEX "ix_dilemmas_difficulty_intended" ON "dilemmas" USING btree ("difficulty_intended" int4_ops);--> statement-breakpoint
CREATE INDEX "ix_dilemmas_parent_id" ON "dilemmas" USING btree ("parent_id" text_ops);--> statement-breakpoint
CREATE INDEX "ix_dilemmas_title" ON "dilemmas" USING btree ("title" text_ops);--> statement-breakpoint
CREATE INDEX "ix_values_md_history_change_type" ON "values_md_history" USING btree ("change_type" text_ops);--> statement-breakpoint
CREATE INDEX "ix_values_md_history_changed_at" ON "values_md_history" USING btree ("changed_at" timestamp_ops);--> statement-breakpoint
CREATE INDEX "ix_values_md_history_participant_id" ON "values_md_history" USING btree ("participant_id" text_ops);
*/