/**
 * Per-request Drizzle client factory.
 *
 * Workers reuse isolates, but we construct the client per `fetch()` so we
 * don't accidentally share state between unrelated requests. neon-http
 * is cheap to construct.
 */
import { drizzle, type NeonHttpDatabase } from 'drizzle-orm/neon-http';
import { neon } from '@neondatabase/serverless';
import * as schema from './schema';

export type Db = NeonHttpDatabase<typeof schema>;

export function getDb(url: string): Db {
  if (!url) throw new Error('DATABASE_URL is empty');
  return drizzle(neon(url), { schema, casing: 'snake_case' });
}
