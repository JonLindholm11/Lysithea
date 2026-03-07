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

from pattern_manager import load_pattern, get_pattern_metadata, map_query_pattern, get_stack_info
from parsers import extract_code_from_response, extract_explanation_from_response
from file_manager import assert_schema_ready, extract_table_from_schema, get_output_path


def generate_queries(resource_name: str):
    """
    Generate all query functions for one resource.

    Args:
        resource_name: e.g. 'products'

    Reads table schema from .lysithea/schema.sql via file_manager.
    Hard fails if schema has not been generated.
    """

    assert_schema_ready()
    table_schema = extract_table_from_schema(resource_name)
    stack        = get_stack_info()

    execute_sequential_query_generation(resource_name, table_schema, stack)
    print(f"\n✅ Query generation complete for {resource_name}")


def _to_commonjs(code: str, resource_name: str) -> str:
    """
    Convert ES module exports to CommonJS.
    - Remove 'export' keyword from async functions
    - Collect all function names and append module.exports
    """
    # Remove 'export ' prefix from async functions
    code = re.sub(r'\bexport\s+(async\s+function)', r'\1', code)

    # Find all top-level async function names
    func_names = re.findall(r'^async function (\w+)\s*\(', code, re.MULTILINE)

    if func_names:
        # Remove any existing module.exports
        code = re.sub(r'\nmodule\.exports\s*=.*', '', code)
        exports = ', '.join(func_names)
        code = code.rstrip() + f'\n\nmodule.exports = {{ {exports} }};\n'

    return code


def _fix_singular_names(code: str, resource: str) -> str:
    """
    Fix LLM tendency to use plural names for single-record functions.
    e.g. createBooks → createBook, updateBooks → updateBook, deleteBooks → deleteBook
    """
    # Derive singular form
    irregular = {
        'categories': 'category', 'statuses': 'status',
        'addresses': 'address',   'aliases': 'alias',
    }
    if resource in irregular:
        singular = irregular[resource]
    elif resource.endswith('ies'):
        singular = resource[:-3] + 'y'
    elif resource.endswith('s'):
        singular = resource[:-1]
    else:
        singular = resource

    cap_resource = resource.capitalize()
    cap_singular = singular.capitalize()

    # createBooks → createBook, updateBooks → updateBook, deleteBooks → deleteBook
    for verb in ('create', 'update', 'delete', 'getById', 'getBy'):
        wrong = f'{verb}{cap_resource}'
        right = f'{verb}{cap_singular}' if verb not in ('getById', 'getBy') else f'get{cap_singular}{verb[3:]}'
        if wrong != right:
            code = code.replace(wrong, right)

    # Also fix getBookById patterns: get{Resource}ById → get{Singular}ById
    wrong_get_by_id = f'get{cap_resource}ById'
    right_get_by_id = f'get{cap_singular}ById'
    if wrong_get_by_id != right_get_by_id:
        code = code.replace(wrong_get_by_id, right_get_by_id)

    return code


def _fix_connection_path(code: str) -> str:
    """Fix incorrect ../../connection path — queries live at db/queries/ so path should be ../connection"""
    code = re.sub(r"require\(['\"]\.\.\/\.\.\/connection['\"]\)", "require('../connection')", code)
    return code


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

    metadata    = get_pattern_metadata('javascript/express/queries/create.js')
    output_dir  = metadata['output_dir'] if metadata else 'output'
    file_naming = metadata['file_naming'] if metadata else f'{resource}.queries.js'
    filename    = file_naming.replace('{resource}', resource)
    output_file = get_output_path(*output_dir.split('/')) / filename
    output_file.parent.mkdir(parents=True, exist_ok=True)

    completed_functions = []

    # Derive singular form for naming guidance
    irregular = {'categories': 'category', 'statuses': 'status', 'addresses': 'address'}
    if resource in irregular:
        singular = irregular[resource]
    elif resource.endswith('ies'):
        singular = resource[:-3] + 'y'
    elif resource.endswith('s'):
        singular = resource[:-1]
    else:
        singular = resource
    cap_singular = singular.capitalize()

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
            singular=singular,
            cap_singular=cap_singular,
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

            # Post-process fixes
            code = _fix_connection_path(code)
            code = _fix_singular_names(code, resource)
            code = _to_commonjs(code, resource)

            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            if completed_functions:
                existing = output_file.read_text(encoding='utf-8')
                # Remove module.exports from existing before appending
                existing = re.sub(r'\nmodule\.exports\s*=.*\n?', '', existing)
                existing = re.sub(r'^//\s*Generated:.*?\n', '', existing, flags=re.MULTILINE)
                # Strip module.exports from new code too before merging
                new_code = re.sub(r'\nmodule\.exports\s*=.*\n?', '', code)
                new_code = re.sub(r"const db = require\(['\"]\.\.\/connection['\"]\);\n?", '', new_code)
                combined = existing.rstrip() + "\n\n" + new_code.strip()
                # Re-collect ALL function names and write single module.exports
                all_funcs = re.findall(r'^async function (\w+)\s*\(', combined, re.MULTILINE)
                combined = combined.rstrip() + f'\n\nmodule.exports = {{ {", ".join(all_funcs)} }};\n'
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


