"""Test VALUES.md generation with sample human judgements."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import httpx
from rich.console import Console
from rich.markdown import Markdown

console = Console()

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv(Path(__file__).parent.parent / ".env")

BASE_URL = "http://localhost:8000"
API_KEY = os.getenv("API_KEY")


async def create_test_judgements():
    """Create sample human judgements for testing."""
    console.print("\n[cyan]Step 1: Creating test judgements...[/cyan]\n")

    # Get dilemmas from bench-1
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/collections/bench-1/dilemmas")
        response.raise_for_status()
        dilemmas = response.json()

    console.print(f"Found {len(dilemmas)} dilemmas in bench-1")

    # Take first 12 dilemmas for variety
    test_dilemmas = dilemmas[:12]

    # Create judgements with different patterns
    judgements = []

    # Pattern: Fairness over efficiency (dilemmas 0-3)
    for i in range(4):
        d = test_dilemmas[i]
        # Use situationTemplate if available, otherwise situation
        situation_text = d.get("situationTemplate") or d.get("situation", "")
        judgements.append({
            "dilemma_id": d["id"],
            "choice_id": d["choices"][0]["id"],  # First choice (often fairness-oriented)
            "confidence": 8.0,
            "reasoning": "Fairness and equity are more important than speed or efficiency here",
            "response_time_ms": 30000,
            "rendered_situation": situation_text,
            "variable_values": None,
            "modifier_indices": None
        })

    # Pattern: Transparency over protection (dilemmas 4-7)
    for i in range(4, 8):
        d = test_dilemmas[i]
        situation_text = d.get("situationTemplate") or d.get("situation", "")
        judgements.append({
            "dilemma_id": d["id"],
            "choice_id": d["choices"][1]["id"] if len(d["choices"]) > 1 else d["choices"][0]["id"],
            "confidence": 7.5,
            "reasoning": "People have the right to know, even if the truth is difficult",
            "response_time_ms": 25000,
            "rendered_situation": situation_text,
            "variable_values": None,
            "modifier_indices": None
        })

    # Pattern: Individual autonomy (dilemmas 8-11)
    for i in range(8, 12):
        d = test_dilemmas[i]
        situation_text = d.get("situationTemplate") or d.get("situation", "")
        judgements.append({
            "dilemma_id": d["id"],
            "choice_id": d["choices"][0]["id"],
            "confidence": 9.0,
            "reasoning": "Individual choice should be respected, even if we disagree",
            "response_time_ms": 20000,
            "rendered_situation": situation_text,
            "variable_values": None,
            "modifier_indices": None
        })

    # Submit judgements
    payload = {
        "participant_id": "test-participant-values-md",
        "demographics": {
            "age": 35,
            "gender": "non-binary",
            "education_level": "masters",
            "country": "US"
        },
        "judgements": judgements
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/judgements",
            json=payload,
            headers={"X-API-Key": API_KEY}
        )
        response.raise_for_status()
        result = response.json()

    console.print(f"[green]✓[/green] Created {len(result['judgement_ids'])} test judgements\n")


async def test_values_generation():
    """Test VALUES.md generation."""
    console.print("[cyan]Step 2: Generating VALUES.md...[/cyan]\n")

    payload = {
        "participant_id": "test-participant-values-md",
        "model_id": "google/gemini-2.5-flash",
        "force_regenerate": False
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/values/generate",
            json=payload,
            headers={"X-API-Key": API_KEY}
        )
        response.raise_for_status()
        result = response.json()

    if result["success"]:
        console.print(f"[green]✓[/green] VALUES.md generated successfully!")
        console.print(f"  From cache: {result['from_cache']}")
        console.print(f"  Judgements analyzed: {result['judgement_count']}")
        console.print(f"  Model: {result['model_id']}")
        console.print(f"  Generated at: {result['generated_at']}\n")

        # Display markdown
        console.print("[bold]Generated VALUES.md:[/bold]\n")
        md = Markdown(result["values_md"])
        console.print(md)

    else:
        console.print(f"[red]✗[/red] Generation failed: {result['error']}")


async def test_cache_retrieval():
    """Test retrieving cached VALUES.md."""
    console.print("\n[cyan]Step 3: Testing cache retrieval...[/cyan]\n")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/values/test-participant-values-md",
            headers={"X-API-Key": API_KEY}
        )
        response.raise_for_status()
        result = response.json()

    console.print(f"[green]✓[/green] Retrieved from cache")
    console.print(f"  From cache: {result['from_cache']}")
    console.print(f"  Version: {result.get('version', 1)}")


async def cleanup():
    """Clean up test data."""
    console.print("\n[cyan]Cleaning up test data...[/cyan]\n")

    import sqlite3
    conn = sqlite3.connect("/Users/gs/dev/values.md/dilemmas/data/dilemmas.db")
    cursor = conn.cursor()

    # Delete test judgements
    cursor.execute(
        "DELETE FROM judgements WHERE judge_type = 'human' AND human_judge_participant_id = ?",
        ("test-participant-values-md",)
    )

    # Delete cached VALUES.md
    cursor.execute(
        "DELETE FROM values_md WHERE participant_id = ?",
        ("test-participant-values-md",)
    )

    conn.commit()
    conn.close()

    console.print("[green]✓[/green] Test data cleaned up\n")


async def main():
    """Run all tests."""
    console.print("\n[bold cyan]Testing VALUES.md Generation[/bold cyan]\n")
    console.print("Prerequisites:")
    console.print("  1. API server running on http://localhost:8000")
    console.print("  2. API_KEY set in .env")
    console.print("  3. bench-1 dilemmas loaded\n")

    try:
        await create_test_judgements()
        await test_values_generation()
        await test_cache_retrieval()

        console.print("\n[bold green]✓ All tests passed![/bold green]\n")

        # Ask about cleanup
        cleanup_choice = input("Clean up test data? (y/n): ")
        if cleanup_choice.lower() == "y":
            await cleanup()

    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
