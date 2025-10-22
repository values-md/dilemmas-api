#!/usr/bin/env python3
"""Launch Datasette to explore the database in your browser.

Datasette provides a beautiful web interface for browsing SQLite databases.
Perfect for exploring dilemmas, their variations, and results.

Usage:
    uv run python scripts/explore_db.py

Opens in browser at http://localhost:8001
Press Ctrl+C to stop
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Launch Datasette web interface."""
    db_path = Path(__file__).parent.parent / "data" / "dilemmas.db"

    if not db_path.exists():
        print(f"✗ Database not found: {db_path}")
        print("\nRun this first to create the database:")
        print("  uv run python scripts/init_db.py")
        return 1

    print("🚀 Launching Datasette to explore the database...\n")
    print(f"   Database: {db_path}")
    print(f"   URL: http://localhost:8001")
    print("\nPress Ctrl+C to stop\n")

    # Launch datasette with nice defaults
    try:
        subprocess.run(
            [
                "uv",
                "run",
                "datasette",
                str(db_path),
                "--port",
                "8001",
                "--open",  # Automatically open browser
                "--metadata",
                "-",  # Read metadata from stdin
            ],
            input=b"""{
                "title": "Dilemmas Explorer",
                "description": "Explore ethical dilemmas and LLM judgements",
                "databases": {
                    "dilemmas": {
                        "tables": {
                            "dilemmas": {
                                "description": "Ethical dilemma test cases with variations"
                            },
                            "judgements": {
                                "description": "LLM decisions and reasoning for each dilemma"
                            }
                        }
                    }
                }
            }""",
            check=True,
        )
    except KeyboardInterrupt:
        print("\n\n✓ Datasette stopped")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Error launching Datasette: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
