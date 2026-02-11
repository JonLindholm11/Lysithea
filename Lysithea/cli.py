# lysithea/cli.py
"""
Main CLI entry point for Lysithea code generator
"""

from coordinator import coordinator_agent
from generator import execute_sequential_generation, generate_middleware
from pattern_manager import list_available_patterns

def main():
    print("Lysithea v0.2.0 - Sequential Pattern Generation")
    print("\nCommands:")
    print("  /pattern   - Toggle pattern mode ON/OFF")
    print("  /list      - List available patterns")
    print("  /status    - Show current mode")
    print("  quit       - Exit")
    print("-" * 50)
    
    use_pattern = False
    
    while True:
        mode = "[PATTERN]" if use_pattern else "[BASELINE]"
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
            print(f"Pattern mode: {'ON' if use_pattern else 'OFF'}")
            continue
            
        try:
            response = get_response(user_input, use_pattern)
            print(f"\n{response}\n")
        except Exception as e:
            print(f"Error: {e}")
            print("Make sure Ollama is running")

def get_response(user_input, use_pattern=False):
    """Get response from Ollama with optional pattern coordination"""
    
    if use_pattern:
        # Use coordinator agent to break down request
        result = coordinator_agent(user_input)
        
        if result:
            # Separate resources from middleware
            resources = result.get('resources', [])
            middleware = result.get('middleware', [])
            
            # Generate resources (if any)
            for resource_data in resources:
                resource_name = resource_data['name']
                operations = resource_data['operations']
                execute_sequential_generation(resource_name, operations)
            
            # Generate middleware (if any)
            for middleware_name in middleware:
                generate_middleware(middleware_name)
            
            # Build completion message
            generated = []
            if resources:
                generated.append(f"{len(resources)} resource(s)")
            if middleware:
                generated.append(f"{len(middleware)} middleware")
            
            return f"\n✅ Generation complete: {', '.join(generated)}"
        else:
            print("[Coordinator could not parse request - falling back to baseline]")
    
    # Baseline mode (no patterns)
    import ollama
    
    prompt = f"""You are a helpful coding assistant.

USER REQUEST: {user_input}

Generate the code and explain your decisions.
"""
    
    try:
        response = ollama.generate(
            model='llama3.1:8b',
            prompt=prompt
        )
        
        return response['response']
    except Exception as e:
        return f"Error generating response: {e}"

if __name__ == "__main__":
    main()