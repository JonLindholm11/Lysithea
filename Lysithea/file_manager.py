# lysithea/file_manager.py
"""
File Manager - Rule of Law gatekeeper

.lysithea/ is the single source of truth.
All generators MUST read state through this module.
No generator may receive resources/schema/stack as function arguments.

Layout:
  .lysithea/
    functions.json   <- written by coordinator.py
    stack.json       <- written by stack_planner.py
    schema.sql       <- written by schema_generator.py
"""

import re
import json
from pathlib import Path
from datetime import datetime

# ─── Canonical state paths ────────────────────────────────────────────────────

LAW_DIR               = Path('.lysithea')
FUNCTIONS_FILE        = LAW_DIR / 'functions.json'
STACK_FILE            = LAW_DIR / 'stack.json'
SCHEMA_FILE           = LAW_DIR / 'schema.sql'
SUPPORTED_STACKS_FILE = Path('supported_stacks.json')

# ─── Bootstrap ────────────────────────────────────────────────────────────────

def ensure_law_dir():
    """Create .lysithea/ if it doesn't exist yet."""
    LAW_DIR.mkdir(parents=True, exist_ok=True)


# ─── Writers (called only by planners / schema_generator) ─────────────────────

def write_functions(functions_dict: dict) -> None:
    """Persist coordinator output to .lysithea/functions.json"""
    ensure_law_dir()
    with open(FUNCTIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(functions_dict, f, indent=2)
    print(f"[file_manager] ✅ Written: {FUNCTIONS_FILE}")


def write_stack(stack_config: dict) -> None:
    """Persist stack_planner output to .lysithea/stack.json"""
    ensure_law_dir()
    with open(STACK_FILE, 'w', encoding='utf-8') as f:
        json.dump(stack_config, f, indent=2)
    print(f"[file_manager] ✅ Written: {STACK_FILE}")


def write_schema(sql_content: str) -> None:
    """Persist schema_generator output to .lysithea/schema.sql"""
    ensure_law_dir()
    SCHEMA_FILE.write_text(sql_content, encoding='utf-8')
    print(f"[file_manager] ✅ Written: {SCHEMA_FILE}")


# ─── Readers (called by all generators) ───────────────────────────────────────

def load_functions() -> dict:
    """
    Load resources + operations from .lysithea/functions.json.

    Hard fails if coordinator has not run yet.

    Returns:
        {
          "products": ["get all", "get by id", "post", "put", "delete"],
          ...
        }
    """
    _require_file(
        FUNCTIONS_FILE,
        "coordinator.py has not run yet — execute coordinator first."
    )
    with open(FUNCTIONS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_stack() -> dict:
    """
    Load stack config from .lysithea/stack.json.

    Hard fails if stack_planner has not run yet.

    Returns:
        {
          "stack": { "backend": {...}, "frontend": {...}, "database": {...} },
          "api_requirements": {...},
          ...
        }
    """
    _require_file(
        STACK_FILE,
        "stack_planner.py has not run yet — execute stack_planner first."
    )
    with open(STACK_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_schema() -> str:
    """
    Load raw SQL schema from .lysithea/schema.sql.

    Hard fails if schema_generator has not run yet.

    Returns:
        Full SQL string.
    """
    _require_file(
        SCHEMA_FILE,
        "schema_generator has not run yet — generate schema first."
    )
    return SCHEMA_FILE.read_text(encoding='utf-8')


def load_resources() -> list:
    """
    Convenience: return resources as a list of dicts expected by generators.

    Derived from functions.json — no separate file needed.

    Returns:
        [{'name': 'products', 'operations': ['get all', ...]}, ...]
    """
    functions = load_functions()
    return [
        {'name': resource, 'operations': ops}
        for resource, ops in functions.items()
    ]


def extract_table_from_schema(table_name: str) -> str | None:
    """
    Extract a single CREATE TABLE block from .lysithea/schema.sql.

    Hard fails if schema has not been generated.

    Args:
        table_name: e.g. 'products'

    Returns:
        'CREATE TABLE products (...);' string, or None if table not found.
    """
    schema_content = load_schema()
    pattern = rf'CREATE TABLE (?:IF NOT EXISTS )?{table_name}\s*\((.*?)\);'
    match = re.search(pattern, schema_content, re.DOTALL | re.IGNORECASE)
    if match:
        return f"CREATE TABLE {table_name} ({match.group(1)});"
    return None


# ─── Status helpers ────────────────────────────────────────────────────────────

def law_status() -> dict:
    """
    Return which law files are present.
    Useful for CLI /status command and orchestrator pre-flight checks.

    Returns:
        {
          'functions': True/False,
          'stack':     True/False,
          'schema':    True/False,
        }
    """
    return {
        'functions': FUNCTIONS_FILE.exists(),
        'stack':     STACK_FILE.exists(),
        'schema':    SCHEMA_FILE.exists(),
    }


def assert_planning_complete() -> None:
    """
    Hard fail if either coordinator or stack_planner have not run.
    Call this at the top of orchestrator.py before any generator is invoked.
    """
    missing = []
    if not FUNCTIONS_FILE.exists():
        missing.append(f"  • {FUNCTIONS_FILE}  (run coordinator.py)")
    if not STACK_FILE.exists():
        missing.append(f"  • {STACK_FILE}  (run stack_planner.py)")

    if missing:
        raise RuntimeError(
            "\n[file_manager] ❌ Rule of Law violated — missing required files:\n"
            + "\n".join(missing)
            + "\n\nRun the planners before invoking any generator."
        )


def assert_schema_ready() -> None:
    """
    Hard fail if schema has not been generated.
    Call this at the top of any generator that depends on schema
    (seeds, queries, routes).
    """
    if not SCHEMA_FILE.exists():
        raise RuntimeError(
            f"\n[file_manager] ❌ Rule of Law violated — {SCHEMA_FILE} not found.\n"
            "Run schema_generator before invoking seed/query/route generators."
        )


def assert_stack_supported() -> None:
    """
    Hard fail if the stack declared in stack.json is not listed as 'complete'
    in supported_stacks.json.

    Call this in orchestrator.py after assert_planning_complete().
    Gives a clear error pointing to the roadmap instead of silent
    pattern-not-found failures deep inside generators.
    """
    if not SUPPORTED_STACKS_FILE.exists():
        return  # No registry file — skip check

    stack     = load_stack()
    backend   = stack.get('stack', {}).get('backend', {})
    language  = backend.get('language', '').lower()
    framework = backend.get('framework', '').lower()

    with open(SUPPORTED_STACKS_FILE, 'r', encoding='utf-8') as f:
        registry = json.load(f)

    supported = registry.get('supported', [])
    match = next(
        (s for s in supported
         if s['language'].lower() == language
         and s['framework'].lower() == framework),
        None
    )

    if not match:
        available = [
            f"  * {s['language']}/{s['framework']}"
            for s in supported if s['status'] == 'complete'
        ]
        raise RuntimeError(
            f"\n[file_manager] Unknown stack: {language}/{framework}\n"
            f"No entry found in supported_stacks.json.\n\n"
            f"Stacks with complete pattern coverage:\n" + "\n".join(available)
        )

    if match['status'] != 'complete':
        raise RuntimeError(
            f"\n[file_manager] Stack not yet implemented: {language}/{framework}\n"
            f"Status: {match['status']}\n"
            f"Notes:  {match.get('notes', '')}\n\n"
            f"To add support, create pattern files under:\n"
            f"  Patterns/{language.capitalize()}/{framework.capitalize()}/"
        )


# ─── Output file helpers (unchanged behaviour) ────────────────────────────────

def save_generated_files(code, explanation, resource_name="generated", append_notes=False):
    """Save generated code and notes to output/"""

    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)

    code_path  = output_dir / f"{resource_name}.js"
    notes_path = output_dir / f"{resource_name}_notes.txt"
    timestamp  = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    code_path.write_text(f"// Generated: {timestamp}\n\n{code}", encoding='utf-8')
    print(f"✅ Saved code: {code_path}")

    if append_notes and notes_path.exists():
        existing = notes_path.read_text(encoding='utf-8')
        notes_path.write_text(
            existing + f"\n\n{'='*60}\nAdded: {timestamp}\n\n=== Explanation ===\n\n{explanation}",
            encoding='utf-8'
        )
    else:
        notes_path.write_text(
            f"Generated: {timestamp}\n\nResource: {resource_name}\n\n=== Explanation ===\n\n{explanation}",
            encoding='utf-8'
        )
    print(f"✅ Saved notes: {notes_path}")

    return code_path, notes_path


# ─── Internal ─────────────────────────────────────────────────────────────────

def _require_file(path: Path, guidance: str) -> None:
    """Raise RuntimeError with clear guidance if a law file is missing."""
    if not path.exists():
        raise RuntimeError(
            f"\n[file_manager] ❌ Rule of Law violated — {path} not found.\n{guidance}"
        )