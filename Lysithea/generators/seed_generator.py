# generators/seed_generator.py

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

"""
Database seed file generation

Rule of Law: reads schema from file_manager.extract_table_from_schema()
             call generate_seeds(resource_name) — no schema arg.
"""

import ollama
from pathlib import Path
from datetime import datetime

from pattern_manager import load_pattern, get_pattern_metadata
from parsers import extract_code_from_response, extract_explanation_from_response
from file_manager import assert_schema_ready, extract_table_from_schema


def generate_seeds(resource_name: str):
    """
    Generate a seed file for one resource.

    Args:
        resource_name: e.g. 'products'

    Reads table schema from .lysithea/schema.sql via file_manager.
    Hard fails if schema has not been generated.
    """

    assert_schema_ready()                                   # Rule of Law guard
    table_schema = extract_table_from_schema(resource_name) # Rule of Law read

    print(f"\n{'='*60}")
    print(f"  GENERATING SEED: {resource_name}")
    print('='*60)

    pattern_path = 'javascript/express/database/seeds/seed_users.js'
    pattern      = load_pattern(pattern_path)
    if not pattern:
        print(f"⚠️  Pattern not found: {pattern_path}")
        return

    metadata    = get_pattern_metadata(pattern_path)
    output_dir  = metadata['output_dir'] if metadata else 'output'
    file_naming = metadata['file_naming'] if metadata else 'seed_{resource}.js'
    filename    = file_naming.replace('{resource}', resource_name)
    output_file = Path('output') / output_dir / filename
    output_file.parent.mkdir(parents=True, exist_ok=True)

    prompt = f"""Generate a JavaScript seed file for the {resource_name} table.

=== TABLE SCHEMA ===
{table_schema if table_schema else 'Schema not available'}

CRITICAL: Use ONLY the columns that exist in the schema above.

=== PATTERN ===
{pattern}

INSTRUCTIONS:
1. Replace "users" with "{resource_name}" everywhere
2. Create 5-10 realistic sample records
3. Use ONLY columns from the schema (no invented foreign keys)
4. Generate realistic data appropriate for {resource_name}
5. Keep async/await pattern and console.log

Output complete JavaScript file, then explain your data choices.
"""

    try:
        response      = ollama.generate(model='llama3.1:8b', prompt=prompt, keep_alive=0)
        response_text = response['response']
        code          = extract_code_from_response(response_text)
        explanation   = extract_explanation_from_response(response_text)

        if not code:
            print(f"⚠️  No code found for {resource_name}")
            return

        timestamp  = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        output_file.write_text(f"// Generated: {timestamp}\n\n{code}", encoding='utf-8')
        print(f"✅ Saved seed: {output_file}")

        notes_file = output_file.parent / f"{resource_name}_seed_notes.txt"
        notes_file.write_text(
            f"Generated: {timestamp}\n\nResource: {resource_name}\n\n=== Data Choices ===\n\n"
            + (explanation or ""),
            encoding='utf-8'
        )
        print(f"✅ Saved notes: {notes_file}")

    except Exception as e:
        print(f"❌ Failed to generate seed for {resource_name}: {e}")

    print('='*60)