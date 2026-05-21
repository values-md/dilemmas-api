/**
 * Drizzle custom column type: JSON serialized into a TEXT column.
 *
 * Matches the Python side's pattern in src/dilemmas/models/db.py where
 * domain models are stored as `dilemma.model_dump_json()` into a TEXT field.
 * Both languages read/write the same string format; structural equality
 * holds after JSON.parse on either side (raw byte-equality does not — JS
 * emits raw UTF-8 while Python's json.dumps defaults to \uXXXX escapes).
 *
 * Caveat: don't combine with .default() — see drizzle-orm#818. Set defaults
 * in application code instead.
 */
import { customType } from 'drizzle-orm/pg-core';

export const jsonText = <T>(name: string) =>
  customType<{ data: T; driverData: string }>({
    dataType() {
      return 'text';
    },
    toDriver(value: T): string {
      return JSON.stringify(value);
    },
    fromDriver(value: string): T {
      return JSON.parse(value) as T;
    },
  })(name);
