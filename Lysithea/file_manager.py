# lysithea/file_manager.py
"""
File system operations - saving generated code and notes
"""

from pathlib import Path
from datetime import datetime

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