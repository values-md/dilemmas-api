"""Export experiment data to CSV and JSON for analysis and reproducibility.

Exports both CSV (for easy analysis) and JSON (for complete reproducibility).

Usage:
    uv run python scripts/export_experiment_data.py <experiment_id> <output_dir>
"""

import asyncio
import csv
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, stdev

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlmodel import select

from dilemmas.db.database import get_database
from dilemmas.models.db import DilemmaDB, JudgementDB


async def export_experiment_data(experiment_id: str, output_dir: Path):
    """Export experiment data to CSV and JSON for complete reproducibility.

    Creates CSV files (in output_dir):
    - raw_judgements.csv: All judgements with full details
    - summary_by_condition.csv: Aggregated metrics by (model, dilemma, temp)
    - summary_by_temperature.csv: Aggregated metrics by temperature

    Creates JSON files (in output_dir.parent):
    - dilemmas.json: Complete dilemma objects used in experiment
    - judgements.json: All judgements with full data
    - config.json: Experiment configuration and metadata

    This makes experiments completely self-contained and future-proof.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    db = get_database()
    async for session in db.get_session():
        # Load all judgements for this experiment
        statement = select(JudgementDB).where(JudgementDB.experiment_id == experiment_id)
        result = await session.execute(statement)
        judgement_dbs = result.scalars().all()

        if not judgement_dbs:
            print(f"No judgements found for experiment {experiment_id}")
            return

        judgements = [jdb.to_domain() for jdb in judgement_dbs]

        # Load dilemma titles
        dilemma_ids = list(set(j.dilemma_id for j in judgements))
        dilemma_statement = select(DilemmaDB).where(DilemmaDB.id.in_(dilemma_ids))
        dilemma_result = await session.execute(dilemma_statement)
        dilemmas_map = {d.id: d.to_domain() for d in dilemma_result.scalars().all()}

        # 1. Export raw judgements
        raw_file = output_dir / "raw_judgements.csv"
        with open(raw_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "judgement_id", "model_id", "dilemma_id", "dilemma_title",
                "temperature", "repetition_number", "choice_id", "confidence",
                "reasoning_length", "response_time_ms"
            ])

            for j in judgements:
                dilemma_title = dilemmas_map.get(j.dilemma_id).title if j.dilemma_id in dilemmas_map else "Unknown"
                writer.writerow([
                    j.id,
                    j.get_judge_id(),
                    j.dilemma_id,
                    dilemma_title,
                    j.ai_judge.temperature if j.ai_judge else None,
                    j.repetition_number,
                    j.choice_id,
                    j.confidence,
                    len(j.reasoning) if j.reasoning else 0,
                    j.response_time_ms,
                ])

        print(f"✓ Exported {len(judgements)} raw judgements to {raw_file}")

        # 2. Compute and export summary by condition
        from collections import Counter

        groups = defaultdict(list)
        for j in judgements:
            key = (j.get_judge_id(), j.dilemma_id, j.ai_judge.temperature if j.ai_judge else None)
            groups[key].append(j)

        condition_file = output_dir / "summary_by_condition.csv"
        with open(condition_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "model_id", "dilemma_id", "dilemma_title", "temperature",
                "repetitions", "choice_consistency_pct", "most_common_choice",
                "avg_confidence", "confidence_stddev", "avg_response_time_ms"
            ])

            for (model_id, dilemma_id, temperature), group_judgements in sorted(groups.items()):
                dilemma_title = dilemmas_map.get(dilemma_id).title if dilemma_id in dilemmas_map else "Unknown"

                # Choice consistency
                choices = [j.choice_id for j in group_judgements if j.choice_id]
                if choices:
                    choice_counts = Counter(choices)
                    most_common_choice, most_common_count = choice_counts.most_common(1)[0]
                    choice_consistency = most_common_count / len(choices) * 100
                else:
                    most_common_choice = "N/A"
                    choice_consistency = 0.0

                # Confidence stats
                confidences = [j.confidence for j in group_judgements if j.confidence is not None]
                avg_confidence = mean(confidences) if confidences else 0.0
                confidence_stddev = stdev(confidences) if len(confidences) >= 2 else 0.0

                # Response time
                response_times = [j.response_time_ms for j in group_judgements if j.response_time_ms]
                avg_response_time = mean(response_times) if response_times else 0.0

                writer.writerow([
                    model_id,
                    dilemma_id,
                    dilemma_title,
                    temperature,
                    len(group_judgements),
                    round(choice_consistency, 1),
                    most_common_choice,
                    round(avg_confidence, 2),
                    round(confidence_stddev, 2),
                    round(avg_response_time, 0),
                ])

        print(f"✓ Exported summary by condition to {condition_file}")

        # 3. Compute and export summary by temperature
        temp_groups = defaultdict(lambda: {
            "choice_consistency": [],
            "confidence_mean": [],
            "confidence_std": [],
            "response_time": []
        })

        for (model_id, dilemma_id, temperature), group_judgements in groups.items():
            choices = [j.choice_id for j in group_judgements if j.choice_id]
            if choices:
                choice_counts = Counter(choices)
                most_common_count = choice_counts.most_common(1)[0][1]
                choice_consistency = most_common_count / len(choices) * 100
                temp_groups[temperature]["choice_consistency"].append(choice_consistency)

            confidences = [j.confidence for j in group_judgements if j.confidence is not None]
            if confidences:
                temp_groups[temperature]["confidence_mean"].append(mean(confidences))
                if len(confidences) >= 2:
                    temp_groups[temperature]["confidence_std"].append(stdev(confidences))

            response_times = [j.response_time_ms for j in group_judgements if j.response_time_ms]
            if response_times:
                temp_groups[temperature]["response_time"].append(mean(response_times))

        temp_file = output_dir / "summary_by_temperature.csv"
        with open(temp_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "temperature", "avg_choice_consistency_pct", "avg_confidence_mean",
                "avg_confidence_stddev", "avg_response_time_ms"
            ])

            for temp in sorted(temp_groups.keys()):
                data = temp_groups[temp]
                writer.writerow([
                    temp,
                    round(mean(data["choice_consistency"]), 1) if data["choice_consistency"] else 0,
                    round(mean(data["confidence_mean"]), 2) if data["confidence_mean"] else 0,
                    round(mean(data["confidence_std"]), 2) if data["confidence_std"] else 0,
                    round(mean(data["response_time"]), 0) if data["response_time"] else 0,
                ])

        print(f"✓ Exported summary by temperature to {temp_file}")

        # 4. Export complete data as JSON for reproducibility

        # Export dilemmas
        dilemmas_file = output_dir.parent / "dilemmas.json"
        dilemmas_data = [d.model_dump(mode='json') for d in dilemmas_map.values()]
        with open(dilemmas_file, 'w') as f:
            json.dump(dilemmas_data, f, indent=2, default=str)
        print(f"✓ Exported {len(dilemmas_data)} dilemmas to {dilemmas_file}")

        # Export judgements
        judgements_file = output_dir.parent / "judgements.json"
        judgements_data = [j.model_dump(mode='json') for j in judgements]
        with open(judgements_file, 'w') as f:
            json.dump(judgements_data, f, indent=2, default=str)
        print(f"✓ Exported {len(judgements_data)} judgements to {judgements_file}")

        # Export config
        config_file = output_dir.parent / "config.json"

        # Extract unique models and temperatures
        models = sorted(list(set(j.get_judge_id() for j in judgements)))
        temperatures = sorted(list(set(
            j.ai_judge.temperature for j in judgements
            if j.ai_judge and j.ai_judge.temperature is not None
        )))

        # Count repetitions
        max_rep = max((j.repetition_number for j in judgements if j.repetition_number), default=0)

        config_data = {
            "experiment_id": experiment_id,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "total_judgements": len(judgements),
            "models": models,
            "temperatures": temperatures,
            "dilemmas": len(dilemmas_data),
            "repetitions": max_rep,
            "mode": judgements[0].mode if judgements else None,
            "system_prompt_type": (
                judgements[0].ai_judge.system_prompt_type
                if judgements and judgements[0].ai_judge
                else None
            ),
        }

        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        print(f"✓ Exported experiment config to {config_file}")

        print(f"\n✓ All data exported to {output_dir.parent}")
        print(f"  - CSV summaries in data/")
        print(f"  - JSON snapshots at root (dilemmas, judgements, config)")


async def main():
    if len(sys.argv) < 3:
        print("Usage: uv run python scripts/export_experiment_data.py <experiment_id> <output_dir>")
        return

    experiment_id = sys.argv[1]
    output_dir = Path(sys.argv[2])

    await export_experiment_data(experiment_id, output_dir)


if __name__ == "__main__":
    asyncio.run(main())
