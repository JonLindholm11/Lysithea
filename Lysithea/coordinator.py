# lysithea/coordinator.py
"""
Coordinator / Function Planner

Reads features from prompt.md, converts them into resources + operations,
then writes the result to .lysithea/functions.json via file_manager.

This is LAW FILE #1 — all generators depend on its output.

functions.json shape:
{
  "users": {
    "operations": ["get all", "get by id", "post", "put", "delete"],
    "frontend":   ["dashboard"]
  },
  "posts": {
    "operations": ["get all", "get by id", "post", "put", "delete"],
    "frontend":   ["dashboard", "form"]
  }
}

prompt.md Frontend Requirements syntax:
  # Frontend Requirements
  - Users: dashboard
  - Posts: dashboard, form
"""

import re
from read_prompt import read_prompt_md
from file_manager import write_functions


def coordinator_agent(user_input=None):
    """
    Entry point used by cli.py (interactive mode).

    Accepts a raw user string or falls back to prompt.md.
    Returns the parsed functions dict for immediate use by the CLI,
    and also persists it as law via file_manager.write_functions().
    """
    import json, ollama

    prompt = f"""You are a coordinator for a code generation system.

Parse this request and return a JSON object with:
- resources: list of objects with 'name' and 'operations' fields
- middleware: list of middleware names needed
- database: list of database components needed (connection, schema, migration)
- schema: list of resource names that need database tables

Request: {user_input}

Return ONLY valid JSON, no explanation.

Example:
{{
  "resources": [{{"name": "products", "operations": ["get all", "get by id", "post", "put", "delete"]}}],
  "middleware": ["auth"],
  "database": ["connection"],
  "schema": ["products"]
}}
"""

    try:
        response = ollama.generate(model='llama3.1:8b', prompt=prompt, keep_alive=0)
        text = response['response']

        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if not json_match:
            print("[coordinator] Could not parse JSON from response")
            return None

        result = json.loads(json_match.group())

        # Persist resources as functions law
        resources = result.get('resources', [])
        if resources:
            functions_dict = {
                r['name']: {
                    'operations': r.get('operations', []),
                    'frontend':   [],
                }
                for r in resources
            }
            write_functions(functions_dict)

        return result

    except Exception as e:
        print(f"[coordinator] Error: {e}")
        return None


def plan_functions_from_prompt(prompt_file='prompt.md'):
    """
    Entry point used by orchestrator.py (file-based mode).

    Reads prompt.md, plans resources + operations + frontend pages,
    and persists to .lysithea/functions.json.

    Frontend Requirements section controls which pages are generated per resource:
      - Users: dashboard          → list page only (no form)
      - Posts: dashboard, form    → list page + form page

    Returns:
        dict of {resource_name: {operations, frontend}} or None on failure.
    """
    prompt_data = read_prompt_md(prompt_file)
    if not prompt_data or 'features' not in prompt_data:
        print("[coordinator] ❌ No features found in prompt.md")
        return None

    # ── Parse frontend requirements ─────────────────────────────────────────
    # frontend_requirements comes back as a flat dict from read_prompt.py:
    # { 'users': 'dashboard', 'posts': 'dashboard, form' }
    raw_frontend = prompt_data.get('frontend_requirements', {})
    frontend_map = {}
    for resource, value in raw_frontend.items():
        resource_key = re.sub(r'\s+', '_', resource.strip().lower())
        resource_key = re.sub(r'[^\w-]', '', resource_key)
        pages = [p.strip().lower() for p in value.split(',') if p.strip()]
        frontend_map[resource_key] = pages

    # ── Build functions dict ────────────────────────────────────────────────
    functions_dict = {}

    for resource, ops in prompt_data['features'].items():
        resource_name = re.sub(r'\s+', '_', resource.strip().lower())
        resource_name = re.sub(r'[^\w-]', '', resource_name)

        ops = ops if isinstance(ops, list) else []

        operations = []
        for op in ops:
            op_clean = op.lower()
            if op_clean == 'crud':
                operations.extend(['get all', 'get by id', 'post', 'put', 'delete'])
            else:
                operations.append(op_clean)

        operations = list(dict.fromkeys(operations))

        # Get frontend pages for this resource — default to empty (no pages)
        frontend_pages = frontend_map.get(resource_name, [])

        functions_dict[resource_name] = {
            'operations': operations,
            'frontend':   frontend_pages,
        }

    # ── Write law file ──────────────────────────────────────────────────────
    write_functions(functions_dict)
    # ───────────────────────────────────────────────────────────────────────

    print(f"[coordinator] Planned {len(functions_dict)} resource(s):")
    for res, data in functions_dict.items():
        pages = ', '.join(data['frontend']) if data['frontend'] else 'no frontend'
        print(f"  - {res}: {', '.join(data['operations'])}  |  frontend: {pages}")

    return functions_dict


if __name__ == "__main__":
    plan_functions_from_prompt('prompt.md')