/**
 * Format a participant's judgements + the referenced dilemmas into the
 * structured prompt the values_generator agent expects. Mirrors
 * src/dilemmas/services/values_generator.py:_format_judgements.
 */
import type { DilemmaData, JudgementData } from '@/db/types';

export function formatJudgements(judgements: JudgementData[], dilemmas: Map<string, DilemmaData>): string {
  const lines: string[] = [`# Analysis of ${judgements.length} Ethical Judgements\n`];

  for (let i = 0; i < judgements.length; i++) {
    const j = judgements[i]!;
    const dilemma = dilemmas.get(j.dilemma_id);
    if (!dilemma) continue;

    lines.push(`## Judgement ${i + 1}: ${dilemma.title}`);
    lines.push('');
    lines.push('**Situation:**');
    lines.push(j.rendered_situation || dilemma.situation_template);
    lines.push('');
    lines.push('**Available Choices:**');
    for (const choice of dilemma.choices) {
      const marker = choice.id === j.choice_id ? '✓' : ' ';
      lines.push(`[${marker}] ${choice.id}: ${choice.description}`);
    }
    lines.push('');
    lines.push(`**Their Choice:** ${j.choice_id}`);
    lines.push('');

    if (j.confidence != null) {
      lines.push(`**Confidence:** ${j.confidence}/10\n`);
    }
    if (j.reasoning) {
      lines.push('**Their Reasoning:**');
      lines.push(j.reasoning);
      lines.push('');
    }
    if (j.variable_values && Object.keys(j.variable_values).length > 0) {
      lines.push('**Context Variables:**');
      for (const [k, v] of Object.entries(j.variable_values)) {
        lines.push(`- ${k}: ${v}`);
      }
      lines.push('');
    }
    lines.push('---\n');
  }

  return lines.join('\n');
}
