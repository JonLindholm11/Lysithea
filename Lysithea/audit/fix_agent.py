# lysithea/audit/fix_agent.py
"""
Lysithea Fix Agent

Workflow:
  1. Parse prompt → extract explicit file/line hints + function identifier
  2. Grep search project (3-tier: PowerShell → Bash grep → Python regex)
  3. Score + rank hits against prompt context (file name, backend/frontend, resource)
  4. Extract full function block (upward walk handles routes, consts, object methods)
  5. Match to pattern via pattern_manager
  6. Generate fix (Ollama call #2, isolated context: function + pattern + prompt)
  7. Return structured result for CLI or GUI output
  8. On confirmation — surgically replace block in file
"""

import os
import re
import sys
import json
import subprocess
from pathlib import Path


# ─── Tier-1: PowerShell Select-String (native Windows) ───────────────────────

def _grep_powershell(pattern: str, search_path: str) -> list[dict]:
    cmd = [
        'powershell', '-NoProfile', '-Command',
        f"Select-String -Path '{search_path}\\*' -Pattern '{pattern}' -Recurse "
        f"-Include '*.js','*.jsx','*.ts','*.py' | "
        f"ForEach-Object {{ $_.Path + ':' + $_.LineNumber + ':' + $_.Line }}"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15, shell=False)
        return _parse_grep_output(result.stdout)
    except Exception:
        return []


# ─── Tier-2: Bash grep ────────────────────────────────────────────────────────

def _grep_bash(pattern: str, search_path: str) -> list[dict]:
    cmd = ['grep', '-rn', '--include=*.js', '--include=*.jsx',
           '--include=*.ts', '--include=*.py', pattern, search_path]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15, shell=False)
        if result.returncode not in (0, 1):
            result = subprocess.run(
                ['bash', '-c',
                 f"grep -rn --include='*.js' --include='*.jsx' "
                 f"--include='*.ts' --include='*.py' '{pattern}' '{search_path}'"],
                capture_output=True, text=True, timeout=15
            )
        return _parse_grep_output(result.stdout)
    except Exception:
        return []


# ─── Tier-3: Python regex fallback ───────────────────────────────────────────

def _grep_python(pattern: str, search_path: str) -> list[dict]:
    results = []
    exts = {'.js', '.jsx', '.ts', '.tsx', '.py'}
    search_root = Path(search_path)

    try:
        compiled = re.compile(re.escape(pattern), re.IGNORECASE)
    except re.error:
        compiled = re.compile(pattern, re.IGNORECASE)

    for filepath in search_root.rglob('*'):
        if filepath.suffix not in exts:
            continue
        if any(part.startswith('.') or part in ('node_modules', '__pycache__', 'dist', 'build')
               for part in filepath.parts):
            continue
        try:
            lines = filepath.read_text(encoding='utf-8', errors='ignore').splitlines()
            for i, line in enumerate(lines, 1):
                if compiled.search(line):
                    results.append({
                        'file': str(filepath),
                        'line_number': i,
                        'line_text': line.strip(),
                    })
        except Exception:
            continue
    return results


def _parse_grep_output(raw: str) -> list[dict]:
    results = []
    for line in raw.strip().splitlines():
        parts = line.split(':', 2)
        if len(parts) >= 3:
            try:
                results.append({
                    'file': parts[0].strip(),
                    'line_number': int(parts[1].strip()),
                    'line_text': parts[2].strip(),
                })
            except ValueError:
                continue
    return results


# ─── 3-tier grep dispatcher ───────────────────────────────────────────────────

def smart_grep(pattern: str, search_path: str) -> list[dict]:
    print(f"[fix_agent] Searching for '{pattern}' in {search_path}...")

    results = _grep_powershell(pattern, search_path)
    if results:
        print(f"[fix_agent] Found {len(results)} match(es) via PowerShell")
        return results

    results = _grep_bash(pattern, search_path)
    if results:
        print(f"[fix_agent] Found {len(results)} match(es) via grep")
        return results

    results = _grep_python(pattern, search_path)
    if results:
        print(f"[fix_agent] Found {len(results)} match(es) via Python search")
        return results

    print("[fix_agent] No matches found")
    return []


# ─── Prompt parser — extract explicit hints before grepping ──────────────────

