"""Analyze OpenRouter costs and timing for bench-1 baseline experiment."""

import pandas as pd
import numpy as np
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

# Load data
df = pd.read_csv('data/openrouter_activity_bench_1.csv')

console.print("\n[bold cyan]═══════════════════════════════════════════════════[/bold cyan]")
console.print("[bold cyan]OpenRouter Cost & Performance Analysis[/bold cyan]")
console.print("[bold cyan]bench-1 Baseline Experiment[/bold cyan]")
console.print("[bold cyan]═══════════════════════════════════════════════════[/bold cyan]\n")

# Parse dates
df['created_at'] = pd.to_datetime(df['created_at'])

# Overall stats
console.print("[bold]Overall Statistics:[/bold]")
console.print(f"  Total API calls: {len(df):,}")
console.print(f"  Date range: {df['created_at'].min()} to {df['created_at'].max()}")
console.print(f"  Duration: {(df['created_at'].max() - df['created_at'].min()).total_seconds() / 3600:.1f} hours")

# Cost analysis
total_cost = df['cost_total'].sum()
total_cache_savings = df['cost_cache'].sum()  # Negative values are savings
net_cost = total_cost + total_cache_savings

console.print(f"\n[bold]Cost Analysis:[/bold]")
console.print(f"  Gross cost: ${total_cost:.2f}")
console.print(f"  Cache savings: ${abs(total_cache_savings):.2f}")
console.print(f"  Net cost: [bold green]${net_cost:.2f}[/bold green]")

# By model
console.print(f"\n[bold]Cost by Model:[/bold]")
by_model = df.groupby('model_permaslug').agg({
    'cost_total': 'sum',
    'cost_cache': 'sum',
    'generation_id': 'count',
    'tokens_prompt': 'sum',
    'tokens_completion': 'sum',
    'generation_time_ms': 'mean'
}).round(2)

by_model['net_cost'] = by_model['cost_total'] + by_model['cost_cache']
by_model['cost_per_call'] = by_model['net_cost'] / by_model['generation_id']
by_model = by_model.sort_values('net_cost', ascending=False)

table = Table(show_header=True)
table.add_column("Model", style="cyan")
table.add_column("Calls", justify="right", style="yellow")
table.add_column("Net Cost", justify="right", style="green")
table.add_column("$/Call", justify="right")
table.add_column("Avg Time (s)", justify="right")

for model, row in by_model.iterrows():
    table.add_row(
        model.split('/')[-1],
        f"{int(row['generation_id']):,}",
        f"${row['net_cost']:.2f}",
        f"${row['cost_per_call']:.4f}",
        f"{row['generation_time_ms']/1000:.1f}"
    )

console.print(table)

# Token usage
console.print(f"\n[bold]Token Usage:[/bold]")
total_prompt = df['tokens_prompt'].sum()
total_completion = df['tokens_completion'].sum()
total_tokens = total_prompt + total_completion

console.print(f"  Total tokens: {total_tokens:,}")
console.print(f"    Prompt: {total_prompt:,} ({total_prompt/total_tokens*100:.1f}%)")
console.print(f"    Completion: {total_completion:,} ({total_completion/total_tokens*100:.1f}%)")
console.print(f"  Cost per 1M tokens: ${net_cost / (total_tokens/1_000_000):.2f}")

# Reasoning tokens
if 'tokens_reasoning' in df.columns and df['tokens_reasoning'].notna().any():
    total_reasoning = df['tokens_reasoning'].sum()
    console.print(f"    Reasoning: {total_reasoning:,}")

# Timing analysis
console.print(f"\n[bold]Performance by Model:[/bold]")
timing = df.groupby('model_permaslug').agg({
    'generation_time_ms': ['mean', 'median', 'std', 'min', 'max']
}).round(0)

timing_table = Table(show_header=True)
timing_table.add_column("Model", style="cyan")
timing_table.add_column("Mean (s)", justify="right")
timing_table.add_column("Median (s)", justify="right")
timing_table.add_column("Std Dev (s)", justify="right")
timing_table.add_column("Min (s)", justify="right")
timing_table.add_column("Max (s)", justify="right")

