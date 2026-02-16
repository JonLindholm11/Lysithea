# generators/seed_generator.py
"""
Database seed file generation - JavaScript seed files with sample data
"""

import ollama
from pathlib import Path
from datetime import datetime

from pattern_manager import load_pattern, get_pattern_metadata
from parsers import extract_code_from_response, extract_explanation_from_response

def generate_seeds(resources, schema_content):
    """Generate seed files for all resources
    
    Args:
        resources: List of resource dicts [{'name': 'products', 'operations': [...]}]
        schema_content: Full SQL schema to understand table structure
    """
    
    print(f"\n{'='*60}")
    print(f"  GENERATING SEEDS: {len(resources)} table(s)")
    print('='*60)
    
    # Load seed pattern
    pattern_path = 'javascript/express/database/seeds/seed_users.js'
    pattern = load_pattern(pattern_path)
    
    if not pattern:
        print(f"⚠️  Pattern not found: {pattern_path}")
        return
    
    print(f"📋 Pattern: {pattern_path}")
    
    # Get output path from pattern metadata
    metadata = get_pattern_metadata(pattern_path)
    output_dir = metadata['output_dir'] if metadata else 'output'
    
    print(f"🔨 Generating seed files for: {', '.join([r['name'] for r in resources])}...")
    
    # Generate seed for each resource
    seed_files = []
    
    for resource_data in resources:
        resource_name = resource_data['name']
        
        # Extract this table's schema
        from file_manager import extract_table_from_schema
        table_schema = extract_table_from_schema(schema_content, resource_name)
        
        prompt = f"""Generate a JavaScript seed file for the {resource_name} table.

=== TABLE SCHEMA ===
{table_schema if table_schema else 'Schema not available'}

CRITICAL: Use ONLY the columns that exist in the schema above. Do NOT add foreign keys like category_id or brand_id unless they appear in the CREATE TABLE statement.

=== PATTERN ===
{pattern}

INSTRUCTIONS:
1. Replace "users" with "{resource_name}" everywhere
2. Create 5-10 realistic sample records
3. Use ONLY columns from the schema (no invented foreign keys)
4. Generate realistic data appropriate for {resource_name}
5. If schema has foreign key columns, use realistic IDs (1, 2, 3, etc.)
6. Use parameterized query with columns in schema order
7. Keep async/await pattern and console.log

Output complete JavaScript file, then explain your data choices.
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
            
            if code:
                # Save seed file
                file_naming = metadata['file_naming'] if metadata else 'seed_{resource}.js'
                filename = file_naming.replace('{resource}', resource_name)
                output_file = Path('output') / output_dir / filename
                output_file.parent.mkdir(parents=True, exist_ok=True)
                
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                final_code = f"// Generated: {timestamp}\n\n{code}"
                output_file.write_text(final_code, encoding='utf-8')
                
                seed_files.append({
                    'resource': resource_name,
                    'file': filename,
                    'explanation': explanation
                })
                
                print(f"  ✅ Generated seed: {filename}")
            else:
                print(f"  ⚠️  No code found for {resource_name}")
                
        except Exception as e:
            print(f"  ❌ Failed to generate {resource_name}: {e}")
    
    if not seed_files:
        print("⚠️  No seed files generated")
        return
    
    # Generate index.js to run all seeds
    generate_seed_index(seed_files, output_dir)
    
    # Save notes
    notes_file = Path('output') / output_dir / "seeds_notes.txt"
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    notes_content = f"Generated: {timestamp}\n\n"
    notes_content += f"Seed Files: {len(seed_files)}\n\n"
    notes_content += "=== Seed Data Decisions ===\n\n"
    
    for seed in seed_files:
        notes_content += f"## {seed['resource'].capitalize()}\n\n"
        if seed['explanation']:
            notes_content += f"{seed['explanation']}\n\n"
    
    notes_file.write_text(notes_content, encoding='utf-8')
    print(f"\n✅ Saved notes: {notes_file}")
    
    print(f"✅ Seed generation complete")
    print('='*60)


def generate_seed_index(seed_files, output_dir):
    """Generate index.js that runs all seed files"""
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Build imports
    imports = []
    calls = []
    
    for seed in seed_files:
        resource = seed['resource']
        func_name = f"seed{resource.capitalize()}"
        imports.append(f"const {{ {func_name} }} = require('./{seed['file'].replace('.js', '')}');")
        calls.append(f"  await {func_name}();")
    
    index_content = f"""// Generated: {timestamp}

{chr(10).join(imports)}

async function runSeeds() {{
  try {{
    console.log('🌱 Starting database seeding...');
    
{chr(10).join(calls)}
    
    console.log('✅ All seeds completed successfully');
    process.exit(0);
  }} catch (error) {{
    console.error('❌ Seeding failed:', error);
    process.exit(1);
  }}
}}

runSeeds();
"""
    
    index_file = Path('output') / output_dir / 'index.js'
    index_file.write_text(index_content, encoding='utf-8')
    print(f"  ✅ Generated seed index: index.js")