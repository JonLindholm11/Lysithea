# lysithea/generator.py
"""
Sequential code generation - builds files incrementally operation by operation
"""

import ollama
import re
from pathlib import Path
from datetime import datetime

from pattern_manager import load_pattern, map_operation_to_pattern
from parsers import extract_code_from_response, extract_explanation_from_response
from file_manager import save_generated_files

def execute_sequential_generation(resource, operations):
    """Execute sequential code generation - one operation at a time, tracking what exists"""
    
    print(f"\n{'='*60}")
    print(f"  SEQUENTIAL GENERATION: {resource}")
    print(f"  Operations: {len(operations)}")
    print('='*60)
    
    output_file = Path('output') / f"{resource}.js"
    completed_routes = []  # Track what we've generated, don't show code
    
    for i, operation in enumerate(operations):
        print(f"\n{'─'*60}")
        print(f"Step {i+1}/{len(operations)}: {operation}")
        print('─'*60)
        
        # Map operation to pattern file
        pattern_path = map_operation_to_pattern(operation)
        
        if not pattern_path:
            print(f"⚠️  Could not map operation '{operation}' to pattern, skipping")
            continue
        
        # Load the pattern
        pattern = load_pattern(pattern_path)
        if not pattern:
            print(f"⚠️  Pattern not found: {pattern_path}, skipping")
            continue
        
        print(f"📋 Pattern: {pattern_path}")
        
        # Check if this is first route or additional
        if completed_routes:
            print(f"📝 File already has: {', '.join(completed_routes)}")
        
        # Generate with ONLY this pattern + list of existing routes
        print(f"🔨 Generating {operation}...")
        
        if completed_routes:
            # We have existing routes - ADD to them
            prompt = f"""You are adding a new operation to an existing Express router file.

EXISTING ROUTES IN FILE (do not modify these):
{chr(10).join(f'- {route}' for route in completed_routes)}

PATTERN TO ADD:
{pattern}

TASK: Add the {operation} route for {resource}.

CRITICAL INSTRUCTIONS:

1. The file already has the routes listed above - DO NOT regenerate or modify them
2. ADD ONLY the new {operation} route from the pattern
3. Adapt the pattern from "users" to "{resource}"

What you MUST change in the NEW route:
- Variable names: users → {resource}
- Table name: FROM users → FROM {resource}
- Route path: /users → /{resource}
- Error messages: "user" → "{resource}"

What you MUST KEEP in the NEW route:
- All SQL queries (just change table/column names)
- All validation logic
- All error handling  
- All security (parameterized queries $1, $2)
- All response structures

4. Generate ONLY the new route code that will be added to the file
5. DO NOT include:
   - Pattern documentation comments (/** ... */)
   - Boilerplate (const express = require...)
   - Module.exports (already in file)
   - Existing routes

OUTPUT FORMAT:
First: Code block with the route
Then: 2-3 sentences explaining what you adapted from the pattern and what validation/security features are included in this route.

Example explanation:
"I adapted the GET by ID pattern for products, changing the table from 'users' to 'products' and the route path. The route includes ID validation, parameterized SQL queries to prevent injection, 404 handling for missing products, and proper error codes."
"""
        else:
            # First operation - generate complete file with boilerplate
            prompt = f"""You are generating production-ready code based on a pattern.

=== REFERENCE PATTERN ===
{pattern}
=== END PATTERN ===

USER REQUEST: Generate {operation} route for {resource} with authentication

CRITICAL INSTRUCTIONS:

1. Follow the pattern structure EXACTLY
2. DO NOT remove any code from the pattern
3. DO NOT create placeholder comments

What you MUST change:
- Variable names: users → {resource}
- Table name: FROM users → FROM {resource}  
- Route path: /users → /{resource}
- Error messages: "user" → "{resource}"

What you MUST KEEP:
- All SQL queries (just change table/column names)
- All validation logic (required fields, regex, duplicate checks)
- All error handling (try/catch, status codes)
- All security (parameterized queries $1, $2)
- All response structures (data, pagination, error codes)

4. DO NOT include pattern documentation comments (/** ... */)
5. Include only essential inline comments

Generate COMPLETE router file with boilerplate (requires, router setup, module.exports).

Then after the code block, briefly explain what you generated.
"""
        
        try:
            response = ollama.generate(
                model='llama3.1:8b',
                prompt=prompt,
                keep_alive=0  # ← Force context clear after each generation
            )
            
            response_text = response['response']

            # DEBUG: Show what we got
            print(f"\n[DEBUG] Response length: {len(response_text)} chars")
            print(f"[DEBUG] First 500 chars:\n{response_text[:500]}\n")

            # Extract code
            code = extract_code_from_response(response_text)
            explanation = extract_explanation_from_response(response_text)
            
            if not code:
                print(f"⚠️  No code block found in response")
                continue
            
            # If this is not the first route, we need to append to existing file
            if completed_routes:
                # Read existing file
                existing_content = output_file.read_text(encoding='utf-8')
                
                # Strip ALL existing timestamp comments
                existing_without_timestamps = re.sub(r'^//\s*Generated:.*?\n', '', existing_content, flags=re.MULTILINE)
                
                # Remove the module.exports line from existing
                existing_without_export = re.sub(r'\s*module\.exports\s*=\s*router\s*;?\s*$', '', existing_without_timestamps, flags=re.MULTILINE)
                
                # Combine: existing code + new route + module.exports
                combined_code = existing_without_export.rstrip() + "\n\n" + code.strip() + "\n\nmodule.exports = router;"
                
                # Save combined with single timestamp
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                final_code = f"// Generated: {timestamp}\n\n{combined_code}"
                output_file.write_text(final_code, encoding='utf-8')
                print(f"✅ Saved code: {output_file}")
                
                # Save explanation (append)
                notes_file = Path('output') / f"{resource}_notes.txt"
                existing_notes = notes_file.read_text(encoding='utf-8')
                
                notes_content = f"\n\n{'='*60}\n"
                notes_content += f"Added: {timestamp} - {operation}\n\n"
                notes_content += "=== Explanation ===\n\n"
                
                if explanation and explanation.strip():
                    notes_content += explanation
                else:
                    notes_content += f"Added {operation} route following the pattern structure with proper validation and error handling."
                
                notes_file.write_text(existing_notes + notes_content, encoding='utf-8')
                print(f"✅ Saved notes: {notes_file}")
            else:
                # First route - save as-is
                save_generated_files(code, explanation, resource, append_notes=False)
            
            # Track this route as completed
            if "by ID" in operation or "by id" in operation.lower():
                route_signature = f"{operation.split()[0].upper()} /{resource}/:id"
            else:
                route_signature = f"{operation.split()[0].upper()} /{resource}"
            
            completed_routes.append(route_signature)
            
            print(f"✅ Step {i+1} complete")
            
        except Exception as e:
            print(f"❌ Generation failed: {e}")
            continue
    
    print(f"\n{'='*60}")
    print(f"  🎉 COMPLETE! Generated {len(completed_routes)} operations")
    print(f"  📄 File: output/{resource}.js")
    print('='*60)