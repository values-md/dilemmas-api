# Data Directory

This directory contains:

## Database Files
- `dilemmas.db` - Main SQLite database (auto-generated, git-ignored)
- Contains tables: `dilemmas`, `judgements`
- Initialize with: `uv run python scripts/init_db.py`
- Explore with: `uv run python scripts/explore_db.py`

## Generated Data
- `dilemmas/` - Generated dilemma test sets (JSON files)
- `results/` - Experiment results and analysis

## Notes
- Database files are git-ignored
- Generated data files can be committed for reproducibility
- Database can be recreated from scratch using initialization scripts
