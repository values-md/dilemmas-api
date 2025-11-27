#!/usr/bin/env python3
"""Validate publication-ready dataset and show summary statistics.

Quick verification that all files are present and data is valid.

Usage:
    uv run python scripts/validate_publication_data.py
"""

import json
import sys
from pathlib import Path
import pandas as pd

PUBLICATION_DIR = Path(__file__).parent.parent / "research" / "2025-10-29-when-agents-act" / "publication_ready"

def validate():
    """Validate publication dataset."""
    print("=" * 70)
    print("🔍 Validating Publication-Ready Dataset")
    print("=" * 70)

    errors = []
    warnings = []

    # 1. Check all required files exist
    print("\n📁 Checking files...")

    required_files = {
        'Core Data': [
            'dilemmas.json',
            'judgements.json',
            'dilemmas_flat.csv',
            'judgements_flat.csv',
        ],
        'Analysis Files': [
            'theory_action_paired.csv',
            'consensus_by_configuration.csv',
            'samples_reversals.csv',
            'difficulty_analysis.csv',
        ],
        'Documentation': [
            'README.md',
            'README_HF.md',
            'CODEBOOK.md',
            'LICENSE.txt',
            'findings.md',
            'config.json',
        ]
    }

    for category, files in required_files.items():
        print(f"\n  {category}:")
        for filename in files:
            path = PUBLICATION_DIR / filename
            if path.exists():
                size = path.stat().st_size
                size_str = f"{size / 1024 / 1024:.1f} MB" if size > 1024*1024 else f"{size / 1024:.0f} KB"
                print(f"    ✓ {filename:<35} {size_str:>10}")
            else:
                print(f"    ✗ {filename:<35} MISSING")
                errors.append(f"Missing file: {filename}")

    # 2. Load and validate data
    print("\n📊 Validating data...")

    try:
        # Load JSON
        with open(PUBLICATION_DIR / 'dilemmas.json') as f:
            dilemmas = json.load(f)
        print(f"  ✓ dilemmas.json loaded: {len(dilemmas)} dilemmas")

        with open(PUBLICATION_DIR / 'judgements.json') as f:
            judgements = json.load(f)
        print(f"  ✓ judgements.json loaded: {len(judgements)} judgements")

        # Load CSVs
        dilemmas_csv = pd.read_csv(PUBLICATION_DIR / 'dilemmas_flat.csv')
        print(f"  ✓ dilemmas_flat.csv loaded: {len(dilemmas_csv)} rows × {len(dilemmas_csv.columns)} columns")

        judgements_csv = pd.read_csv(PUBLICATION_DIR / 'judgements_flat.csv')
        print(f"  ✓ judgements_flat.csv loaded: {len(judgements_csv)} rows × {len(judgements_csv.columns)} columns")

        # Load theory_action_paired
        paired = pd.read_csv(PUBLICATION_DIR / 'theory_action_paired.csv')
        print(f"  ✓ theory_action_paired.csv loaded: {len(paired)} rows × {len(paired.columns)} columns")

    except Exception as e:
        errors.append(f"Data loading error: {e}")
        print(f"  ✗ Error loading data: {e}")
        return 1

    # 3. Check counts match
    print("\n🔢 Checking data consistency...")

    if len(dilemmas) != len(dilemmas_csv):
        warnings.append(f"Dilemma count mismatch: JSON={len(dilemmas)}, CSV={len(dilemmas_csv)}")
        print(f"  ⚠ Dilemma count mismatch")
    else:
        print(f"  ✓ Dilemma count matches: {len(dilemmas)}")

    if len(judgements) != len(judgements_csv):
        warnings.append(f"Judgement count mismatch: JSON={len(judgements)}, CSV={len(judgements_csv)}")
        print(f"  ⚠ Judgement count mismatch")
    else:
        print(f"  ✓ Judgement count matches: {len(judgements)}")

    # 4. Summary statistics
    print("\n📈 Dataset Statistics:")
    print(f"  • Total dilemmas: {len(dilemmas)}")
    print(f"  • Total judgements: {len(judgements)}")

    # Models
    models = judgements_csv['model_id'].unique()
    print(f"  • Models: {len(models)}")
    for model in sorted(models):
        count = (judgements_csv['model_id'] == model).sum()
        print(f"    - {model}: {count} judgements")

    # Modes
    modes = judgements_csv['mode'].value_counts()
    print(f"  • Modes:")
    for mode, count in modes.items():
        print(f"    - {mode}: {count} judgements")

    # Theory-action pairs
    print(f"  • Theory-action pairs: {len(paired)}")

    # Reversals
    if 'reversed' in paired.columns:
        reversals = paired['reversed'].sum()
        reversal_rate = (reversals / len(paired)) * 100
        print(f"  • Decision reversals: {reversals} ({reversal_rate:.1f}%)")

    # 5. Check key fields
    print("\n🔑 Checking key fields...")

    required_judgement_fields = [
        'judgement_id', 'dilemma_id', 'model_id', 'mode',
        'choice_id', 'confidence', 'perceived_difficulty'
    ]

    for field in required_judgement_fields:
        if field not in judgements_csv.columns:
            errors.append(f"Missing field in judgements_flat.csv: {field}")
            print(f"  ✗ Missing: {field}")
        else:
            missing = judgements_csv[field].isna().sum()
            if missing > 0:
                warnings.append(f"{field} has {missing} missing values")
                print(f"  ⚠ {field}: {missing} missing values")
            else:
                print(f"  ✓ {field}: complete")

    # 6. Final summary
    print("\n" + "=" * 70)
    if errors:
        print("❌ VALIDATION FAILED")
        print("\nErrors:")
        for error in errors:
            print(f"  • {error}")
    elif warnings:
        print("⚠️  VALIDATION PASSED WITH WARNINGS")
        print("\nWarnings:")
        for warning in warnings:
            print(f"  • {warning}")
    else:
        print("✅ ALL CHECKS PASSED!")

    print("=" * 70)

    print(f"\n📂 Dataset location: {PUBLICATION_DIR}")

    print("\n🚀 Ready to upload!")
    print("\nNext steps:")
    print("  1. Kaggle: https://www.kaggle.com/datasets (upload all files)")
    print("  2. Hugging Face: https://huggingface.co/new-dataset (rename README_HF.md → README.md)")

    return 0 if not errors else 1

if __name__ == "__main__":
    sys.exit(validate())
