# lysithea/generators/project_files_generator.py

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

"""
Project file generation (.gitignore, README.md)

Rule of Law: reads stack from file_manager.load_stack()
             reads resources from file_manager.load_resources()
             call generate_project_files() — no args.
"""

import re
from pathlib import Path

from pattern_manager import load_pattern, extract_metadata_from_content
from file_manager import assert_planning_complete, load_stack, load_resources, get_output_path


def generate_project_files():
    """
    Generate .gitignore and README.md for the project root.

    Reads stack and resources from file_manager.
    Hard fails if planning has not run yet.
    """

    assert_planning_complete()      # Rule of Law guard
    stack_config = load_stack()     # Rule of Law read
    resources    = load_resources() # Rule of Law read

    backend      = stack_config.get('stack', {}).get('backend', {})
    language     = backend.get('language', '').lower()
    framework    = backend.get('framework', '').lower()
    project_name = stack_config.get('project_name', 'my-app')
    db_name      = project_name.lower().replace('-', '_').replace(' ', '_')

    _generate_gitignore(language, framework)
    _generate_readme(language, framework, project_name, db_name, resources)


def _generate_gitignore(language, framework):
    print(f"\n{'='*60}")
    print(f"  GENERATING .gitignore")
    print('='*60)

    pattern_path = f"{language}/{framework}/gitignore-pattern.js"
    pattern      = load_pattern(pattern_path)
    if not pattern:
        print(f"⚠️  Pattern not found: {pattern_path}")
        return

    metadata    = extract_metadata_from_content(pattern)
    output_dir  = metadata['output_dir']
    file_naming = metadata['file_naming']

    # Strip doc comments
    content = re.sub(r'/\*\*[\s\S]*?\*/', '', pattern).strip()

    # .gitignore and README go at project root (book-store/), not inside backend/
    from file_manager import get_project_dir
    output_file = get_project_dir() / file_naming
    output_file.write_text(content + '\n', encoding='utf-8')
    print(f"✅ Saved: {output_file}")
    print('='*60)


def _generate_readme(language, framework, project_name, db_name, resources):
    print(f"\n{'='*60}")
    print(f"  GENERATING README.md")
    print('='*60)

    pattern_path = f"{language}/{framework}/readme-pattern.js"
    pattern      = load_pattern(pattern_path)
    if not pattern:
        print(f"⚠️  Pattern not found: {pattern_path}")
        return

    metadata    = extract_metadata_from_content(pattern)
    file_naming = metadata['file_naming']

    # Strip doc comments
    content = re.sub(r'/\*\*[\s\S]*?\*/', '', pattern).strip()

    # Build endpoints table for each resource
    endpoints = ""
    for resource_data in resources:
        name = resource_data['name'].lower()
        endpoints += f"\n### {name.capitalize()}\n"
        endpoints += "| Method | Endpoint | Description |\n"
        endpoints += "|--------|----------|-------------|\n"
        endpoints += f"| GET | /api/{name} | Get all {name} |\n"
        endpoints += f"| GET | /api/{name}/:id | Get {name} by ID |\n"
        endpoints += f"| POST | /api/{name} | Create {name} |\n"
        endpoints += f"| PUT | /api/{name}/:id | Update {name} |\n"
        endpoints += f"| DELETE | /api/{name}/:id | Delete {name} |\n"

    content = (content
        .replace('/* PROJECT_NAME */', project_name)
        .replace('/* DB_NAME */', db_name)
        .replace('/* ENDPOINTS */', endpoints.strip())
    )

    # README goes at project root (book-store/)
    from file_manager import get_project_dir
    output_file = get_project_dir() / file_naming
    output_file.write_text(content + '\n', encoding='utf-8')
    print(f"✅ Saved: {output_file}")
    print('='*60)