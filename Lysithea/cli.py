# lysithea/cli.py
"""
Main CLI entry point for Lysithea code generator.

Usage:
  python cli.py                        — interactive generation mode
  python cli.py --fix "prompt"         — fix agent (searches cwd)
  python cli.py --fix "prompt" --path ./my-project
  lysithea --fix "prompt"              — after: pip install -e .
  lysithea --fix "prompt" --path ./my-project
"""

import argparse
import sys
import os


# ─── Fix agent CLI output ─────────────────────────────────────────────────────

def run_fix_cli(prompt: str, path: str, side: str = 'auto'):
    """Run the fix agent and handle y/n confirmation in the terminal."""
    from audit.fix_agent import run_fix_agent, apply_fix

    result = run_fix_agent(prompt, path, side=side)

    if not result:
        print("\n[Lysithea] Fix agent could not locate the function. "
              "Try being more specific or check that --path is correct.")
        sys.exit(1)

    sep = "─" * 60

    # ── Needs more info ───────────────────────────────────────────────────────
    if result.get('needs_more_info'):
        print(f"\n{sep}")
        print(f"  LYSITHEA FIX AGENT — More Info Needed")
        print(sep)
        print(f"\n  ℹ  {result['reason']}")
        candidates = result.get('candidates', [])
        if candidates:
            print(f"\n  Possible matches:")
            for f in candidates:
                print(f"    • {f}")
        print(f"\n{sep}")
        sys.exit(0)

    # ── No bug found ──────────────────────────────────────────────────────────
    if result.get('no_bug'):
        print(f"\n{sep}")
        print(f"  LYSITHEA FIX AGENT — No Issue Found")
        print(sep)
        print(f"\n  ✅ {result['diagnosis']}")
        print(f"\n  File  : {result['file']}")
        print(f"  Lines : {result['start_line']}–{result['end_line']}")
        print(f"\n{sep}")
        sys.exit(0)

    # ── Fix proposed ──────────────────────────────────────────────────────────
    print(f"\n{sep}")
    print(f"  LYSITHEA FIX AGENT")
    print(sep)
    print(f"  Pattern : {result['pattern_name']}")
    if result.get('pattern_logic'):
        print(f"  Logic   : {result['pattern_logic']}")
    print(f"  File    : {result['file']}")
    print(f"  Lines   : {result['start_line']}–{result['end_line']}")
    print(sep)
    print(f"\n  ⚠  Issue Diagnosed:")
    print(f"     {result['diagnosis']}")
    print(f"\n  ✦  Proposed Fix:")
    print()

    for line in result['fixed_block'].splitlines():
        print(f"    {line}")

    print(f"\n{sep}")

    # ── y/n confirmation ─────────────────────────────────────────────────────
    while True:
        try:
            answer = input("\n  Apply this fix? [y/n] > ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\n  Cancelled.")
            sys.exit(0)

        if answer in ('y', 'yes'):
            ok = apply_fix(
                result['file'],
                result['start_line'],
                result['end_line'],
                result['fixed_block'],
            )
            if ok:
                print(f"\n  ✅ Fix applied to {result['file']}")
            else:
                print("\n  ❌ Write failed. Check file permissions.")
            break
        elif answer in ('n', 'no'):
            print("\n  Fix discarded. No files changed.")
            break
        else:
            print("  Please enter y or n.")


# ─── Interactive generation mode ─────────────────────────────────────────────

