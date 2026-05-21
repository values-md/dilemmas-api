/**
 * POST /api/values/restore
 *
 * Restore a previous version of a participant's VALUES.md. Reads from
 * values_md_history by version row ID, writes back to the cache row with
 * a bumped version + 'restored' change_type, and appends a fresh history
 * row. Mirrors src/dilemmas/api/app.py:restore_values_version.
 *
 * Note: `version_id` is the *row ID* of the history entry (a UUID string),
 * not the version number. The values.md Next.js client passes it as-is.
 */
import type { APIRoute } from 'astro';
import { z } from 'zod';
import { env } from 'cloudflare:workers';
import { randomUUID } from 'node:crypto';
import { eq } from 'drizzle-orm';
import { getDb } from '@/db/client';
import { valuesMd, valuesMdHistory } from '@/db/schema';
import { requireApiKey } from '@/lib/auth';
import { jsonNoStore } from '@/lib/json-response';

const Schema = z.object({
  participant_id: z.string(),
  version_id: z.string(),
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

  const db = getDb(env.DATABASE_URL);

  const restoreRows = await db
    .select()
    .from(valuesMdHistory)
    .where(eq(valuesMdHistory.id, body.version_id))
    .limit(1);

  const restore = restoreRows[0];
  if (!restore || restore.participantId !== body.participant_id) {
    return jsonNoStore({ detail: `Version '${body.version_id}' not found` }, 404);
  }

  const existingRows = await db
    .select()
    .from(valuesMd)
    .where(eq(valuesMd.participantId, body.participant_id))
    .limit(1);
  const cur = existingRows[0];
  if (!cur) {
    return jsonNoStore(
      { detail: `No current VALUES.md found for participant '${body.participant_id}'` },
      404,
    );
  }

  const newVersion = cur.version + 1;
  const now = new Date();

  await db
    .update(valuesMd)
    .set({
      markdownText: restore.markdownText,
      structuredJson: restore.structuredJson,
      generatedAt: restore.generatedAt,
      modelId: restore.modelId,
      judgementCount: restore.judgementCount,
      version: newVersion,
      lastChangeType: 'restored',
    })
    .where(eq(valuesMd.participantId, body.participant_id));

  await db.insert(valuesMdHistory).values({
    id: randomUUID(),
    participantId: body.participant_id,
    markdownText: restore.markdownText,
    structuredJson: restore.structuredJson,
    version: newVersion,
    changeType: 'restored',
    generatedAt: restore.generatedAt,
    modelId: restore.modelId,
    judgementCount: restore.judgementCount,
    changedAt: now,
  });

  return jsonNoStore({
    success: true,
    participant_id: body.participant_id,
    version: newVersion,
    restored_from_version: restore.version,
    change_type: 'restored',
  });
};
