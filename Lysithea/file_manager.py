# lysithea/file_manager.py
"""
File Manager - Rule of Law gatekeeper

.lysithea/ is the single source of truth.
All generators MUST read state through this module.
No generator may receive resources/schema/stack as function arguments.

Layout:
  ../../{project_name}/          <- two levels up from Lysithea/
    .lysithea/
      functions.json             <- written by coordinator.py
      stack.json                 <- written by stack_planner.py
      schema.sql                 <- written by schema_generator.py
    app.js
    package.json
    api/
    db/
"""

import re
import json
from pathlib import Path
from datetime import datetime

SUPPORTED_STACKS_FILE = Path('supported_stacks.json')


# ─── Project directory resolution ─────────────────────────────────────────────

def get_project_name(prompt_file='prompt.md') -> str:
    """
    Read project name from prompt.md and convert to a safe folder name.

    e.g. 'Book Store' -> 'book-store'

    Falls back to 'my-app' if prompt.md is missing or has no project name.
    """
    path = Path(prompt_file)
    if not path.exists():
        return 'my-app'

    found_heading = False
    for line in path.read_text(encoding='utf-8').splitlines():
        if re.match(r'^#\s+Project Name', line, re.IGNORECASE):
            found_heading = True
            continue
        if found_heading:
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                return re.sub(r'[^\w\s-]', '', stripped).strip().lower().replace(' ', '-')

    return 'my-app'


def get_project_dir(prompt_file='prompt.md') -> Path:
    """
    Return the root output directory for the project.

    Two levels up from Lysithea/ so it sits alongside it:
      ../../{project_name}/
    """
    return Path(__file__).parent.parent.parent / get_project_name(prompt_file)


def get_law_dir(prompt_file='prompt.md') -> Path:
    """Return {project_dir}/.lysithea/"""
    return get_project_dir(prompt_file) / '.lysithea'


# ─── Dynamic path accessors ───────────────────────────────────────────────────
# Using functions instead of module-level constants so paths are
# always resolved from the current prompt.md at call time.

def _project_dir() -> Path:
    return get_project_dir()

def _law_dir() -> Path:
    return get_law_dir()

def _functions_file() -> Path:
    return _law_dir() / 'functions.json'

def _stack_file() -> Path:
    return _law_dir() / 'stack.json'

def _schema_file() -> Path:
    return _law_dir() / 'schema.sql'


# ─── Bootstrap ────────────────────────────────────────────────────────────────

def ensure_law_dir() -> None:
    """Create project dir and .lysithea/ if they don't exist yet."""
    _law_dir().mkdir(parents=True, exist_ok=True)


# ─── Writers (called only by planners / schema_generator) ─────────────────────

def write_functions(functions_dict: dict) -> None:
    """Persist coordinator output to {project}/.lysithea/functions.json"""
    ensure_law_dir()
    with open(_functions_file(), 'w', encoding='utf-8') as f:
        json.dump(functions_dict, f, indent=2)
    print(f"[file_manager] ✅ Written: {_functions_file()}")


def write_stack(stack_config: dict) -> None:
    """Persist stack_planner output to {project}/.lysithea/stack.json"""
    ensure_law_dir()
    with open(_stack_file(), 'w', encoding='utf-8') as f:
        json.dump(stack_config, f, indent=2)
    print(f"[file_manager] ✅ Written: {_stack_file()}")


def write_schema(sql_content: str) -> None:
    """Persist schema_generator output to {project}/.lysithea/schema.sql"""
    ensure_law_dir()
    _schema_file().write_text(sql_content, encoding='utf-8')
    print(f"[file_manager] ✅ Written: {_schema_file()}")


# ─── Readers (called by all generators) ───────────────────────────────────────

def load_functions() -> dict:
    """
    Load resources + operations from .lysithea/functions.json.
    Hard fails if coordinator has not run yet.
    """
    _require_file(
        _functions_file(),
        "coordinator.py has not run yet — execute coordinator first."
    )
    with open(_functions_file(), 'r', encoding='utf-8') as f:
        return json.load(f)


