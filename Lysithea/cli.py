# lysithea/cli.py
"""
Main CLI entry point for Lysithea code generator
"""

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


def main():
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
            # Rule of Law violations surface here with clear messages
            print(str(e))
        except Exception as e:
            print(f"Error: {e}")
            print("Make sure Ollama is running")


def get_response(user_input, use_pattern=False):
    """Get response from Ollama with optional pattern coordination."""

    if use_pattern:
        result = coordinator_agent(user_input)  # writes functions.json
        plan_stack_from_prompt()                # writes stack.json

        if result:
            resources  = result.get('resources', [])
            middleware = result.get('middleware', [])
            database   = result.get('database', [])
            schema     = result.get('schema', [])

            # Schema FIRST — writes .lysithea/schema.sql
            if schema:
                generate_schema()

            # Seeds and queries — read schema from file_manager (hard fail if missing)
            for resource_data in resources:
                resource_name = resource_data['name']
                generate_seeds(resource_name)
                generate_queries(resource_name)

            # Database connection
            for db_item in database:
                generate_database(db_item)

            # Middleware
            for mw in middleware:
                generate_middleware(mw)

            # Routes — read schema + queries from file_manager
            for resource_data in resources:
                execute_sequential_generation(resource_data['name'])

            generated = []
            if schema:
                generated.append(f"{len(schema)} schema")
            if resources:
                generated.append(f"{len(resources)} resource(s)")
            if middleware:
                generated.append(f"{len(middleware)} middleware")
            if database:
                generated.append(f"{len(database)} database")

            return f"\n✅ Generation complete: {', '.join(generated)}"
        else:
            print("[Coordinator could not parse request — falling back to baseline]")

    # Baseline mode
    import ollama
    try:
        response = ollama.generate(
            model='llama3.1:8b',
            prompt=f"You are a helpful coding assistant.\n\nUSER REQUEST: {user_input}\n\nGenerate the code and explain your decisions.",
        )
        return response['response']
    except Exception as e:
        return f"Error generating response: {e}"


if __name__ == "__main__":
    main()