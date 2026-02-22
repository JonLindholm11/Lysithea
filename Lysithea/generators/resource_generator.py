# lysithea/generators/resource_generator.py
"""
Sequential code generation - builds files incrementally operation by operation
"""

import ollama
import re
from pathlib import Path
from datetime import datetime

from pattern_manager import load_pattern, map_operation_to_pattern, get_pattern_metadata
from parsers import extract_code_from_response, extract_explanation_from_response
from file_manager import save_generated_files, extract_table_from_schema

def execute_sequential_generation(resource, schema=None):
    """Execute sequential code generation based on query functions"""
    
    print(f"\n{'='*60}")
    print(f"  SEQUENTIAL GENERATION: {resource}")
    print('='*60)
    
    # Calculate output path
    output_dir = 'api/routes'
    filename = f'{resource}.js'
    output_file = Path('output') / output_dir / filename
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Load query function NAMES
    query_file_path = Path('output') / 'db' / 'queries' / f'{resource}.queries.js'
    all_query_functions = []
    if query_file_path.exists():
        try:
            content = query_file_path.read_text(encoding='utf-8', errors='ignore')
            pattern = r'export async function (\w+)\('
            all_query_functions = re.findall(pattern, content)
            print(f"📋 Found {len(all_query_functions)} query functions")
        except Exception as e:
            print(f"⚠️  Could not extract query functions: {e}")
    
    if not all_query_functions:
        print("⚠️  No query functions found, cannot generate routes")
        return
    
    # --------------------------
    # Write deterministic boilerplate at the top
    # --------------------------
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    import_line = f'const {{ {", ".join(all_query_functions)} }} = require("../../db/queries/{resource}.queries");\n'
    
    boilerplate = (
        f"// Generated: {timestamp}\n\n"
        "const express = require('express');\n"
        "const router = express.Router();\n"
        "const { authenticateToken } = require('../middleware/auth');\n"
        f"{import_line}\n"
    )
    
    # Write boilerplate to file (module.exports will be appended later)
    output_file.write_text(boilerplate, encoding='utf-8')
    
    # Initialize notes file if schema is provided
    notes_file = output_file.parent / f"{resource}_notes.txt"
    if schema:
        notes_content = f"Generated: {timestamp}\n\nResource: {resource}\n\n"
        notes_content += "=== Database Schema ===\n\n"
        notes_content += f"```sql\n{schema}\n```\n\n"
        notes_content += "=== Generation Log ===\n\n"
        notes_file.write_text(notes_content, encoding='utf-8')
    
    # Map each query function to a route
    routes_to_generate = []
    for func_name in all_query_functions:
        route_info = map_query_to_route(func_name, resource)
        if route_info:
            routes_to_generate.append(route_info)
    
    print(f"📋 Will generate {len(routes_to_generate)} routes based on query functions")
    
    completed_routes = []
    
    for i, route_info in enumerate(routes_to_generate):
        print(f"\n{'─'*60}")
        print(f"Step {i+1}/{len(routes_to_generate)}: {route_info['method']} {route_info['path']}")
        print(f"Using query function: {route_info['func']}")
        print('─'*60)
        
        # Map HTTP method to pattern
        method_lower = route_info['method'].lower()
        if method_lower == 'get' and ':id' in route_info['path']:
            pattern_path = 'javascript/express/routes/get-users-by-id-auth.js'
        elif method_lower == 'get':
            pattern_path = 'javascript/express/routes/get-users-auth.js'
        elif method_lower == 'post':
            pattern_path = 'javascript/express/routes/post-users-auth.js'
        elif method_lower == 'put':
            pattern_path = 'javascript/express/routes/put-users-auth.js'
        elif method_lower == 'delete':
            pattern_path = 'javascript/express/routes/delete-users-auth.js'
        else:
            print(f"⚠️  No pattern for {method_lower}, skipping")
            continue
        
        # Load the pattern
        pattern = load_pattern(pattern_path)
        if not pattern:
            print(f"⚠️  Pattern not found: {pattern_path}, skipping")
            continue
        
        print(f"📋 Pattern: {pattern_path}")
        
        # Build prompt for the LLM
        prompt = f"""You are adding a new route to an EXISTING Express router file.

THE FILE ALREADY HAS:
- Express and router setup at the top
- Query function imports at the top: const {{ {", ".join(all_query_functions)} }} = require("../../db/queries/{resource}.queries");
- These routes: {chr(10).join(f'- {route}' for route in completed_routes)}
- module.exports at the bottom

PATTERN TO ADD:
{pattern}

{'=== DATABASE SCHEMA ===' if schema else ''}
{f'The {resource} table columns:{chr(10)}{schema}{chr(10)}CRITICAL: Use ONLY these exact column names.' if schema else ''}
{'=== END SCHEMA ===' if schema else ''}

QUERY FUNCTION TO USE:
{route_info['func']} - This function is ALREADY IMPORTED at the top

TASK: Add a {route_info['method']} {route_info['path']} route that uses {route_info['func']}

CRITICAL - DO NOT ADD:
- express/router setup (already exists)
- Query function imports (ALREADY IMPORTED AT TOP)
- module.exports (already at bottom)  
- ANY require() statements - the function is already imported!

ONLY ADD:
router.{method_lower}("{route_info['path']}", authenticateToken, async (req, res) => {{
  // Use {route_info['func']} which is already imported
}});

Change "users" to "{resource}" in the pattern.
Use the {route_info['func']} function that is ALREADY imported at the top.

Generate ONLY the router.{method_lower}(...) code block. Nothing else. No imports!
"""
        
        try:
            response = ollama.generate(
                model='llama3.1:8b',
                prompt=prompt,
                keep_alive=0
            )
            
            response_text = response['response']
            code = extract_code_from_response(response_text)
            explanation = extract_explanation_from_response(response_text)
            
            if not code:
                print(f"⚠️  No code block found in response")
                continue
            
            # Append generated route
            existing_content = output_file.read_text(encoding='utf-8', errors='ignore')
            combined_code = existing_content.rstrip() + "\n\n" + code.strip()
            output_file.write_text(combined_code, encoding='utf-8')
            
            # Append notes
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if notes_file.exists():
                existing_notes = notes_file.read_text(encoding='utf-8', errors='ignore')
            else:
                existing_notes = ''
            notes_content = f"\n{'='*60}\nAdded: {timestamp} - {route_info['method']} {route_info['path']}\nQuery function: {route_info['func']}\n\n"
            notes_content += "=== Explanation ===\n\n"
            notes_content += explanation if explanation else f"Added {route_info['method']} route using {route_info['func']}."
            notes_file.write_text(existing_notes + notes_content, encoding='utf-8')
            
            completed_routes.append(f"{route_info['method']} {route_info['path']}")
            print(f"✅ Step {i+1} complete")
            
        except Exception as e:
            print(f"❌ Generation failed: {e}")
            continue
    
    # Finally, add module.exports at bottom
    final_content = output_file.read_text(encoding='utf-8', errors='ignore').rstrip() + "\n\nmodule.exports = router;\n"
    output_file.write_text(final_content, encoding='utf-8')
    
    print(f"\n{'='*60}")
    print(f"  COMPLETE! Generated {len(completed_routes)} routes")
    print(f"  File: {output_file}")
    print('='*60)


