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
from file_manager import assert_schema_ready, extract_table_from_schema, get_output_path


def execute_sequential_generation(resource: str):
    """
    Generate Express route file for one resource.

    Args:
        resource:     e.g. 'products'
    Reads table schema from .lysithea/schema.sql via file_manager.
    Hard fails if schema has not been generated.
    """

    assert_schema_ready()
    schema = extract_table_from_schema(resource)
    stack  = get_stack_info()

    print(f"\n{'='*60}")
    print(f"  SEQUENTIAL GENERATION: {resource}")
    print(f"  Stack: {stack['language']}/{stack['framework']}")
    print('='*60)

    output_dir  = 'api/routes'
    output_file = get_output_path(*output_dir.split('/')) / f'{resource}.js'
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Load query function names from generated file
    query_file = get_output_path('db', 'queries') / f'{resource}.queries.js'
    all_query_functions = []
    if query_file.exists():
        try:
            content = query_file.read_text(encoding='utf-8', errors='ignore')
            # Match both CommonJS (async function) and ES module (export async function)
            all_query_functions = re.findall(r'(?:export\s+)?async function (\w+)\(', content)
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
        short_path   = route_info['short_path']

        print(f"\n{'─'*60}")
        print(f"Step {i+1}/{len(routes_to_generate)}: {route_info['method']} {short_path}")
        print(f"Query function: {route_info['func']}")

        op_key       = "get by id" if (method_lower == 'get' and ':id' in short_path) else method_lower
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

        # Build method-specific extra rules to prevent auth-pattern bleed
        method_specific_rules = _build_method_rules(method_lower, short_path, resource, route_info['func'], all_query_functions)

        prompt = f"""You are adding a new route to an EXISTING Express router file.

THE FILE ALREADY HAS:
- Express and router setup
- Query function imports: const {{ {", ".join(all_query_functions)} }} = require("../../db/queries/{resource}.queries");
- These routes already added: {', '.join(completed_routes) or 'none yet'}
- module.exports at the bottom
{schema_block}

PATTERN TO ADD:
{pattern}

TASK: Add a {route_info['method']} {short_path} route using {route_info['func']}.

CRITICAL RULES:
- The router is already mounted at /api/{resource} in app.js
- So route paths MUST be "{short_path}" NOT "/{resource}" or "/{resource}/:id"
- DO NOT add express/router setup, require() imports, or module.exports
- ONLY add: router.{method_lower}("{short_path}", authenticateToken, async (req, res) => {{ ... }});
- The ONLY query functions available are: {", ".join(all_query_functions)}
- Do NOT call any function not in that list — especially getUserByEmail or any auth function
- Do NOT delete fields from the response unless the schema has a password_hash column
{method_specific_rules}

Use {route_info['func']} (already imported). Adapt all variable names to use '{resource}'.
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

            # Post-process: fix any route paths the LLM got wrong
            code = _fix_route_paths(code, resource, short_path, method_lower)

            existing = output_file.read_text(encoding='utf-8', errors='ignore')
            output_file.write_text(existing.rstrip() + "\n\n" + code.strip(), encoding='utf-8')

            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if notes_file.exists():
                existing_notes = notes_file.read_text(encoding='utf-8', errors='ignore')
            else:
                existing_notes = ''
            notes_file.write_text(
                existing_notes
                + f"\n{'='*60}\nAdded: {timestamp} - {route_info['method']} {short_path}\n\n"
                + (explanation or f"Added {route_info['method']} route."),
                encoding='utf-8'
            )

            completed_routes.append(f"{route_info['method']} {short_path}")
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


def _build_method_rules(method: str, short_path: str, resource: str, func: str, all_funcs: list) -> str:
    """
    Return method-specific rules to prevent the LLM copying patterns that don't apply.
    Prevents auth-route logic (email checks, getUserByEmail) leaking into generic routes.
    """
    if method == 'post':
        return (
            f"- This is a standard CREATE route, NOT an auth/register route\n"
            f"- Do NOT add email-duplicate checks or any existence check before inserting\n"
            f"- Do NOT reference req.params.id — POST routes have no :id parameter\n"
            f"- Do NOT call getUserByEmail or any function not in the imports list\n"
            f"- Name the request body variable 'fields' or 'data', NOT '{resource}' or '{resource}s'\n"
            f"- Name the created record 'newRecord', NOT 'new{resource.capitalize()}' or 'new{resource.capitalize()}s'\n"
            f"- Simply validate req.body fields, call {func}(req.body), return 201"
        )
    elif method == 'put':
        return (
            f"- Do NOT reference req.params.id as a string — parse it with parseInt first\n"
            f"- Call {func}(id, req.body) where id = parseInt(req.params.id)"
        )
    elif method == 'delete':
        return (
            f"- Do NOT reference req.params.id as a string — parse it with parseInt first\n"
            f"- Call {func}(id) where id = parseInt(req.params.id)"
        )
    elif method == 'get' and ':id' in short_path:
        return (
            f"- Do NOT reference req.params.id as a string — parse it with parseInt first\n"
            f"- Call {func}(id) where id = parseInt(req.params.id)"
        )
    return ""


def _fix_route_paths(code: str, resource: str, short_path: str, method: str) -> str:
    """
    Post-process: replace any doubled resource paths the LLM may have written.
    e.g. router.get("/books/:id", ...) → router.get("/:id", ...)
         router.get("/books", ...)     → router.get("/", ...)
    """
    # Fix /{resource}/:id → /:id
    code = re.sub(
        rf'(router\.{method}\s*\()\s*["\']/{resource}/:id["\']',
        r'\1"/:id"',
        code
    )
    # Fix /{resource}/by-... → /by-...
    code = re.sub(
        rf'(router\.{method}\s*\()\s*["\']/{resource}(/by-[^"\']+)["\']',
        r'\1"\2"',
        code
    )
    # Fix /{resource} → /  (only when it's the full path, not a prefix)
    code = re.sub(
        rf'(router\.{method}\s*\()\s*["\']/{resource}["\']',
        r'\1"/"',
        code
    )
    return code


def map_query_to_route(func_name, resource):
    """Map a query function name to its Express route definition."""
    irregular = {
        'categories': 'category', 'statuses': 'status',
        'addresses':  'address',  'aliases':  'alias',
        'matrices':   'matrix',   'indices':  'index',
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
        return {'method': 'POST',   'short_path': '/',    'func': func_name}

    # GET all — matches: getUsers, getAllUsers, getPosts, getAllPosts, etc.
    elif (
        func_name == f'get{resource_cap}s'
        or func_name == f'getAll{resource_cap}s'
        or func_name == f'getAll{resource_cap}'
    ):
        return {'method': 'GET',    'short_path': '/',    'func': func_name}

    # GET by ID — matches: getUserById, getPostById, etc.
    elif 'ById' in func_name and func_name.startswith(f'get{resource_cap}'):
        return {'method': 'GET',    'short_path': '/:id', 'func': func_name}

    elif func_name.startswith(f'update{resource_cap}'):
        return {'method': 'PUT',    'short_path': '/:id', 'func': func_name}

    elif func_name.startswith(f'delete{resource_cap}'):
        return {'method': 'DELETE', 'short_path': '/:id', 'func': func_name}

    # GET by field — matches: getUsersByEmail, getPostsByUserId, etc.
    elif func_name.startswith(f'get{resource_cap}sBy') or func_name.startswith(f'get{resource_cap}By'):
        after_by    = func_name.split('By', 1)[1]
        field_name  = after_by.replace('WithDetails', '')
        field_snake = re.sub(r'(?<!^)(?=[A-Z])', '_', field_name).lower()
        return {'method': 'GET', 'short_path': f'/by-{field_snake}/:{field_snake}', 'func': func_name}

    # Skip join-only list variants (e.g. getUsersWithDetails) — covered by getAll
    elif func_name.startswith(f'get{resource_cap}s') and 'With' in func_name:
        return None

    return None