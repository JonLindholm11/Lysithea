# generators/schema_generator.py
"""
Database schema generation - CREATE TABLE statements for all resources
"""

import ollama
from pathlib import Path
from datetime import datetime

from pattern_manager import load_pattern, get_pattern_metadata
from parsers import extract_code_from_response, extract_explanation_from_response

def generate_schema(resources):
    """Generate database schema file with tables for all resources
    
    Args:
        resources: List of resource dicts [{'name': 'products', 'operations': [...]}]
    """
    
    print(f"\n{'='*60}")
    print(f"  GENERATING SCHEMA: {len(resources)} table(s)")
    print('='*60)
    
    # Load schema pattern
    pattern_path = 'javascript/express/database/schema.sql'
    pattern = load_pattern(pattern_path)
    
    if not pattern:
        print(f"⚠️  Pattern not found: {pattern_path}")
        return None
    
    print(f"📋 Pattern: {pattern_path}")
    
    # Get output path from pattern metadata
    metadata = get_pattern_metadata(pattern_path)
    output_dir = metadata['output_dir'] if metadata else 'output'
    file_naming = metadata['file_naming'] if metadata else 'schema.sql'
    output_file = Path('output') / output_dir / file_naming
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"🔨 Generating schema for: {', '.join([r['name'] for r in resources])}...")
    
    # Generate schema for each resource
    all_schemas = []
    schema_explanations = {}  # Store AI's reasoning
    
    for resource_data in resources:
        resource_name = resource_data['name']
        
        prompt = f"""Generate a PostgreSQL CREATE TABLE statement for: {resource_name}

Think about what fields this resource would realistically need:
- What are the core attributes? (e.g., products have name/price, users have email/username)
- What relationships exist? (e.g., orders need customer_id, reviews need product_id)
- What common operations happen? (e.g., products need stock tracking, users need roles)

Examples of well-designed tables:
- products: name, description, price, stock_quantity, sku, image_url, category_id
- users: email, username, password_hash, first_name, last_name, role
- orders: customer_id, order_date, total, status

Use these as inspiration, not rules. Design what makes sense for {resource_name}.

ALWAYS include: id (PRIMARY KEY), created_at, updated_at, is_deleted, deleted_at
Add appropriate indexes for common queries.
Remove pattern documentation comments.

Output the SQL code in a code block, then explain your field choices in 2-3 sentences.
"""
        
        try:
            response = ollama.generate(
                model='llama3.1:8b',
                prompt=prompt,
                keep_alive=0
            )
            
            response_text = response['response']
            
            print(f"\n[DEBUG] Response length: {len(response_text)} chars")
            print(f"[DEBUG] First 500 chars:\n{response_text[:500]}\n")
            
            code = extract_code_from_response(response_text)
            explanation = extract_explanation_from_response(response_text)
            
            if code:
                all_schemas.append(f"-- Table: {resource_name}\n{code}")
                print(f"  ✅ Generated table: {resource_name}")
                
                # Save explanation for notes
                if explanation and explanation.strip():
                    schema_explanations[resource_name] = explanation.strip()
            else:
                print(f"  ⚠️  No code found for {resource_name}")
                
        except Exception as e:
            print(f"  ❌ Failed to generate {resource_name}: {e}")
    
    if not all_schemas:
        print("⚠️  No schemas generated")
        return None
    
    # Combine all schemas into one file
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    final_schema = f"-- Generated: {timestamp}\n"
    final_schema += f"-- Database schema for {len(resources)} table(s)\n\n"
    final_schema += "\n\n".join(all_schemas)
    
    output_file.write_text(final_schema, encoding='utf-8')
    print(f"\n✅ Saved: {output_file}")
    
    # Save notes with AI's reasoning
    notes_file = output_file.parent / "schema_notes.txt"
    notes_content = f"Generated: {timestamp}\n\n"
    notes_content += f"Tables: {', '.join([r['name'] for r in resources])}\n\n"
    notes_content += "=== Schema Design Decisions ===\n\n"
    
    # Add each table's reasoning
    for resource_data in resources:
        resource_name = resource_data['name']
        notes_content += f"## {resource_name.capitalize()}\n\n"
        
        if resource_name in schema_explanations:
            notes_content += f"{schema_explanations[resource_name]}\n\n"
        else:
            notes_content += f"Generated standard CRUD table structure.\n\n"
    
    notes_content += "=== Description ===\n\n"
    notes_content += f"Database schema with {len(resources)} table(s). Includes primary keys, indexes, and timestamp tracking."
    
    notes_file.write_text(notes_content, encoding='utf-8')
    print(f"✅ Saved notes: {notes_file}")
    
    print(f"✅ Schema generation complete")
    print('='*60)
    
    return final_schema  # Return so routes can use it