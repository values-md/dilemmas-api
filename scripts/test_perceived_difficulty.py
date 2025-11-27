"""Test that perceived_difficulty field works correctly."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dilemmas.models.judgement import Judgement
from dilemmas.services.judge import JudgementDecision

# Test that we can create a JudgementDecision with the new field
decision = JudgementDecision(
    choice_id='test',
    reasoning='This is a test reasoning that is long enough to meet minimum requirements',
    confidence=7.5,
    perceived_difficulty=8.0
)
print('✓ JudgementDecision created with perceived_difficulty')
print(f'  Confidence: {decision.confidence}')
print(f'  Difficulty: {decision.perceived_difficulty}')

# Test that old judgements without the field still load
old_judgement_json = {
    'id': 'test-123',
    'dilemma_id': 'dilemma-456',
    'judge_type': 'ai',
    'mode': 'theory',
    'rendered_situation': 'Test situation',
    'choice_id': 'choice1',
    'confidence': 7.0,
    'reasoning': 'Test reasoning',
    'created_at': '2025-01-01T00:00:00',
    'ai_judge': {
        'model_id': 'test-model',
        'temperature': 1.0,
        'system_prompt_type': 'none'
    }
}

judgement = Judgement(**old_judgement_json)
print(f'\n✓ Old judgement loaded without perceived_difficulty')
print(f'  perceived_difficulty defaults to: {judgement.perceived_difficulty}')

# Test that new judgements with the field work
new_judgement_json = {
    **old_judgement_json,
    'id': 'test-456',
    'perceived_difficulty': 9.0
}

judgement2 = Judgement(**new_judgement_json)
print(f'\n✓ New judgement loaded with perceived_difficulty')
print(f'  perceived_difficulty: {judgement2.perceived_difficulty}')

print('\n✅ All tests passed! Field is backward compatible.')
