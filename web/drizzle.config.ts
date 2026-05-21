import { defineConfig } from 'drizzle-kit';
import { readFileSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

// Pull DATABASE_URL from .dev.vars so drizzle-kit can connect locally without
// requiring DATABASE_URL to be exported in the shell. Path resolution is
// robust to whatever cwd / loader drizzle-kit uses.
function loadDevVars(): Record<string, string> {
  const candidates = [
    // import.meta.dirname (Node 20.11+, but undefined under some loaders)
    typeof import.meta.dirname === 'string' ? import.meta.dirname : null,
    // import.meta.url fallback
    (() => { try { return resolve(fileURLToPath(import.meta.url), '..'); } catch { return null; } })(),
    // cwd fallback (drizzle-kit runs from project root)
    process.cwd(),
  ].filter((p): p is string => Boolean(p));

  for (const dir of candidates) {
    const path = resolve(dir, '.dev.vars');
    if (!existsSync(path)) continue;
    const text = readFileSync(path, 'utf8');
    const out: Record<string, string> = {};
    for (const line of text.split(/\r?\n/)) {
      const m = line.match(/^\s*([A-Z_][A-Z0-9_]*)\s*=\s*"?([^"\n]*)"?\s*$/);
      if (m) out[m[1]] = m[2];
    }
    return out;
  }
  return {};
}

const dev = loadDevVars();
const url = process.env.DATABASE_URL || dev.DATABASE_URL;
if (!url) {
  throw new Error('DATABASE_URL not set in environment or web/.dev.vars');
}

export default defineConfig({
  dialect: 'postgresql',
  schema: './src/db/schema.ts',
  out: './drizzle',
  dbCredentials: { url },
  casing: 'snake_case',
  introspect: { casing: 'camel' },
});