def map_query_to_route(func_name, resource):
    """Map query function name to route details"""
    if resource.endswith('s'):
        resource_singular = resource[:-1]
    else:
        resource_singular = resource
    
    resource_cap = resource_singular.capitalize()
    
    # CREATE
    if func_name.startswith(f'create{resource_cap}'):
        return {'method': 'POST', 'path': f'/{resource}', 'func': func_name}
    
    # GET ALL (without joins)
    elif func_name == f'get{resource_cap}s':
        return {'method': 'GET', 'path': f'/{resource}', 'func': func_name}
    
    # GET BY ID
    elif 'ById' in func_name and func_name.startswith(f'get{resource_cap}'):
        return {'method': 'GET', 'path': f'/{resource}/:id', 'func': func_name}
    
    # UPDATE
    elif func_name.startswith(f'update{resource_cap}'):
        return {'method': 'PUT', 'path': f'/{resource}/:id', 'func': func_name}
    
    # DELETE
    elif func_name.startswith(f'delete{resource_cap}'):
        return {'method': 'DELETE', 'path': f'/{resource}/:id', 'func': func_name}
    
    # GET BY FIELD (e.g., getProductsByCategoryId)
    elif func_name.startswith(f'get{resource_cap}sBy'):
        after_by = func_name.split('By')[1]
        field_name = after_by.replace('WithDetails', '')
        field_snake = re.sub(r'(?<!^)(?=[A-Z])', '_', field_name).lower()
        return {'method': 'GET', 'path': f'/{resource}/by-{field_snake}/:{field_snake}', 'func': func_name}
    
    # GET WITH JOINS (all records) - skip if basic getProducts exists
    elif func_name.startswith(f'get{resource_cap}s') and 'With' in func_name:
        return None
    
    return None