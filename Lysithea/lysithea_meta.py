# lysithea/lysithea_meta.py
"""
Writes and reads the .lysithea project metadata file.

The metadata file lives at {project_dir}/.lysithea/.lysithea and allows
the GUI to discover, import, and track projects generated via the CLI —
bridging the two workflows seamlessly.

.lysithea shape:
{
  "id":        "uuid4",
  "name":      "MyShopApp",
  "stack": {
    "backend":  "express",
    "frontend": "react",
    "database": "postgresql",
    "auth":     "jwt"
  },
  "createdAt": "2026-03-08T00:00:00",
  "updatedAt": "2026-03-08T00:00:00"
}
"""

import json
import uuid
import os
from datetime import datetime, timezone

META_FILENAME  = '.lysithea'
META_SUBDIR    = '.lysithea'   # subfolder inside the project root


def _meta_path(project_path: str) -> str:
    """Return full path to the .lysithea metadata file."""
    return os.path.join(project_path, META_SUBDIR, META_FILENAME)


def write_project_meta(project_path: str, stack: dict, project_name: str = None) -> dict:
    """
    Write (or update) the .lysithea metadata file in {project_path}/.lysithea/.

    Called by orchestrator.py after all generation is complete so the
    project folder is guaranteed to exist.

    Preserves existing id and createdAt if file already exists (idempotent).

    Args:
        project_path: Absolute path to the generated project folder (not the parent).
        stack:        Stack config dict from stack.json (via load_stack()).
        project_name: Human-readable name. Falls back to folder name if not given.

    Returns:
        The metadata dict that was written.
    """
    meta_file = _meta_path(project_path)
    meta_dir  = os.path.dirname(meta_file)

    # Preserve existing id + createdAt if already initialised
    existing = {}
    if os.path.exists(meta_file):
        try:
            with open(meta_file, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        except (json.JSONDecodeError, OSError):
            existing = {}

    now = datetime.now(timezone.utc).isoformat()

    # Derive a clean name: explicit arg > stack project_name > folder basename
    name = (
        project_name
        or stack.get('project_name')
        or os.path.basename(os.path.abspath(project_path))
    )

    # Handle nested or flat stack dicts
    stack_inner = stack.get('stack', stack)
    meta = {
        'id':        existing.get('id', str(uuid.uuid4())),
        'name':      name,
        'stack': {
            'backend':  stack_inner.get('backend',  'express'),
            'frontend': stack_inner.get('frontend', 'react'),
            'database': stack_inner.get('database', 'postgresql'),
            'auth':     stack_inner.get('security', stack_inner.get('auth', 'jwt')),
        },
        'createdAt': existing.get('createdAt', now),
        'updatedAt': now,
    }

    os.makedirs(meta_dir, exist_ok=True)
    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=2)

    print(f"[lysithea_meta] ✅ Written: {meta_file}")
    return meta


def read_project_meta(project_path: str) -> dict | None:
    """
    Read the .lysithea metadata file from a project folder.
    Returns None if the file does not exist or cannot be parsed.
    """
    meta_file = _meta_path(project_path)
    if not os.path.exists(meta_file):
        return None
    try:
        with open(meta_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None