def run_interactive():
    from coordinator import coordinator_agent
    from planners.stack_planner import plan_stack_from_prompt
    from generators import (
        execute_sequential_generation,
        generate_middleware,
        generate_database,
        generate_schema,
        generate_seeds,
        generate_queries,
    )
    from pattern_manager import list_available_patterns
    from file_manager import law_status, load_resources, extract_table_from_schema

    print("Lysithea v0.3.0 - Rule of Law Pattern Generation")
    print("\nCommands:")
    print("  /pattern   - Toggle pattern mode ON/OFF")
    print("  /list      - List available patterns")
    print("  /status    - Show current mode + law file status")
    print("  quit       - Exit")
    print("-" * 50)

    use_pattern = False

    while True:
        mode       = "[PATTERN]" if use_pattern else "[BASELINE]"
        user_input = input(f"\n{mode} > ")

        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break

        if user_input.lower() == '/pattern':
            use_pattern = not use_pattern
            print(f"Pattern mode: {'ON' if use_pattern else 'OFF'}")
            continue

        if user_input.lower() == '/list':
            patterns = list_available_patterns()
            if patterns:
                print("\nAvailable patterns:")
                for p in patterns:
                    print(f"  - {p}")
            else:
                print("No patterns found")
            continue

        if user_input.lower() == '/status':
            print(f"\nPattern mode: {'ON' if use_pattern else 'OFF'}")
            status = law_status()
            print("\n.lysithea/ law files:")
            for name, present in status.items():
                icon = "✅" if present else "❌"
                print(f"  {icon}  {name}")
            continue

        try:
            response = get_response(user_input, use_pattern)
            print(f"\n{response}\n")
        except RuntimeError as e:
            print(str(e))
        except Exception as e:
            print(f"Error: {e}")
            print("Make sure Ollama is running")


def get_response(user_input, use_pattern=False):
    """Get response from Ollama with optional pattern coordination."""
    from coordinator import coordinator_agent
    from planners.stack_planner import plan_stack_from_prompt
    from generators import (
        execute_sequential_generation,
        generate_middleware,
        generate_database,
        generate_schema,
        generate_seeds,
        generate_queries,
    )

    if use_pattern:
        result = coordinator_agent(user_input)
        plan_stack_from_prompt()

        if result:
            resources  = result.get('resources', [])
            middleware = result.get('middleware', [])
            database   = result.get('database', [])
            schema     = result.get('schema', [])

            if schema:
                generate_schema()

            for resource_data in resources:
                resource_name = resource_data['name']
                generate_seeds(resource_name)
                generate_queries(resource_name)

            for db_item in database:
                generate_database(db_item)

            for mw in middleware:
                generate_middleware(mw)

            for resource_data in resources:
                execute_sequential_generation(resource_data['name'])

            generated = []
            if schema:     generated.append(f"{len(schema)} schema")
            if resources:  generated.append(f"{len(resources)} resource(s)")
            if middleware: generated.append(f"{len(middleware)} middleware")
            if database:   generated.append(f"{len(database)} database")

            return f"\n✅ Generation complete: {', '.join(generated)}"
        else:
            print("[Coordinator could not parse request — falling back to baseline]")

    import ollama
    try:
        response = ollama.generate(
            model='llama3.1:8b',
            prompt=f"You are a helpful coding assistant.\n\nUSER REQUEST: {user_input}\n\nGenerate the code and explain your decisions.",
        )
        return response['response']
    except Exception as e:
        return f"Error generating response: {e}"


# ─── Entry point ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog='lysithea',
        description='Lysithea — AI-powered code scaffolding and audit tool'
    )
    parser.add_argument(
        '--fix', '-f',
        metavar='PROMPT',
        help='Audit and fix a function. Accepts natural language or a pasted error/stack trace.',
    )
    parser.add_argument(
        '--path', '-p',
        metavar='PATH',
        default=None,
        help='Path to the project directory to search (defaults to current working directory).',
    )

    parser.add_argument(
        '--side', '-s',
        metavar='SIDE',
        choices=['backend', 'frontend', 'auto'],
        default='auto',
        help='Which side to search: backend, frontend, or auto (default: auto).',
    )

    args = parser.parse_args()

    if args.fix:
        search_path = args.path or os.getcwd()
        search_path = os.path.abspath(search_path)
        run_fix_cli(args.fix, search_path, side=args.side)
    else:
        run_interactive()


if __name__ == "__main__":
    main()