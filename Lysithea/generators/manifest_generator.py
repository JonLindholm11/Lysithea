# lysithea/generators/manifest_generator.py

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

"""
Manifest Generator (Pattern-based)

Rule of Law: reads stack config from file_manager.load_stack()
             call generate_manifest() — no stack_config arg.
"""

from pathlib import Path
from datetime import datetime
from pattern_manager import load_pattern
from file_manager import load_stack, assert_planning_complete
from file_manager import save_generated_files
import json
import re


def generate_manifest():
    """
    Generate manifest/dependency file (package.json, requirements.txt, etc.)

    Reads stack config from .lysithea/stack.json via file_manager.
    Hard fails if stack_planner has not run yet.
    """

    assert_planning_complete()   # Rule of Law guard
    stack_config = load_stack()  # Rule of Law read

    backend          = stack_config.get("stack", {}).get("backend", {})
    language         = backend.get("language", "").lower()
    framework        = backend.get("framework", "").lower()

    frontend         = stack_config.get("stack", {}).get("frontend", {})
    frontend_framework = frontend.get("framework", "").lower()

    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if language == "javascript":
        if frontend_framework == "react":
            pattern_path = "patterns/javascript/react/package-json-pattern.js"
        else:
            pattern_path = f"patterns/javascript/{frontend_framework}/package-json-pattern.js"
        filename = "package.json"
    elif language == "python":
        pattern_path = f"patterns/python/{framework}/requirements-pattern.txt"
        filename = "requirements.txt"
    elif language == "ruby":
        pattern_path = f"patterns/ruby/{framework}/Gemfile-pattern.rb"
        filename = "Gemfile"
    else:
        print(f"⚠️  Unsupported language '{language}', cannot generate manifest")
        return

    pattern = load_pattern(pattern_path)
    if not pattern:
        print(f"❌ Manifest pattern not found: {pattern_path}")
        return

    pattern = re.sub(r'/\*\*[\s\S]*?\*/', '', pattern).strip()

    if language == "javascript":
        dependencies    = frontend.get("dependencies", {})
        devDependencies = frontend.get("devDependencies", {})
        pattern = pattern.replace("/* DEPENDENCIES */",     json.dumps(dependencies, indent=2))
        pattern = pattern.replace("/* DEV_DEPENDENCIES */", json.dumps(devDependencies, indent=2))
    elif language == "python":
        deps    = backend.get("dependencies", [])
        pattern = pattern.replace("/* DEPENDENCIES */", "\n".join(deps))

    output_file = str(output_dir / filename)
    save_generated_files(output_file, pattern, timestamp)

    print(f"[manifest_generator] ✅ Generated {output_file} using {pattern_path}")