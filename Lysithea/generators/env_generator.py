# lysithea/generators/env_generator.py

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

"""
.env.example generation

Rule of Law: reads stack from file_manager.load_stack()
             call generate_env() — no args.
"""

import re
from pathlib import Path

from pattern_manager import load_pattern, extract_metadata_from_content
from file_manager import assert_planning_complete, load_stack, get_output_path


def generate_env():
    """
    Generate .env.example for the current stack.

    Reads stack from .lysithea/stack.json via file_manager.
    Hard fails if planning has not run yet.
    """

    assert_planning_complete()   # Rule of Law guard
    stack_config = load_stack()  # Rule of Law read

    backend      = stack_config.get('stack', {}).get('backend', {})
    language     = backend.get('language', '').lower()
    framework    = backend.get('framework', '').lower()
    project_name = stack_config.get('project_name', 'my-app').lower().replace(' ', '_')

    print(f"\n{'='*60}")
    print(f"  GENERATING .env.example")
    print(f"  Stack: {language}/{framework}")
    print('='*60)

    pattern_path = f"{language}/{framework}/env-example-pattern.js"
    pattern      = load_pattern(pattern_path)
    if not pattern:
        print(f"⚠️  Pattern not found: {pattern_path}")
        return

    metadata    = extract_metadata_from_content(pattern)
    output_dir  = metadata['output_dir']
    file_naming = metadata['file_naming']

    # Strip doc comment block
    pattern = re.sub(r'/\*\*[\s\S]*?\*/', '', pattern).strip()

    # Inject project name as DB name
    content = pattern.replace('/* PROJECT_NAME */', project_name)

    output_file = get_output_path(*output_dir.split('/')) / file_naming
    output_file.write_text(content + '\n', encoding='utf-8')

    print(f"✅ Saved: {output_file}")
    print('='*60)