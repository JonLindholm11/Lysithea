# lysithea/generators/frontend_generator.py

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

"""
Frontend generation — React 18 + Tailwind + React Router v6 + React Query

Rule of Law: reads stack/style/resources from file_manager
             call generate_frontend() — no args.

Two passes:
  1. Static files  — pure pattern substitution, no LLM
  2. Dynamic files — LLM adapts pattern per resource (list page, form, hooks, api)
"""

import re
import ollama
from pathlib import Path
from datetime import datetime

from pattern_manager import load_pattern, extract_metadata_from_content
from parsers import extract_code_from_response
from file_manager import (
    assert_planning_complete,
    assert_schema_ready,
    load_stack,
    load_resources,
    extract_table_from_schema,
    get_output_path,
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _frontend_path(*parts):
    """Return absolute path inside frontend/ output directory."""
    from file_manager import get_project_dir
    project_dir = get_project_dir()
    path = project_dir / 'frontend' / Path(*parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _write(rel_path, content, timestamp=None):
    """Write a frontend file and print confirmation."""
    ts   = timestamp or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    path = _frontend_path(rel_path)
    path.write_text(content, encoding='utf-8')
    print(f"  ✅ {rel_path}")
    return path


def _load_base(filename):
    path = f'javascript/react/base/{filename}'
    result = load_pattern(path)
    if not result:
        print(f"  ⚠️  Pattern not found: {path}")
        print(f"      Expected at: Patterns/Javascript/React/base/{filename}")
    return result


def _load_style(style, filename):
    path = f'javascript/react/styles/{style}/{filename}'
    pattern = load_pattern(path)
    if not pattern:
        fallback = f'javascript/react/styles/corporate/{filename}'
        pattern = load_pattern(fallback)
        if not pattern:
            print(f"  ⚠️  Pattern not found: {path}")
            print(f"      Expected at: Patterns/Javascript/React/styles/{style}/{filename}")
    return pattern


def _strip_doc(content):
    """Remove /** ... */ doc comments from pattern content."""
    return re.sub(r'/\*\*[\s\S]*?\*/', '', content).strip()


def _resource_title(name):
    """books → Books, book_orders → BookOrders"""
    return ''.join(w.capitalize() for w in re.split(r'[_\s]', name))


def _resource_camel(name):
    """books → books (stays lowercase for hook names like useBooks)"""
    return name


# ─── Static file generation (no LLM) ─────────────────────────────────────────

def _generate_static(project_name, style, resources):
    """Generate all files that need only simple placeholder substitution."""

    print("\n  — Static files —")

    # package.json
    raw = _load_base('package-json-pattern.js')
    if raw:
        content = _strip_doc(raw).replace('/* PROJECT_NAME */', project_name.lower())
        _write('package.json', content)

    # vite.config.js
    raw = _load_base('vite-config-pattern.js')
    if raw:
        _write('vite.config.js', _strip_doc(raw))

    # tailwind.config.js
    raw = _load_base('tailwind-config-pattern.js')
    if raw:
        _write('tailwind.config.js', _strip_doc(raw))

    # index.html
    raw = _load_base('index-html-pattern.js')
    if raw:
        content = _strip_doc(raw).replace('/* PROJECT_NAME */', project_name)
        _write('index.html', content)

    # .env.example
    raw = _load_base('env-example-pattern.js')
    if raw:
        _write('.env.example', _strip_doc(raw))

    # src/main.jsx
    raw = _load_base('main-jsx-pattern.js')
    if raw:
        _write('src/main.jsx', _strip_doc(raw))

    # postcss.config.js
    raw = _load_base('postcss-config-pattern.js')
    if raw:
        _write('postcss.config.js', _strip_doc(raw))

    # src/index.css
    raw = _load_base('index-css-pattern.js')
    if raw:
        _write('src/index.css', _strip_doc(raw))

    # src/api/client.js
    raw = _load_base('api-client-pattern.js')
    if raw:
        _write('src/api/client.js', _strip_doc(raw))

    # src/api/auth.api.js
    raw = _load_base('auth-api-pattern.js')
    if raw:
        _write('src/api/auth.api.js', _strip_doc(raw))

    # src/context/AuthContext.jsx
    raw = _load_base('auth-context-pattern.js')
    if raw:
        _write('src/context/AuthContext.jsx', _strip_doc(raw))

    # src/pages/Login.jsx
    raw = _load_style(style, 'login-page-pattern.js')
    if raw:
        _write('src/pages/Login.jsx', _strip_doc(raw))

    # src/pages/Register.jsx
    raw = _load_style(style, 'register-page-pattern.js')
    if raw:
        _write('src/pages/Register.jsx', _strip_doc(raw))

    # src/components/Layout.jsx — inject nav links + project name
    raw = _load_style(style, 'layout-pattern.js')
    if raw:
        content = _strip_doc(raw)
        nav_links = _build_nav_links(resources)
        content = content.replace('/* NAV_LINKS */', nav_links)
        content = content.replace('/* PROJECT_NAME */', project_name)
        _write('src/components/Layout.jsx', content)

    # src/pages/Dashboard.jsx — inject stat cards + quick links
    raw = _load_style(style, 'dashboard-page-pattern.js')
    if raw:
        content     = _strip_doc(raw)
        stat_cards  = _build_stat_cards(resources, style)
        quick_links = _build_quick_links(resources)
        stat_imports = _build_stat_imports(resources)
        content = content.replace('/* STAT_IMPORTS */', stat_imports)
        content = content.replace('/* STAT_COUNT */', str(len(resources)))
        content = content.replace('/* STAT_CARDS */', stat_cards)
        content = content.replace('/* QUICK_LINKS */', quick_links)
        _write('src/pages/Dashboard.jsx', content)


def _build_nav_links(resources):
    lines = ['const navLinks = [']
    lines.append("  { to: '/', label: 'Dashboard' },")
    for r in resources:
        title = _resource_title(r['name'])
        lines.append(f"  {{ to: '/{r['name']}', label: '{title}' }},")
    lines.append('];')
    return '\n'.join(lines)


def _build_stat_cards(resources, style):
    cards = []
    for r in resources:
        title = _resource_title(r['name'])
        name  = r['name']
        cards.append(
            f'        <div className="bg-white rounded-lg border border-gray-200 p-6">\n'
            f'          <p className="text-sm text-gray-500">{title}</p>\n'
            f'        </div>'
        )
    return '\n'.join(cards)


def _build_stat_imports(resources):
    # Simple — Dashboard just shows resource names as text cards, no extra imports needed
    return ''


def _build_quick_links(resources):
    links = []
    for r in resources:
        title = _resource_title(r['name'])
        links.append(
            f"          <a href=\"/{r['name']}\" "
            f"className=\"text-sm text-blue-700 border border-blue-200 rounded px-3 py-1 hover:bg-blue-50\">"
            f"{title}</a>"
        )
    return '\n'.join(links)


# ─── App.jsx generation (no LLM) ─────────────────────────────────────────────

def _generate_app(style, resources):
    raw = _load_style(style, 'app-pattern.js')
    if not raw:
        print("  ⚠️  app-pattern.js not found")
        return

    content = _strip_doc(raw)

    # Build page imports
    page_imports = []
    route_lines  = []
    for r in resources:
        title = _resource_title(r['name'])
        page_imports.append(f"import {title}List from './pages/{title}List';")
        page_imports.append(f"import {title}Form from './pages/{title}Form';")
        route_lines.append(f"        <Route path=\"/{r['name']}\"         element={{<{title}List />}} />")
        route_lines.append(f"        <Route path=\"/{r['name']}/new\"     element={{<{title}Form />}} />")
        route_lines.append(f"        <Route path=\"/{r['name']}/:id\"     element={{<{title}Form />}} />")

    content = content.replace('/* PAGE_IMPORTS */', '\n'.join(page_imports))
    content = content.replace('/* ROUTES */',       '\n'.join(route_lines))
    _write('src/App.jsx', content)


# ─── LLM-driven per-resource generation ──────────────────────────────────────

def _generate_resource_files(resource_name, table_schema, style):
    title  = _resource_title(resource_name)
    print(f"\n  — {title} —")

    _generate_resource_api(resource_name, title, table_schema)
    _generate_resource_hooks(resource_name, title, table_schema)
    _generate_resource_list(resource_name, title, table_schema, style)
    _generate_resource_form(resource_name, title, table_schema, style)


def _generate_resource_api(resource_name, title, table_schema):
    pattern = _load_base('resource-api-pattern.js')
    if not pattern:
        return

    prompt = f"""You are generating a fetch API service for the '{resource_name}' resource.

=== COMPLETE PATTERN ===
{_strip_doc(pattern)}

=== NAME SUBSTITUTION — apply these EXACTLY ===
- Export object name: {resource_name}Api
- API endpoints:      /{resource_name} and /{resource_name}/:id
- Keep import:        './client'
- Keep all 5 methods: getAll, getById, create, update, delete

=== CRITICAL RULES ===
- Every reference must use '{resource_name}', never 'user'/'users'
- Output ONLY a ```javascript code block, no explanation
"""
    code = _llm(prompt)
    if code:
        _write(f'src/api/{resource_name}.api.js', code)


def _generate_resource_hooks(resource_name, title, table_schema):
    pattern = _load_base('resource-hooks-pattern.js')
    if not pattern:
        return

    prompt = f"""You are generating React Query hooks for the '{resource_name}' resource.

=== COMPLETE PATTERN ===
{_strip_doc(pattern)}

=== EXACT FUNCTION NAMES — copy these precisely, no variations ===
- Import path:    '../api/{resource_name}.api'
- API object:     {resource_name}Api
- QUERY_KEY:      '{resource_name}'

Function 1 (list):    export function use{title}s(page = 1, limit = 20)
Function 2 (single):  export function use{title}(id)
Function 3 (create):  export function useCreate{title}()
Function 4 (update):  export function useUpdate{title}()
Function 5 (delete):  export function useDelete{title}()

=== CRITICAL RULES ===
- Function 1 and Function 2 MUST have different names: use{title}s vs use{title}
- Do NOT name both functions use{title}s — that causes a duplicate export error
- Do NOT add extra 's' to useCreate{title}, useUpdate{title}, useDelete{title}
- Every function name must reference '{title}', never 'User' or other resource names
- Output ONLY a ```javascript code block, no explanation
"""
    code = _llm(prompt)
    if code:
        _write(f'src/hooks/use{title}.js', code)


def _generate_resource_list(resource_name, title, table_schema, style):
    pattern = _load_style(style, 'resource-list-pattern.js')
    if not pattern:
        return

    # Derive display columns from schema
    columns = _schema_to_columns(table_schema, resource_name)
    headers = '\n'.join(
        f'              <th className="text-left px-4 py-3 font-medium text-gray-600">{col["label"]}</th>'
        for col in columns
    )
    cells = '\n'.join(
        f'                <td className="px-4 py-3 text-gray-700">{{item.{col["key"]}}}</td>'
        for col in columns
    )

    prompt = f"""You are generating a React list page for the '{resource_name}' resource.

=== COMPLETE PATTERN (already filled in, adapt names only) ===
{_strip_doc(pattern)
    .replace('/* TABLE_HEADERS */', headers)
    .replace('/* TABLE_CELLS */',   cells)}

=== NAME SUBSTITUTION — apply these EXACTLY ===
- Component name:    {title}List
- List hook:         use{title}s
- Delete mutation:   useDelete{title}
- Import path:       '../hooks/use{title}'
- List route:        '/{resource_name}'
- New item route:    '/{resource_name}/new'
- Edit item route:   '/{resource_name}/:id'

=== CRITICAL RULES ===
- Every variable, hook call, and import must reference '{resource_name}' or '{title}', never 'user'/'User'
- Output ONLY a ```jsx code block, no explanation
"""
    code = _llm(prompt)
    if code:
        _write(f'src/pages/{title}List.jsx', code)


def _generate_resource_form(resource_name, title, table_schema, style):
    pattern = _load_style(style, 'resource-form-pattern.js')
    if not pattern:
        return

    columns     = _schema_to_columns(table_schema, resource_name)
    form_fields = _build_form_fields(columns)
    initial     = '{' + ', '.join(f"{c['key']}: ''" for c in columns) + '}'
    populate    = '{' + ', '.join(f"{c['key']}: existing.data.{c['key']} ?? ''" for c in columns) + '}'

    prompt = f"""You are generating a React form component for the '{resource_name}' resource.

=== COMPLETE PATTERN (already filled in, adapt names only) ===
{_strip_doc(pattern)
    .replace('/* FORM_FIELDS */',  form_fields)
    .replace('/* INITIAL_FORM */', initial)
    .replace('/* POPULATE_FORM */', populate)}

=== NAME SUBSTITUTION — apply these EXACTLY, no mixing ===
- Component name:        {title}Form
- List hook:             use{title}s     (for fetching all records)
- Single record hook:    use{title}      (for fetching one record by id)
- Create mutation:       useCreate{title}
- Update mutation:       useUpdate{title}
- Delete mutation:       useDelete{title}
- Import path:           '../hooks/use{title}'
- Navigate after save:   '/{resource_name}'
- Back link:             '/{resource_name}'

=== CRITICAL RULES ===
- Line fetching single record MUST be: const {{ data: existing, isLoading }} = use{title}(id);
- Do NOT use use{title}s(id) — that is the list hook, not the single record hook
- Do NOT mix user/User variable names into {resource_name}/{title} component
- Every variable, hook call, and mutation must reference '{resource_name}' or '{title}', never 'user' or 'User'
- Output ONLY a ```jsx code block, no explanation
"""
    code = _llm(prompt)
    if code:
        _write(f'src/pages/{title}Form.jsx', code)


# ─── Schema → column helpers ──────────────────────────────────────────────────

SKIP_COLUMNS = {
    'id', 'created_at', 'updated_at', 'is_deleted', 'deleted_at', 'password_hash'
}

def _schema_to_columns(table_schema, resource_name):
    """Extract user-facing columns from CREATE TABLE SQL."""
    if not table_schema:
        return [{'key': 'name', 'label': 'Name', 'type': 'text'}]

    columns = []
    for line in table_schema.splitlines():
        line = line.strip().rstrip(',')
        if not line or line.upper().startswith(('CREATE', 'PRIMARY', 'FOREIGN', 'UNIQUE', 'INDEX', 'CHECK', ')')):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        col_name = parts[0].lower()
        col_type = parts[1].upper() if len(parts) > 1 else 'TEXT'
        if col_name in SKIP_COLUMNS:
            continue
        columns.append({
            'key':   col_name,
            'label': col_name.replace('_', ' ').title(),
            'type':  _sql_to_input_type(col_type),
        })
    return columns or [{'key': 'name', 'label': 'Name', 'type': 'text'}]


def _sql_to_input_type(sql_type):
    sql_type = sql_type.upper()
    if 'INT' in sql_type:                        return 'number'
    if 'DECIMAL' in sql_type or 'NUMERIC' in sql_type or 'FLOAT' in sql_type: return 'number'
    if 'BOOL' in sql_type:                       return 'checkbox'
    if 'DATE' in sql_type or 'TIME' in sql_type: return 'date'
    return 'text'


def _build_form_fields(columns):
    fields = []
    for col in columns:
        input_type = col['type']
        key   = col['key']
        label = col['label']
        if input_type == 'checkbox':
            field = (
                '        <div className="flex items-center gap-2">\n'
                f'          <input\n'
                f'            type="checkbox"\n'
                f'            id="{key}"\n'
                f'            checked={{!!form.{key}}}\n'
                f'            onChange={{e => setForm(f => ({{...f, {key}: e.target.checked}}))}}'  '\n'
                f'            className="h-4 w-4 text-blue-600 border-gray-300 rounded"\n'
                f'          />\n'
                f'          <label htmlFor="{key}" className="text-sm font-medium text-gray-700">\n'
                f'            {label}\n'
                f'          </label>\n'
                f'        </div>'
            )
        else:
            field = (
                f'        <div>\n'
                f'          <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>\n'
                f'          <input\n'
                f'            type="{input_type}"\n'
                f'            value={{form.{key}}}\n'
                f'            onChange={{e => setForm(f => ({{...f, {key}: e.target.value}}))}}'  '\n'
                f'            className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"\n'
                f'          />\n'
                f'        </div>'
            )
        fields.append(field)
    return '\n'.join(fields)


# ─── LLM call ─────────────────────────────────────────────────────────────────

def _llm(prompt):
    try:
        response = ollama.generate(model='llama3.1:8b', prompt=prompt, keep_alive=0)
        return extract_code_from_response(response['response'])
    except Exception as e:
        print(f"  ❌ LLM error: {e}")
        return None


# ─── Main entry point ─────────────────────────────────────────────────────────

def generate_frontend():
    """
    Generate the full React frontend for the current project.

    Reads stack/style/resources from file_manager.
    Hard fails if planners or schema have not run.
    """
    assert_planning_complete()
    assert_schema_ready()

    stack         = load_stack()
    resources     = load_resources()
    project_name  = stack.get('project_name', 'my-app')
    style         = stack.get('style', 'corporate')

    # Show resolved patterns directory for debugging
    from pathlib import Path
    import pattern_manager as _pm
    _patterns_dir = Path(_pm.__file__).parent.parent / 'Patterns'
    print(f"  Patterns dir: {_patterns_dir}")
    print(f"  React patterns exist: {(_patterns_dir / 'Javascript' / 'React').exists()}")
    print(f"\n{'='*60}")
    print(f"  GENERATING FRONTEND")
    print(f"  Project: {project_name}  |  Style: {style}")
    print(f"  Resources: {', '.join(r['name'] for r in resources)}")
    print('='*60)

    # Pass 1: static files
    _generate_static(project_name, style, resources)

    # App.jsx (no LLM, but depends on resource list)
    _generate_app(style, resources)

    # Pass 2: per-resource LLM files
    print("\n  — LLM-driven resource files —")
    for r in resources:
        schema = extract_table_from_schema(r['name'])
        _generate_resource_files(r['name'], schema, style)

    print(f"\n{'='*60}")
    print(f"  ✅ Frontend generation complete")
    print('='*60)