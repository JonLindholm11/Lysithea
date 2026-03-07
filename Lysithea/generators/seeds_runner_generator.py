# lysithea/generators/seeds_runner_generator.py

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

"""
run_seeds.js generation

Rule of Law: reads resources from file_manager.load_resources()
             call generate_seeds_runner() — no args.
"""

import re
from pathlib import Path

from pattern_manager import load_pattern, extract_metadata_from_content
from file_manager import assert_planning_complete, load_resources, get_output_path


def generate_seeds_runner():
    """
    Generate db/seeds/run_seeds.js that imports and calls all seed files.

    Reads resources from .lysithea/functions.json via file_manager.
    Hard fails if planning has not run yet.
    """

    assert_planning_complete()      # Rule of Law guard
    resources = load_resources()    # Rule of Law read

    print(f"\n{'='*60}")
    print(f"  GENERATING run_seeds.js")
    print('='*60)

    pattern_path = 'javascript/express/database/seeds/run-seeds-pattern.js'
    pattern      = load_pattern(pattern_path)
    if not pattern:
        print(f"⚠️  Pattern not found: {pattern_path}")
        return

    # Extract metadata before stripping doc comments
    metadata    = extract_metadata_from_content(pattern)
    output_dir  = metadata['output_dir']
    file_naming = metadata['file_naming']

    # Strip doc comments
    pattern = re.sub(r'/\*\*[\s\S]*?\*/', '', pattern).strip()

    # Build imports and calls for each resource
    imports = ""
    calls   = ""
    for resource_data in resources:
        name     = resource_data['name'].lower()
        fn_name  = f"seed{name.capitalize()}"
        imports += f"const {{ {fn_name} }} = require('./{name}.seed');\n"
        calls   += f"    await {fn_name}();\n"

    content = pattern.replace('/* IMPORTS */', imports.strip()).replace('/* CALLS */', calls)

    output_file = get_output_path(*output_dir.split('/')) / file_naming
    output_file.write_text(content + '\n', encoding='utf-8')

    print(f"✅ Saved: {output_file}")
    print('='*60)