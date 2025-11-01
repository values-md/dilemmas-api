# Quick Start - bench-1 Baseline Experiment

## Overview
- **Experiment ID:** `b191388e-3994-4ebd-96cc-af0d033c5230`
- **12,808 judgements** across 4 models, 20 dilemmas, 1,601 variations, 2 modes
- **Cost:** ~$62
- **Time:** ~14 hours
- **Failsafe:** Auto-resume if interrupted

## Run Overnight

```bash
cd research/2025-10-29-bench1-baseline

# Test first (dry-run)
uv run python run.py --dry-run

# Start overnight run
./start.sh

# Monitor progress
tail -f experiment.log

# Check progress (in another terminal)
uv run python check_progress.py
```

## If Interrupted

The experiment **auto-resumes** - just run again:

```bash
uv run python run.py
```

It will skip completed judgements and continue where it left off.

## After Completion

```bash
# Export data
uv run python ../../scripts/export_experiment_data.py <experiment_id> data/

# Analyze (TODO: create analyze.py)
uv run python analyze.py
```

The experiment ID is shown when you start the run.

## Files Created

- `experiment.log` - Full execution log
- Database records in `data/dilemmas.db` with `experiment_id`

## Monitoring

**Live progress:**
```bash
tail -f experiment.log
```

**Summary stats:**
```bash
uv run python check_progress.py
```

Shows:
- Total progress (X / 12,808)
- Breakdown by model and mode
- Estimated time remaining

## Troubleshooting

**Rate limit errors (429):**
- Script auto-retries with exponential backoff
- Reduces to 5 concurrent requests (conservative)
- If persistent, check OpenRouter account balance

**Database errors:**
- Logged to `experiment.log`
- Failed judgements tracked in summary
- Can retry manually after fixing

**Interrupted run:**
- Just run `uv run python run.py` again
- Auto-resumes from last checkpoint
- Safe to Ctrl+C anytime

## Expected Output

After ~14 hours:
- 12,808 judgements in database
- Linked by `experiment_id`
- Ready for export and analysis
