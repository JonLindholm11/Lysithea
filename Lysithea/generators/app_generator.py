# lysithea/generators/app_generator.py
"""
Sequential App.js generation
- Fully stack-agnostic: picks patterns based on stack_config
"""

from pathlib import Path
from datetime import datetime
from pattern_manager import load_pattern
from file_manager import save_generated_files
import re

def generate_app_js(stack_config, resources):
    """Generate main app.js file incrementally based on stack_config"""

    output_dir = Path('output')
    filename = 'app.js'
    output_file = output_dir / filename
    output_file.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Bug 3 fix: use .get() for safe key access
    language = stack_config.get('backend', {}).get('language', '').lower()
    framework = stack_config.get('backend', {}).get('framework', '').lower()
    pattern_path = f"patterns/{language}/{framework}/app-js-pattern.js"

    pattern = load_pattern(pattern_path)
    if not pattern:
        print(f"⚠️ Pattern not found: {pattern_path}")
        return

    # Bug 2 fix: strip JSDoc block comment header
    pattern = re.sub(r'/\*\*[\s\S]*?\*/', '', pattern).strip()

    # Bug 4 fix: guard against None or invalid resources
    resources = resources or []

    # Dynamically generate imports and route usage based on resources
    imports = ""
    routes = ""
    for res in resources:
        # Bug 5 fix: normalize resource name to lowercase
        res = res.lower()
        imports += f"const {res}Router = require('./api/routes/{res}');\n"
        routes += f"app.use('/{res}', {res}Router);\n"

    # Merge pattern with dynamic imports/routes
    content = pattern.replace('/* IMPORTS */', imports).replace('/* ROUTES */', routes)

    # Bug 1 fix: convert Path to string for save_generated_files
    save_generated_files(str(output_file), content, timestamp)
    print(f"[App.js Generator] Generated {output_file}")