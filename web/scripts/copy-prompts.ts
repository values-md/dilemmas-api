/**
 * Copy prompt files from ../prompts/ into web/src/prompts/ so they can be
 * bundled into the Worker via Vite's `?raw` imports. Runs as `predev` and
 * `prebuild`.
 *
 * Idempotent.
 */
import { cp, mkdir, rm } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const SRC = resolve(here, '../../prompts');
const DST = resolve(here, '../src/prompts');

async function main() {
  if (!existsSync(SRC)) {
    console.warn(`[copy-prompts] prompts dir not found: ${SRC} — skipping`);
    return;
  }
  await rm(DST, { recursive: true, force: true });
  await mkdir(DST, { recursive: true });
  await cp(SRC, DST, { recursive: true });
  console.log(`[copy-prompts] copied ${SRC} → ${DST}`);
}

main().catch((err) => {
  console.error('[copy-prompts] failed:', err);
  process.exit(1);
});
