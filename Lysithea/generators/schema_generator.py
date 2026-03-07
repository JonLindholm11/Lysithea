# generators/schema_generator.py

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

"""
Database schema generation

Rule of Law: reads resources from file_manager.load_resources()
             reads schema notes from file_manager.load_stack()
             writes schema to file_manager.write_schema()

Constraints:
- Table name must match resource name exactly
- Columns defined in prompt.md are required; LLM may add sensible extras
- Foreign keys must only reference other tables defined in prompt.md
- Hard fail if a resource has no schema notes in prompt.md
"""

import ollama
from pathlib import Path
from datetime import datetime

from pattern_manager import load_pattern, get_pattern_metadata, extract_metadata_from_content
from parsers import extract_code_from_response, extract_explanation_from_response
from file_manager import get_output_path,  load_resources, load_stack, write_schema


def generate_schema():
    resources    = load_resources()
    stack        = load_stack()
    schema_notes  = stack.get('database_schema', {}).get('tables', {})
    defined_tables = list(schema_notes.keys())
    relationships  = stack.get('database_schema', {}).get('relationships', [])

    print(f"\n{'='*60}")
    print(f"  GENERATING SCHEMA: {len(resources)} table(s)")
    print('='*60)

    # Hard fail if any resource is missing schema notes
    missing = [r['name'] for r in resources if r['name'] not in schema_notes]
    if missing:
        raise RuntimeError(
            f"\n[schema_generator] Missing schema notes in prompt.md for: {', '.join(missing)}\n\n"
            f"Add entries under '# Database / Schema Notes' -> '- Tables:' for each resource.\n\n"
            f"Example:\n"
            f"  # Database / Schema Notes\n"
            f"  - Tables:\n"
            + "\n".join(f"    - {m}: column1, column2, column3" for m in missing)
        )

    pattern_path = 'javascript/express/database/schema.sql'
    pattern      = load_pattern(pattern_path)
    if not pattern:
        print(f"Warning: Pattern not found: {pattern_path}")
        return

    print(f"Pattern: {pattern_path}")

    metadata = extract_metadata_from_content(pattern)
    output_dir  = metadata['output_dir'] if metadata else 'db'
    file_naming = metadata['file_naming'] if metadata else 'schema.sql'
    output_file = get_output_path(*output_dir.split('/')) / file_naming

    resource_names = [r['name'] for r in resources]
    print(f"Generating schema for: {', '.join(resource_names)}...")

    all_schemas         = []
    schema_explanations = {}

    for resource_data in resources:
        resource_name = resource_data['name']
        user_columns  = schema_notes.get(resource_name, '')
        fk_block      = _build_fk_guidance(defined_tables, resource_name, relationships)

        prompt = f"""Generate a PostgreSQL CREATE TABLE statement for ONLY the '{resource_name}' table.

=== REQUIRED COLUMNS ===
{user_columns}

=== SYSTEM COLUMNS (always include) ===
- id SERIAL PRIMARY KEY
- created_at TIMESTAMP DEFAULT NOW()
- updated_at TIMESTAMP
- is_deleted BOOLEAN DEFAULT FALSE
- deleted_at TIMESTAMP

=== FOREIGN KEY RULES ===
{fk_block}

=== STRICT RULES - FOLLOW EXACTLY ===
1. Generate ONLY the {resource_name} table. Do NOT generate any other tables.
2. Do NOT add columns that are not listed in REQUIRED COLUMNS or SYSTEM COLUMNS above.
3. The table name MUST be exactly: {resource_name}
4. Do NOT add CREATE TABLE for any other resource (e.g. books, users, orders).
5. Output ONLY one CREATE TABLE block followed by CREATE INDEX statements.

=== PATTERN (for structure reference only) ===
{pattern}

Output ONLY the SQL for the {resource_name} table, then briefly explain your decisions.
"""

        try:
            response      = ollama.generate(model='llama3.1:8b', prompt=prompt, keep_alive=0)
            response_text = response['response']
            code          = extract_code_from_response(response_text)
            explanation   = extract_explanation_from_response(response_text)

            if code:
                all_schemas.append(f"-- Table: {resource_name}\n{code}")
                print(f"  Generated table: {resource_name}")
                if explanation and explanation.strip():
                    schema_explanations[resource_name] = explanation.strip()
            else:
                print(f"  Warning: No SQL found for {resource_name}")

        except Exception as e:
            print(f"  Error: Failed to generate {resource_name}: {e}")

    if not all_schemas:
        print("Warning: No schemas generated")
        return

    timestamp    = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    final_schema = (
        f"-- Generated: {timestamp}\n"
        f"-- Database schema for {len(resources)} table(s)\n\n"
        + "\n\n".join(all_schemas)
    )

    write_schema(final_schema)

    output_file.write_text(final_schema, encoding='utf-8')
    print(f"Mirrored to: {output_file}")

    notes_file    = output_file.parent / "schema_notes.txt"
    notes_content = (
        f"Generated: {timestamp}\n\n"
        f"Tables: {', '.join(resource_names)}\n\n"
        f"=== Design Decisions ===\n\n"
    )
    for r in resources:
        name = r['name']
        notes_content += f"## {name.capitalize()}\n\n"
        notes_content += schema_explanations.get(name, "Generated from prompt.md schema notes.\n") + "\n\n"
    notes_file.write_text(notes_content, encoding='utf-8')
    print(f"Saved notes: {notes_file}")
    print(f"Schema generation complete")
    print('='*60)


def _build_fk_guidance(defined_tables: list, current_table: str, relationships: list) -> str:
    """
    Build FK guidance from explicitly defined relationships in prompt.md only.
    If no relationships are defined, forbid all foreign keys.
    """
    # Find relationships that involve current_table
    relevant = [r for r in relationships if current_table in r.lower()]

    if not relevant:
        return (
            f"CRITICAL: Do NOT add any foreign keys, REFERENCES, or extra columns "
            f"that are not listed in the required columns above. "
            f"No relationships were defined for the {current_table} table in prompt.md. "
            f"Adding a user_id, book_id, or any other _id column is FORBIDDEN unless it "
            f"appears explicitly in the required columns list above."
        )

    allowed = ", ".join(relevant)
    return (
        f"The following relationships were explicitly defined in prompt.md:\n{allowed}\n"
        f"ONLY add foreign keys for these exact relationships. "
        f"Do NOT invent any other foreign keys or reference columns."
    )