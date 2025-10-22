#!/usr/bin/env python3
"""Start the FastAPI server for exploring dilemmas.

Usage:
    uv run python scripts/serve.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import uvicorn

if __name__ == "__main__":
    print("Starting VALUES.md Dilemma Explorer...")
    print("Visit: http://localhost:8000")
    print()

    uvicorn.run(
        "dilemmas.api.app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
