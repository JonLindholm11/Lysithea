# lysithea/planners/stack_planner.py
"""
Stack & Requirements Planner

Reads prompt.md, extracts stack/API/frontend/database config,
and writes the result to .lysithea/stack.json via file_manager.

This is LAW FILE #2 — all generators depend on its output.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from read_prompt import read_prompt_md
from file_manager import write_stack


def plan_stack_from_prompt(prompt_file='prompt.md'):
    """
    Read prompt.md, build stack config dict,
    and persist it as law via file_manager.write_stack().

    Returns:
        stack_config dict or None on failure.
    """
    prompt_data = read_prompt_md(prompt_file)
    if not prompt_data:
        print("[stack_planner] ❌ Could not read prompt.md")
        return None

    stack_config = {
        "project_name":          prompt_data.get("project_name", "my-app"),
        "style":                 prompt_data.get("style", "corporate"),
        "stack":                 prompt_data.get("stack", {}),
        "api_requirements":      prompt_data.get("api_requirements", {}),
        "frontend_requirements": prompt_data.get("frontend_requirements", {}),
        "database_schema":       prompt_data.get("database_schema", {}),
        "extra_notes":           prompt_data.get("extra_notes", ""),
    }

    # ── Write law file ──────────────────────────────────────────────
    write_stack(stack_config)
    # ───────────────────────────────────────────────────────────────

    print("[stack_planner] Stack config extracted:")
    print(f"  Frontend:  {stack_config['stack'].get('frontend')}")
    print(f"  Backend:   {stack_config['stack'].get('backend')}")
    print(f"  Database:  {stack_config['stack'].get('database')}")

    return stack_config


if __name__ == "__main__":
    plan_stack_from_prompt('prompt.md')