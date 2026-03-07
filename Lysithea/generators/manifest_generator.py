# lysithea/generators/manifest_generator.py

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

"""
Manifest (package.json / requirements.txt) generation

Rule of Law: reads stack config from file_manager.load_stack()
             call generate_manifest() — no args.
"""

import json
import re
from pathlib import Path
from datetime import datetime

from pattern_manager import load_pattern
from file_manager import load_stack, assert_planning_complete


def generate_manifest():
    """
    Generate package.json (JS) or requirements.txt (Python) for the current stack.

    Reads stack from .lysithea/stack.json via file_manager.
    Hard fails if stack_planner has not run yet.
    """

    assert_planning_complete()   # Rule of Law guard
    stack_config = load_stack()  # Rule of Law read

    backend   = stack_config.get("stack", {}).get("backend", {})
    language  = backend.get("language", "").lower()
    framework = backend.get("framework", "").lower()

    project_name = stack_config.get("project_name", "my-app").lower().replace(" ", "-")

    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if language == "javascript":
        pattern_path = f"{language}/{framework}/package-json-pattern.js"
        output_file  = output_dir / "package.json"
    elif language == "python":
        pattern_path = f"{language}/{framework}/requirements-pattern.txt"
        output_file  = output_dir / "requirements.txt"
    elif language == "ruby":
        pattern_path = f"{language}/{framework}/Gemfile-pattern.rb"
        output_file  = output_dir / "Gemfile"
    else:
        print(f"⚠️  Unsupported language '{language}' for manifest generation")
        return

    pattern = load_pattern(pattern_path)
    if not pattern:
        print(f"⚠️  Manifest pattern not found: {pattern_path}")
        return

    # Strip doc comments
    pattern = re.sub(r'/\*\*[\s\S]*?\*/', '', pattern).strip()

    # Inject project name
    content = pattern.replace('/* PROJECT_NAME */', project_name)

    output_file.write_text(f"{content}\n", encoding='utf-8')
    print(f"[manifest_generator] ✅ Generated {output_file}")