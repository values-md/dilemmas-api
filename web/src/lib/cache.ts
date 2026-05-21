/**
 * Per-isolate TTL cache. Survives across requests within a single Worker
 * isolate's lifetime; rebuilt on cold start. Mirrors the simple TTL cache
 * in src/dilemmas/api/app.py and src/dilemmas/api/research_parser.py.
 *
 * Compose this BEHIND Cloudflare's edge cache: the edge catches the bulk,
 * this catches the tail of cache-miss requests that land on the same isolate.
 */
type Entry<T> = { expiresAt: number; value: T };
const store = new Map<string, Entry<unknown>>();

export async function memo<T>(key: string, ttlMs: number, loader: () => Promise<T>): Promise<T> {
  const now = Date.now();
  const hit = store.get(key) as Entry<T> | undefined;
  if (hit && hit.expiresAt > now) return hit.value;
  const value = await loader();
  store.set(key, { expiresAt: now + ttlMs, value });
  return value;
}

/** Drop a single cache entry (used by writes to invalidate related reads). */
export function bust(key: string): void {
  store.delete(key);
}

/** Drop every entry whose key starts with the given prefix. */
export function bustPrefix(prefix: string): void {
  for (const k of store.keys()) if (k.startsWith(prefix)) store.delete(k);
}
