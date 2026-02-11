# lysithea/coordinator.py
"""
Coordinator agent that breaks down user requests into resources and operations
"""

import ollama
import re

def coordinator_agent(user_input):
    """Break down user request into sequential generation steps"""
    
    prompt = f"""You are a parser that extracts resources and operations from requests.

Input: "{user_input}"

CRITICAL INSTRUCTION: List ONLY the resources that appear in the user's request by name. These can include things like "get by a variable" - if mentioned, take note of exactly what resource they needed in the request.

Rules:
1. Find resource name (products, users, orders, etc.)
2. Map to operations: GET all, GET by ID, POST, PUT, DELETE
4. Output ONLY the format below - NO explanations, NO prose

Required format:
RESOURCES:
- [resource]: [operations]

Input: "CRUD for users"  
RESOURCES:
- users: GET all, GET by ID, POST, PUT, DELETE

Now parse: "{user_input}"

Output (format only, no explanations):
"""
    
    print("\n[Coordinator Agent analyzing request...]")

    try:
        response = ollama.generate(
            model='llama3.1:8b',
            prompt=prompt
        )
        
        ai_response = response['response'].strip()
        print(f"\n{ai_response}\n")
        
        # Parse multiple resources and their operations
        resources = []  # List of {name: "products", operations: [...]}
        
        in_resources = False
        for line in ai_response.split('\n'):
            line = line.strip()
            
            # Check if we're entering resources section
            if 'RESOURCES:' in line or 'RESOURCE:' in line:
                in_resources = True
                continue
            
            # Parse each resource line: "- products: GET all, POST, PUT"
            if in_resources and line.startswith('-'):
                # Split on first colon: "- products: GET all, POST"
                if ':' in line:
                    parts = line.lstrip('- ').split(':', 1)
                    resource_name = parts[0].strip()
                    operations_str = parts[1].strip() if len(parts) > 1 else ""
                    
                    # Clean resource name
                    resource_name = resource_name.lstrip('/').strip()
                    resource_name = re.sub(r'[^\w-]', '', resource_name)
                    
                    # Parse operations (comma-separated)
                    operations = []
                    if operations_str:
                        for op in operations_str.split(','):
                            op_clean = op.strip()
                            if op_clean:
                                operations.append(op_clean)
                    
                    if resource_name and operations:
                        resources.append({
                            'name': resource_name,
                            'operations': operations
                        })
        
        if not resources:
            print("[Could not parse any resources]")
            return None
        
        print(f"[Parsed: {len(resources)} resource(s)]")
        for res in resources:
            print(f"  - {res['name']}: {len(res['operations'])} operations")
        
        return resources
        
    except Exception as e:
        print(f"[Coordinator error: {e}]")
        return None