for model in timing.index:
    mean_ms = timing.loc[model, ('generation_time_ms', 'mean')]
    median_ms = timing.loc[model, ('generation_time_ms', 'median')]
    std_ms = timing.loc[model, ('generation_time_ms', 'std')]
    min_ms = timing.loc[model, ('generation_time_ms', 'min')]
    max_ms = timing.loc[model, ('generation_time_ms', 'max')]

    timing_table.add_row(
        model.split('/')[-1],
        f"{mean_ms/1000:.1f}",
        f"{median_ms/1000:.1f}",
        f"{std_ms/1000:.1f}",
        f"{min_ms/1000:.1f}",
        f"{max_ms/1000:.1f}"
    )

console.print(timing_table)

# Cache hit analysis
console.print(f"\n[bold]Cache Performance:[/bold]")
cache_hits = (df['cost_cache'] < 0).sum()
cache_hit_rate = cache_hits / len(df) * 100
console.print(f"  Cache hits: {cache_hits:,} / {len(df):,} ({cache_hit_rate:.1f}%)")
console.print(f"  Total savings from cache: ${abs(total_cache_savings):.2f}")
console.print(f"  Avg savings per hit: ${abs(total_cache_savings) / cache_hits:.4f}")

# Efficiency metrics
console.print(f"\n[bold]Efficiency Metrics:[/bold]")
console.print(f"  Cost per judgement: ${net_cost / 12802:.4f} (12,802 judgements)")
console.print(f"  Judgements per dollar: {12802 / net_cost:.1f}")
console.print(f"  Total experiment time: {(df['created_at'].max() - df['created_at'].min()).total_seconds() / 3600:.1f} hours")
console.print(f"  Avg time per judgement: {len(df) / 12802 * (df['generation_time_ms'].mean() / 1000):.1f}s")

# Cost breakdown by operation type (theory vs action, based on finish reason)
console.print(f"\n[bold]By Finish Reason:[/bold]")
by_finish = df.groupby('finish_reason_normalized').agg({
    'cost_total': 'sum',
    'cost_cache': 'sum',
    'generation_id': 'count'
}).round(2)
by_finish['net_cost'] = by_finish['cost_total'] + by_finish['cost_cache']

for reason, row in by_finish.iterrows():
    pct = row['generation_id'] / len(df) * 100
    console.print(f"  {reason}: {int(row['generation_id']):,} calls ({pct:.1f}%) - ${row['net_cost']:.2f}")

# Hourly cost distribution
console.print(f"\n[bold]Cost Over Time:[/bold]")
df['hour'] = df['created_at'].dt.floor('H')
hourly = df.groupby('hour').agg({
    'cost_total': 'sum',
    'cost_cache': 'sum',
    'generation_id': 'count'
})
hourly['net_cost'] = hourly['cost_total'] + hourly['cost_cache']

console.print(f"  Peak hour cost: ${hourly['net_cost'].max():.2f}")
console.print(f"  Avg hourly cost: ${hourly['net_cost'].mean():.2f}")
console.print(f"  Hours active: {len(hourly)}")

# Cancelled/failed calls
cancelled = df[df['cancelled'] == True]
if len(cancelled) > 0:
    console.print(f"\n[bold yellow]Cancelled Calls:[/bold yellow]")
    console.print(f"  Total cancelled: {len(cancelled)}")
    console.print(f"  Cost of cancelled: ${cancelled['cost_total'].sum():.2f}")

console.print("\n[bold cyan]═══════════════════════════════════════════════════[/bold cyan]\n")

# Save summary
summary = {
    'total_calls': len(df),
    'total_cost': total_cost,
    'cache_savings': abs(total_cache_savings),
    'net_cost': net_cost,
    'cost_per_judgement': net_cost / 12802,
    'total_tokens': int(total_tokens),
    'total_prompt_tokens': int(total_prompt),
    'total_completion_tokens': int(total_completion),
    'cache_hit_rate': cache_hit_rate,
    'duration_hours': (df['created_at'].max() - df['created_at'].min()).total_seconds() / 3600,
    'by_model': by_model.to_dict('index')
}

import json
with open('output/cost_analysis.json', 'w') as f:
    json.dump(summary, f, indent=2)

console.print("[green]✓ Saved cost analysis to output/cost_analysis.json[/green]\n")