def parse_prompt_hints(prompt: str, side: str = 'auto') -> dict:
    """
    Extract explicit file/line hints and context signals from the prompt.
    `side` is the hard user-selected override: 'backend' | 'frontend' | 'auto'.
    """
    p = prompt.lower()

    # ── Explicit line number ─────────────────────────────────────────────────
    line_match = re.search(r'\bline\s+(\d+)\b', p)
    explicit_line = int(line_match.group(1)) if line_match else None

    # ── Explicit filename ────────────────────────────────────────────────────
    file_match = re.search(r'\b([\w\-]+\.(js|jsx|ts|tsx|py))\b', prompt, re.IGNORECASE)
    explicit_file = file_match.group(1) if file_match else None

    # ── Backend / frontend preference ────────────────────────────────────────
    # Hard override from user selection takes priority over prompt keywords
    if side == 'backend':
        prefer_backend  = True
        prefer_frontend = False
    elif side == 'frontend':
        prefer_backend  = False
        prefer_frontend = True
    else:
        # Auto: infer from prompt keywords
        backend_keywords  = ('backend', 'route', 'routes', 'server', 'express',
                             'controller', 'middleware', 'endpoint')
        frontend_keywords = ('frontend', 'client', 'react', 'component', 'page', 'ui')
        prefer_backend  = any(kw in p for kw in backend_keywords)
        prefer_frontend = any(kw in p for kw in frontend_keywords) and not prefer_backend

    # ── Resource name ─────────────────────────────────────────────────────────
    # Longer/more specific names first so 'post' (HTTP method) doesn't shadow
    # resource nouns like 'users', 'products'. Also skip matches that are clearly
    # HTTP method words by requiring them not to be preceded by 'route' context.
    resource_match = re.search(
        r'\b(customers?|permissions?|articles?|messages?|comments?|products?|'
        r'sessions?|orders?|roles?|items?|users?)\b', p
    )
    resource_name = resource_match.group(1).rstrip('s') if resource_match else None

    return {
        'explicit_file':   explicit_file,
        'explicit_line':   explicit_line,
        'prefer_backend':  prefer_backend,
        'prefer_frontend': prefer_frontend,
        'resource_name':   resource_name,
        'side':            side,
    }


# ─── Hit scorer — rank grep results against prompt context ───────────────────

def score_hit(hit: dict, hints: dict) -> int:
    """
    Score a single grep hit against the extracted prompt hints.
    Higher score = better match. Used to rank multiple grep results.
    """
    score = 0
    file_lower = hit['file'].replace('\\', '/').lower()
    file_name  = Path(hit['file']).name.lower()

    # ── Baseline: route files always preferred over api-client files ─────────
    # A file sitting in a routes/ or controllers/ dir is almost always where
    # the real bug lives. A *.api.js or *.service.js file is a frontend wrapper.
    in_routes_dir     = any(f'/{d}/' in file_lower for d in ('routes', 'controllers', 'middleware'))
    is_api_client_ext = bool(re.search(r'\.(api|service|client|request)\.(js|ts|jsx|tsx)$', file_name))
    in_frontend_dir   = any(f'/{d}/' in file_lower for d in ('frontend', 'client', 'src/api',
                                                               'src/pages', 'src/components',
                                                               'src/hooks'))

    if in_routes_dir:
        score += 40     # strong baseline for actual route files
    if is_api_client_ext:
        score -= 30     # penalty for frontend api wrapper files
    if in_frontend_dir and not in_routes_dir:
        score -= 15     # general frontend directory penalty

    # ── Explicit filename match (strongest signal) ───────────────────────────
    if hints['explicit_file']:
        hint_file = hints['explicit_file'].lower()
        if file_name == hint_file:
            score += 100          # exact filename match
        elif hint_file.split('.')[0] in file_name:
            score += 50           # partial name match (users in users.routes.js)

    # ── Explicit line number proximity ───────────────────────────────────────
    if hints['explicit_line']:
        distance = abs(hit['line_number'] - hints['explicit_line'])
        if distance == 0:
            score += 80
        elif distance <= 5:
            score += 40
        elif distance <= 20:
            score += 10

    # ── Backend/frontend keyword preference from prompt ───────────────────────
    # Use tighter path segments so '/src/api/' doesn't get the backend bonus
    strict_backend_dirs  = ('/routes/', '/controllers/', '/backend/', '/server/', '/middleware/')
    strict_frontend_dirs = ('/frontend/', '/client/', '/src/api/', '/src/pages/',
                            '/src/components/', '/src/hooks/')

    if hints['prefer_backend']:
        if any(d in file_lower for d in strict_backend_dirs):
            score += 30
        if any(d in file_lower for d in strict_frontend_dirs):
            score -= 20

    if hints['prefer_frontend']:
        if any(d in file_lower for d in strict_frontend_dirs):
            score += 30
        if any(d in file_lower for d in strict_backend_dirs):
            score -= 20

    # ── Resource name in filename ────────────────────────────────────────────
    if hints['resource_name'] and hints['resource_name'] in file_name:
        score += 20

    # ── Prefer non-test, non-spec files ──────────────────────────────────────
    if any(x in file_lower for x in ('.test.', '.spec.', '__tests__', '/test/')):
        score -= 15

    # ── Penalise middleware — unlikely to be where a resource route bug lives ─
    if '/middleware/' in file_lower:
        score -= 25

    return score


def _hit_is_route_handler(hit: dict) -> bool:
    """Return True if the hit line itself looks like a route declaration."""
    line = hit.get('line_text', '').strip()
    return bool(re.match(r'router\.(get|post|put|delete|patch|use)\s*\(', line, re.IGNORECASE))


