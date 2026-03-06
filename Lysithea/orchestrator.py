# lysithea/orchestrator.py
"""
Orchestrator for Lysithea MVP
- Runs Function Planner
- Runs Stack & Requirements Planner
- Passes outputs to micro-agents (Query, Middleware, API, Frontend)
"""

import json
from pathlib import Path
from coordinator import plan_functions_from_prompt
from planners.stack_planner import plan_stack_from_prompt

from generators.resource_generator import execute_sequential_generation
# from generators.middleware_agent import middleware_agent
# from generators.api_agent import api_agent
# from generators.frontend_agent import frontend_agent

def orchestrate(prompt_file='prompt.md'):
    print("\n[Orchestrator] Starting Lysithea pipeline...")

    # Step 1: Run Function Planner
    functions = plan_functions_from_prompt(prompt_file)
    if not functions:
        print("[Orchestrator] Function planning failed. Aborting.")
        return

    # Step 2: Run Stack & Requirements Planner
    stack_config = plan_stack_from_prompt(prompt_file)
    if not stack_config:
        print("[Orchestrator] Stack planning failed. Aborting.")
        return

    # Step 3: Pass outputs to micro-agents
    print("\n[Orchestrator] Passing tasks to micro-agents...")

    for resource, operations in functions.items():
        print(f"\n➡️ Generating resource: {resource} ({', '.join(operations)})")

        # Bug 3 fix: pull schema from correct nested path stack_config['database_schema']
        db_schema = stack_config.get('database_schema', {}).get(resource)

        # Bug 3 fix: warn when schema is missing instead of silently passing None
        if not db_schema:
            print(f"⚠️ No schema found for resource: {resource}, proceeding without it")

        # Bug 4 fix: pass operations and stack_config so resource_generator can resolve patterns
        execute_sequential_generation(
            resource,
            operations=operations,
            stack_config=stack_config,
            schema=db_schema
        )

        # Placeholders for other agents
        # middleware_agent(resource, operations, stack_config.get('api_requirements', {}))
        # api_agent(resource, operations, stack_config.get('api_requirements', {}))
        # frontend_agent(resource, operations, stack_config.get('frontend_requirements', {}))

    print("\n[Orchestrator] Lysithea pipeline complete.")

if __name__ == "__main__":
    orchestrate('prompt.md')