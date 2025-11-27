"""Fix tool_name mapping in existing dilemmas.

For dilemmas that have available_tools but no tool_name set in choices,
this script infers the mapping and updates the database.

Strategy:
1. For dilemmas with same number of choices and tools: use LLM to map
2. For dilemmas without tools: skip (don't need action mode)
3. For mismatches: report and skip
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from dilemmas.db.database import get_session
from dilemmas.llm.openrouter import create_openrouter_model
from dilemmas.models.db import DilemmaDB
from dilemmas.models.dilemma import Dilemma

console = Console()

# Database setup
DATABASE_URL = "sqlite+aiosqlite:///data/dilemmas.db"
engine = create_async_engine(DATABASE_URL, echo=False)


class ChoiceToolPair(BaseModel):
    """A single choice-to-tool mapping."""

    choice_id: str = Field(..., description="The choice ID (e.g., 'notify', 'wait')")
    tool_name: str = Field(..., description="The tool name this choice should call")


class ToolMapping(BaseModel):
    """Mapping from choice IDs to tool names."""

    mappings: list[ChoiceToolPair] = Field(
        ...,
        description="List of choice-to-tool mappings. Each choice must map to exactly one tool.",
    )


async def infer_mapping(dilemma: Dilemma) -> dict[str, str]:
    """Use LLM to infer which choice maps to which tool.

    Args:
        dilemma: Dilemma with choices and available_tools

    Returns:
        Dict mapping choice_id -> tool_name
    """
    # Format choices
    choices_text = "\n".join([
        f"- **{c.id}**: {c.label} - {c.description}"
        for c in dilemma.choices
    ])

    # Format tools
    tools_text = "\n".join([
        f"- **{t.name}**: {t.description}"
        for t in dilemma.available_tools
    ])

    prompt = f"""Map each choice to the most appropriate tool.

**Dilemma**: {dilemma.title}

**Choices** (need tool_name):
{choices_text}

**Available Tools**:
{tools_text}

---

For each choice, determine which tool would be called to execute that action.
The mapping should be semantically coherent - the tool should make sense for the choice.

Return a list of (choice_id, tool_name) tuples. Each choice must map to exactly one tool.
"""

    # Create agent
    agent = Agent(
        create_openrouter_model("openai/gpt-4.1-mini", temperature=0.3),
        output_type=ToolMapping,
    )

    result = await agent.run(prompt)
    mapping: ToolMapping = result.output

    # Convert to dict
    return {pair.choice_id: pair.tool_name for pair in mapping.mappings}


async def fix_dilemmas():
    """Fix tool mapping for all dilemmas."""
    console.print("\n[bold cyan]Fixing Tool Mappings in Existing Dilemmas[/bold cyan]\n")

    async with AsyncSession(engine) as session:
        # Load all dilemmas
        result = await session.exec(select(DilemmaDB))
        dilemma_dbs = result.all()
        dilemmas = [db.to_domain() for db in dilemma_dbs]

        console.print(f"Found {len(dilemmas)} dilemmas\n")

        # Analyze
        needs_fixing = []
        already_good = []
        no_tools = []
        mismatches = []

        for dilemma in dilemmas:
            has_tools = len(dilemma.available_tools) > 0
            choices_with_tools = sum(1 for c in dilemma.choices if c.tool_name is not None)

            if not has_tools:
                no_tools.append(dilemma)
            elif choices_with_tools == len(dilemma.choices):
                already_good.append(dilemma)
            elif len(dilemma.choices) == len(dilemma.available_tools):
                needs_fixing.append(dilemma)
            else:
                mismatches.append(dilemma)

        # Report
        table = Table(title="Dilemma Status")
        table.add_column("Category", style="cyan")
        table.add_column("Count", style="yellow", justify="right")
        table.add_column("Action", style="green")

        table.add_row("Already mapped", str(len(already_good)), "✓ Skip")
        table.add_row("No tools", str(len(no_tools)), "✓ Skip (theory mode only)")
        table.add_row("Needs fixing", str(len(needs_fixing)), "→ Fix with LLM")
        table.add_row("Mismatches", str(len(mismatches)), "⚠ Manual review needed")

        console.print(table)
        console.print()

        if not needs_fixing:
            console.print("[green]✓ All dilemmas are already correctly mapped![/green]")
            return

        # Fix dilemmas
        console.print(f"\n[yellow]Fixing {len(needs_fixing)} dilemmas...[/yellow]\n")

        for i, dilemma in enumerate(needs_fixing, 1):
            console.print(f"[{i}/{len(needs_fixing)}] {dilemma.title[:60]}...")

            try:
                # Infer mapping
                mapping = await infer_mapping(dilemma)

                # Validate mapping
                tool_names = {t.name for t in dilemma.available_tools}
                for choice_id, tool_name in mapping.items():
                    if tool_name not in tool_names:
                        console.print(
                            f"  [red]✗ Invalid mapping: {choice_id} → {tool_name} (not in available_tools)[/red]"
                        )
                        continue

                # Apply mapping
                for choice in dilemma.choices:
                    if choice.id in mapping:
                        choice.tool_name = mapping[choice.id]

                # Save to database
                dilemma_db = DilemmaDB.from_domain(dilemma)
                await session.merge(dilemma_db)
                await session.commit()

                # Show mapping
                for choice in dilemma.choices:
                    console.print(f"  ✓ {choice.id} → {choice.tool_name}")

            except Exception as e:
                console.print(f"  [red]✗ Error: {e}[/red]")
                continue

        console.print("\n[green]✓ Tool mapping complete![/green]")

        # Show mismatches that need manual review
        if mismatches:
            console.print("\n[yellow]⚠ Dilemmas needing manual review:[/yellow]")
            for dilemma in mismatches:
                console.print(
                    f"  - {dilemma.title}: {len(dilemma.choices)} choices, {len(dilemma.available_tools)} tools"
                )


if __name__ == "__main__":
    asyncio.run(fix_dilemmas())
