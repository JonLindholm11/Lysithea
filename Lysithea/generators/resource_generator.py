# lysithea/generators/resource_generator.py

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

"""
Route generation (sequential, per operation)

Rule of Law: reads schema from file_manager.extract_table_from_schema()
             call execute_sequential_generation(resource_name) — no schema arg.
"""

import ollama
import re
from pathlib import Path
from datetime import datetime

from pattern_manager import load_pattern, map_operation_to_pattern, get_pattern_metadata, get_stack_info
from parsers import extract_code_from_response, extract_explanation_from_response
from file_manager import assert_schema_ready, extract_table_from_schema


def execute_sequential_generation(resource: str):
    """
    Generate Express route file for one resource.

    Args:
        resource:     e.g. 'products'
    Reads table schema from .lysithea/schema.sql via file_manager.
    Hard fails if schema has not been generated.
    """

    assert_schema_ready()                              # Rule of Law guard
    schema = extract_table_from_schema(resource)       # Rule of Law read
    stack  = get_stack_info()                          # stack from file_manager

    print(f"\n{'='*60}")
    print(f"  SEQUENTIAL GENERATION: {resource}")
    print(f"  Stack: {stack['language']}/{stack['framework']}")
    print('='*60)

    output_dir  = 'api/routes'
    output_file = Path('output') / output_dir / f'{resource}.js'
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Load query function names from generated file
    query_file = Path('output') / 'db' / 'queries' / f'{resource}.queries.js'
    all_query_functions = []
    if query_file.exists():
        try:
            content             = query_file.read_text(encoding='utf-8', errors='ignore')
            all_query_functions = re.findall(r'export async function (\w+)\(', content)
            print(f"📋 Found {len(all_query_functions)} query functions")
        except Exception as e:
            print(f"⚠️  Could not extract query functions: {e}")

    if not all_query_functions:
        print("⚠️  No query functions found — cannot generate routes")
        return

    timestamp   = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    import_line = f'const {{ {", ".join(all_query_functions)} }} = require("../../db/queries/{resource}.queries");\n'
    boilerplate = (
        f"// Generated: {timestamp}\n\n"
        "const express = require('express');\n"
        "const router = express.Router();\n"
        "const { authenticateToken } = require('../middleware/auth');\n"
        f"{import_line}\n"
    )
    output_file.write_text(boilerplate, encoding='utf-8')

    notes_file = output_file.parent / f"{resource}_notes.txt"
    if schema:
        notes_file.write_text(
            f"Generated: {timestamp}\n\nResource: {resource}\n\n"
            f"=== Database Schema ===\n\n```sql\n{schema}\n```\n\n=== Generation Log ===\n\n",
            encoding='utf-8'
        )

    # Map query functions → routes
    routes_to_generate = [
        r for r in (map_query_to_route(fn, resource) for fn in all_query_functions)
        if r is not None
    ]
    print(f"📋 Will generate {len(routes_to_generate)} routes")

    completed_routes = []

    for i, route_info in enumerate(routes_to_generate):
        method_lower = route_info['method'].lower()
        print(f"\n{'─'*60}")
        print(f"Step {i+1}/{len(routes_to_generate)}: {route_info['method']} {route_info['path']}")
        print(f"Query function: {route_info['func']}")

        # Resolve pattern path from stack — GET/:id needs its own key
        op_key       = "get by id" if (method_lower == 'get' and ':id' in route_info['path']) else method_lower
        pattern_path = map_operation_to_pattern(op_key, stack)
        if not pattern_path:
            print(f"No pattern mapped for {method_lower}, skipping")
            continue

        pattern = load_pattern(pattern_path)
        if not pattern:
            print(f"⚠️  Pattern not found: {pattern_path}, skipping")
            continue

        schema_block = (
            f"\n=== DATABASE SCHEMA ===\n{schema}\nCRITICAL: Use ONLY these column names.\n=== END SCHEMA ==="
            if schema else ""
        )

        prompt = f"""You are adding a new route to an EXISTING Express router file.

THE FILE ALREADY HAS:
- Express and router setup
- Query function imports: const {{ {", ".join(all_query_functions)} }} = require("../../db/queries/{resource}.queries");
- These routes already added: {', '.join(completed_routes) or 'none yet'}
- module.exports at the bottom
{schema_block}

PATTERN TO ADD:
{pattern}

TASK: Add a {route_info['method']} {route_info['path']} route using {route_info['func']}.

DO NOT ADD: express/router setup, require() imports, module.exports.
ONLY ADD: router.{method_lower}("{route_info['path']}", authenticateToken, async (req, res) => {{ ... }});

Adapt "users" → "{resource}". Use {route_info['func']} (already imported).
Generate ONLY the router.{method_lower}(...) block. No imports.
"""

        try:
            response      = ollama.generate(model='llama3.1:8b', prompt=prompt, keep_alive=0)
            response_text = response['response']
            code          = extract_code_from_response(response_text)
            explanation   = extract_explanation_from_response(response_text)

            if not code:
                print(f"⚠️  No code block found")
                continue

            existing = output_file.read_text(encoding='utf-8', errors='ignore')
            output_file.write_text(existing.rstrip() + "\n\n" + code.strip(), encoding='utf-8')

            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if notes_file.exists():
                existing_notes = notes_file.read_text(encoding='utf-8', errors='ignore')
            else:
                existing_notes = ''
            notes_file.write_text(
                existing_notes
                + f"\n{'='*60}\nAdded: {timestamp} - {route_info['method']} {route_info['path']}\n\n"
                + (explanation or f"Added {route_info['method']} route."),
                encoding='utf-8'
            )

            completed_routes.append(f"{route_info['method']} {route_info['path']}")
            print(f"✅ Step {i+1} complete")

        except Exception as e:
            print(f"❌ Generation failed: {e}")
            continue

    final = output_file.read_text(encoding='utf-8', errors='ignore').rstrip() + "\n\nmodule.exports = router;\n"
    output_file.write_text(final, encoding='utf-8')

    print(f"\n{'='*60}")
    print(f"  COMPLETE! {len(completed_routes)} routes generated for {resource}")
    print(f"  File: {output_file}")
    print('='*60)


