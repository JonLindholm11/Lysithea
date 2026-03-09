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

import os

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

from lysithea_meta import write_project_meta

from generators.schema_generator import generate_schema
from generators.seed_generator import generate_seeds
from generators.query_generator import generate_queries
from generators.database_generator import generate_database
from generators.middleware_generator import generate_middleware
from generators.resource_generator import execute_sequential_generation
from generators.frontend_generator import generate_frontend
from generators.app_generator import generate_app_js
from generators.manifest_generator import generate_manifest
from generators.auth_generator import generate_auth
from generators.env_generator import generate_env
from generators.seeds_runner_generator import generate_seeds_runner
from generators.project_files_generator import generate_project_files


def orchestrate(prompt_file='prompt.md'):
    print("\n[Orchestrator] Starting Lysithea pipeline...")

    # Resolve project path — GUI passes LYSITHEA_PROJECT_PATH env var,
    # CLI falls back to cwd.
    project_path = os.environ.get('LYSITHEA_PROJECT_PATH', os.getcwd())

    # ── Step 1: Run planners (write law files) ──────────────────────
    print("\n[Orchestrator] Step 1/6 — Running planners...")
    plan_functions_from_prompt(prompt_file)
    plan_stack_from_prompt(prompt_file)

    # ── Step 2: Pre-flight check — hard fail if law files missing ───
    print("\n[Orchestrator] Step 2/6 — Verifying law files...")
    assert_planning_complete()
    assert_stack_supported()
    print("[Orchestrator] ✅ Planning complete — law files and stack verified")

    # ── Step 2b: Write .lysithea project metadata ───────────────────
    # Runs immediately after planners so CLI users can import into GUI.
    print("\n[Orchestrator] Writing project metadata...")
    stack = load_stack()
    write_project_meta(project_path, stack)
    print("[Orchestrator] ✅ .lysithea written — project importable into GUI")

    # ── Step 3: Read state exclusively from file_manager ───────────
    resources = load_resources()
    stack     = load_stack()

    # ── Step 4: Schema ──────────────────────────────────────────────
    print("\n[Orchestrator] Step 3/6 — Generating schema...")
    generate_schema()
    assert_schema_ready()
    print("[Orchestrator] ✅ Schema ready")

    # ── Step 5: Database + middleware ───────────────────────────────
    print("\n[Orchestrator] Step 4/6 — Generating database + middleware...")
    generate_database('connection')

    api_requirements = stack.get('api_requirements', {})
    if api_requirements.get('security'):
        generate_middleware('auth')

    generate_auth()

    # ── Step 5: Seeds, queries, routes ─────────────────────────────
    print("\n[Orchestrator] Step 5/6 — Generating seeds, queries, and routes...")
    for resource_data in resources:
        resource_name = resource_data['name']
        print(f"\n➡️  Resource: {resource_name}")
        generate_seeds(resource_name)
        generate_queries(resource_name)
        execute_sequential_generation(resource_name)

    # ── Step 6: App entry + manifest + env + project files ─────────
    print("\n[Orchestrator] Step 6/6 — Generating app.js, package.json, .env, README...")
    generate_app_js()
    generate_manifest()
    generate_env()
    generate_seeds_runner()
    generate_project_files()

    # ── Step 6b: Frontend ───────────────────────────────────────────
    print("\n[Orchestrator] Generating frontend...")
    generate_frontend()

    # ── Final: Update .lysithea updatedAt timestamp ─────────────────
    write_project_meta(project_path, stack)

    print("\n[Orchestrator] ✅ Lysithea pipeline complete.")


if __name__ == "__main__":
    orchestrate('prompt.md')