# lysithea/planners/stack_planner.py
"""
Stack & Requirements Planner
- Reads prompt.md
- Extracts stack, API, frontend, database, and extra notes
- Produces a structured dict for all generators
"""

import json
from pathlib import Path
from read_prompt import read_prompt_md  # reusing your existing prompt parser

OUTPUT_FILE = Path('.lysithea/stack.json')
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

def plan_stack_from_prompt(prompt_file='prompt.md'):
    prompt_data = read_prompt_md(prompt_file)
    if not prompt_data:
        print("[Error] Could not read prompt.md")
        return None

    # Build stack/config dict
    stack_config = {
        "stack": prompt_data.get("stack", {}),
        "api_requirements": prompt_data.get("api_requirements", {}),
        "frontend_requirements": prompt_data.get("frontend_requirements", {}),
        "database_schema": prompt_data.get("database_schema", {}),
        "extra_notes": prompt_data.get("extra_notes", "")
    }

    # Save to stack.json
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(stack_config, f, indent=2)

    print(f"[Stack Planner] Stack/config extracted.")
    print(f"  Frontend: {stack_config['stack'].get('frontend')}")
    print(f"  Backend: {stack_config['stack'].get('backend')}")
    print(f"  Database: {stack_config['stack'].get('database')}")
    return stack_config

if __name__ == "__main__":
    plan_stack_from_prompt('prompt.md')