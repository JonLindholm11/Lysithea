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
5. if the user requires authentication include the authentication patterns required, also do not duplicate middleware / authentication if its noted once it will work for all resources
6. If routes need database access (CRUD operations interact with data), include database connection automatically. Database connection is required for: GET all, GET by ID, POST, PUT, DELETE operations.
7. Requests for GET alone are requesting GET all
8. Requests for GET by ID request single item

Required format:
RESOURCES:
- [resource]: [operations]
MIDDLEWARE:
- [type]
DATABASE:
- connection

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
        
        # Parse resources and middleware in one pass
        resources = []
        middleware = []
        database = []
        in_resources = False
        in_middleware = False
        in_database = False
        
        for line in ai_response.split('\n'):
            line = line.strip()
            
            # Check if entering resources section
            if 'RESOURCES:' in line or 'RESOURCE:' in line:
                in_resources = True
                in_middleware = False
                in_database = False
                continue
            
            # Check if entering middleware section
            if 'MIDDLEWARE' in line:
                in_middleware = True
                in_resources = False
                in_database = False
                continue

            if 'DATABASE' in line:
                in_database = True
                in_middleware = False
                in_resources = False
            
            # Parse resource lines (must have colon)
            if in_resources and line.startswith('-') and ':' in line:
                parts = line.lstrip('- ').split(':', 1)
                resource_name = parts[0].strip()
                operations_str = parts[1].strip() if len(parts) > 1 else ""
                
                # Clean resource name
                resource_name = resource_name.lstrip('/').strip()
                resource_name = re.sub(r'[^\w-]', '', resource_name)
                
                # Parse operations
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
            
            # Parse middleware lines (no colon needed)
            if in_middleware and line.startswith('-'):
                middleware_name = line.lstrip('- ').strip().lower()  # ← Add .lower()
                if middleware_name:
                    middleware.append(middleware_name)

            
                
            if in_database and line.startswith('-'):
                db_item = line.lstrip('- ').strip().lower()
                if db_item:
                    database.append(db_item)
        
        # Return as dict
        result = {
            'resources': resources,
            'middleware': middleware,
            'database' : database
        }
        
        if not resources and not middleware and not database:  # ← Add database check
            print("[Could not parse anything]")
            return None

        print(f"[Parsed: {len(resources)} resource(s), {len(middleware)} middleware, {len(database)} database]")
        for res in resources:
            print(f"  - {res['name']}: {len(res['operations'])} operations")
        for mw in middleware:
            print(f"  - {mw} (middleware)")
        for db in database:  # ← Add this
            print(f"  - {db} (database)")
                
        return result
        
    except Exception as e:
        print(f"[Coordinator error: {e}]")
        return None