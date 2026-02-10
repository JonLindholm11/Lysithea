# cli.py

import ollama
from pathlib import Path

def load_pattern(pattern_path):
    """Load a pattern file"""
    full_path = Path('..') / 'patterns' / pattern_path
    if not full_path.exists():
        return None
    return full_path.read_text()

def list_available_patterns():
    """Get list of all available patterns (only used for /list command now)"""
    pattern_dir = Path('..') / 'patterns'
    if not pattern_dir.exists():
        return []
    
    patterns = []
    for pattern_file in pattern_dir.rglob('*.js'):
        relative_path = pattern_file.relative_to(pattern_dir)
        patterns.append(str(relative_path))
    
    return patterns

def select_pattern_with_ai(user_input):
    """Use AI to analyze request and suggest a pattern path, then verify it exists"""
    
    # Step 1: AI suggests a pattern path without seeing all files
    analysis_prompt = f"""You are a pattern selector for a code generator.

CRITICAL: You MUST respond with the COMPLETE relative path from the patterns/ directory.

Available pattern structures:
- javascript/express/routes/ (Express.js route patterns)
- javascript/express/middleware/ (Express.js middleware patterns)
- python/fastapi/routes/ (FastAPI route patterns)
- python/fastapi/middleware/ (FastAPI middleware patterns)

User request: "{user_input}"

Analyze the request and determine:
1. What language/framework is needed (javascript/express, python/fastapi, etc.)
2. What type of pattern (routes, middleware, models, etc.)
3. What specific file matches

You MUST respond with the FULL path including language and framework.

WRONG EXAMPLES:
- routes/users-get.js
- get-users-auth.js

CORRECT EXAMPLES:
- javascript/express/routes/get-users-auth.js
- python/fastapi/routes/get-users-auth.py

Format your response EXACTLY like this (no extra text):
ANALYSIS: [your reasoning including language/framework choice]
SUGGESTED_PATTERN: [FULL path like javascript/express/routes/get-users-auth.js]
"""
    
    print("\n[AI analyzing request...]")
    
    try:
        response = ollama.generate(
            model='llama3.1:8b',
            prompt=analysis_prompt
        )
        
        ai_response = response['response'].strip()
        print(f"\n{ai_response}\n")
        
        # Extract suggested pattern
        suggested_pattern = None
        for line in ai_response.split('\n'):
            if 'SUGGESTED_PATTERN:' in line:
                suggested_pattern = line.split('SUGGESTED_PATTERN:')[1].strip()
                break
        
        if not suggested_pattern or suggested_pattern == "NONE":
            print("[No pattern suggested]")
            return None
        
        # Step 2: Check if suggested pattern exists
        pattern_path = Path('..') / 'patterns' / suggested_pattern
        
        if not pattern_path.exists():
            print(f"[Pattern '{suggested_pattern}' does not exist]")
            
            # Show what DOES exist in that directory
            parent_dir = pattern_path.parent
            if parent_dir.exists():
                available = [f.name for f in parent_dir.glob('*.js')]
                if available:
                    print(f"Available in {parent_dir.relative_to(Path('..') / 'patterns')}/:")
                    for f in available:
                        print(f"  - {f}")
                    
                    # AI finds similar pattern to adapt
                    fallback_prompt = f"""The exact pattern '{suggested_pattern}' doesn't exist.

Available patterns in the same category:
{chr(10).join(f"- {f}" for f in available)}

User request: "{user_input}"

Which of these available patterns can be ADAPTED to fulfill the user's request?
Consider patterns that have similar structure (GET routes, authentication, etc.)

Respond with ONLY the filename that's most similar.
If none are suitable, respond with: NONE
"""
                    
                    print("\n[AI finding similar pattern to adapt...]")
                    fallback_response = ollama.generate(
                        model='llama3.1:8b',
                        prompt=fallback_prompt
                    )
                    
                    fallback_pattern = fallback_response['response'].strip()
                    print(f"AI suggests adapting: {fallback_pattern}")
                    
                    # Validate fallback pattern exists
                    for available_file in available:
                        if available_file in fallback_pattern or fallback_pattern in available_file:
                            approval = input(f"\nAdapt '{available_file}' for this request? (yes/no): ").strip().lower()
                            if approval == 'yes':
                                # Return the path relative to patterns/
                                return str(parent_dir.relative_to(Path('..') / 'patterns') / available_file)
                            else:
                                print("[Pattern adaptation rejected - using baseline]")
                                return None
            
            # Fallback to manual input
            approval = input("\nSpecify a different pattern or press Enter to skip: ").strip()
            if not approval:
                return None
            suggested_pattern = approval
        
        # Step 3: Ask user for approval (pattern exists)
        approval = input(f"Use pattern '{suggested_pattern}'? (yes/no/specify): ").strip().lower()
        
        if approval == 'no':
            print("[Pattern rejected - using baseline]")
            return None
        elif approval == 'yes':
            return suggested_pattern
        else:
            # User wants to specify manually
            manual_pattern = input("Enter pattern path (e.g., javascript/express/routes/get-users-auth.js): ").strip()
            manual_path = Path('..') / 'patterns' / manual_pattern
            
            if manual_path.exists():
                return manual_pattern
            else:
                print(f"[Pattern '{manual_pattern}' not found - using baseline]")
                return None
                
    except Exception as e:
        print(f"[Error in pattern selection: {e}]")
        return None

