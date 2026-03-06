# lysithea/coordinator.py
"""
Coordinator / Function Planner
- Reads features from prompt.md
- Converts them into resources + operations
- Writes functions.json for generators
"""

import json
import re
from pathlib import Path
from read_prompt import read_prompt_md

OUTPUT_FILE = Path('.lysithea/functions.json')

def plan_functions_from_prompt(prompt_file='prompt.md'):

    # Bug 1 fix: mkdir inside function, not at module level
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    prompt_data = read_prompt_md(prompt_file)
    if not prompt_data or 'features' not in prompt_data:
        print("[Error] No features found in prompt.md")
        return None

    functions_dict = {}

    for resource, ops in prompt_data['features'].items():
        resource_name = re.sub(r'\s+', '_', resource.strip().lower())
        resource_name = re.sub(r'[^\w-]', '', resource_name)

        # Bug 2 fix: guard against None or non-list ops
        ops = ops if isinstance(ops, list) else []

        operations = []

        for op in ops:
            op_clean = op.lower()
            if op_clean == 'crud':
                operations.extend(['get all', 'get by id', 'post', 'put', 'delete'])
            else:
                operations.append(op_clean)

        # Deduplicate operations
        operations = list(dict.fromkeys(operations))

        functions_dict[resource_name] = operations

    # Bug 4 fix: wrap write in try/except
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(functions_dict, f, indent=2)
    except OSError as e:
        print(f"[Coordinator] Failed to write functions.json: {e}")
        return None

    print(f"[Coordinator] Planned {len(functions_dict)} resource(s) with operations.")
    for res, ops in functions_dict.items():
        print(f"  - {res}: {', '.join(ops)}")

    return functions_dict

if __name__ == "__main__":
    plan_functions_from_prompt('prompt.md')