def select_best_hit(hits: list[dict], hints: dict) -> dict:
    """
    Score all hits and return the highest-scoring one, or a needs_more_info
    sentinel if the top score is too low to be confident.

    Confidence thresholds:
      - Score < 20  : not enough signal at all → needs_more_info
      - Top two hits are within 10 points AND in different files → ambiguous → needs_more_info

    Returns either a normal hit dict or:
        { 'needs_more_info': True, 'reason': str, 'candidates': [file, ...] }
    """
    if len(hits) == 1:
        s = score_hit(hits[0], hints)
        if s < 20:
            return {
                'needs_more_info': True,
                'reason': 'Only one match found but confidence is too low. Try adding a filename or line number.',
                'candidates': [hits[0]['file']],
            }
        return hits[0]

    def sort_key(h):
        base  = score_hit(h, hints)
        bonus = 10 if _hit_is_route_handler(h) else 0
        return (base + bonus, _hit_is_route_handler(h))

    scored = sorted(hits, key=sort_key, reverse=True)

    top       = scored[0]
    top_score = score_hit(top, hints) + (10 if _hit_is_route_handler(top) else 0)

    print(f"[fix_agent] Ranking {len(scored)} hit(s):")
    for i, h in enumerate(scored[:5]):
        s = score_hit(h, hints) + (10 if _hit_is_route_handler(h) else 0)
        marker    = '→' if i == 0 else ' '
        route_tag = ' [route]' if _hit_is_route_handler(h) else ''
        print(f"[fix_agent]   {marker} [{s:+d}] {h['file']} line {h['line_number']}{route_tag}")

    # ── Confidence checks ─────────────────────────────────────────────────────
    if top_score < 20:
        # No meaningful signal — too risky to guess
        unique_files = list(dict.fromkeys(h['file'] for h in scored[:5]))
        return {
            'needs_more_info': True,
            'reason': (
                'Not enough context to confidently identify the right file. '
                'Try adding the filename, line number, or which resource is affected.'
            ),
            'candidates': unique_files,
        }

    second       = scored[1]
    second_score = score_hit(second, hints) + (10 if _hit_is_route_handler(second) else 0)

    # Collect all hits within 10 points of the top score
    top_group = [
        h for h in scored
        if (score_hit(h, hints) + (10 if _hit_is_route_handler(h) else 0)) >= top_score - 10
    ]
    unique_files_in_group = list(dict.fromkeys(h['file'] for h in top_group))

    if len(unique_files_in_group) > 1:
        # Multiple different files are equally likely — ask for clarification
        return {
            'needs_more_info': True,
            'reason': (
                f'Multiple files are equally likely matches. '
                f'Could you clarify which file or resource is affected?'
            ),
            'candidates': unique_files_in_group[:4],
        }

    return top


# ─── Function block extractor ─────────────────────────────────────────────────

def extract_function_block(file_path: str, hit_line: int) -> dict | None:
    """
    Extract the full function block around hit_line.

    Handles three JS patterns:
      1. router.get('/users', auth, async (req, res) => { ... })
      2. const getUsers = async (req, res) => { ... }
      3. Object method shorthand inside an object literal:
             export const usersApi = {
               getById: (id) => client.get(`/users/${id}`),   ← hit
             }
         For this case we walk up to the object declaration so the full
         object is captured, giving the LLM full context.

    Uses brace-depth + paren-depth counting to find the closing boundary.
    """
    try:
        content = Path(file_path).read_text(encoding='utf-8', errors='ignore')
        lines   = content.splitlines()
    except Exception as e:
        print(f"[fix_agent] Could not read {file_path}: {e}")
        return None

    total   = len(lines)
    hit_idx = hit_line - 1  # convert to 0-based

    # ── Step 1: Walk upward ───────────────────────────────────────────────────
    # We look back up to 20 lines (extended from 10 to catch object declarations).
    start_idx = hit_idx
    for i in range(hit_idx, max(hit_idx - 20, -1), -1):
        line = lines[i].strip()

        is_route   = re.match(r'router\.(get|post|put|delete|patch|use)\s*\(', line, re.IGNORECASE)
        is_const   = re.match(r'(const|let|var|function|async\s+function)\s+\w+', line)
        is_export  = re.match(r'(module\.exports|export\s+(default\s+)?(const|function|async))', line)
        is_def     = re.match(r'def\s+\w+', line)  # Python

        # Object literal declaration: export const fooApi = { or const fooApi = {
        is_obj_decl = re.match(r'(export\s+)?(const|let|var)\s+\w+\s*=\s*\{', line)

        if is_route or is_const or is_export or is_def or is_obj_decl:
            start_idx = i
            break

    # ── Step 2: Walk forward with brace + paren depth counting ───────────────
    brace_depth = 0
    paren_depth = 0
    end_idx     = start_idx
    started     = False
    in_string   = False
    string_char = ''

    for i in range(start_idx, total):
        line = lines[i]
        j    = 0
        while j < len(line):
            ch = line[j]

            # Track string literals to avoid counting braces inside strings
            if in_string:
                if ch == '\\':
                    j += 2  # skip escaped char
                    continue
                if ch == string_char:
                    in_string = False
            else:
                if ch in ('"', "'", '`'):
                    in_string   = True
                    string_char = ch
                elif ch == '{':
                    brace_depth += 1
                    started      = True
                elif ch == '}':
                    brace_depth -= 1
                elif ch == '(':
                    paren_depth += 1
                    started      = True
                elif ch == ')':
                    paren_depth -= 1

            j += 1

        # Block is closed when both depths return to 0 after having opened
        if started and brace_depth <= 0 and paren_depth <= 0:
            end_idx = i
            break
    else:
        end_idx = min(start_idx + 80, total - 1)

    block = '\n'.join(lines[start_idx:end_idx + 1])
    return {
        'file':       file_path,
        'start_line': start_idx + 1,
        'end_line':   end_idx   + 1,
        'block':      block,
    }