def get_response(user_input, use_pattern=False):
    """Get response from Ollama with optional pattern"""
    
    # Initialize prompt as None
    prompt = None
    
    if use_pattern:
        # AI selects the best pattern
        pattern_path = select_pattern_with_ai(user_input)
        
        if pattern_path:
            pattern = load_pattern(pattern_path)
            print(f"[Using pattern: {pattern_path}]")
            
            prompt = f"""You are generating production-ready code based on an existing pattern.

=== REFERENCE PATTERN (FOLLOW THIS STRUCTURE EXACTLY) ===
{pattern}
=== END PATTERN ===

USER REQUEST: {user_input}

INSTRUCTIONS:
1. Use the EXACT structure from the reference pattern above
2. Copy the error handling approach from the pattern
3. Copy the authentication/security implementation from the pattern
4. Adapt variable names and endpoint paths to match the user's request
5. Do NOT invent new middleware or controller structures - use what's in the pattern
6. Generate ONLY the production code - exclude all pattern documentation comments (/** ... */)
7. Include only inline comments that are essential to understanding the code

Your code should look structurally identical to the pattern, just adapted for: {user_input}

Output format:
1. First, generate the clean production-ready code in a code block
2. Then briefly explain (2-3 sentences) how it mirrors the pattern structure

Do NOT include:
- Pattern documentation headers (/** PATTERN: ... */)
- USE WHEN sections
- DEMONSTRATES sections
- USAGE EXAMPLE sections
- Any multi-line documentation comments from the pattern file
"""
        else:
            print("[No matching pattern found - using baseline]")
            prompt = f"""You are a helpful coding assistant.

USER REQUEST: {user_input}

Generate the code and explain:
- Why you structured it this way
- What you included and why
"""
    else:
        # Baseline - no pattern
        prompt = f"""You are a helpful coding assistant.

USER REQUEST: {user_input}

Generate the code and explain your decisions.
"""
    
    # Make sure prompt is set before calling ollama
    if prompt is None:
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

def main():
    print("Lysithea v0.1.0 - Pattern Test")
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
            status = "ON" if use_pattern else "OFF"
            print(f"Pattern mode: {status}")
            continue
        
        if user_input.lower() == '/list':
            patterns = list_available_patterns()
            if patterns:
                print("\nAvailable patterns:")
                for p in patterns:
                    print(f"  - {p}")
            else:
                print("No patterns found in patterns/ directory")
            continue
        
        if user_input.lower() == '/status':
            status = "ON (AI selects patterns)" if use_pattern else "OFF (baseline)"
            print(f"Pattern mode: {status}")
            if use_pattern:
                patterns = list_available_patterns()
                print(f"Available patterns: {len(patterns)}")
            continue
            
        try:
            response = get_response(user_input, use_pattern)
            print(f"\n{response}\n")
            
        except Exception as e:
            print(f"Error: {e}")
            print("Make sure Ollama is running")

if __name__ == "__main__":
    main()