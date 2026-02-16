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
2. Map EXACTLY what user requests - don't infer additional operations
3. BE LITERAL about operations:
   - "GET" or "GET all" → GET all ONLY
   - "GET by ID" or "GET :id" → GET by ID ONLY
   - "CRUD" → ALL 5 operations: GET all, GET by ID, POST, PUT, DELETE
   - "POST" → POST only
   - "PUT" → PUT only
   - "DELETE" → DELETE only
4. Output ONLY the format below - NO explanations, NO comments, NO extra text after items
5. If user requires authentication, include under MIDDLEWARE (no duplicates across resources)
6. If generating any RESOURCES (routes), automatically include:
   MIDDLEWARE:
   - auth
   DATABASE:
   - connection
   SCHEMA:
   - tables
   
   Routes always need both authentication and database connection.
7. Do not add operations the user didn't explicitly request

Examples:

Input: "CRUD for products"
RESOURCES:
- products: GET all, GET by ID, POST, PUT, DELETE
MIDDLEWARE:
- auth
DATABASE:
- connection
SCHEMA:
- tables

Input: "GET users"
RESOURCES:
- users: GET all
MIDDLEWARE:
- auth
DATABASE:
- connection
SCHEMA:
- tables

Input: "POST and PUT for orders"
RESOURCES:
- orders: POST, PUT
MIDDLEWARE:
- auth
DATABASE:
- connection
SCHEMA:
- tables

Required format (include sections as needed):

RESOURCES:
- [resource]: [operations]

MIDDLEWARE:
- auth  ← ALWAYS include when RESOURCES present

DATABASE:
- connection  ← ALWAYS include when RESOURCES present

SCHEMA:
- tables  ← ALWAYS include when RESOURCES present

IMPORTANT: Any request with RESOURCES automatically gets MIDDLEWARE (auth), DATABASE (connection), and SCHEMA (tables).

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
        schema = []
        in_resources = False
        in_middleware = False
        in_database = False
        in_schema = False
        
        for line in ai_response.split('\n'):
            line = line.strip()
            
            # Check if entering resources section
            if 'RESOURCES:' in line or 'RESOURCE:' in line:
                in_resources = True
                in_middleware = False
                in_database = False
                in_schema = False
                continue
            
            # Check if entering middleware section
            if 'MIDDLEWARE' in line:
                in_middleware = True
                in_resources = False
                in_database = False
                in_schema = False
                continue

            if 'DATABASE' in line:
                in_database = True
                in_middleware = False
                in_resources = False
                in_schema = False
                continue
            
            if 'SCHEMA' in line:
                in_schema = True
                in_database = False
                in_middleware = False
                in_resources = False
                continue

            
            # Parse resource lines (must have colon)
            if in_resources and line.startswith('-') and ':' in line:
                parts = line.lstrip('- ').split(':', 1)
                resource_name = parts[0].strip()
                operations_str = parts[1].strip() if len(parts) > 1 else ""
                
                # Clean resource name
                resource_name = resource_name.lstrip('/').strip()
                resource_name = re.sub(r'[^\w-]', '', resource_name)
                resource_name = resource_name.lower()
                
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

            if in_schema and line.startswith('-'):
                schema_item = line.lstrip('- ').strip().lower()
                if schema_item:
                    schema.append(schema_item)
        
        # Return as dict
        result = {
            'resources': resources,
            'middleware': middleware,
            'database' : database,
            'schema' : schema
        }
        
        if not resources and not middleware and not database:
            print("[Could not parse anything]")
            return None

        print(f"[Parsed: {len(resources)} resource(s), {len(middleware)} middleware, {len(database)} database, {len(schema)} schema]")
        for res in resources:
            print(f"  - {res['name']}: {len(res['operations'])} operations")
        for mw in middleware:
            print(f"  - {mw} (middleware)")
        for db in database:
            print(f"  - {db} (database)")
        for sch in schema:
            print(f" -{sch} (schema)")
                
        return result
        
    except Exception as e:
        print(f"[Coordinator error: {e}]")
        return None