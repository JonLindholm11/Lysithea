# lysithea/generators/auth_generator.py

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

"""
Auth route generation (register + login)

Rule of Law: reads stack from file_manager.load_stack()
             reads resources from file_manager.load_resources()
             only generates if a 'users' table is defined
             call generate_auth() — no args.
"""

import re
from pathlib import Path
from datetime import datetime

from pattern_manager import load_pattern, get_pattern_metadata, extract_metadata_from_content, get_stack_info
from file_manager import get_output_path,  assert_planning_complete, load_resources


def generate_auth():
    """
    Generate auth.js (register + login routes) if a users table exists.

    Reads resources from .lysithea/functions.json to check for users table.
    Hard fails if planning has not run yet.
    """

    assert_planning_complete()      # Rule of Law guard
    resources = load_resources()    # Rule of Law read
    stack     = get_stack_info()

    # Only generate if users table is defined in prompt.md
    resource_names = [r['name'].lower() for r in resources]
    if 'users' not in resource_names:
        print("[auth_generator] ℹ️  No users table found — skipping auth route generation")
        return

    print(f"\n{'='*60}")
    print(f"  GENERATING AUTH ROUTES")
    print(f"  Stack: {stack['language']}/{stack['framework']}")
    print('='*60)

    pattern_path = f"{stack['language']}/{stack['framework']}/routes/auth-routes.js"
    pattern      = load_pattern(pattern_path)
    if not pattern:
        print(f"⚠️  Auth pattern not found: {pattern_path}")
        return

    print(f"📋 Pattern: {pattern_path}")

    # Extract metadata BEFORE stripping doc comments
    metadata    = extract_metadata_from_content(pattern)
    output_dir  = metadata['output_dir']
    file_naming = metadata['file_naming']

    # Strip doc comments
    pattern = re.sub(r'/\*\*[\s\S]*?\*/', '', pattern).strip()
    output_file = get_output_path(*output_dir.split('/')) / file_naming

    # Load user query functions so we can build the correct import line
    query_file = get_output_path('db', 'queries') / 'users.queries.js'
    query_functions = []
    if query_file.exists():
        try:
            content         = query_file.read_text(encoding='utf-8', errors='ignore')
            query_functions = re.findall(r'export async function (\w+)\(', content)
        except Exception as e:
            print(f"⚠️  Could not read user query functions: {e}")

    timestamp   = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    import_line = ""
    if query_functions:
        import_line = (
            f"const {{ {', '.join(query_functions)} }} = "
            f"require('../../db/queries/users.queries');\n"
        )

    content = (
        f"// Generated: {timestamp}\n\n"
        f"{import_line}\n"
        f"{pattern}\n"
    )

    output_file.write_text(content, encoding='utf-8')
    print(f"✅ Saved: {output_file}")
    print('='*60)