def _build_prompt(query_type, display_name, field_name, resource, singular, cap_singular,
                  table_schema, pattern, completed_functions):
    """Build the LLM prompt for a given query type."""
    existing_block = (
        f"EXISTING FUNCTIONS (do not modify):\n"
        + "\n".join(f"- {f}" for f in completed_functions)
        if completed_functions else ""
    )
    schema_block = f"TABLE SCHEMA:\n{table_schema}" if table_schema else ""

    # Naming rules appended to every prompt
    naming_rules = f"""
CRITICAL NAMING RULES:
- Single-record functions MUST use singular resource name: {singular}
- create{cap_singular} (NOT create{resource.capitalize()})
- get{cap_singular}s (list — plural OK here)
- get{cap_singular}ById (singular)
- update{cap_singular} (singular)
- delete{cap_singular} (singular)
- Use CommonJS: NO 'export' keyword. Use: async function name() {{}}
- Connection import: const db = require('../connection');
- Do NOT use ../../connection
"""

    if query_type.startswith('get-by-field-with-join:') or query_type.startswith('get-by-field:'):
        with_join   = 'with-join' in query_type
        func_suffix = 'WithDetails' if with_join else ''
        title_field = field_name.replace('_', ' ').title().replace(' ', '')
        func_name   = f"get{cap_singular}By{title_field}{func_suffix}"
        sql_hint    = (
            f"Build LEFT JOINs for all REFERENCES in schema. WHERE {field_name} = $1"
            if with_join else
            f"SELECT * FROM {resource} WHERE {field_name} = $1, return all matching rows"
        )

        if completed_functions:
            return f"""{existing_block}\n\n{schema_block}\n\nPATTERN TO ADD:\n{pattern}
{naming_rules}
TASK: Add {display_name} function for {resource}.
Function name: {func_name}
Parameter: {field_name}
SQL: {sql_hint}

Generate ONLY the new function. No imports. Wrap in ```javascript fences.
Then briefly explain."""
        else:
            return f"""{schema_block}\n\n=== PATTERN ===\n{pattern}
{naming_rules}
Generate {display_name} function for {resource}.
Function name: {func_name}
Parameter: {field_name}
SQL: {sql_hint}
Include db import at top. Full file. Wrap in ```javascript fences.
Then explain."""

    else:
        if completed_functions:
            return f"""{existing_block}\n\n{schema_block}\n\nPATTERN TO ADD:\n{pattern}
{naming_rules}
TASK: Add the {query_type} function for {resource}.
- Adapt from "users"/"orders" to "{resource}"
- Use ONLY columns from the schema
- Do NOT include imports (already in file)
- Generate ONLY the new function

Wrap in ```javascript fences. Then explain briefly."""
        else:
            return f"""{schema_block}\n\n=== PATTERN ===\n{pattern}
{naming_rules}
Generate {query_type} function for {resource}.
- Replace "user"/"users" with "{resource}" / "{singular}"
- Use ONLY columns from the schema
- Include db import: const db = require('../connection');

Full file. Wrap in ```javascript fences. Then explain."""