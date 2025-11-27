"""Test script for alignment API endpoint.

Tests the /api/alignment/test endpoint by submitting sample judgements
and checking the response format.
"""

import asyncio
from datetime import datetime, timezone

from dilemmas.models.judgement import Judgement, HumanJudgeDetails


async def test_alignment_api():
    """Test the alignment API with sample judgements."""
    import httpx
    import os

    # API configuration
    API_URL = os.getenv("RESEARCH_API_URL", "http://127.0.0.1:8000")
    API_KEY = os.getenv("API_KEY", "dev-key-12345")

    # Create sample judgements that match LLM test data
    # Note: These need to match actual dilemma_ids and variable_values from the experiment
    sample_judgements = [
        Judgement(
            dilemma_id="test-dilemma-1",  # Replace with real dilemma ID
            judge_type="human",
            human_judge=HumanJudgeDetails(
                participant_id="test-participant-123",
            ),
            mode="theory",
            rendered_situation="Test situation",
            variable_values={"{TEST_VAR}": "test value"},
            modifier_indices=[0],
            choice_id="choice_a",
            confidence=7.5,
            perceived_difficulty=6.0,
            reasoning="Test reasoning",
        ),
    ]

    # Convert to dict for JSON serialization
    judgements_data = [j.model_dump(mode="json") for j in sample_judgements]

    print(f"Testing alignment API at {API_URL}/api/alignment/test")
    print(f"Submitting {len(judgements_data)} judgement(s)...\n")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{API_URL}/api/alignment/test",
                json=judgements_data,
                headers={"X-API-Key": API_KEY},
            )

            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print("\n✅ Success!")
                print(f"Test mode: {result.get('test_mode')}")
                print(f"Judgements submitted: {result.get('judgements_submitted')}")
                print(f"Models compared: {len(result.get('alignments', []))}")

                print("\nTop 3 alignments:")
                for i, alignment in enumerate(result.get("alignments", [])[:3], 1):
                    print(f"\n{i}. {alignment['model_name']}")
                    print(f"   Alignment score: {alignment['alignment_score']}%")
                    print(f"   Judgements compared: {alignment['judgements_compared']}")
                    print(f"   Metrics:")
                    metrics = alignment['metrics']
                    print(f"     - Choice agreement: {metrics['choice_agreement']:.1%}")
                    print(f"     - Confidence similarity: {metrics['confidence_similarity']:.1%}")
                    print(f"     - Difficulty similarity: {metrics['difficulty_similarity']:.1%}")

            else:
                print(f"\n❌ Error: {response.status_code}")
                print(response.text)

        except Exception as e:
            print(f"\n❌ Exception: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("=" * 60)
    print("Alignment API Test")
    print("=" * 60 + "\n")

    asyncio.run(test_alignment_api())
