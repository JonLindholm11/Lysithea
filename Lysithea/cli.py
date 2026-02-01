import os
from dotenv import load_dotenv

load_dotenv()

# Demo mode for development without API key
DEMO_MODE = not os.getenv("ANTHROPIC_API_KEY")

if not DEMO_MODE:
    import anthropic

def generate_demo_project():
    """Show saved demo generation"""
    return """
[Architect Agent] Planning todo API...

[Database Agent] Creating schema...
✓ users table
✓ todos table

[Backend Agent] Building FastAPI endpoints...
✓ POST /auth/register
✓ GET /todos

✅ Demo project generated!
Files: /examples/demo-todo-api/
"""

def get_response(user_input):
    """Get response from Claude or demo response"""
    
    if DEMO_MODE:
        # Show demo message
        print(f"\n[DEMO MODE] I would help you with: {user_input}")
        print("\nOnce you add your API key, I'll use Claude to give real responses.")
        print("Would you like to see our demo project generation?")
        
        # Ask for choice
        choice = input("(y/n): ").lower()
        
        # Return based on choice
        if choice in ['y', 'yes']:
            return generate_demo_project()
        else:
            return "Demo skipped. Add your API key to .env to use Lysithea for real."
    
    # Real Claude API call
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"You are a helpful coding assistant. {user_input}"
        }]
    )
    return response.content[0].text

def main():
    print("Lysithea v0.1.0 - Multi-Agent Development Platform")
    
    if DEMO_MODE:
        print("⚠️  Running in DEMO MODE - add ANTHROPIC_API_KEY to .env for real responses")
    
    print("Type your request (or 'quit' to exit)")
    print("-" * 50)
    
    while True:
        user_input = input("\n> ")
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
            
        try:
            response = get_response(user_input)
            print(f"\n{response}\n")
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()