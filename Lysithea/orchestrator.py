# lysithea/orchestrator.py
"""
Orchestrator for Lysithea

Rule of Law flow:
  1. coordinator.py    → writes .lysithea/functions.json
  2. stack_planner.py  → writes .lysithea/stack.json
  3. schema_generator  → writes .lysithea/schema.sql
  4. All generators    → read state from file_manager, receive NO data via args

Orchestrator enforces ordering and hard-fails on missing law files.
"""

from coordinator import plan_functions_from_prompt
from planners.stack_planner import plan_stack_from_prompt

from file_manager import (
    assert_planning_complete,
    assert_stack_supported,
    assert_schema_ready,
    load_resources,
    load_stack,
    extract_table_from_schema,
)

from generators.schema_generator import generate_schema
from generators.seed_generator import generate_seeds
from generators.query_generator import generate_queries
from generators.database_generator import generate_database
from generators.middleware_generator import generate_middleware
from generators.resource_generator import execute_sequential_generation


def orchestrate(prompt_file='prompt.md'):
    print("\n[Orchestrator] Starting Lysithea pipeline...")

    # ── Step 1: Run planners (write law files) ──────────────────────
    print("\n[Orchestrator] Step 1/5 — Running planners...")
    plan_functions_from_prompt(prompt_file)
    plan_stack_from_prompt(prompt_file)

    # ── Step 2: Pre-flight check — hard fail if law files missing ───
    print("\n[Orchestrator] Step 2/5 — Verifying law files...")
    assert_planning_complete()      # raises if functions/stack missing
    assert_stack_supported()        # raises if stack has no pattern coverage
    print("[Orchestrator] ✅ Planning complete — law files and stack verified")

    # ── Step 3: Read state exclusively from file_manager ───────────
    resources  = load_resources()    # reads .lysithea/functions.json
    stack      = load_stack()        # reads .lysithea/stack.json

    # ── Step 4: Schema (writes .lysithea/schema.sql) ────────────────
    print("\n[Orchestrator] Step 3/5 — Generating schema...")
    generate_schema()               # reads resources via load_resources()
                                    # writes schema via write_schema()

    assert_schema_ready()           # hard fail if schema write failed
    print("[Orchestrator] ✅ Schema ready")

    # ── Step 5: Generate all artifacts ─────────────────────────────
    print("\n[Orchestrator] Step 4/5 — Generating database + middleware...")

    # Database connection (stack-agnostic — reads stack from file_manager)
    generate_database('connection')

    # Middleware (reads from file_manager internally)
    api_requirements = stack.get('api_requirements', {})
    if api_requirements.get('security'):
        generate_middleware('auth')

    print("\n[Orchestrator] Step 5/5 — Generating seeds, queries, and routes...")

    for resource_data in resources:
        resource_name = resource_data['name']
        print(f"\n➡️  Resource: {resource_name}")

        # Seeds and queries read schema from file_manager internally
        generate_seeds(resource_name)
        generate_queries(resource_name)

        # Routes read queries + schema from file_manager internally
        execute_sequential_generation(resource_name)

    print("\n[Orchestrator] ✅ Lysithea pipeline complete.")


if __name__ == "__main__":
    orchestrate('prompt.md')