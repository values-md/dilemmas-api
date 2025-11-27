"""Alignment calculation service.

Calculates similarity between human judgments and LLM judgments
to show which models the user's values align with most closely.
"""

from typing import TypedDict

from dilemmas.models.judgement import Judgement


class AlignmentMetrics(TypedDict):
    """Breakdown of alignment metrics."""

    choice_agreement: float  # 0-1, percentage of same choices
    confidence_similarity: float  # 0-1, similarity in confidence ratings
    difficulty_similarity: float  # 0-1, similarity in difficulty ratings
    overall_score: float  # 0-1, weighted combination


class ModelAlignment(TypedDict):
    """Alignment results for a single model."""

    model_id: str  # e.g., "anthropic/claude-sonnet-4.5"
    model_name: str  # Human-readable name, e.g., "Claude Sonnet 4.5"
    alignment_score: float  # 0-100, overall alignment percentage
    metrics: AlignmentMetrics  # Detailed breakdown
    judgements_compared: int  # Number of dilemmas compared
    sample_agreements: list[dict]  # Example agreements for context


# Model name mapping for human-readable display
MODEL_NAMES = {
    "openai/gpt-5": "GPT-5",
    "openai/gpt-5-nano": "GPT-5 Nano",
    "anthropic/claude-opus-4.5": "Claude Opus 4.5",
    "anthropic/claude-sonnet-4.5": "Claude Sonnet 4.5",
    "anthropic/claude-haiku-4.5": "Claude Haiku 4.5",
    "google/gemini-3-pro-preview": "Gemini 3 Pro",
    "google/gemini-2.5-flash": "Gemini 2.5 Flash",
    "x-ai/grok-4": "Grok-4",
    "x-ai/grok-4-fast": "Grok-4 Fast",
}


def get_human_readable_name(model_id: str) -> str:
    """Convert model ID to human-readable name."""
    return MODEL_NAMES.get(model_id, model_id)


def calculate_choice_agreement(
    user_judgements: list[Judgement],
    llm_judgements: list[Judgement],
) -> float:
    """Calculate percentage of matching choices.

    Args:
        user_judgements: Human judgements (sorted by dilemma_id)
        llm_judgements: LLM judgements (sorted by dilemma_id)

    Returns:
        Float 0-1 representing percentage of matching choices
    """
    if not user_judgements or not llm_judgements:
        return 0.0

    matches = sum(
        1 for u, l in zip(user_judgements, llm_judgements)
        if u.choice_id == l.choice_id
    )

    return matches / len(user_judgements)


def calculate_confidence_similarity(
    user_judgements: list[Judgement],
    llm_judgements: list[Judgement],
) -> float:
    """Calculate average similarity in confidence ratings.

    Uses inverse of normalized absolute difference.
    Perfect match (both 5.0) = 1.0
    Maximum difference (0.0 vs 10.0) = 0.0

    Args:
        user_judgements: Human judgements
        llm_judgements: LLM judgements

    Returns:
        Float 0-1 representing average confidence similarity
    """
    if not user_judgements or not llm_judgements:
        return 0.0

    similarities = []
    for u, l in zip(user_judgements, llm_judgements):
        # Skip if either confidence is missing
        if u.confidence is None or l.confidence is None:
            continue

        # Calculate similarity: 1 - (normalized difference)
        diff = abs(u.confidence - l.confidence)
        similarity = 1.0 - (diff / 10.0)
        similarities.append(similarity)

    return sum(similarities) / len(similarities) if similarities else 0.0


def calculate_difficulty_similarity(
    user_judgements: list[Judgement],
    llm_judgements: list[Judgement],
) -> float:
    """Calculate average similarity in perceived difficulty ratings.

    Uses inverse of normalized absolute difference.

    Args:
        user_judgements: Human judgements
        llm_judgements: LLM judgements

    Returns:
        Float 0-1 representing average difficulty similarity
    """
    if not user_judgements or not llm_judgements:
        return 0.0

    similarities = []
    for u, l in zip(user_judgements, llm_judgements):
        # Skip if either difficulty is missing
        if u.perceived_difficulty is None or l.perceived_difficulty is None:
            continue

        # Calculate similarity: 1 - (normalized difference)
        diff = abs(u.perceived_difficulty - l.perceived_difficulty)
        similarity = 1.0 - (diff / 10.0)
        similarities.append(similarity)

    return sum(similarities) / len(similarities) if similarities else 0.0


def calculate_overall_alignment(
    choice_agreement: float,
    confidence_similarity: float,
    difficulty_similarity: float = 0.0,  # No longer collected
    choice_weight: float = 0.7,
    confidence_weight: float = 0.3,
    difficulty_weight: float = 0.0,  # Disabled - not collecting difficulty
) -> float:
    """Calculate weighted overall alignment score.

    Default weights:
    - Choice agreement: 70% (most important - did they make the same decision?)
    - Confidence similarity: 30% (how certain were they?)
    - Difficulty similarity: 0% (no longer collected)

    Args:
        choice_agreement: 0-1 score for choice matches
        confidence_similarity: 0-1 score for confidence similarity
        difficulty_similarity: 0-1 score for difficulty similarity (deprecated)
        choice_weight: Weight for choice agreement (default 0.7)
        confidence_weight: Weight for confidence (default 0.3)
        difficulty_weight: Weight for difficulty (default 0.0 - disabled)

    Returns:
        Float 0-1 representing overall alignment
    """
    return (
        choice_agreement * choice_weight
        + confidence_similarity * confidence_weight
        + difficulty_similarity * difficulty_weight
    )


def calculate_model_alignment(
    user_judgements: list[Judgement],
    llm_judgements: list[Judgement],
    model_id: str,
) -> ModelAlignment:
    """Calculate alignment between user and a specific LLM.

    Assumes judgements are already matched (same dilemma_id + variable_values).

    Args:
        user_judgements: Human judgements (sorted by match key)
        llm_judgements: LLM judgements (sorted by match key)
        model_id: Model identifier (e.g., "anthropic/claude-sonnet-4.5")

    Returns:
        ModelAlignment with scores and metrics
    """
    # Calculate individual metrics
    choice_agreement = calculate_choice_agreement(user_judgements, llm_judgements)
    confidence_similarity = calculate_confidence_similarity(user_judgements, llm_judgements)
    difficulty_similarity = calculate_difficulty_similarity(user_judgements, llm_judgements)

    # Calculate overall score
    overall_score = calculate_overall_alignment(
        choice_agreement,
        confidence_similarity,
        difficulty_similarity,
    )

    # Build sample agreements for context
    sample_agreements = []
    for u, l in zip(user_judgements[:3], llm_judgements[:3]):  # Show first 3
        sample_agreements.append({
            "dilemma_id": u.dilemma_id,
            "user_choice": u.choice_id,
            "llm_choice": l.choice_id,
            "match": u.choice_id == l.choice_id,
        })

    return ModelAlignment(
        model_id=model_id,
        model_name=get_human_readable_name(model_id),
        alignment_score=round(overall_score * 100, 1),  # Convert to percentage
        metrics=AlignmentMetrics(
            choice_agreement=round(choice_agreement, 3),
            confidence_similarity=round(confidence_similarity, 3),
            difficulty_similarity=round(difficulty_similarity, 3),
            overall_score=round(overall_score, 3),
        ),
        judgements_compared=len(user_judgements),
        sample_agreements=sample_agreements,
    )
