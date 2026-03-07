# lysithea/generators/middleware_generator.py

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

"""
Middleware file generation

Rule of Law: reads stack from file_manager.load_stack()
             resolves pattern path via pattern_manager.map_middleware_pattern()
             call generate_middleware(middleware_name) — no stack arg.
"""

import ollama
from pathlib import Path
from datetime import datetime

from pattern_manager import load_pattern, get_pattern_metadata, extract_metadata_from_content, map_middleware_pattern, get_stack_info
from parsers import extract_code_from_response, extract_explanation_from_response
from file_manager import get_output_path,  assert_planning_complete


def generate_middleware(middleware_name: str):
    """
    Generate a middleware file for the current stack.

    Args:
        middleware_name: e.g. 'auth', 'validation', 'error'

    Reads stack from .lysithea/stack.json to resolve the correct pattern.
    Hard fails if stack_planner has not run yet.
    """

    assert_planning_complete()           # Rule of Law guard
    stack        = get_stack_info()      # reads from file_manager internally
    pattern_path = map_middleware_pattern(middleware_name, stack)

    print(f"\n{'='*60}")
    print(f"  GENERATING MIDDLEWARE: {middleware_name}")
    print(f"  Stack: {stack['language']}/{stack['framework']}")
    print('='*60)

    if not pattern_path:
        print(f"⚠️  No middleware pattern mapped for '{middleware_name}' "
              f"on {stack['language']}/{stack['framework']}")
        return

    pattern = load_pattern(pattern_path)
    if not pattern:
        print(f"⚠️  Pattern file not found: {pattern_path}")
        print(f"    To add support, create: Patterns/{stack['language_dir']}/{stack['framework_dir']}/middleware/")
        return

    print(f"📋 Pattern: {pattern_path}")

    metadata = extract_metadata_from_content(pattern)
    output_dir  = metadata['output_dir'] if metadata else 'api/middleware'
    file_naming = metadata['file_naming'] if metadata else f'{middleware_name}.{_ext(stack)}'
    output_file = get_output_path(*output_dir.split('/')) / file_naming

    print(f"🔨 Generating {middleware_name} middleware...")

    prompt = f"""You are generating a complete middleware file from a pattern.

=== PATTERN ===
{pattern}

Generate the complete middleware file exactly as shown in the pattern.
Remove only the documentation comments (/** ... */).
Keep all the actual code, imports, and exports.

Output just the code in a code block.
"""

    try:
        response      = ollama.generate(model='llama3.1:8b', prompt=prompt, keep_alive=0)
        code          = extract_code_from_response(response['response'])

        if not code:
            print(f"⚠️  No code block found in response")
            return

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        output_file.write_text(f"// Generated: {timestamp}\n\n{code}", encoding='utf-8')
        print(f"✅ Saved: {output_file}")

        notes_file = output_file.parent / f"{middleware_name}_notes.txt"
        notes_file.write_text(
            f"Generated: {timestamp}\n\nMiddleware: {middleware_name}\n"
            f"Stack: {stack['language']}/{stack['framework']}\n\n"
            f"=== Description ===\n\n"
            f"Authentication middleware for JWT token verification.",
            encoding='utf-8'
        )
        print(f"✅ Saved notes: {notes_file}")
        print(f"✅ Middleware generation complete")

    except Exception as e:
        print(f"❌ Generation failed: {e}")

    print('='*60)


def _ext(stack: dict) -> str:
    from pattern_manager import _ext_for_language
    return _ext_for_language(stack['language']).lstrip('.')