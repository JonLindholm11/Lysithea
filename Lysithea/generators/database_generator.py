# generators/database_generator.py
"""
Database file generation - connection, schemas, migrations
"""

import ollama
from pathlib import Path
from datetime import datetime

from pattern_manager import load_pattern, get_pattern_metadata
from parsers import extract_code_from_response

def generate_database(db_type):
    """Generate database files (connection, schema, etc.)"""
    
    print(f"\n{'='*60}")
    print(f"  GENERATING DATABASE: {db_type}")
    print('='*60)
    
    # Map database type to pattern file
    pattern_map = {
        'connection': 'javascript/express/database/connection.js',
        'schema': 'javascript/express/database/schema.sql',
        'migration': 'javascript/express/database/migration.sql',
    }
    
    pattern_path = pattern_map.get(db_type)
    
    if not pattern_path:
        print(f"⚠️  Unknown database type: {db_type}")
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
    file_naming = metadata['file_naming'] if metadata else f'{db_type}.js'
    output_file = Path('output') / output_dir / file_naming
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"🔨 Generating {db_type}...")
    
    # Database files don't need adaptation - use pattern as-is
    prompt = f"""You are generating a complete database file from a pattern.

=== PATTERN ===
{pattern}

Generate the complete file exactly as shown in the pattern.
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
        print(f"✅ Database generation complete")
        
    except Exception as e:
        print(f"❌ Generation failed: {e}")

    print('='*60)