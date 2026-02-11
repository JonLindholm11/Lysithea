# cli.py

import ollama
from pathlib import Path
import re
from datetime import datetime

def load_pattern(pattern_path):
    """Load a pattern file"""
    full_path = Path('..') / 'patterns' / pattern_path
    if not full_path.exists():
        return None
    return full_path.read_text()

def list_available_patterns():
    """Get list of all available patterns (only used for /list command now)"""
    pattern_dir = Path('..') / 'patterns'
    if not pattern_dir.exists():
        return []
    
    patterns = []
    for pattern_file in pattern_dir.rglob('*.js'):
        relative_path = pattern_file.relative_to(pattern_dir)
        patterns.append(str(relative_path))
    
    return patterns

def coordinator_agent(user_input):
    """Break down user request into sequential generation steps"""
    
    prompt = f"""You are a task coordinator for a code generator.

User request: "{user_input}"

Your job: Break this into SEQUENTIAL steps for code generation.

Available operations:
- GET all (list with pagination and authentication)
- GET by ID (single resource by ID with authentication)
- POST (create new resource with validation and authentication)
- PUT (update existing resource with validation and authentication)
- DELETE (remove resource with authentication)

Analyze the request and identify:
1. What resource is being requested (e.g., "products", "users", "orders")
2. What operations are needed

Common patterns:
- "complete CRUD" = all 5 operations
- "basic API" = GET all, GET by ID, POST
- "read-only API" = GET all, GET by ID

Format your response EXACTLY like this:

RESOURCE: [resource name]
OPERATIONS:
- GET all
- GET by ID
- POST
- PUT
- DELETE

Only list operations that were requested. List them in this order for best results.
"""
    
    print("\n[Coordinator Agent analyzing request...]")
    
    try:
        response = ollama.generate(
            model='llama3.1:8b',
            prompt=prompt
        )
        
        ai_response = response['response'].strip()
        print(f"\n{ai_response}\n")
        
        # Parse resource name
        resource = None
        for line in ai_response.split('\n'):
            if 'RESOURCE:' in line:
                resource = line.split('RESOURCE:')[1].strip()
                # Clean the resource name - remove leading slashes and special chars
                resource = resource.lstrip('/').strip()
                resource = re.sub(r'[^\w-]', '', resource)
                break
        
        # Parse operations
        operations = []
        in_operations = False
        for line in ai_response.split('\n'):
            if 'OPERATIONS:' in line or 'OPERATION:' in line:
                in_operations = True
                continue
            
            if in_operations and line.strip().startswith('-'):
                op = line.strip().lstrip('- ').strip()
                if op:
                    operations.append(op)
        
        if not resource or not operations:
            print("[Could not parse coordinator response]")
            return None, None
        
        print(f"[Parsed: Resource='{resource}', Operations={len(operations)}]")
        return resource, operations
        
        if not resource or not operations:
            print("[Could not parse coordinator response]")
            return None, None
        
        print(f"[Parsed: Resource='{resource}', Operations={len(operations)}]")
        return resource, operations
        
    except Exception as e:
        print(f"[Coordinator error: {e}]")
        return None, None

def map_operation_to_pattern(operation):
    """Map operation name to pattern file"""
    op_lower = operation.lower()
    
    if 'get' in op_lower and ('by id' in op_lower or 'by-id' in op_lower or 'single' in op_lower):
        return 'javascript/express/routes/get-users-by-id-auth.js'
    elif 'get' in op_lower:
        return 'javascript/express/routes/get-users-auth.js'
    elif 'post' in op_lower or 'create' in op_lower:
        return 'javascript/express/routes/post-users-auth.js'
    elif 'put' in op_lower or 'update' in op_lower:
        return 'javascript/express/routes/put-user-auth.js'
    elif 'delete' in op_lower or 'remove' in op_lower:
        return 'javascript/express/routes/delete-users-auth.js'
    
    return None

def generate_with_pattern(resource, operations_so_far, pattern_paths):
    """Generate code using multiple patterns"""
    
    # Load all patterns for operations so far
    patterns_content = []
    for pattern_path in pattern_paths:
        pattern = load_pattern(pattern_path)
        if pattern:
            patterns_content.append(f"=== PATTERN: {pattern_path} ===\n{pattern}\n")
    
    if not patterns_content:
        return None
    
    all_patterns = "\n".join(patterns_content)
    operations_list = ", ".join(operations_so_far)
    
    prompt = f"""You are generating production-ready code based on existing patterns.

{all_patterns}

USER REQUEST: Generate {operations_list} routes for {resource} with authentication

CRITICAL INSTRUCTIONS:

1. You have {len(patterns_content)} pattern(s) above - one for each operation
2. Generate ONE cohesive Express router file with ALL {len(patterns_content)} operations
3. Follow each pattern's structure exactly for its operation

4. DO NOT REMOVE ANY CODE from the patterns
5. DO NOT create placeholder comments like "// logic here" or "// implementation here"
6. KEEP ALL implementation details - queries, pagination, validation, error handling

7. What you MUST change:
   - Resource name: "users" → "{resource}"
   - Table name: FROM users → FROM {resource}
   - Route paths: /users → /{resource}
   - Variable names: user/users → {resource} (singular/plural appropriately)
   - Error messages: "user" → "{resource}"

8. What you MUST KEEP EXACTLY:
   - All SQL queries (just change table/column names)
   - All pagination logic (page, limit, offset, totalPages)
   - All validation logic (required fields, format checks)
   - All error handling (try/catch, proper status codes)
   - All security (parameterized queries with $1, $2, etc.)
   - All response structures

9. DO NOT include pattern documentation comments (/** ... */)
10. Include only essential inline comments

Generate COMPLETE, WORKING code. No placeholders. No TODOs.
One code block with all {len(patterns_content)} operations.
"""
    
    try:
        response = ollama.generate(
            model='llama3.1:8b',
            prompt=prompt
        )
        
        return response['response']
    except Exception as e:
        print(f"[Generation error: {e}]")
        return None