# ─── File type classifier ────────────────────────────────────────────────────

def _classify_file_type(file_path: str, function_block: str) -> str:
    """
    Classify what kind of file we're looking at so we can choose the right
    prompt strategy and skip irrelevant pattern lookups.

    Returns one of:
        'express_route'     — backend Express router handler
        'api_client'        — frontend axios/fetch wrapper (e.g. usersApi = {...})
        'react_component'   — React component or hook
        'python_route'      — FastAPI / Django view
        'unknown'
    """
    fp    = file_path.replace('\\', '/').lower()
    fname = Path(file_path).name.lower()
    block = function_block.lower()

    # ── Express route ─────────────────────────────────────────────────────────
    if re.search(r'router\.(get|post|put|delete|patch)', block):
        return 'express_route'
    if any(seg in fp for seg in ('/routes/', '/controllers/', '/middleware/')):
        return 'express_route'

    # ── Frontend API client ───────────────────────────────────────────────────
    # Matches: usersApi = {}, client.get(), axios.get(), fetch(
    is_api_object = re.search(r'\w+api\s*=\s*\{', block)
    is_client_call = re.search(r'\bclient\.(get|post|put|delete|patch)\b', block)
    is_axios_call  = re.search(r'\baxios\.(get|post|put|delete|patch)\b', block)
    is_fetch_call  = re.search(r'\bfetch\s*\(', block)
    in_api_dir     = any(seg in fp for seg in ('/api/', '/services/', '/requests/'))
    has_api_suffix = re.search(r'\.(api|service|client|request)\.(js|ts|jsx|tsx)$', fname)

    if is_api_object or is_client_call or is_axios_call or is_fetch_call:
        if in_api_dir or has_api_suffix:
            return 'api_client'

    # ── React component / hook ────────────────────────────────────────────────
    if re.search(r'use[A-Z]\w+|useState|useEffect|useQuery|useMutation', block):
        return 'react_component'
    if any(seg in fp for seg in ('/components/', '/pages/', '/hooks/')):
        return 'react_component'

    # ── Python route ─────────────────────────────────────────────────────────
    if re.search(r'@(app|router)\.(get|post|put|delete)', block):
        return 'python_route'
    if re.search(r'def\s+\w+.*request', block):
        return 'python_route'

    return 'unknown'


# ─── Pattern matcher ─────────────────────────────────────────────────────────

def _infer_stack_from_file(file_path: str) -> dict:
    ext = Path(file_path).suffix.lower()
    if ext in ('.js', '.jsx', '.ts', '.tsx'):
        return {'language': 'javascript', 'framework': 'express',
                'language_dir': 'Javascript', 'framework_dir': 'Express'}
    if ext == '.py':
        return {'language': 'python', 'framework': 'fastapi',
                'language_dir': 'Python', 'framework_dir': 'FastAPI'}
    return {'language': 'javascript', 'framework': 'express',
            'language_dir': 'Javascript', 'framework_dir': 'Express'}


def _load_pattern_content(project_path: str, file_path: str, function_block: str) -> dict:
    file_type = _classify_file_type(file_path, function_block)
    print(f"[fix_agent] File type: {file_type}")

    # ── Frontend files: no pattern needed, use type-specific LLM prompt ──────
    if file_type in ('api_client', 'react_component'):
        return {
            'pattern_name':    file_type,
            'pattern_content': '',
            'file_type':       file_type,
        }

    # ── Backend: attempt pattern_manager first, then fallback scan ───────────
    lysithea_pkg    = _find_lysithea_pkg(project_path)
    pattern_content = None
    pattern_name    = None

    if lysithea_pkg:
        sys.path.insert(0, str(lysithea_pkg))
        try:
            import pattern_manager as pm
            try:
                stack = pm.get_stack_info()
            except Exception:
                stack = _infer_stack_from_file(file_path)

            op           = _detect_operation(function_block)
            pattern_path = pm.map_operation_to_pattern(op, stack)

            if pattern_path:
                pattern_content = pm.load_pattern(pattern_path)
                pattern_name    = pattern_path
        except Exception as e:
            print(f"[fix_agent] Pattern manager unavailable: {e}")
        finally:
            if str(lysithea_pkg) in sys.path:
                sys.path.remove(str(lysithea_pkg))

    if not pattern_content:
        pattern_name, pattern_content = _fallback_pattern_scan(project_path, function_block)

    return {
        'pattern_name':    pattern_name or 'no pattern matched',
        'pattern_content': pattern_content or '',
        'file_type':       file_type,
    }


def _detect_operation(block: str) -> str:
    b = block.lower()
    if re.search(r'router\.get|async.*get.*all|select.*from', b):
        if re.search(r'by.id|where.*id|req\.params', b):
            return 'get by id'
        return 'get all'
    if re.search(r'router\.post|insert into|\.create\(', b):
        return 'post'
    if re.search(r'router\.put|router\.patch|update.*set|\.update\(', b):
        return 'put'
    if re.search(r'router\.delete|delete from|\.destroy\(', b):
        return 'delete'
    # Frontend API client — GET by ID shape
    if re.search(r'client\.(get|post|put|delete|patch)', b):
        if re.search(r'\$\{.*id\}|/\:id|byId', b):
            return 'get by id'
        return 'get all'
    return 'get all'


