/**
 * Copies images from ../research/<slug>/{figures,*.png} into
 * public/research-static/<slug>/... so the Worker can serve them via the
 * Assets binding. Runs as `predev` and `prebuild`.
 *
 * Idempotent: removes the destination tree first.
 */
import { cp, mkdir, readdir, rm } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const SRC = resolve(here, '../../research');
const DST = resolve(here, '../public/research-static');

const SLUG_RE = /^\d{4}-\d{2}-\d{2}-/;

async function main() {
  if (!existsSync(SRC)) {
    console.warn(`[copy-research-figures] research dir not found: ${SRC} — skipping`);
    return;
  }

  // Wipe and recreate.
  await rm(DST, { recursive: true, force: true });
  await mkdir(DST, { recursive: true });

  let copied = 0;
  for (const entry of await readdir(SRC, { withFileTypes: true })) {
    if (!entry.isDirectory() || !SLUG_RE.test(entry.name)) continue;
    const slugSrc = join(SRC, entry.name);
    const slugDst = join(DST, entry.name);

    // figures/ subdir
    const figuresSrc = join(slugSrc, 'figures');
    if (existsSync(figuresSrc)) {
      await cp(figuresSrc, join(slugDst, 'figures'), { recursive: true });
      copied++;
    }

    // Top-level images (some experiments put them at slug root)
    for (const f of await readdir(slugSrc, { withFileTypes: true })) {
      if (!f.isFile()) continue;
      if (!/\.(png|jpe?g|svg|gif|webp)$/i.test(f.name)) continue;
      await mkdir(slugDst, { recursive: true });
      await cp(join(slugSrc, f.name), join(slugDst, f.name));
    }
  }
  console.log(`[copy-research-figures] copied figures from ${copied} experiment(s) → ${DST}`);
}

main().catch((err) => {
  console.error('[copy-research-figures] failed:', err);
  process.exit(1);
});
