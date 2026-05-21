/**
 * Single shared-secret auth. Matches the Python side's verify_api_key in
 * src/dilemmas/api/auth.py — same header name, same comparison.
 *
 * The secret name on the TS side is INTERNAL_API_KEY (the Python side calls
 * it API_KEY, the Next.js side calls it RESEARCH_API_KEY — all the same value).
 */
import { env } from 'cloudflare:workers';

const HEADER = 'x-api-key';

/**
 * Returns null when authorized, or a 401 Response when not.
 * Use as: `const denied = requireApiKey(req); if (denied) return denied;`
 */
export function requireApiKey(req: Request): Response | null {
  const expected = env.INTERNAL_API_KEY;
  if (!expected) {
    return jsonError(500, 'Server misconfigured: INTERNAL_API_KEY not set');
  }
  const got = req.headers.get(HEADER);
  if (!got || !timingSafeEqual(got, expected)) {
    return jsonError(401, 'Invalid or missing X-API-Key');
  }
  return null;
}

function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

export function jsonError(status: number, detail: string): Response {
  return new Response(JSON.stringify({ detail }), {
    status,
    headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
  });
}