def load_stack() -> dict:
    """
    Load stack config from .lysithea/stack.json.
    Hard fails if stack_planner has not run yet.
    """
    _require_file(
        _stack_file(),
        "stack_planner.py has not run yet — execute stack_planner first."
    )
    with open(_stack_file(), 'r', encoding='utf-8') as f:
        return json.load(f)


def load_schema() -> str:
    """
    Load raw SQL schema from .lysithea/schema.sql.
    Hard fails if schema_generator has not run yet.
    """
    _require_file(
        _schema_file(),
        "schema_generator has not run yet — generate schema first."
    )
    return _schema_file().read_text(encoding='utf-8')


def load_resources() -> list:
    """
    Convenience: return resources as a list of dicts expected by generators.
    Derived from functions.json — no separate file needed.
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
    """
    schema_content = load_schema()
    pattern = rf'CREATE TABLE (?:IF NOT EXISTS )?{table_name}\s*\((.*?)\);'
    match = re.search(pattern, schema_content, re.DOTALL | re.IGNORECASE)
    if match:
        return f"CREATE TABLE {table_name} ({match.group(1)});"
    return None


# ─── Output path helper ───────────────────────────────────────────────────────

def get_output_path(*parts) -> Path:
    """
    Build a path inside the project backend directory and ensure it exists.

    Everything goes under backend/ — app.js, package.json, api/, db/ etc.
    The frontend will have its own sibling frontend/ directory later.

    Usage:
        get_output_path('.')            ->  ../../book-store/backend/
        get_output_path('api/routes')   ->  ../../book-store/backend/api/routes/
        get_output_path('db', 'queries')->  ../../book-store/backend/db/queries/
    """
    # Flatten any slash-separated strings and filter out empty segments and '.'
    flat = []
    for p in parts:
        flat.extend(str(p).split('/'))
    flat = [p for p in flat if p and p != '.']

    if flat:
        path = _project_dir() / 'backend' / Path(*flat)
    else:
        path = _project_dir() / 'backend'

    path.mkdir(parents=True, exist_ok=True)
    return path


# ─── Status helpers ───────────────────────────────────────────────────────────

def law_status() -> dict:
    """Return which law files are present."""
    return {
        'functions': _functions_file().exists(),
        'stack':     _stack_file().exists(),
        'schema':    _schema_file().exists(),
    }


def assert_planning_complete() -> None:
    """Hard fail if either coordinator or stack_planner have not run."""
    missing = []
    if not _functions_file().exists():
        missing.append(f"  • {_functions_file()}  (run coordinator.py)")
    if not _stack_file().exists():
        missing.append(f"  • {_stack_file()}  (run stack_planner.py)")

    if missing:
        raise RuntimeError(
            "\n[file_manager] ❌ Rule of Law violated — missing required files:\n"
            + "\n".join(missing)
            + "\n\nRun the planners before invoking any generator."
        )


def assert_schema_ready() -> None:
    """Hard fail if schema has not been generated."""
    if not _schema_file().exists():
        raise RuntimeError(
            f"\n[file_manager] ❌ Rule of Law violated — {_schema_file()} not found.\n"
            "Run schema_generator before invoking seed/query/route generators."
        )


def assert_stack_supported() -> None:
    """
    Hard fail if the stack declared in stack.json is not listed as 'complete'
    in supported_stacks.json.
    """
    if not SUPPORTED_STACKS_FILE.exists():
        return

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


# ─── Output file helpers ──────────────────────────────────────────────────────

def save_generated_files(output_file, code, timestamp, append_notes=False):
    """Save generated code to the given output_file path."""
    path = Path(output_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"// Generated: {timestamp}\n\n{code}", encoding='utf-8')
    print(f"✅ Saved: {path}")
    return path


# ─── Internal ─────────────────────────────────────────────────────────────────

def _require_file(path: Path, guidance: str) -> None:
    """Raise RuntimeError with clear guidance if a law file is missing."""
    if not path.exists():
        raise RuntimeError(
            f"\n[file_manager] ❌ Rule of Law violated — {path} not found.\n{guidance}"
        )