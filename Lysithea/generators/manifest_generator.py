# lysithea/generators/manifest_generator.py
"""
Manifest Generator (Pattern-based)
- Fully stack-agnostic
- Generates package.json, requirements.txt, Gemfile, etc. from required patterns
"""

from pathlib import Path
from datetime import datetime
from pattern_manager import load_pattern
from file_manager import save_generated_files
import json
import re

def generate_manifest(stack_config):
    """
    Generate manifest/dependency files based on patterns.
    Requires a manifest pattern for each backend/frontend combo.
    """
    
    backend = stack_config.get("backend", {})
    language = backend.get("language", "").lower()
    framework = backend.get("framework", "").lower()
    
    frontend = stack_config.get("frontend", {})
    frontend_framework = frontend.get("framework", "").lower()
    
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Determine pattern path based on stack
    if language == "javascript":
        if frontend_framework == "react":
            pattern_path = "patterns/javascript/react/package-json-pattern.js"
        else:
            # Bug 2 fix: use frontend_framework, not backend framework
            pattern_path = f"patterns/javascript/{frontend_framework}/package-json-pattern.js"
        filename = "package.json"
    elif language == "python":
        pattern_path = f"patterns/python/{framework}/requirements-pattern.txt"
        filename = "requirements.txt"
    elif language == "ruby":
        pattern_path = f"patterns/ruby/{framework}/Gemfile-pattern.rb"
        filename = "Gemfile"
    else:
        print(f"⚠️ Unsupported language '{language}', cannot generate manifest")
        return
    
    # Load pattern (must exist)
    pattern = load_pattern(pattern_path)
    if not pattern:
        print(f"❌ Manifest pattern not found: {pattern_path}")
        return

    # Bug 3 fix: strip JSDoc block comment header before injecting / saving
    pattern = re.sub(r'/\*\*[\s\S]*?\*/', '', pattern).strip()
    
    # Inject dependencies if needed (for JS / Python, optional)
    if language == "javascript":
        # Bug 1 fix: pull deps from frontend, not backend
        dependencies = frontend.get("dependencies", {})
        devDependencies = frontend.get("devDependencies", {})
        pattern = pattern.replace("/* DEPENDENCIES */", json.dumps(dependencies, indent=2))
        pattern = pattern.replace("/* DEV_DEPENDENCIES */", json.dumps(devDependencies, indent=2))
    elif language == "python":
        deps = backend.get("dependencies", [])
        pattern = pattern.replace("/* DEPENDENCIES */", "\n".join(deps))
    
    # Bug 4 fix: convert Path to string for save_generated_files
    output_file = str(output_dir / filename)
    save_generated_files(output_file, pattern, timestamp)
    
    print(f"[Manifest Generator] Generated {output_file} using pattern {pattern_path}")