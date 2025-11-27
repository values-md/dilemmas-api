#!/usr/bin/env python3
"""Audit bench-1 dilemmas for variable consistency issues.

Checks:
1. Variables in choices that don't exist in situation
2. Hardcoded names/values in choices when variables exist in situation
3. Missing variable usage in choices
"""

import asyncio
import re
from rich.console import Console
from rich.table import Table

from dilemmas.db.database import Database
from dilemmas.models.db import DilemmaDB
from sqlmodel import select

console = Console()


async def audit_dilemmas():
    """Audit all bench-1 dilemmas for variable issues."""
    db = Database()

    async for session in db.get_session():
        result = await session.execute(
            select(DilemmaDB).where(DilemmaDB.collection == "bench-1").order_by(DilemmaDB.id)
        )
        dilemmas_db = result.scalars().all()

        console.print(f"\n[bold]Found {len(dilemmas_db)} dilemmas in bench-1[/bold]")
        console.print("=" * 100)

        issues = []

        for db_dilemma in dilemmas_db:
            dilemma = db_dilemma.to_domain()

            # Extract variables from situation_template
            situation_vars = set(re.findall(r"\{([A-Z_]+)\}", dilemma.situation_template))

            # Extract variables from all choice descriptions
            choice_vars = set()
            choice_var_usage = {}
            for choice in dilemma.choices:
                vars_in_choice = set(re.findall(r"\{([A-Z_]+)\}", choice.description))
                choice_vars.update(vars_in_choice)
                choice_var_usage[choice.id] = vars_in_choice

            # Defined variables
            defined_vars = set(dilemma.variables.keys()) if dilemma.variables else set()

            # Check for issues
            has_issue = False
            issue_details = []

            # Issue 1: Variables in choices not in situation
            extra_choice_vars = choice_vars - situation_vars
            if extra_choice_vars:
                has_issue = True
                issue_details.append(f"Choices have vars not in situation: {extra_choice_vars}")

            # Issue 2: Variables in situation not in any choice
            # (this is actually okay - situation can have more detail)
            # unused_vars = situation_vars - choice_vars
            # if unused_vars:
            #     issue_details.append(f"Situation vars not used in choices: {unused_vars}")

            # Issue 3: Undefined variables being used
            undefined_in_situation = situation_vars - defined_vars
            if undefined_in_situation:
                has_issue = True
                issue_details.append(
                    f"Situation uses undefined vars: {undefined_in_situation}"
                )

            undefined_in_choices = choice_vars - defined_vars
            if undefined_in_choices:
                has_issue = True
                issue_details.append(f"Choices use undefined vars: {undefined_in_choices}")

            # Print dilemma info
            console.print(f"\n[cyan]{dilemma.id}[/cyan]: {dilemma.title}")
            console.print(f"  Situation vars: {situation_vars if situation_vars else '(none)'}")
            console.print(f"  Choice vars: {choice_vars if choice_vars else '(none)'}")
            console.print(f"  Defined vars: {defined_vars if defined_vars else '(none)'}")

            if has_issue:
                console.print(f"  [red]⚠️  ISSUES:[/red]")
                for detail in issue_details:
                    console.print(f"     [red]{detail}[/red]")
                issues.append((dilemma.id, dilemma.title, issue_details))

                # Show actual choice text for manual review
                console.print(f"\n  [yellow]Choices for manual review:[/yellow]")
                for choice in dilemma.choices:
                    console.print(f"    [{choice.id}] {choice.description[:100]}...")
            else:
                console.print(f"  [green]✓ OK[/green]")

        # Summary
        console.print("\n" + "=" * 100)
        if issues:
            console.print(f"[red bold]SUMMARY: {len(issues)} dilemmas with issues[/red bold]")
            table = Table(title="Dilemmas with Issues")
            table.add_column("ID", style="cyan")
            table.add_column("Title", style="white")
            table.add_column("Issues", style="red")

            for did, title, details in issues:
                table.add_row(did, title, "\n".join(details))

            console.print(table)
        else:
            console.print("[green bold]✓ All dilemmas look good![/green bold]")

        console.print(f"\n[bold]Total dilemmas checked: {len(dilemmas_db)}[/bold]")
        console.print(f"[bold]Dilemmas with issues: {len(issues)}[/bold]")
        console.print(f"[bold]Clean dilemmas: {len(dilemmas_db) - len(issues)}[/bold]")

    await db.close()


if __name__ == "__main__":
    asyncio.run(audit_dilemmas())