def map_query_to_route(func_name, resource):
    """Map a query function name to its Express route definition."""
    irregular = {
        'categories': 'category', 'statuses': 'status',
        'addresses': 'address',   'aliases': 'alias',
        'matrices': 'matrix',     'indices': 'index',
    }
    if resource in irregular:
        resource_singular = irregular[resource]
    elif resource.endswith('ies'):
        resource_singular = resource[:-3] + 'y'
    elif resource.endswith('s'):
        resource_singular = resource[:-1]
    else:
        resource_singular = resource

    resource_cap = resource_singular.capitalize()

    if func_name.startswith(f'create{resource_cap}'):
        return {'method': 'POST',   'path': f'/{resource}',     'func': func_name}
    elif func_name == f'get{resource_cap}s':
        return {'method': 'GET',    'path': f'/{resource}',     'func': func_name}
    elif 'ById' in func_name and func_name.startswith(f'get{resource_cap}'):
        return {'method': 'GET',    'path': f'/{resource}/:id', 'func': func_name}
    elif func_name.startswith(f'update{resource_cap}'):
        return {'method': 'PUT',    'path': f'/{resource}/:id', 'func': func_name}
    elif func_name.startswith(f'delete{resource_cap}'):
        return {'method': 'DELETE', 'path': f'/{resource}/:id', 'func': func_name}
    elif func_name.startswith(f'get{resource_cap}sBy'):
        after_by   = func_name.split('By')[1]
        field_name = after_by.replace('WithDetails', '')
        field_snake = re.sub(r'(?<!^)(?=[A-Z])', '_', field_name).lower()
        return {'method': 'GET', 'path': f'/{resource}/by-{field_snake}/:{field_snake}', 'func': func_name}
    elif func_name.startswith(f'get{resource_cap}s') and 'With' in func_name:
        return None  # skip join variants when base getAll exists

    return None