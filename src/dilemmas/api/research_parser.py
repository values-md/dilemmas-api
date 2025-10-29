"""Parser for research experiments folder structure."""

import json
import re
import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ExperimentMetadata:
    """Metadata for a research experiment."""

    slug: str  # e.g., "2025-10-23-consistency"
    title: str  # e.g., "Consistency Across Temperatures"
    date: str  # e.g., "2025-10-23"
    status: str  # "completed" or "in_progress"
    summary: str  # Short summary from findings.md (abstract from YAML)
    key_finding: str  # Main finding
    research_question: str  # Research question from YAML
    models: list[str]  # Models tested
    data_stats: dict[str, Any]  # Stats from YAML frontmatter or config.json
    tags: list[str]  # Tags from YAML
    has_findings: bool
    has_readme: bool
    has_data: bool


def parse_yaml_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter from markdown file.

    Args:
        text: Full markdown text with optional YAML frontmatter

    Returns:
        Tuple of (frontmatter_dict, remaining_markdown)
        If no frontmatter, returns ({}, original_text)
    """
    # Check for YAML frontmatter (--- at start)
    if not text.startswith('---\n'):
        return {}, text

    # Find the closing ---
    parts = text.split('---\n', 2)
    if len(parts) < 3:
        return {}, text

    frontmatter_text = parts[1]
    markdown_content = parts[2]

    try:
        frontmatter = yaml.safe_load(frontmatter_text)
        return frontmatter or {}, markdown_content
    except yaml.YAMLError:
        return {}, text


def parse_research_folder(research_dir: Path) -> list[ExperimentMetadata]:
    """Parse research folder and extract experiment metadata.

    Args:
        research_dir: Path to research/ folder

    Returns:
        List of experiment metadata, sorted by date (newest first)
    """
    experiments = []

    # Find all experiment folders (YYYY-MM-DD-name pattern)
    for folder in research_dir.iterdir():
        if not folder.is_dir():
            continue

        # Match YYYY-MM-DD-name pattern
        match = re.match(r"(\d{4}-\d{2}-\d{2})-(.*)", folder.name)
        if not match:
            continue

        date, name = match.groups()
        slug = folder.name

        # Parse config.json if it exists
        config_path = folder / "config.json"
        config = {}
        if config_path.exists():
            try:
                config = json.loads(config_path.read_text())
            except json.JSONDecodeError:
                pass

        # Parse findings.md for title and summary
        findings_path = folder / "findings.md"
        title = name.replace("-", " ").title()
        summary = ""
        key_finding = ""
        research_question = ""
        status = "completed"
        models = []
        tags = []

        if findings_path.exists():
            findings_text = findings_path.read_text()

            # Parse YAML frontmatter if present
            frontmatter, markdown_content = parse_yaml_frontmatter(findings_text)

            if frontmatter:
                # Extract from YAML frontmatter (new format)
                title = frontmatter.get("title", title)
                summary = frontmatter.get("abstract", "").strip()
                key_finding = frontmatter.get("key_finding", "")
                research_question = frontmatter.get("research_question", "")
                status = frontmatter.get("status", "completed")
                models = frontmatter.get("models", [])
                tags = frontmatter.get("tags", [])

                # Use experiment_id from frontmatter if present
                if "experiment_id" in frontmatter:
                    config["experiment_id"] = frontmatter["experiment_id"]

                # Use data stats from frontmatter if present
                if "data" in frontmatter:
                    data_info = frontmatter["data"]
                    if isinstance(data_info, dict):
                        config["dilemmas_count"] = data_info.get("dilemmas", 0)
                        config["judgements_count"] = data_info.get("judgements", 0)
                        config["conditions"] = data_info.get("conditions", 0)
            else:
                # Fallback: parse markdown (old format)
                # Extract title from first # heading
                title_match = re.search(r"^#\s+(?:Findings:\s+)?(.+)$", findings_text, re.MULTILINE)
                if title_match:
                    title = title_match.group(1).strip()

                # Extract status (look for ✅ or 🔜)
                if "Status:** ✅" in findings_text or "Status: ✅" in findings_text:
                    status = "completed"
                elif "Status:** 🔜" in findings_text or "Status: 🔜" in findings_text:
                    status = "in_progress"

                # Extract research question as summary
                question_match = re.search(
                    r"##\s+Research Question\s*\n+(.+?)(?=\n##|\Z)",
                    findings_text,
                    re.DOTALL
                )
                if question_match:
                    research_question = question_match.group(1).strip()
                    summary = research_question
                    # Clean up markdown formatting
                    summary = re.sub(r'\*\*', '', summary)  # Remove bold
                    summary = re.sub(r'\n+', ' ', summary)  # Single line

                # Extract key finding (first bullet under Key Findings)
                key_finding_match = re.search(
                    r"##\s+Key Findings?\s*\n+.*?\*\*(.+?)\*\*",
                    findings_text,
                    re.DOTALL
                )
                if key_finding_match:
                    key_finding = key_finding_match.group(1).strip()

        # Check for other files
        has_findings = findings_path.exists()
        has_readme = (folder / "README.md").exists()
        has_data = (folder / "data").exists() and any((folder / "data").iterdir())

        # Extract data stats from config (or already populated from frontmatter)
        data_stats = {
            "experiment_id": config.get("experiment_id", ""),
            "dilemmas_count": config.get("dilemmas_count", 0),
            "judgements_count": config.get("judgements_count", 0),
            "conditions": config.get("conditions", 0),
        }

        # Use models from frontmatter if available, otherwise from config
        if not models:
            models = config.get("models", [])

        experiments.append(
            ExperimentMetadata(
                slug=slug,
                title=title,
                date=date,
                status=status,
                summary=summary,
                key_finding=key_finding,
                research_question=research_question,
                models=models,
                data_stats=data_stats,
                tags=tags,
                has_findings=has_findings,
                has_readme=has_readme,
                has_data=has_data,
            )
        )

    # Sort by date, newest first
    experiments.sort(key=lambda e: e.date, reverse=True)

    return experiments


def render_markdown(markdown_text: str, strip_first_h1: bool = True) -> str:
    """Render markdown to HTML.

    Args:
        markdown_text: Raw markdown text
        strip_first_h1: If True, removes the first H1 heading (used when title is shown separately)

    Returns:
        HTML string
    """
    import html
    from markdown import markdown

    # Strip first H1 if requested (to avoid double titles)
    if strip_first_h1:
        lines = markdown_text.split('\n')
        # Find and remove the first H1 (skipping blank lines)
        for i, line in enumerate(lines):
            if line.strip() and line.startswith('# '):
                # Found first H1, remove it and join the rest
                markdown_text = '\n'.join(lines[:i] + lines[i+1:])
                break

    # Fix list rendering: ensure blank line before lists
    # This fixes the common issue where lists don't render if there's no blank line before them
    lines = markdown_text.split('\n')
    fixed_lines = []
    for i, line in enumerate(lines):
        # Check if this line starts a list (numbered or bulleted)
        is_list_item = line.strip() and (
            re.match(r'^\d+\.', line.strip()) or  # Numbered list: 1. item
            line.strip().startswith(('- ', '* ', '+ '))  # Bulleted list
        )

        # Check if previous line exists and is not blank
        prev_line_exists = i > 0
        prev_line_not_blank = prev_line_exists and lines[i-1].strip()

        # If this is a list item and previous line is not blank, add blank line
        if is_list_item and prev_line_not_blank:
            fixed_lines.append('')  # Add blank line before list

        fixed_lines.append(line)

    markdown_text = '\n'.join(fixed_lines)

    # Use python-markdown library if available, otherwise fallback
    try:
        return markdown(
            markdown_text,
            extensions=[
                'fenced_code',
                'tables',
                'toc',
                'sane_lists',  # Better list handling
            ]
        )
    except ImportError:
        # Fallback: simple HTML escaping and basic formatting
        text = html.escape(markdown_text)
        # Convert **bold** to <strong>
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        # Convert *italic* to <em>
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        # Convert newlines to <br>
        text = text.replace('\n', '<br>')
        return text
