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

from pattern_manager import load_pattern, get_pattern_metadata, get_stack_info
from file_manager import assert_planning_complete, load_resources, get_output_path


def generate_auth():
    """
    Generate auth.js (register + login routes) if a users table exists.

    Reads resources from .lysithea/functions.json to check for users table.
    Hard fails if planning has not run yet.
    """

    assert_planning_complete()
    resources = load_resources()
    stack     = get_stack_info()

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

    # Strip doc comments
    pattern = re.sub(r'/\*\*[\s\S]*?\*/', '', pattern).strip()

    metadata    = get_pattern_metadata(pattern_path)
    output_dir  = metadata['output_dir'] if metadata else 'api/routes'
    file_naming = metadata['file_naming'] if metadata else 'auth.js'
    output_file = get_output_path(*output_dir.split('/')) / file_naming
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Load user query functions from generated file
    query_file = get_output_path('db', 'queries') / 'users.queries.js'
    query_functions = []
    if query_file.exists():
        try:
            content = query_file.read_text(encoding='utf-8', errors='ignore')
            # Match CommonJS async functions (after _to_commonjs post-processing)
            query_functions = re.findall(r'^async function (\w+)\s*\(', content, re.MULTILINE)
        except Exception as e:
            print(f"⚠️  Could not read user query functions: {e}")

    # Always ensure getUserByEmail and createUser are imported for auth to work
    required_for_auth = {'getUserByEmail', 'createUser'}
    import_funcs = list(dict.fromkeys(query_functions))  # deduplicate, preserve order
    # Add required functions if missing (fallback safety)
    for fn in required_for_auth:
        if fn not in import_funcs:
            import_funcs.append(fn)

    timestamp   = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    import_line = (
        f"const {{ {', '.join(import_funcs)} }} = "
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