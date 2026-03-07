# lysithea/generators/app_generator.py

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

"""
App.js generation

Rule of Law: reads stack config from file_manager.load_stack()
             reads resources from file_manager.load_resources()
             call generate_app_js() — no args.
"""

from pathlib import Path
from datetime import datetime
from pattern_manager import load_pattern
from file_manager import get_output_path,  load_stack, load_resources, assert_planning_complete
import re


def generate_app_js():
    """
    Generate main app.js file based on stack config and resources.

    Reads stack from .lysithea/stack.json via file_manager.
    Reads resources from .lysithea/functions.json via file_manager.
    Hard fails if either planner has not run yet.
    """

    assert_planning_complete()      # Rule of Law guard
    stack_config = load_stack()     # Rule of Law read
    resources    = load_resources() # Rule of Law read

    stack     = stack_config.get("stack", {})
    language  = stack.get("backend", {}).get("language", "").lower()
    framework = stack.get("backend", {}).get("framework", "").lower()

    pattern_path = f"{language}/{framework}/app-js-pattern.js"
    pattern      = load_pattern(pattern_path)
    if not pattern:
        print(f"⚠️  Pattern not found: {pattern_path}")
        return

    # Strip doc comments
    pattern = re.sub(r'/\*\*[\s\S]*?\*/', '', pattern).strip()

    # Build route imports and mounts
    imports = ""
    routes  = ""

    # Mount auth routes if users table exists
    resource_names = [r['name'].lower() for r in resources]
    if 'users' in resource_names:
        imports += "const authRouter = require('./api/routes/auth');\n"
        routes  += "app.use('/api/auth', authRouter);\n"

    for resource_data in resources:
        res      = resource_data['name'].lower()
        imports += f"const {res}Router = require('./api/routes/{res}');\n"
        routes  += f"app.use('/api/{res}', {res}Router);\n"

    content = pattern.replace('/* IMPORTS */', imports.strip()).replace('/* ROUTES */', routes.strip())

    output_file = get_output_path() / 'app.js'

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    output_file.write_text(f"// Generated: {timestamp}\n\n{content}\n", encoding='utf-8')

    print(f"[app_generator] ✅ Generated {output_file}")