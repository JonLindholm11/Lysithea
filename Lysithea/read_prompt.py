# lysithea/read_prompt.py
"""
Parses prompt.md into a structured dict for use by coordinator and stack_planner.

Expected prompt.md format:
  # Project Name
  # Stack
  # Features
  # API Requirements
  # Frontend Requirements
  # Database / Schema Notes
  # Extra Notes
"""

import re
from pathlib import Path


def read_prompt_md(prompt_file='prompt.md') -> dict | None:
    """
    Read and parse a prompt.md file into a structured dict.

    Returns:
        {
          'project_name': 'My App',
          'stack': {
            'frontend': 'React 18 + Tailwind',
            'backend':  { 'language': 'javascript', 'framework': 'express' },
            'database': 'PostgreSQL',
          },
          'features': {
            'products': ['create', 'read', 'update', 'delete'],
            'users':    ['crud'],
          },
          'api_requirements': {
            'security': 'JWT',
            'endpoint_style': 'RESTful',
            'validation': True,
            'rate_limiting': False,
          },
          'frontend_requirements': { ... },
          'database_schema': { ... },
          'extra_notes': '...',
        }
        or None if the file cannot be read.
    """
    path = Path(prompt_file)
    if not path.exists():
        print(f"[read_prompt] ❌ File not found: {prompt_file}")
        return None

    content = path.read_text(encoding='utf-8')
    sections = _split_sections(content)

    return {
        'project_name':          _parse_project_name(sections),
        'stack':                 _parse_stack(sections),
        'features':              _parse_features(sections),
        'api_requirements':      _parse_api_requirements(sections),
        'frontend_requirements': _parse_frontend_requirements(sections),
        'database_schema':       _parse_database_schema(sections),
        'extra_notes':           sections.get('extra notes', '').strip(),
    }


# ─── Section splitter ─────────────────────────────────────────────────────────

def _split_sections(content: str) -> dict:
    """
    Split markdown into a dict keyed by lowercased heading text.

    '# Stack\\nFrontend: React' → {'stack': 'Frontend: React'}
    """
    sections = {}
    current_heading = None
    current_lines   = []

    for line in content.splitlines():
        heading_match = re.match(r'^#+\s+(.+)', line)
        if heading_match:
            if current_heading is not None:
                sections[current_heading] = '\n'.join(current_lines).strip()
            current_heading = heading_match.group(1).strip().lower()
            current_lines   = []
        else:
            if current_heading is not None:
                current_lines.append(line)

    if current_heading is not None:
        sections[current_heading] = '\n'.join(current_lines).strip()

    return sections


# ─── Section parsers ──────────────────────────────────────────────────────────

def _parse_project_name(sections: dict) -> str:
    return sections.get('project name', 'Unnamed Project').strip()


def _parse_stack(sections: dict) -> dict:
    """
    Parse the Stack section into a structured dict.

    Handles lines like:
      Frontend: React 18 + Tailwind
      Backend: Express.js + Node 20
      Database: PostgreSQL
    """
    raw     = sections.get('stack', '')
    result  = {}

    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith('<'):
            continue

        if ':' not in line:
            continue

        key, _, value = line.partition(':')
        key   = key.strip().lower()
        value = value.strip()

        if not value or value.startswith('<'):
            continue

        if key == 'frontend':
            result['frontend'] = value

        elif key == 'backend':
            result['backend'] = _parse_backend(value)

        elif key == 'database':
            result['database'] = value

    # Defaults
    if 'backend' not in result:
        result['backend'] = {'language': 'javascript', 'framework': 'express'}

    return result


