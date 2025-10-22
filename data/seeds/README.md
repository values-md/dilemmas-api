# Dilemma Seeds

This directory contains seed components used to generate ethical dilemmas.

## Purpose

Rather than asking an LLM to "generate a dilemma" (which leads to clichés), we:
1. Randomly sample components from these seed files
2. Combine them in interesting ways
3. Ask the LLM to synthesize a coherent dilemma from these constraints

This ensures diversity and reduces repetitive patterns.

## File Formats

**Simple lists (one per line):**
- `domains.txt` - AI system types (autonomous_vehicle, medical_ai, etc.)
- `moral_foundations.txt` - Moral dimension being tested

**Category format (category: item):**
- `actors.txt` - People/entities involved
  - Format: `category: actor_name`
  - Categories: individual, vulnerable, authority, group, abstract

**Complex format (id | description | example):**
- `conflicts.txt` - Core ethical tensions
  - Format: `conflict_id | short_description | example_scenario`

**Category format (category: specific):**
- `stakes.txt` - What's at risk
  - Format: `category: specific_stake`
  - Categories: physical, emotional, financial, social, legal, etc.

**Free text (one per line):**
- `constraints.txt` - Modifiers and conditions
  - Can be combined to increase difficulty
  - Examples: time pressure, uncertainty, irreversibility

## Extending Seeds

Simply add new lines to any file! The format is designed to be git-friendly and easy to edit.

## Usage

The DilemmaGenerator service reads these files and randomly samples:
- 1 domain
- 2-4 actors
- 1-2 conflicts
- 0-3 constraints (more = harder)
- 1-2 stakes
- 1 moral foundation

Then passes these to the LLM with a structured prompt.
