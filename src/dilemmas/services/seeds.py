"""Seed loading utilities for dilemma generation.

Loads seed components from simple text files in data/seeds/.
"""

import random
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class Actor(BaseModel):
    """An actor parsed from actors.txt."""

    category: str
    name: str


class Conflict(BaseModel):
    """A conflict parsed from conflicts.txt."""

    id: str
    description: str
    example: str


class Stake(BaseModel):
    """A stake parsed from stakes.txt."""

    category: str
    specific: str


class SeedLibrary(BaseModel):
    """Complete seed library loaded from files."""

    domains: list[str] = Field(default_factory=list)
    actors: list[Actor] = Field(default_factory=list)
    conflicts: list[Conflict] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    stakes: list[Stake] = Field(default_factory=list)
    moral_foundations: list[str] = Field(default_factory=list)


def load_seeds(seeds_dir: Path | str | None = None) -> SeedLibrary:
    """Load all seed files from data/seeds/ directory.

    Args:
        seeds_dir: Path to seeds directory. If None, uses data/seeds/ in project root.

    Returns:
        SeedLibrary with all components loaded.
    """
    if seeds_dir is None:
        seeds_dir = Path(__file__).parent.parent.parent.parent / "data" / "seeds"
    else:
        seeds_dir = Path(seeds_dir)

    library = SeedLibrary()

    # Load simple lists (one per line, ignore comments and empty lines)
    library.domains = _load_simple_list(seeds_dir / "domains.txt")
    library.moral_foundations = _load_simple_list(seeds_dir / "moral_foundations.txt")
    library.constraints = _load_simple_list(seeds_dir / "constraints.txt")

    # Load actors (format: category: name)
    library.actors = _load_actors(seeds_dir / "actors.txt")

    # Load conflicts (format: id | description | example)
    library.conflicts = _load_conflicts(seeds_dir / "conflicts.txt")

    # Load stakes (format: category: specific)
    library.stakes = _load_stakes(seeds_dir / "stakes.txt")

    return library


def _load_simple_list(file_path: Path) -> list[str]:
    """Load a simple list file (one item per line, ignore # comments)."""
    if not file_path.exists():
        return []

    items = []
    with open(file_path) as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if line and not line.startswith("#"):
                items.append(line)
    return items


def _load_actors(file_path: Path) -> list[Actor]:
    """Load actors from actors.txt (format: category: name)."""
    if not file_path.exists():
        return []

    actors = []
    with open(file_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                if ":" in line:
                    category, name = line.split(":", 1)
                    actors.append(
                        Actor(category=category.strip(), name=name.strip())
                    )
    return actors


def _load_conflicts(file_path: Path) -> list[Conflict]:
    """Load conflicts from conflicts.txt (format: id | description | example)."""
    if not file_path.exists():
        return []

    conflicts = []
    with open(file_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 3:
                    conflicts.append(
                        Conflict(
                            id=parts[0], description=parts[1], example=parts[2]
                        )
                    )
    return conflicts


def _load_stakes(file_path: Path) -> list[Stake]:
    """Load stakes from stakes.txt (format: category: specific)."""
    if not file_path.exists():
        return []

    stakes = []
    with open(file_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                if ":" in line:
                    category, specific = line.split(":", 1)
                    stakes.append(
                        Stake(category=category.strip(), specific=specific.strip())
                    )
    return stakes


class DilemmaSeed(BaseModel):
    """Components sampled for generating a dilemma."""

    domain: str
    actors: list[str]  # Just the names, not full Actor objects
    conflict: Conflict
    constraints: list[str]
    stakes: list[Stake]
    moral_foundation: str
    difficulty_target: int = Field(ge=1, le=10)


def generate_random_seed(
    library: SeedLibrary,
    difficulty: int,
    num_actors: int = 3,
    num_constraints: int | None = None,
    num_stakes: int = 2,
) -> DilemmaSeed:
    """Generate a random seed by sampling from the library.

    Args:
        library: Seed library to sample from
        difficulty: Target difficulty (1-10). Higher difficulty = more constraints
        num_actors: Number of actors to sample (default: 3)
        num_constraints: Number of constraints. If None, auto-calculated from difficulty
        num_stakes: Number of stakes to sample (default: 2)

    Returns:
        DilemmaSeed with randomly sampled components
    """
    # Auto-calculate constraints based on difficulty if not specified
    if num_constraints is None:
        if difficulty <= 3:
            num_constraints = random.randint(0, 1)  # Easy: 0-1 constraints
        elif difficulty <= 6:
            num_constraints = random.randint(1, 2)  # Medium: 1-2 constraints
        else:
            num_constraints = random.randint(2, 4)  # Hard: 2-4 constraints

    return DilemmaSeed(
        domain=random.choice(library.domains),
        actors=[actor.name for actor in random.sample(library.actors, num_actors)],
        conflict=random.choice(library.conflicts),
        constraints=random.sample(library.constraints, min(num_constraints, len(library.constraints))),
        stakes=random.sample(library.stakes, min(num_stakes, len(library.stakes))),
        moral_foundation=random.choice(library.moral_foundations),
        difficulty_target=difficulty,
    )


# Singleton instance
_library: SeedLibrary | None = None


def get_seed_library() -> SeedLibrary:
    """Get or create the singleton seed library instance."""
    global _library
    if _library is None:
        _library = load_seeds()
    return _library