def _fallback_pattern_scan(project_path: str, function_block: str) -> tuple[str, str]:
    op     = _detect_operation(function_block)
    op_map = {
        'get all':   'get-users-auth.js',
        'get by id': 'get-users-by-id-auth.js',
        'post':      'post-users-auth.js',
        'put':       'put-users-auth.js',
        'delete':    'delete-users-auth.js',
    }
    target = op_map.get(op, 'get-users-auth.js')

    check = Path(project_path)
    for _ in range(6):
        patterns_dir = check / 'Patterns'
        if patterns_dir.exists():
            for f in patterns_dir.rglob(target):
                try:
                    return str(f.relative_to(patterns_dir)), f.read_text(encoding='utf-8')
                except Exception:
                    pass
        check = check.parent

    return '', ''


def _find_lysithea_pkg(project_path: str) -> Path | None:
    check = Path(project_path)
    for _ in range(6):
        for name in ('Lysithea', 'lysithea'):
            candidate = check / name
            if (candidate / 'pattern_manager.py').exists():
                return candidate
        check = check.parent
    return None


# ─── Ollama helpers ───────────────────────────────────────────────────────────

def _ollama_call(prompt: str, system: str = '', num_predict: int = 2048) -> str:
    try:
        import ollama
        messages = []
        if system:
            messages.append({'role': 'system', 'content': system})
        messages.append({'role': 'user', 'content': prompt})
        response = ollama.chat(
            model='llama3.1:8b',
            messages=messages,
            options={'temperature': 0.1, 'num_predict': num_predict},
        )
        return response['message']['content'].strip()
    except ImportError:
        raise RuntimeError("[fix_agent] ollama package not installed. Run: pip install ollama")
    except Exception as e:
        raise RuntimeError(f"[fix_agent] Ollama error: {e}")


# ─── Call #1: Extract grep candidates from prompt ────────────────────────────

def extract_grep_candidates(prompt: str, hints: dict) -> list[str]:
    """
    Return an ordered list of grep search terms to try, from most specific
    to most general. We try multiple candidates so that if the first doesn't
    find the right file, the next one might.

    For backend prompts describing conceptual operations like "get by id",
    we include both the camelCase name AND the route pattern (/:id) because
    Express routes don't contain identifiers like 'getById' — they contain
    router.get('/:id', ...).

    Returns e.g. ['getUserById', '/:id', 'router.get'] ordered by specificity.
    """
    system = (
        "You extract search terms from developer bug reports. "
        "Given a prompt, return the most useful grep search terms to find the "
        "relevant code in a project. "
        "Reply ONLY with a JSON array of strings — most specific first. "
        "Include the camelCase function name if mentioned, and for route handlers "
        "also include the URL pattern (e.g. '/:id'). "
        "IMPORTANT route URL conventions for Express.js: "
        "  GET all      → router.get('/', ...)       — URL is just '/' "
        "  GET by id    → router.get('/:id', ...)    — URL is '/:id' "
        "  POST create  → router.post('/', ...)      — URL is just '/' "
        "  PUT update   → router.put('/:id', ...)    — URL is '/:id' "
        "  PATCH update → router.patch('/:id', ...)  — URL is '/:id' "
        "  DELETE       → router.delete('/:id', ...) — URL is '/:id' "
        "Maximum 4 terms. Do NOT include resource names like 'users', 'products', 'orders' — "
        "use route patterns and method names only. No explanation, no markdown."
    )

    side_hint = ''
    if hints.get('prefer_backend'):
        side_hint = 'This is a backend/Express.js project. Include route patterns like /:id if relevant.\n'
    elif hints.get('prefer_frontend'):
        side_hint = 'This is a frontend project.\n'

    user = (
        f"{side_hint}"
        f"Prompt: {prompt}\n\n"
        f"Return a JSON array of grep search strings. Example: [\"getUserById\", \"/:id\"]"
    )

    raw = _ollama_call(user, system, num_predict=128)
    raw = re.sub(r'^```[a-z]*\n?', '', raw.strip())
    raw = re.sub(r'\n?```$',       '', raw.strip())

    candidates = []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            candidates = [str(c).strip() for c in parsed if c and str(c).strip()]
    except (json.JSONDecodeError, Exception):
        # Fall back to extracting a single camelCase name from the raw text
        name = re.sub(r'[^a-zA-Z0-9_$]', '', raw.split('\n')[0].strip())
        if name:
            candidates = [name]

    # Deduplicate preserving order
    seen = set()
    result = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            result.append(c)

    print(f"[fix_agent] Grep candidates: {result}")
    return result


# ─── Static analysis helpers ─────────────────────────────────────────────────

