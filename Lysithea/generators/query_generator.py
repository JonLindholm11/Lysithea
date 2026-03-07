# generators/query_generator.py

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

"""
Database query function generation

Rule of Law: reads schema from file_manager.extract_table_from_schema()
             call generate_queries(resource_name) — no schema arg.
"""

import ollama
import re
from pathlib import Path
from datetime import datetime

from pattern_manager import load_pattern, get_pattern_metadata, extract_metadata_from_content, map_query_pattern, get_stack_info
from parsers import extract_code_from_response, extract_explanation_from_response
from file_manager import get_output_path,  assert_schema_ready, extract_table_from_schema


def generate_queries(resource_name: str):
    """
    Generate all query functions for one resource.

    Args:
        resource_name: e.g. 'products'

    Reads table schema from .lysithea/schema.sql via file_manager.
    Hard fails if schema has not been generated.
    """

    assert_schema_ready()                                    # Rule of Law guard
    table_schema = extract_table_from_schema(resource_name) # Rule of Law read
    stack        = get_stack_info()                          # stack from file_manager

    execute_sequential_query_generation(resource_name, table_schema, stack)
    print(f"\n✅ Query generation complete for {resource_name}")


def execute_sequential_query_generation(resource: str, table_schema: str | None, stack: dict | None = None):
    """Generate query functions one at a time for a resource."""

    print(f"\n{'='*60}")
    print(f"  SEQUENTIAL QUERY GENERATION: {resource}")
    print('='*60)

    has_foreign_keys    = 'REFERENCES' in table_schema if table_schema else False
    foreign_key_columns = []

    if has_foreign_keys and table_schema:
        fk_pattern          = r'(\w+)\s+(?:INTEGER|BIGINT)\s+REFERENCES'
        foreign_key_columns = re.findall(fk_pattern, table_schema, re.IGNORECASE)

    query_types = ['create', 'get-all']

    if has_foreign_keys:
        query_types.append('get-by-id-with-join')
        query_types.append('get-with-joins')
        for fk in foreign_key_columns:
            query_types.append(f'get-by-field-with-join:{fk}')
    else:
        query_types.append('get-by-id')

    query_types.extend(['update', 'delete'])

    print(f"📊 Foreign keys detected: {foreign_key_columns if foreign_key_columns else 'None'}")
    print(f"  Query types: {len(query_types)}")
    print('='*60)

    # Resolve output path — hardcoded since query patterns are consistent
    output_dir  = 'db/queries'
    filename    = f'{resource}.queries.js'
    file_naming = filename
    output_file = get_output_path(*output_dir.split('/')) / filename

    completed_functions = []

    for i, query_type in enumerate(query_types):
        print(f"\n{'─'*60}")

        if query_type.startswith('get-by-field-with-join:'):
            field_name   = query_type.split(':')[1]
            pattern_path = map_query_pattern('get-by-field-with-join', stack)
            display_name = f"get-by-{field_name}-with-join"
        elif query_type.startswith('get-by-field:'):
            field_name   = query_type.split(':')[1]
            pattern_path = map_query_pattern('get-by-field', stack)
            display_name = f"get-by-{field_name}"
        else:
            pattern_path = map_query_pattern(query_type, stack)
            display_name = query_type
            field_name   = None

        print(f"Step {i+1}/{len(query_types)}: {display_name}")
        print('─'*60)

        pattern = load_pattern(pattern_path)
        if not pattern:
            print(f"⚠️  Pattern not found: {pattern_path}, skipping")
            continue

        prompt = _build_prompt(
            query_type=query_type,
            display_name=display_name,
            field_name=field_name,
            resource=resource,
            table_schema=table_schema,
            pattern=pattern,
            completed_functions=completed_functions,
        )

        try:
            response      = ollama.generate(model='llama3.1:8b', prompt=prompt, keep_alive=0)
            response_text = response['response']
            code          = extract_code_from_response(response_text)
            explanation   = extract_explanation_from_response(response_text)

            if not code:
                print(f"⚠️  No code block found in response")
                continue

            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            if completed_functions:
                existing = output_file.read_text(encoding='utf-8')
                existing = re.sub(r'^//\s*Generated:.*?\n', '', existing, flags=re.MULTILINE)
                combined = existing.rstrip() + "\n\n" + code.strip()
                output_file.write_text(f"// Generated: {timestamp}\n\n{combined}", encoding='utf-8')
            else:
                output_file.write_text(f"// Generated: {timestamp}\n\n{code}", encoding='utf-8')

            print(f"✅ Saved: {output_file}")

            notes_file = output_file.parent / f"{resource}.queries_notes.txt"
            if completed_functions and notes_file.exists():
                existing_notes = notes_file.read_text(encoding='utf-8')
                notes_file.write_text(
                    existing_notes
                    + f"\n\n{'='*60}\nAdded: {timestamp} - {display_name}\n\n"
                    + (explanation or f"Added {display_name}."),
                    encoding='utf-8'
                )
            else:
                notes_file.write_text(
                    f"Generated: {timestamp}\n\nResource: {resource}\n\n=== Explanation ===\n\n"
                    + (explanation or f"Generated {display_name}."),
                    encoding='utf-8'
                )

            completed_functions.append(f"{display_name}_{resource}")
            print(f"✅ Step {i+1} complete")

        except Exception as e:
            print(f"❌ Generation failed: {e}")
            continue

    print(f"\n{'='*60}")
    print(f"  🎉 COMPLETE! {len(completed_functions)} query functions for {resource}")
    print(f"  📄 File: {output_file}")
    print('='*60)


