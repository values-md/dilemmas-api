/**
 * POST /api/values/update
 *
 * Manual edit to a participant's VALUES.md. Bumps version on the cache row,
 * appends to values_md_history with change_type='manual_edit'. Mirrors
 * src/dilemmas/api/app.py:update_values_md.
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
  markdown_text: z.string(),
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

  const existing = await db
    .select()
    .from(valuesMd)
    .where(eq(valuesMd.participantId, body.participant_id))
    .limit(1);

  if (existing.length === 0) {
    return jsonNoStore(
      { detail: `No VALUES.md found for participant '${body.participant_id}'. Generate one first.` },
      404,
    );
  }

  const cur = existing[0]!;
  const newVersion = cur.version + 1;
  const now = new Date();

  await db
    .update(valuesMd)
    .set({
      markdownText: body.markdown_text,
      version: newVersion,
      lastChangeType: 'manual_edit',
    })
    .where(eq(valuesMd.participantId, body.participant_id));

  await db.insert(valuesMdHistory).values({
    id: randomUUID(),
    participantId: body.participant_id,
    markdownText: body.markdown_text,
    structuredJson: cur.structuredJson,
    version: newVersion,
    changeType: 'manual_edit',
    generatedAt: cur.generatedAt,
    modelId: cur.modelId,
    judgementCount: cur.judgementCount,
    changedAt: now,
  });

  return jsonNoStore({
    success: true,
    participant_id: body.participant_id,
    version: newVersion,
    change_type: 'manual_edit',
  });
};
