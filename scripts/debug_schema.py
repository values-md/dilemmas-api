"""Debug: Print the JSON schema that's sent to the LLM."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dilemmas.models.extraction import VariableExtraction
import json

# Get the JSON schema
schema = VariableExtraction.model_json_schema()

print("JSON Schema sent to LLM:\n")
print(json.dumps(schema, indent=2))

print("\n" + "=" * 80)
print("\nVariable schema specifically:\n")
if "$defs" in schema and "Variable" in schema["$defs"]:
    print(json.dumps(schema["$defs"]["Variable"], indent=2))
