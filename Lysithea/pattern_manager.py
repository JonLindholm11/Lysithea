# lysithea/pattern_manager.py
"""
Pattern file management

Pattern paths are resolved dynamically from the current stack
(language + framework) read from .lysithea/stack.json.

Pattern directory convention:
  Patterns/{Language}/{Framework}/{category}/{pattern}.{ext}

Examples:
  Patterns/Javascript/Express/Routes/get-all-auth.js
  Patterns/Python/FastAPI/routes/get-users-auth.py
  Patterns/Go/Gin/routes/get-users-auth.go
  Patterns/Ruby/Rails/routes/get-users-auth.rb
"""

import re
from pathlib import Path


# ─── Stack resolution ─────────────────────────────────────────────────────────

def get_stack_info() -> dict:
    """
    Read language and framework from .lysithea/stack.json.

    Returns:
        {
          'language':  'javascript',
          'framework': 'express',
          'language_dir':  'Javascript',   # title-cased for Patterns/ directory
          'framework_dir': 'Express',
        }

    Hard fails if stack_planner has not run yet (via load_stack).
    """
    from file_manager import load_stack

    stack    = load_stack()
    backend  = stack.get('stack', {}).get('backend', {})
    language  = backend.get('language', 'javascript').lower()
    framework = backend.get('framework', 'express').lower()

    return {
        'language':      language,
        'framework':     framework,
        'language_dir':  language.capitalize(),
        'framework_dir': framework.capitalize(),
    }


def get_pattern_base(stack: dict | None = None) -> str:
    """
    Return the base pattern directory for the current stack.

    Args:
        stack: optional override dict (same shape as get_stack_info()).
               If omitted, reads from file_manager.

    Returns:
        e.g. 'javascript/express'  (lowercase, used in load_pattern paths)
    """
    info = stack or get_stack_info()
    return f"{info['language']}/{info['framework']}"


# ─── Pattern loading ──────────────────────────────────────────────────────────

def get_pattern_metadata(pattern_path: str) -> dict | None:
    """Extract @output-dir and @file-naming metadata from a pattern file."""
    pattern_content = load_pattern(pattern_path)
    if not pattern_content:
        return None
    return extract_metadata_from_content(pattern_content)


def extract_metadata_from_content(pattern_content: str) -> dict:
    """Extract @output-dir and @file-naming from an already-loaded pattern string."""
    output_dir_match = re.search(r'@output-dir\s+(.+)', pattern_content)
    output_dir       = output_dir_match.group(1).strip() if output_dir_match else '.'

    file_naming_match = re.search(r'@file-naming\s+(.+)', pattern_content)
    file_naming       = file_naming_match.group(1).strip() if file_naming_match else '{resource}.js'

    return {
        'output_dir':  output_dir,
        'file_naming': file_naming,
    }


def load_pattern(pattern_path: str) -> str | None:
    """
    Load a pattern file relative to the Patterns/ directory.

    Args:
        pattern_path: case-insensitive logical path,
                      e.g. 'javascript/express/routes/get-users-auth.js'
                      The loader will try an exact match first, then
                      a title-cased directory match for the on-disk layout.
    """
    # Try exact path first (for future stacks that may use lowercase dirs)
    exact = Path('..') / 'Patterns' / pattern_path
    if exact.exists():
        return exact.read_text(encoding='utf-8')

    parts    = Path(pattern_path).parts
    filename = parts[-1]          # preserve filename exactly as-is
    dirs     = parts[:-1]         # only capitalize directory segments

    # Try capitalizing all directory segments, preserve filename
    # e.g. javascript/express/routes/get-users-auth.js
    #   → Patterns/Javascript/Express/Routes/get-users-auth.js
    if dirs:
        cap_all = Path('..') / 'Patterns' / Path(*[p.capitalize() for p in dirs]) / filename
        if cap_all.exists():
            return cap_all.read_text(encoding='utf-8')

    # Try capitalizing only language/framework, preserve rest including filename
    # e.g. javascript/express/routes/get-users-auth.js
    #   → Patterns/Javascript/Express/routes/get-users-auth.js
    if len(parts) >= 3:
        mixed = Path('..') / 'Patterns' / dirs[0].capitalize() / dirs[1].capitalize() / Path(*parts[2:])
        if mixed.exists():
            return mixed.read_text(encoding='utf-8')

    return None


