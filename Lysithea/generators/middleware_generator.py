import ollama
import re
from pathlib import Path
from datetime import datetime

from pattern_manager import load_pattern, map_operation_to_pattern, get_pattern_metadata
from parsers import extract_code_from_response, extract_explanation_from_response
from file_manager import save_generated_files

def generate_middleware(middleware_name):
    """Generate a standalone middleware file (no operations loop)"""
    
    print(f"\n{'='*60}")
    print(f"  GENERATING MIDDLEWARE: {middleware_name}")
    print('='*60)
    
    # Map middleware name to pattern file
    # For now, simple mapping - later you can make this smarter
    pattern_map = {
        'auth': 'javascript/express/middleware/auth-middleware.js',
        'authentication': 'javascript/express/middleware/auth-middleware.js',
        'validation': 'javascript/express/middleware/validation-middleware.js',
        'error': 'javascript/express/middleware/error-middleware.js',
    }
    
    pattern_path = pattern_map.get(middleware_name)
    
    if not pattern_path:
        print(f"⚠️  Unknown middleware type: {middleware_name}")
        return
    
    # Load pattern
    pattern = load_pattern(pattern_path)
    if not pattern:
        print(f"⚠️  Pattern not found: {pattern_path}")
        return
    
    print(f"📋 Pattern: {pattern_path}")
    
    # Get output path from pattern metadata
    metadata = get_pattern_metadata(pattern_path)
    output_dir = metadata['output_dir'] if metadata else 'output'
    file_naming = metadata['file_naming'] if metadata else f'{middleware_name}.js'
    output_file = Path('output') / output_dir / file_naming
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"🔨 Generating {middleware_name} middleware...")
    
    # Middleware doesn't need adaptation - use pattern as-is
    prompt = f"""You are generating a complete middleware file from a pattern.

=== PATTERN ===
{pattern}

Generate the complete middleware file exactly as shown in the pattern.
Remove only the documentation comments (/** ... */).
Keep all the actual code, imports, and exports.

Output just the code in a code block.
"""
    
    try:
        response = ollama.generate(
            model='llama3.1:8b',
            prompt=prompt,
            keep_alive=0
        )
        
        response_text = response['response']
        code = extract_code_from_response(response_text)
        
        if not code:
            print(f"⚠️  No code block found")
            return
        
        # Save to file
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        final_code = f"// Generated: {timestamp}\n\n{code}"
        output_file.write_text(final_code, encoding='utf-8')

        print(f"✅ Saved: {output_file}")

        # ADD THIS: Save notes file
        notes_file = output_file.parent / f"{middleware_name}_notes.txt"
        notes_content = f"Generated: {timestamp}\n\n"
        notes_content += f"Middleware: {middleware_name}\n\n"
        notes_content += "=== Description ===\n\n"
        notes_content += f"Authentication middleware for JWT token verification. Protects routes by validating Bearer tokens and adding decoded user data to req.user."
        notes_file.write_text(notes_content, encoding='utf-8')
        print(f"✅ Saved notes: {notes_file}")

        print(f"✅ Middleware generation complete")
        
    except Exception as e:
        print(f"❌ Generation failed: {e}")

    print('='*60)