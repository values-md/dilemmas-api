/**
 * Per-request Drizzle client factory over the D1 binding.
 *
 * Workers reuse isolates, but we construct the client per `fetch()` so we
 * don't accidentally share state between unrelated requests. The drizzle
 * wrapper is cheap to construct; the underlying D1Database binding is
 * managed by the runtime.
 */
import { drizzle, type DrizzleD1Database } from 'drizzle-orm/d1';
import * as schema from './schema';

export type Db = DrizzleD1Database<typeof schema>;

export function getDb(d1: D1Database): Db {
  if (!d1) throw new Error('D1 binding DB is missing');
  return drizzle(d1, { schema, casing: 'snake_case' });
}
