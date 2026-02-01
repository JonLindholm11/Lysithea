# Lysithea

Open-source multi-agent AI development platform powered by Claude.

## 🚧 Early Development

This project is in active early development. Expect breaking changes and incomplete features.

## Vision

Lysithea uses 7 specialized AI agents that coordinate to build complete applications from natural language prompts.

### The 7 Agents

🏗️ **Architect** - Orchestrates the entire development process and interfaces directly with the user. Plans implementation and delegates tasks to specialized agents.

🔌 **API Agent** - Builds server-side logic, REST/GraphQL endpoints, business logic, and middleware.

🗄️ **Database Agent** - Designs database schemas, manages migrations, handles seeding, and optimizes queries.

⚛️ **Frontend Agent** - Creates UI components, manages state, implements routing, and handles user interactions.

🎨 **Design Agent** - Implements styling with CSS/Tailwind, ensures responsive design, and validates visual output.

✅ **Testing Agent** - Writes unit tests, integration tests, and end-to-end tests to ensure code quality.

🔍 **Checker Agent** - Reviews outputs from all agents, ensures consistency, maintains project scope, and documents changes.

## Current Status

- [ ] Basic CLI
- [ ] Architect Agent
- [ ] API Agent
- [ ] Database Agent
- [ ] Frontend Agent
- [ ] Design Agent
- [ ] Testing Agent
- [ ] Checker Agent

## Quick Start
```bash
# Clone
git clone https://github.com/yourusername/lysithea.git
cd lysithea

# Install dependencies
pip install -r requirements.txt --break-system-packages

# Configure
echo "ANTHROPIC_API_KEY=your_key_here" > .env

# Run
python -m lysithea.cli
```

## Requirements

- Python 3.9+
- Anthropic API key ([Get one here](https://console.anthropic.com))

## Contributing

This project is in early stages. Contributions welcome once core architecture is established.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Roadmap

See [ROADMAP.md](ROADMAP.md) for planned features and milestones.

---

Built with ❤️ by [Jon Lindholm] | [GitHub](https://github.com/JonLindholm11) | [LinkedIn](https://www.linkedin.com/in/jon-lindholm-3507b338a/)