def _build_prompt(query_type, display_name, field_name, resource, table_schema, pattern, completed_functions):
    """Build the LLM prompt for a given query type."""
    existing_block = (
        f"EXISTING FUNCTIONS (do not modify):\n"
        + "\n".join(f"- {f}" for f in completed_functions)
        if completed_functions else ""
    )
    schema_block = f"TABLE SCHEMA:\n{table_schema}" if table_schema else ""

    if query_type.startswith('get-by-field-with-join:') or query_type.startswith('get-by-field:'):
        with_join    = 'with-join' in query_type
        func_suffix  = 'WithDetails' if with_join else ''
        title_field  = field_name.replace('_', ' ').title().replace(' ', '')
        func_name    = f"get{resource.capitalize()}By{title_field}{func_suffix}"
        sql_hint     = (
            f"Build LEFT JOINs for all REFERENCES in schema. WHERE {field_name} = $1"
            if with_join else
            f"SELECT * FROM {resource} WHERE {field_name} = $1, return all matching rows"
        )

        if completed_functions:
            return f"""{existing_block}\n\n{schema_block}\n\nPATTERN TO ADD:\n{pattern}

TASK: Add {display_name} function for {resource}.
Function name: {func_name}
Parameter: {field_name}
SQL: {sql_hint}

Generate ONLY the new function. No imports. Wrap in ```javascript fences.
Then briefly explain."""
        else:
            return f"""{schema_block}\n\n=== PATTERN ===\n{pattern}

Generate {display_name} function for {resource}.
Function name: {func_name}
Parameter: {field_name}
SQL: {sql_hint}
Include db import at top. Full file. Wrap in ```javascript fences.
Then explain."""

    else:
        if completed_functions:
            return f"""{existing_block}\n\n{schema_block}\n\nPATTERN TO ADD:\n{pattern}

TASK: Add the {query_type} function for {resource}.
- Adapt from "users"/"orders" to "{resource}"
- Use ONLY columns from the schema
- Do NOT include imports (already in file)
- Generate ONLY the new function

Wrap in ```javascript fences. Then explain briefly."""
        else:
            return f"""{schema_block}\n\n=== PATTERN ===\n{pattern}

Generate {query_type} function for {resource}.
- Replace "user"/"users" with "{resource}"
- Use ONLY columns from the schema
- Include db import: const db = require('../../connection');

Full file. Wrap in ```javascript fences. Then explain."""