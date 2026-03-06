# lysithea/generators/database_generator.py

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

"""
Database file generation (connection, schema, migrations)

Rule of Law: reads stack from file_manager.load_stack()
             resolves pattern path via pattern_manager.map_database_pattern()
             call generate_database(db_type) — no stack arg.
"""

import ollama
from pathlib import Path
from datetime import datetime

from pattern_manager import load_pattern, get_pattern_metadata, map_database_pattern, get_stack_info
from parsers import extract_code_from_response
from file_manager import assert_planning_complete


def generate_database(db_type: str):
    """
    Generate a database file (connection, schema, migration) for the current stack.

    Args:
        db_type: 'connection', 'schema', or 'migration'

    Reads stack from .lysithea/stack.json to resolve the correct pattern.
    Hard fails if stack_planner has not run yet.
    """

    assert_planning_complete()           # Rule of Law guard
    stack        = get_stack_info()      # reads from file_manager internally
    pattern_path = map_database_pattern(db_type, stack)

    print(f"\n{'='*60}")
    print(f"  GENERATING DATABASE: {db_type}")
    print(f"  Stack: {stack['language']}/{stack['framework']}")
    print('='*60)

    if not pattern_path:
        print(f"⚠️  No database pattern mapped for '{db_type}' "
              f"on {stack['language']}/{stack['framework']}")
        return

    pattern = load_pattern(pattern_path)
    if not pattern:
        print(f"⚠️  Pattern file not found: {pattern_path}")
        print(f"    To add support, create: Patterns/{stack['language_dir']}/{stack['framework_dir']}/database/")
        return

    print(f"📋 Pattern: {pattern_path}")

    metadata    = get_pattern_metadata(pattern_path)
    output_dir  = metadata['output_dir'] if metadata else 'db'
    file_naming = metadata['file_naming'] if metadata else f'{db_type}{_ext(stack, db_type)}'
    output_file = Path('output') / output_dir / file_naming
    output_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"🔨 Generating {db_type}...")

    prompt = f"""You are generating a complete database file from a pattern.

=== PATTERN ===
{pattern}

Generate the complete file exactly as shown in the pattern.
Remove only the documentation comments (/** ... */).
Keep all the actual code, imports, and exports.

Output just the code in a code block.
"""

    try:
        response = ollama.generate(model='llama3.1:8b', prompt=prompt, keep_alive=0)
        code     = extract_code_from_response(response['response'])

        if not code:
            print(f"⚠️  No code block found in response")
            return

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        output_file.write_text(f"// Generated: {timestamp}\n\n{code}", encoding='utf-8')
        print(f"✅ Saved: {output_file}")

        notes_file = output_file.parent / f"{db_type}_notes.txt"
        notes_file.write_text(
            f"Generated: {timestamp}\n\nDatabase: {db_type}\n"
            f"Stack: {stack['language']}/{stack['framework']}\n\n"
            f"=== Description ===\n\n"
            f"Database {db_type} file for {stack['framework']}.",
            encoding='utf-8'
        )
        print(f"✅ Saved notes: {notes_file}")
        print(f"✅ Database generation complete")

    except Exception as e:
        print(f"❌ Generation failed: {e}")

    print('='*60)


def _ext(stack: dict, db_type: str) -> str:
    """Return appropriate file extension — SQL files stay .sql."""
    if db_type in ('schema', 'migration'):
        return '.sql'
    from pattern_manager import _ext_for_language
    return _ext_for_language(stack['language'])