def extract_code_from_response(response_text):
    """Extract code block from AI response and remove documentation comments"""
    pattern = r'```(?:javascript|python|jsx|js|py|typescript|ts)?\n(.*?)```'
    matches = re.findall(pattern, response_text, re.DOTALL)
    
    if matches:
        code = matches[0].strip()
        code = re.sub(r'/\*\*.*?\*/', '', code, flags=re.DOTALL)
        code = re.sub(r'\n{3,}', '\n\n', code)
        return code.strip()
    
    return None

def extract_explanation_from_response(response_text):
    """Extract explanation text (everything after code block)"""
    parts = re.split(r'```.*?```', response_text, flags=re.DOTALL)
    if len(parts) > 1:
        return parts[-1].strip()
    return response_text.strip()

def save_generated_files(code, explanation, resource_name="generated", append_notes=False):
    """Save code and explanation to files"""
    
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    
    code_filename = f"{resource_name}.js"
    notes_filename = f"{resource_name}_notes.txt"
    
    code_path = output_dir / code_filename
    notes_path = output_dir / notes_filename
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Save code (always overwrite)
    code_with_timestamp = f"// Generated: {timestamp}\n\n{code}"
    code_path.write_text(code_with_timestamp, encoding='utf-8')
    print(f"✅ Saved code: {code_path}")
    
    # Save notes (append if requested)
    if append_notes and notes_path.exists():
        # Append to existing notes
        existing_notes = notes_path.read_text(encoding='utf-8')
        notes_content = f"\n\n{'='*60}\n"
        notes_content += f"Added: {timestamp}\n\n"
        notes_content += "=== Explanation ===\n\n"
        notes_content += explanation
        notes_path.write_text(existing_notes + notes_content, encoding='utf-8')
    else:
        # Create new notes file
        notes_content = f"Generated: {timestamp}\n\n"
        notes_content += f"Resource: {resource_name}\n\n"
        notes_content += "=== Explanation ===\n\n"
        notes_content += explanation
        notes_path.write_text(notes_content, encoding='utf-8')
    
    print(f"✅ Saved notes: {notes_path}")
    
    return code_path, notes_path

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
                prompt=prompt
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

def get_response(user_input, use_pattern=False):
    """Get response from Ollama with optional pattern coordination"""
    
    if use_pattern:
        # Use coordinator agent to break down request
        resource, operations = coordinator_agent(user_input)
        
        if resource and operations:
            # Execute sequential generation
            execute_sequential_generation(resource, operations)
            return f"\n✅ Sequential generation complete for {resource}"
        else:
            print("[Coordinator could not parse request - falling back to baseline]")
    
    # Baseline mode (no patterns)
    prompt = f"""You are a helpful coding assistant.

USER REQUEST: {user_input}

Generate the code and explain your decisions.
"""
    
    try:
        response = ollama.generate(
            model='llama3.1:8b',
            prompt=prompt
        )
        
        return response['response']
    except Exception as e:
        return f"Error generating response: {e}"

def main():
    print("Lysithea v0.2.0 - Sequential Pattern Generation")
    print("\nCommands:")
    print("  /pattern   - Toggle pattern mode ON/OFF")
    print("  /list      - List available patterns")
    print("  /status    - Show current mode")
    print("  quit       - Exit")
    print("-" * 50)
    
    use_pattern = False
    
    while True:
        mode = "[PATTERN]" if use_pattern else "[BASELINE]"
        user_input = input(f"\n{mode} > ")
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        
        if user_input.lower() == '/pattern':
            use_pattern = not use_pattern
            print(f"Pattern mode: {'ON' if use_pattern else 'OFF'}")
            continue
        
        if user_input.lower() == '/list':
            patterns = list_available_patterns()
            if patterns:
                print("\nAvailable patterns:")
                for p in patterns:
                    print(f"  - {p}")
            else:
                print("No patterns found")
            continue
        
        if user_input.lower() == '/status':
            print(f"Pattern mode: {'ON' if use_pattern else 'OFF'}")
            continue
            
        try:
            response = get_response(user_input, use_pattern)
            print(f"\n{response}\n")
        except Exception as e:
            print(f"Error: {e}")
            print("Make sure Ollama is running")

if __name__ == "__main__":
    main()