def list_available_patterns() -> list[str]:
    """Return all pattern files relative to Patterns/."""
    pattern_dir = Path('..') / 'Patterns'
    if not pattern_dir.exists():
        return []
    return [
        str(p.relative_to(pattern_dir))
        for p in pattern_dir.rglob('*')
        if p.is_file()
    ]


# ─── Operation → pattern mapping ─────────────────────────────────────────────

def map_operation_to_pattern(operation: str, stack: dict | None = None) -> str | None:
    """
    Map an operation name to the correct pattern file path for the current stack.

    Args:
        operation: e.g. 'get all', 'get by id', 'post', 'put', 'delete'
        stack:     optional stack override dict (shape of get_stack_info()).
                   If omitted, reads from file_manager.

    Returns:
        Pattern path string, e.g.
        'javascript/express/routes/get-users-auth.js'
        'python/fastapi/routes/get-all.py'
        or None if no mapping exists.
    """
    info = stack or get_stack_info()
    base = get_pattern_base(info)
    ext  = _ext_for_language(info['language'])
    op   = operation.lower()

    # GET by ID (must come before generic GET)
    if 'get' in op and ('by id' in op or 'by-id' in op):
        return f"{base}/routes/get-users-by-id-auth{ext}"

    # GET by attribute (any other get-by-X)
    if 'get' in op and 'by' in op:
        return f"{base}/routes/get-users-by-id-auth{ext}"

    # GET all
    if 'get' in op:
        return f"{base}/routes/get-users-auth{ext}"

    if 'post' in op or 'create' in op:
        return f"{base}/routes/post-users-auth{ext}"

    if 'put' in op or 'update' in op:
        return f"{base}/routes/put-users-auth{ext}"

    if 'delete' in op or 'remove' in op:
        return f"{base}/routes/delete-users-auth{ext}"

    return None


def map_query_pattern(query_type: str, stack: dict | None = None) -> str | None:
    """
    Map a query type name to the correct pattern file path for the current stack.

    Args:
        query_type: e.g. 'create', 'get-all', 'get-by-id', 'update', 'delete',
                    'get-by-id-with-join', 'get-with-joins',
                    'get-by-field', 'get-by-field-with-join'
        stack:      optional stack override.

    Returns:
        Pattern path string or None.
    """
    info = stack or get_stack_info()
    base = get_pattern_base(info)
    ext  = _ext_for_language(info['language'])

    # Strip any ':field_name' suffix (e.g. 'get-by-field-with-join:category_id')
    query_base = query_type.split(':')[0]

    return f"{base}/queries/{query_base}{ext}"


def map_middleware_pattern(middleware_name: str, stack: dict | None = None) -> str | None:
    """
    Map a middleware name to the correct pattern file path for the current stack.

    Args:
        middleware_name: e.g. 'auth', 'validation', 'error'
        stack:           optional stack override.

    Returns:
        Pattern path string or None.
    """
    info = stack or get_stack_info()
    base = get_pattern_base(info)
    ext  = _ext_for_language(info['language'])

    middleware_map = {
        'auth':           f"{base}/middleware/auth-middleware{ext}",
        'authentication': f"{base}/middleware/auth-middleware{ext}",
        'validation':     f"{base}/middleware/validation-middleware{ext}",
        'error':          f"{base}/middleware/error-middleware{ext}",
    }

    return middleware_map.get(middleware_name.lower())


def map_database_pattern(db_type: str, stack: dict | None = None) -> str | None:
    """
    Map a database component name to the correct pattern file path.

    Args:
        db_type: e.g. 'connection', 'schema', 'migration'
        stack:   optional stack override.

    Returns:
        Pattern path string or None.
    """
    info = stack or get_stack_info()
    base = get_pattern_base(info)

    # Schema is always SQL regardless of backend language
    db_ext = '.sql' if db_type in ('schema', 'migration') else _ext_for_language(info['language'])

    database_map = {
        'connection': f"{base}/database/connection{_ext_for_language(info['language'])}",
        'schema':     f"{base}/database/schema.sql",
        'migration':  f"{base}/database/migration.sql",
    }

    return database_map.get(db_type.lower())


# ─── Internal ─────────────────────────────────────────────────────────────────

def _ext_for_language(language: str) -> str:
    """Return the file extension for a given backend language."""
    ext_map = {
        'javascript': '.js',
        'typescript': '.ts',
        'python':     '.py',
        'go':         '.go',
        'ruby':       '.rb',
        'rust':       '.rs',
    }
    return ext_map.get(language.lower(), '.js')