def _find_undeclared_variables(block: str) -> list[str]:
    """
    Fast static scan: find JS identifiers that are used but never declared
    within the block. Catches the classic 'missing query assignment' bug where
    `user` is referenced but `const user = await ...` was removed.

    Returns a list of undeclared identifier names, empty if none found.
    Only reports names that are likely local variables (lowercase, not keywords,
    not globals), filtering out string content by blanking quoted sections.
    """
    # ── Strip string literals so we don't flag words inside them ─────────────
    def blank_strings(s: str) -> str:
        """Replace content inside quotes with underscores, preserving length."""
        result = []
        i = 0
        while i < len(s):
            ch = s[i]
            if ch in ('"', "'", '`'):
                quote = ch
                result.append(ch)
                i += 1
                while i < len(s):
                    c = s[i]
                    if c == '\\':
                        result.append('__')
                        i += 2
                        continue
                    if c == quote:
                        result.append(c)
                        i += 1
                        break
                    result.append('_')
                    i += 1
            else:
                result.append(ch)
                i += 1
        return ''.join(result)

    clean_block = blank_strings(block)
    lines       = block.splitlines()
    clean_lines = clean_block.splitlines()

    # ── Collect declared names from clean block ───────────────────────────────
    declared = set()

    for m in re.finditer(r'\b(?:const|let|var)\s+(?:\{([^}]+)\}|(\w+))', clean_block):
        if m.group(1):
            for part in m.group(1).split(','):
                name = part.strip().split(':')[0].strip()
                if re.match(r'^[a-zA-Z_$]\w*$', name):
                    declared.add(name)
        elif m.group(2):
            declared.add(m.group(2))

    # function/arrow parameters: (req, res), (id, data), async (req, res)
    for m in re.finditer(r'\(([^)]*)\)', clean_block):
        for part in m.group(1).split(','):
            name = re.sub(r'\s*=.*', '', part.strip())   # strip defaults
            name = re.sub(r'^\.\.\.', '', name)           # strip rest spread
            name = name.strip()
            if re.match(r'^[a-zA-Z_$]\w*$', name):
                declared.add(name)

    # catch (error)
    for m in re.finditer(r'\bcatch\s*\(\s*(\w+)\s*\)', clean_block):
        declared.add(m.group(1))

    # Common globals always in scope
    always_in_scope = {
        'req', 'res', 'next', 'console', 'process', 'JSON', 'Math',
        'parseInt', 'parseFloat', 'isNaN', 'isFinite', 'String', 'Number',
        'Boolean', 'Object', 'Array', 'Promise', 'Error', 'Date', 'Map',
        'Set', 'undefined', 'null', 'true', 'false', 'NaN', 'Infinity',
        'require', 'module', 'exports', '__dirname', '__filename',
        'setTimeout', 'clearTimeout', 'setInterval', 'clearInterval',
        'router', 'db', 'pool', 'client', 'authenticateToken',
    }
    declared |= always_in_scope

    JS_KEYWORDS = {
        'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'return',
        'throw', 'new', 'delete', 'typeof', 'void', 'instanceof', 'in',
        'of', 'try', 'catch', 'finally', 'async', 'await', 'import',
        'export', 'default', 'class', 'extends', 'super', 'this', 'static',
        'get', 'set', 'from', 'break', 'continue', 'const', 'let', 'var',
        'function', 'return', 'debugger', 'with', 'yield',
    }

    # ── Scan clean lines for usages ───────────────────────────────────────────
    undeclared = []
    usage_re   = re.compile(r'\b([a-z_$][a-zA-Z0-9_$]*)\b')  # lowercase-start only

    for clean_line in clean_lines:
        stripped = clean_line.strip()
        if stripped.startswith('//') or stripped.startswith('*'):
            continue
        # Skip pure declaration lines
        if re.match(r'\b(?:const|let|var|function|async\s+function)\b', stripped):
            continue

        for m in usage_re.finditer(stripped):
            name = m.group(1)
            if name in declared or name in JS_KEYWORDS:
                continue
            if len(name) <= 1:
                continue
            # Skip if immediately preceded by a dot (property access) or colon
            start = m.start()
            pre  = stripped[start - 1] if start > 0 else ' '
            post_idx = m.end()
            post = stripped[post_idx:post_idx + 1]
            if pre in ('.', ':'):
                continue
            if post == ':':
                continue   # object key — skip
            if name not in undeclared:
                undeclared.append(name)

    # Filter out any blanked string artefacts (all underscores)
    undeclared = [n for n in undeclared if not re.match(r'^_+$', n)]
    return undeclared


# ─── Call #1b: Pre-check — does the code actually have a bug? ────────────────

def check_for_bug(prompt: str, function_block: str, file_type: str) -> dict:
    """
    Two-stage check:
      1. Fast static scan for undeclared variables — catches missing query
         assignments without an LLM call.
      2. LLM yes/no check for everything else.

    Returns:
        { 'has_bug': bool, 'reason': str }
    """
    # ── Stage 1: Static undeclared variable scan ──────────────────────────────
    if file_type in ('express_route', 'python_route', 'unknown'):
        undeclared = _find_undeclared_variables(function_block)
        if undeclared:
            reason = (
                f"Variable(s) used but never declared in this block: "
                f"{', '.join(undeclared)}. A query or assignment is likely missing."
            )
            print(f"[fix_agent] Static check found undeclared: {undeclared}")
            return {'has_bug': True, 'reason': reason, 'static': True}

    # ── Stage 2: LLM reasoning check ─────────────────────────────────────────
    system = (
        "You are a code reviewer. Your job is to determine whether a specific bug "
        "exists in a code block. "
        "IMPORTANT: Only report a bug if you can point to a specific line that is wrong. "
        "Do NOT invent bugs or flag code that looks correct. "
        "If all variables are properly declared and assigned before use, say has_bug: false. "
        "Pay close attention to variables that are used but never assigned — this is "
        "a common bug where a database query or API call was accidentally removed. "
        "Reply ONLY with a JSON object with two keys: "
        "'has_bug' (boolean) and 'reason' (one sentence). "
        "No markdown, no explanation outside the JSON."
    )
    user = (
        f"DEVELOPER PROMPT / COMPLAINT:\n{prompt}\n\n"
        f"CODE TO CHECK:\n{function_block}\n\n"
        f"Does the code contain the bug described? "
        f"Check carefully for variables used before being assigned. "
        f"Reply ONLY with JSON: {{\"has_bug\": true/false, \"reason\": \"...\"}}"
    )

    raw = _ollama_call(user, system, num_predict=256)
    raw = re.sub(r'^```[a-z]*\n?', '', raw.strip())
    raw = re.sub(r'\n?```$',       '', raw.strip())

    try:
        parsed = json.loads(raw)
        has_bug = bool(parsed.get('has_bug', True))
        reason  = parsed.get('reason', '')
        return {'has_bug': has_bug, 'reason': reason}
    except (json.JSONDecodeError, Exception):
        return {'has_bug': True, 'reason': ''}



