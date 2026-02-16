# generators/query_generator.py
"""
Database query function generation - Sequential generation of query files
"""

import ollama
import re
from pathlib import Path
from datetime import datetime

from pattern_manager import load_pattern, get_pattern_metadata
from parsers import extract_code_from_response, extract_explanation_from_response

def generate_queries(resources, schema_content):
    """Generate query files for all resources
    
    Args:
        resources: List of resource dicts [{'name': 'products', 'operations': [...]}]
        schema_content: Full SQL schema to understand table structure
    """
    
    print(f"\n{'='*60}")
    print(f"  GENERATING QUERIES: {len(resources)} resource(s)")
    print('='*60)
    
    for resource_data in resources:
        resource_name = resource_data['name']
        
        # Extract this table's schema
        from file_manager import extract_table_from_schema
        table_schema = extract_table_from_schema(schema_content, resource_name)
        
        # Generate queries sequentially for this resource
        execute_sequential_query_generation(resource_name, table_schema)
    
    print(f"\n✅ Query generation complete")
    print('='*60)


def execute_sequential_query_generation(resource, table_schema):
    """Generate query functions one at a time for a resource"""
    
    print(f"\n{'='*60}")
    print(f"  SEQUENTIAL QUERY GENERATION: {resource}")
    print('='*60)
    
    # Parse schema to detect features
    has_foreign_keys = 'REFERENCES' in table_schema if table_schema else False
    
    # Extract foreign key column names for get-by-field queries
    foreign_key_columns = []
    if has_foreign_keys and table_schema:
        # Find all "column_name INTEGER REFERENCES"
        fk_pattern = r'(\w+)\s+(?:INTEGER|BIGINT)\s+REFERENCES'
        foreign_key_columns = re.findall(fk_pattern, table_schema, re.IGNORECASE)
    
    # Build query types list based on schema
    query_types = ['create', 'get-all']
    
    if has_foreign_keys:
        # Has FKs - use JOIN versions
        query_types.append('get-by-id-with-join')     # With details
        query_types.append('get-with-joins')          # All with details
        
        # Add get-by-field WITH joins for each FK
        for fk in foreign_key_columns:
            query_types.append(f'get-by-field-with-join:{fk}')
    else:
        # No FKs - use simple versions
        query_types.append('get-by-id')               # Simple
    
    query_types.extend(['update', 'delete'])
    
    print(f"📊 Detected foreign keys: {foreign_key_columns if foreign_key_columns else 'None'}")
    print(f"  Query types: {len(query_types)}")
    print('='*60)
    
    # Calculate output path ONCE before loop starts
    first_pattern_path = 'javascript/express/queries/create.js'
    first_pattern = load_pattern(first_pattern_path)
    
    if not first_pattern:
        print(f"⚠️  Pattern not found: {first_pattern_path}")
        return
    
    metadata = get_pattern_metadata(first_pattern_path)
    output_dir = metadata['output_dir'] if metadata else 'output'
    file_naming = metadata['file_naming'] if metadata else f'{resource}.queries.js'
    filename = file_naming.replace('{resource}', resource)
    output_file = Path('output') / output_dir / filename
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    completed_functions = []
    
    for i, query_type in enumerate(query_types):
        print(f"\n{'─'*60}")
        
        # Check if this is a get-by-field variant with specific column
        if query_type.startswith('get-by-field-with-join:'):
            field_name = query_type.split(':')[1]
            pattern_path = 'javascript/express/queries/get-by-field-with-join.js'
            display_name = f"get-by-{field_name}-with-join"
            print(f"Step {i+1}/{len(query_types)}: {display_name}")
        elif query_type.startswith('get-by-field:'):
            field_name = query_type.split(':')[1]
            pattern_path = 'javascript/express/queries/get-by-field.js'
            display_name = f"get-by-{field_name}"
            print(f"Step {i+1}/{len(query_types)}: {display_name}")
        else:
            pattern_path = f'javascript/express/queries/{query_type}.js'
            display_name = query_type
            print(f"Step {i+1}/{len(query_types)}: {query_type}")
        
        print('─'*60)
        
        # Load pattern
        pattern = load_pattern(pattern_path)
        
        if not pattern:
            print(f"⚠️  Pattern not found: {pattern_path}, skipping")
            continue
        
        print(f"📋 Pattern: {pattern_path}")
        
        # Check if this is first function or additional
        if completed_functions:
            print(f"📝 File already has: {', '.join(completed_functions)}")
        
        # Generate with ONLY this pattern + list of existing functions
        print(f"🔨 Generating {display_name}...")
        
        # Build prompt based on query type
        if query_type.startswith('get-by-field-with-join:'):
            field_name = query_type.split(':')[1]
            
            if completed_functions:
                prompt = f"""You are adding a new query function to an existing query file.

EXISTING FUNCTIONS (do not modify):
{chr(10).join(f'- {func}' for func in completed_functions)}

TABLE SCHEMA:
{table_schema if table_schema else 'Schema not available'}

PATTERN TO ADD:
{pattern}

TASK: Add a get-by-{field_name} WITH JOIN function for {resource}.

CRITICAL INSTRUCTIONS:

1. The file already has the functions listed above - DO NOT regenerate or modify them
2. ADD ONLY the new function from the pattern
3. Function name: get{resource.capitalize()}By{field_name.replace('_', ' ').title().replace(' ', '')}WithDetails
4. Parameter: {field_name}
5. Parse REFERENCES from schema to determine which tables to JOIN
6. Build LEFT JOINs for all foreign key relationships
7. SQL: SELECT with JOINs, WHERE {field_name} = $1
8. Return all matching rows with joined data

What you MUST KEEP:
- Parameterized query ($1)
- Error handling
- Return structure

Generate ONLY the new function code.
DO NOT include imports.

Wrap your code in ```javascript code fences.

Then after the code block, briefly explain the function.
"""
            else:
                prompt = f"""You are generating production-ready query code based on a pattern.

=== REFERENCE PATTERN ===
{pattern}
=== END PATTERN ===

TABLE SCHEMA:
{table_schema if table_schema else 'Schema not available'}

USER REQUEST: Generate get-by-{field_name} WITH JOIN function for {resource}

CRITICAL INSTRUCTIONS:

1. Follow the pattern structure EXACTLY
2. Include the db import at top
3. Function name: get{resource.capitalize()}By{field_name.replace('_', ' ').title().replace(' ', '')}WithDetails
4. Parameter: {field_name}
5. Parse REFERENCES from schema to build JOINs
6. SQL: SELECT with JOINs, WHERE {field_name} = $1
7. Return all matching rows with joined data

Generate COMPLETE file with imports.

Wrap your code in ```javascript code fences.

Then after the code block, briefly explain what you generated.
"""
        elif query_type.startswith('get-by-field:'):
            field_name = query_type.split(':')[1]
            
            if completed_functions:
                prompt = f"""You are adding a new query function to an existing query file.

EXISTING FUNCTIONS (do not modify):
{chr(10).join(f'- {func}' for func in completed_functions)}

TABLE SCHEMA:
{table_schema if table_schema else 'Schema not available'}

PATTERN TO ADD:
{pattern}

TASK: Add a get-by-{field_name} function for {resource}.

CRITICAL INSTRUCTIONS:

1. The file already has the functions listed above - DO NOT regenerate or modify them
2. ADD ONLY the new function from the pattern
3. Function name: get{resource.capitalize()}By{field_name.replace('_', ' ').title().replace(' ', '')}
4. Parameter: {field_name}
5. SQL: SELECT * FROM {resource} WHERE {field_name} = $1
6. Return all matching rows (not just first)

Generate ONLY the new function code.
DO NOT include imports.

Wrap your code in ```javascript code fences.

Then after the code block, briefly explain the function.
"""
            else:
                prompt = f"""You are generating production-ready query code based on a pattern.

=== REFERENCE PATTERN ===
{pattern}
=== END PATTERN ===

TABLE SCHEMA:
{table_schema if table_schema else 'Schema not available'}

USER REQUEST: Generate get-by-{field_name} function for {resource}

CRITICAL INSTRUCTIONS:

1. Follow the pattern structure EXACTLY
2. Include the db import at top
3. Function name: get{resource.capitalize()}By{field_name.replace('_', ' ').title().replace(' ', '')}
4. Parameter: {field_name}
5. SQL: SELECT * FROM {resource} WHERE {field_name} = $1
6. Return all matching rows

Generate COMPLETE file with imports.

Wrap your code in ```javascript code fences.

Then after the code block, briefly explain what you generated.
"""
        else:
            # Regular query type (create, get-all, etc.)
            if completed_functions:
                prompt = f"""You are adding a new query function to an existing query file.

EXISTING FUNCTIONS (do not modify):
{chr(10).join(f'- {func}' for func in completed_functions)}

TABLE SCHEMA:
{table_schema if table_schema else 'Schema not available'}

PATTERN TO ADD:
{pattern}

TASK: Add the {query_type} function for {resource}.

CRITICAL INSTRUCTIONS:

1. The file already has the functions listed above - DO NOT regenerate or modify them
2. ADD ONLY the new {query_type} function from the pattern
3. Adapt the pattern from "users"/"orders" to "{resource}"

What you MUST change in the NEW function:
- Variable names: users/orders → {resource}
- Table name: FROM users/orders → FROM {resource}
- Use ONLY columns from the schema above

What you MUST KEEP in the NEW function:
- All SQL queries (just change table/column names)
- All parameterized queries ($1, $2)
- All error handling
- All return structures

4. For get-with-joins or get-by-id-with-join: Parse REFERENCES from schema to build JOINs automatically
5. Generate ONLY the new function code
6. DO NOT include imports (already in file)
7. Generate ONLY ONE function - do not create variations or extras

Wrap your code in ```javascript code fences.

OUTPUT FORMAT:
First: Code block with the function
Then: 2-3 sentences explaining what you adapted from the pattern.
"""
            else:
                prompt = f"""You are generating production-ready query code based on a pattern.

=== REFERENCE PATTERN ===
{pattern}
=== END PATTERN ===

TABLE SCHEMA:
{table_schema if table_schema else 'Schema not available'}

USER REQUEST: Generate {query_type} function for {resource}

CRITICAL INSTRUCTIONS:

1. Follow the pattern structure EXACTLY
2. Include the db import: const db = require('../../connection');
3. Replace "user"/"users"/"orders" with "{resource}"
4. Use ONLY columns from the schema above
5. For get-with-joins or get-by-id-with-join: Parse REFERENCES from schema to build JOINs automatically
6. Keep parameterized queries, error handling, returns

Generate COMPLETE file with imports.

Wrap your code in ```javascript code fences.

Then after the code block, briefly explain what you generated.
"""
        
        try:
            response = ollama.generate(
                model='llama3.1:8b',
                prompt=prompt,
                keep_alive=0
            )
            
            response_text = response['response']
            
            # Extract code and explanation
            code = extract_code_from_response(response_text)
            explanation = extract_explanation_from_response(response_text)
            
            if not code:
                print(f"⚠️  No code block found in response")
                continue
            
            # If this is not the first function, append to existing file
            if completed_functions:
                # Read existing file
                existing_content = output_file.read_text(encoding='utf-8')
                
                # Strip ALL existing timestamp comments
                existing_without_timestamps = re.sub(r'^//\s*Generated:.*?\n', '', existing_content, flags=re.MULTILINE)
                
                # Combine: existing code + new function
                combined_code = existing_without_timestamps.rstrip() + "\n\n" + code.strip()
                
                # Save combined with single timestamp
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                final_code = f"// Generated: {timestamp}\n\n{combined_code}"
                output_file.write_text(final_code, encoding='utf-8')
                print(f"✅ Saved code: {output_file}")
                
                # Save explanation (append to notes)
                notes_file = output_file.parent / f"{resource}.queries_notes.txt"
                existing_notes = notes_file.read_text(encoding='utf-8')
                
                notes_content = f"\n\n{'='*60}\n"
                notes_content += f"Added: {timestamp} - {display_name}\n\n"
                notes_content += "=== Explanation ===\n\n"
                
                if explanation and explanation.strip():
                    notes_content += explanation
                else:
                    notes_content += f"Added {display_name} query function following schema structure."
                
                notes_file.write_text(existing_notes + notes_content, encoding='utf-8')
                print(f"✅ Saved notes: {notes_file}")
            else:
                # First function - save to calculated output_file path
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                final_code = f"// Generated: {timestamp}\n\n{code}"
                output_file.write_text(final_code, encoding='utf-8')
                print(f"✅ Saved code: {output_file}")
                
                # Save notes
                notes_file = output_file.parent / f"{resource}.queries_notes.txt"
                notes_content = f"Generated: {timestamp}\n\n"
                notes_content += f"Resource: {resource}\n\n"
                notes_content += "=== Explanation ===\n\n"
                notes_content += explanation if explanation else f"Generated {display_name} query function"
                notes_file.write_text(notes_content, encoding='utf-8')
                
                print(f"✅ Saved notes: {notes_file}")
            
            # Track this function as completed
            func_name = f"{display_name}_{resource}"
            completed_functions.append(func_name)
            
            print(f"✅ Step {i+1} complete")
            
        except Exception as e:
            print(f"❌ Generation failed: {e}")
            continue
    
    print(f"\n{'='*60}")
    print(f"  🎉 COMPLETE! Generated {len(completed_functions)} query functions")
    print(f"  📄 File: {output_file}")
    print('='*60)