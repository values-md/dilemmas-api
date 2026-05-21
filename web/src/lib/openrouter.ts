/**
 * Minimal OpenRouter client. Talks to /v1/chat/completions (OpenAI-compatible).
 *
 * Used by the 3 live LLM endpoints (values/generate, values_generate inputs,
 * etc.). We deliberately don't pull in any SDK — this is one fetch each and
 * a Zod-validated structured-output path when we need it.
 */
import { env } from 'cloudflare:workers';

interface ChatTextOpts {
  model: string;
  system: string;
  user: string;
  temperature?: number;
  maxTokens?: number;
}

interface OpenRouterResponse {
  choices: Array<{ message: { content: string } }>;
  usage?: { prompt_tokens: number; completion_tokens: number; total_tokens: number };
  error?: { message: string; type?: string };
}

const ENDPOINT = 'https://openrouter.ai/api/v1/chat/completions';

/**
 * Plain-text chat completion. Used by /api/values/generate (the model is
 * asked to output Markdown directly, no JSON wrapping).
 */
export async function chatText(opts: ChatTextOpts): Promise<string> {
  const apiKey = env.OPENROUTER_API_KEY;
  if (!apiKey) throw new Error('OPENROUTER_API_KEY not set');

  const res = await fetch(ENDPOINT, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
      'HTTP-Referer': 'https://research.values.md',
      'X-Title': 'VALUES.md research',
    },
    body: JSON.stringify({
      model: opts.model,
      messages: [
        { role: 'system', content: opts.system },
        { role: 'user', content: opts.user },
      ],
      temperature: opts.temperature ?? 0.7,
      max_tokens: opts.maxTokens ?? 4000,
    }),
  });

  const body = (await res.json()) as OpenRouterResponse;
  if (!res.ok || body.error) {
    const detail = body.error?.message ?? `HTTP ${res.status}`;
    throw new Error(`OpenRouter: ${detail}`);
  }
  const content = body.choices?.[0]?.message?.content;
  if (typeof content !== 'string') throw new Error('OpenRouter: empty completion');
  return content;
}