def generate_fix(prompt: str, function_block: str, pattern_content: str,
                 file_path: str = '', file_type: str = 'unknown') -> dict:
    """
    Fresh context window: function + pattern + original prompt → fix.
    System prompt is tailored to the file_type so the LLM doesn't invent
    irrelevant fixes (e.g. security advice for a plain API client).
    """

    # ── Type-specific system prompts ─────────────────────────────────────────
    if file_type == 'api_client':
        system = (
            "You are a senior frontend engineer reviewing a JavaScript API client module. "
            "These files contain a plain object with methods that call an HTTP client "
            "(axios, fetch, or a custom client wrapper). "
            "Common bugs in these files are: wrong URL path, wrong HTTP method, "
            "missing or wrong parameter in the URL template, wrong request body shape. "
            "Your job is to fix the specific bug described — do NOT add validation, "
            "error handling, or security logic that was not there before. "
            "Keep the same code style and object shape. "
            "IMPORTANT: The filename tells you the resource — do not rename resource paths. "
            "Reply ONLY with a JSON object — no markdown, no explanation outside the JSON."
        )
    elif file_type == 'react_component':
        system = (
            "You are a senior frontend engineer reviewing a React component or hook. "
            "Common bugs are: wrong dependency arrays, incorrect state updates, "
            "wrong API call being made, missing await, wrong data shape being read. "
            "Fix only the specific bug described. Keep the same component structure. "
            "Reply ONLY with a JSON object — no markdown, no explanation outside the JSON."
        )
    else:
        system = (
            "You are a senior backend engineer reviewing an Express.js route handler for bugs. "
            "Common bugs include: missing database query (variable used but never assigned via await), "
            "wrong SQL/query parameters, missing error handling, wrong status codes, "
            "wrong field names in the response object. "
            "If a variable like 'user', 'product', or 'result' is used but never assigned in the block, "
            "the fix is to add the missing query call before it is used — use the pattern as a reference "
            "for the correct query shape. "
            "IMPORTANT: The filename tells you the resource — do not change resource names. "
            "Fix only the actual bug described. "
            "Reply ONLY with a JSON object — no markdown, no explanation outside the JSON."
        )

    pattern_section = (
        f"REFERENCE PATTERN:\n{pattern_content}\n\n"
        if pattern_content
        else ''
    )

    file_context = f"FILE: {Path(file_path).name}\n" if file_path else ""

    user = (
        f"ORIGINAL PROMPT / ERROR:\n{prompt}\n\n"
        f"{file_context}"
        f"BROKEN FUNCTION:\n{function_block}\n\n"
        f"{pattern_section}"
        f"Return a JSON object with these exact keys:\n"
        f"  diagnosis     — one sentence describing the actual bug\n"
        f"  pattern_logic — one sentence describing what correct code looks like here\n"
        f"  fixed_block   — the complete corrected code as a string\n\n"
        f"JSON only, no markdown fences."
    )

    raw = _ollama_call(user, system, num_predict=2048)
    raw = re.sub(r'^```[a-z]*\n?', '', raw.strip())
    raw = re.sub(r'\n?```$',       '', raw.strip())

    try:
        parsed = json.loads(raw)
        return {
            'diagnosis':     parsed.get('diagnosis',     'No diagnosis provided'),
            'pattern_logic': parsed.get('pattern_logic', ''),
            'fixed_block':   parsed.get('fixed_block',   function_block),
        }
    except json.JSONDecodeError:
        code_match = re.search(r'```(?:js|javascript|python)?\n(.*?)```', raw, re.DOTALL)
        fixed = code_match.group(1).strip() if code_match else function_block
        return {
            'diagnosis':     raw[:300],
            'pattern_logic': '',
            'fixed_block':   fixed,
        }


# ─── File write — surgical replace ───────────────────────────────────────────