def _parse_backend(value: str) -> dict:
    """
    Turn a backend string into language + framework.

    'Express.js + Node 20'  → {'language': 'javascript', 'framework': 'express'}
    'FastAPI + Python 3.12' → {'language': 'python',     'framework': 'fastapi'}
    'Gin + Go 1.22'         → {'language': 'go',         'framework': 'gin'}
    'Rails 7 + Ruby 3.3'    → {'language': 'ruby',       'framework': 'rails'}
    """
    v = value.lower()

    if 'express' in v:
        return {'language': 'javascript', 'framework': 'express'}
    if 'fastapi' in v:
        return {'language': 'python', 'framework': 'fastapi'}
    if 'flask' in v:
        return {'language': 'python', 'framework': 'flask'}
    if 'django' in v:
        return {'language': 'python', 'framework': 'django'}
    if 'gin' in v:
        return {'language': 'go', 'framework': 'gin'}
    if 'fiber' in v:
        return {'language': 'go', 'framework': 'fiber'}
    if 'rails' in v:
        return {'language': 'ruby', 'framework': 'rails'}
    if 'sinatra' in v:
        return {'language': 'ruby', 'framework': 'sinatra'}

    # Fallback — try to extract first word as framework
    first_word = re.split(r'[\s\+\.]', v)[0]
    return {'language': 'javascript', 'framework': first_word or 'express'}


def _parse_features(sections: dict) -> dict:
    """
    Parse the Features section into {resource: [operations]}.

    Handles lines like:
      - Products: create, read, update, delete
      - Users: crud
      - Orders: get all, post, delete
    """
    raw      = sections.get('features', '')
    features = {}

    for line in raw.splitlines():
        line = line.strip().lstrip('-').strip()
        if not line or ':' not in line or line.startswith('<'):
            continue

        key, _, value = line.partition(':')
        key   = key.strip().lower()
        value = value.strip()

        if not value or value.startswith('<'):
            continue

        # Split operations by comma
        ops = [op.strip().lower() for op in value.split(',') if op.strip()]
        if ops:
            features[key] = ops

    return features


def _parse_api_requirements(sections: dict) -> dict:
    """Parse the API Requirements section into a flat dict."""
    raw    = sections.get('api requirements', '')
    result = {}

    for line in raw.splitlines():
        line = line.strip().lstrip('-').strip()
        if not line or ':' not in line or line.startswith('<'):
            continue

        key, _, value = line.partition(':')
        key   = key.strip().lower().replace(' ', '_')
        value = value.strip()

        if not value or value.startswith('<'):
            continue

        # Coerce obvious booleans
        if value.lower() in ('true', 'yes'):
            result[key] = True
        elif value.lower() in ('false', 'no'):
            result[key] = False
        else:
            result[key] = value

    return result


def _parse_frontend_requirements(sections: dict) -> dict:
    """Parse the Frontend Requirements section into a flat dict."""
    raw    = sections.get('frontend requirements', '')
    result = {}

    for line in raw.splitlines():
        line = line.strip().lstrip('-').strip()
        if not line or ':' not in line or line.startswith('<'):
            continue

        key, _, value = line.partition(':')
        key   = key.strip().lower().replace(' ', '_')
        value = value.strip()

        if not value or value.startswith('<'):
            continue

        result[key] = value

    return result


def _parse_database_schema(sections: dict) -> dict:
    """
    Parse the Database / Schema Notes section.

    Returns a dict with 'tables' and 'relationships' keys.
    """
    # Try both heading variants
    raw = sections.get('database / schema notes', '') or sections.get('database schema notes', '')

    tables        = {}
    relationships = []

    current = None
    for line in raw.splitlines():
        line = line.strip().lstrip('-').strip()
        if not line or line.startswith('<'):
            continue

        if line.lower().startswith('tables'):
            current = 'tables'
            continue
        if line.lower().startswith('relationships'):
            current = 'relationships'
            continue

        if current == 'tables' and ':' in line:
            name, _, cols = line.partition(':')
            tables[name.strip().lower()] = cols.strip()

        elif current == 'relationships':
            relationships.append(line)

    return {
        'tables':        tables,
        'relationships': relationships,
    }


# ─── CLI helper ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import json
    result = read_prompt_md('prompt.md')
    if result:
        print(json.dumps(result, indent=2))