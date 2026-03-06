# lysithea/coordinator.py
"""
Coordinator / Function Planner

Reads features from prompt.md, converts them into resources + operations,
then writes the result to .lysithea/functions.json via file_manager.

This is LAW FILE #1 — all generators depend on its output.
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
                r['name']: r.get('operations', [])
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

    Reads prompt.md, plans resources + operations,
    and persists to .lysithea/functions.json.

    Returns:
        dict of {resource_name: [operations]} or None on failure.
    """
    prompt_data = read_prompt_md(prompt_file)
    if not prompt_data or 'features' not in prompt_data:
        print("[coordinator] ❌ No features found in prompt.md")
        return None

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
        functions_dict[resource_name] = operations

    # ── Write law file ──────────────────────────────────────────────
    write_functions(functions_dict)
    # ───────────────────────────────────────────────────────────────

    print(f"[coordinator] Planned {len(functions_dict)} resource(s):")
    for res, ops in functions_dict.items():
        print(f"  - {res}: {', '.join(ops)}")

    return functions_dict


if __name__ == "__main__":
    plan_functions_from_prompt('prompt.md')