def apply_fix(file_path: str, start_line: int, end_line: int, fixed_block: str) -> bool:
    try:
        content  = Path(file_path).read_text(encoding='utf-8', errors='ignore')
        lines    = content.splitlines(keepends=True)
        before   = lines[:start_line - 1]
        after    = lines[end_line:]
        fixed_lines         = fixed_block.splitlines(keepends=False)
        fixed_with_newlines = [l + '\n' for l in fixed_lines]
        new_content = ''.join(before + fixed_with_newlines + after)
        Path(file_path).write_text(new_content, encoding='utf-8')
        print(f"[fix_agent] ✅ Fix applied to {file_path} (lines {start_line}–{end_line})")
        return True
    except Exception as e:
        print(f"[fix_agent] ❌ Failed to write fix: {e}")
        return False


# ─── Main pipeline ────────────────────────────────────────────────────────────

def run_fix_agent(prompt: str, search_path: str, side: str = 'auto') -> dict | None:
    """
    Full pipeline. Returns a result dict for CLI or GUI, or None on failure.
    side: 'backend' | 'frontend' | 'auto'
    """
    print(f"\n[fix_agent] ══════════════ Lysithea Fix Agent ══════════════")
    print(f"[fix_agent] Prompt : {prompt[:120]}")
    print(f"[fix_agent] Path   : {search_path}")
    print(f"[fix_agent] Side   : {side}")

    # ── Step 1: Parse prompt for explicit hints ───────────────────────────────
    hints = parse_prompt_hints(prompt, side=side)
    if hints['explicit_file']:
        print(f"[fix_agent] Hint — file: {hints['explicit_file']}")
    if hints['explicit_line']:
        print(f"[fix_agent] Hint — line: {hints['explicit_line']}")
    if hints['prefer_backend']:
        print(f"[fix_agent] Hint — context: backend")
    if hints['prefer_frontend']:
        print(f"[fix_agent] Hint — context: frontend")

    # ── Step 2: Extract grep candidates ──────────────────────────────────────
    candidates = extract_grep_candidates(prompt, hints)
    if not candidates:
        print("[fix_agent] Could not extract search terms from prompt.")
        return None

    # ── Step 3: Grep each candidate, collect and score all hits ──────────────
    # We run all candidates and pool the results so the scorer sees the full
    # picture — a route pattern hit in routes/users.js should beat a camelCase
    # hit in frontend/src/api/users.api.js even if found by a different term.
    all_hits = []
    seen_keys = set()  # deduplicate by file+line

    for candidate in candidates:
        hits = smart_grep(candidate, search_path)
        for h in hits:
            key = (h['file'], h['line_number'])
            if key not in seen_keys:
                seen_keys.add(key)
                all_hits.append(h)

    if not all_hits:
        print(f"[fix_agent] No matches found for any candidate. Try a more specific prompt.")
        return None

    print(f"[fix_agent] Total unique hits across all candidates: {len(all_hits)}")

    # ── Step 4: Score + select best hit ──────────────────────────────────────
    hit = select_best_hit(all_hits, hints)

    if hit.get('needs_more_info'):
        print(f"[fix_agent] Needs more info: {hit['reason']}")
        return {
            'needs_more_info': True,
            'reason':          hit['reason'],
            'candidates':      hit.get('candidates', []),
        }

    print(f"[fix_agent] Match  : {hit['file']} line {hit['line_number']}")

    # ── Step 5: Extract full function block ───────────────────────────────────
    fn_data = extract_function_block(hit['file'], hit['line_number'])
    if not fn_data:
        print("[fix_agent] Could not extract function block.")
        return None

    print(f"[fix_agent] Block  : lines {fn_data['start_line']}–{fn_data['end_line']} "
          f"({fn_data['end_line'] - fn_data['start_line'] + 1} lines)")

    # ── Step 6: Load pattern ──────────────────────────────────────────────────
    pattern_data = _load_pattern_content(search_path, hit['file'], fn_data['block'])
    print(f"[fix_agent] Pattern: {pattern_data['pattern_name']}")

    # ── Step 6b: Pre-check — does the bug actually exist? ────────────────────
    print(f"[fix_agent] Checking for bug presence...")
    bug_check = check_for_bug(prompt, fn_data['block'], pattern_data.get('file_type', 'unknown'))
    print(f"[fix_agent] Bug present: {bug_check['has_bug']} — {bug_check['reason']}")

    if not bug_check['has_bug']:
        print(f"[fix_agent] No bug detected — returning clean result.")
        return {
            'pattern_name':   pattern_data['pattern_name'],
            'pattern_logic':  '',
            'diagnosis':      bug_check['reason'] or 'Code looks correct for what it is meant to do.',
            'fixed_block':    fn_data['block'],   # unchanged
            'file':           fn_data['file'],
            'start_line':     fn_data['start_line'],
            'end_line':       fn_data['end_line'],
            'original_block': fn_data['block'],
            'no_bug':         True,
        }

    # ── Step 7: Generate fix (fresh context window) ───────────────────────────
    print(f"[fix_agent] Generating fix...")
    fix_data = generate_fix(
        prompt,
        fn_data['block'],
        pattern_data['pattern_content'],
        file_path=hit['file'],
        file_type=pattern_data.get('file_type', 'unknown'),
    )

    return {
        'pattern_name':   pattern_data['pattern_name'],
        'pattern_logic':  fix_data['pattern_logic'],
        'diagnosis':      fix_data['diagnosis'],
        'fixed_block':    fix_data['fixed_block'],
        'file':           fn_data['file'],
        'start_line':     fn_data['start_line'],
        'end_line':       fn_data['end_line'],
        'original_block': fn_data['block'],
    }