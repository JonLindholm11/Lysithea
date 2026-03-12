<div align="center">

# 🌙 Lysithea

**AI-powered code scaffolding for full-stack applications — powered by local LLMs.**

Write a `prompt.md`. Get a production-ready Express + React + PostgreSQL application.

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.8+-blue)
![Ollama](https://img.shields.io/badge/ollama-llama3.1%3A8b-green)
![Stack](https://img.shields.io/badge/stack-Express%20%7C%20React%20%7C%20PostgreSQL-orange)

</div>

---

## What is Lysithea?

Lysithea is a local, open-source multi-agent scaffolding tool. You describe your application in a `prompt.md` file — your resources, operations, auth requirements, and database schema — and Lysithea's agent pipeline generates a fully structured, runnable full-stack application.

No cloud. No API keys. Runs entirely on your machine via [Ollama](https://ollama.com).

---

## How It Works

```
prompt.md  →  [Coordinator]  →  functions.json
           →  [Stack Planner] →  stack.json
                                      ↓
                             [Orchestrator]
                                      ↓
          ┌───────────────────────────────────────┐
          │  manifest_generator                   │
          │  resource_generator  (routes, models) │
          │  frontend_generator  (React pages)    │
          │  auth_generator      (JWT auth)       │
          │  query_generator     (SQL schema)     │
          │  app_generator       (entry point)    │
          └───────────────────────────────────────┘
                                      ↓
                         Full-stack application
```

1. **Coordinator** reads your `prompt.md` and plans resources + operations → `functions.json`
2. **Stack Planner** extracts your stack config → `stack.json`
3. **Orchestrator** runs both planners and passes outputs to the generators
4. **Generators** use pattern files as structural templates, injecting LLM-generated logic at the right placeholders

---

## Quick Start

### Prerequisites

- Python 3.8+
- [Ollama](https://ollama.com) with `llama3.1:8b` pulled
- Node.js 18+
- PostgreSQL

### Installation

```bash
git clone https://github.com/JonLindholm11/Lysithea.git
cd Lysithea
pip install -r requirements.txt

# Optional: install the global lysithea command
pip install -e .
```

## Usage Options

Lysithea can be used two ways depending on your workflow:

| | Option | Best For |
|---|--------|----------|
| 🖥️ | **Electron GUI** | Visual project management, browsing patterns, configuring your stack with a form-based interface |
| ⌨️ | **CLI** | Scripting, automation, or if you prefer to stay in the terminal |

Both options produce identical output — the same generated application either way.

---

## CLI Usage

### Generate a project

**1. Write your `prompt.md`**

```markdown
# Project: Book Store API

## Stack
- Backend: Express.js
- Frontend: React
- Database: PostgreSQL
- Auth: JWT

## Resources
- Books: title, author, genre, price
- Users: name, email, password

## Operations
- Books: list, create, read, update, delete
- Users: register, login

## Frontend Requirements
- Books: dashboard, form
- Users: dashboard
```

**2. Run Lysithea**

```bash
# Interactive mode
python cli.py

# Or after pip install -e .
lysithea
```

**3. Start your app**

```bash
cd output/my-book-store
npm install && npm run dev
```

### Fix or modify an existing project

Already generated a project and want to make targeted changes? Use the `--fix` agent to update your application without regenerating from scratch.

```bash
# Searches current working directory for the project
python cli.py --fix "add pagination to the posts endpoint"

# Point it at a specific project path
python cli.py --fix "add pagination to the posts endpoint" --path ./my-book-store

# After pip install -e .
lysithea --fix "add pagination to the posts endpoint"
lysithea --fix "add pagination to the posts endpoint" --path ./my-book-store
```

---

## Demo Projects

These projects were fully scaffolded by Lysithea. Each repo includes the original `prompt.md` used to generate it.

| | Project | Complexity | Description |
|---|---------|------------|-------------|
| 📦 | **Project 1** | Simple | (add GitHub link) |
| 📦 | **Project 2** | Medium | (add GitHub link) |
| 📦 | **Project 3** | Complex | (add GitHub link) |

---

## Community Prompts

> 📁 **[lysithea-prompts](https://github.com/JonLindholm11/lysithea-prompts)** — A community-maintained library of `prompt.md` files for common app types.

New to Lysithea? Browse the prompt library to find a starting point instead of writing one from scratch. Built something cool? Submit your `prompt.md` and share it with others.

---

## Project Structure

```
Lysithea/
├── coordinator.py          # Plans resources + operations → functions.json
├── stack_planner.py        # Extracts stack config → stack.json
├── orchestrator.py         # Runs planning + generation pipeline
├── pattern_manager.py      # Loads .js pattern files, handles placeholders
├── file_manager.py         # All file I/O
├── generators/
│   ├── manifest_generator.py
│   ├── app_generator.py
│   ├── resource_generator.py
│   ├── frontend_generator.py
│   ├── auth_generator.py
│   ├── query_generator.py
│   └── project_files_generator.py
└── Patterns/
    └── Javascript/
        └── Express/        # Pattern templates with /* PLACEHOLDER */ syntax
```

---

## Patterns

Lysithea uses pattern files as structural scaffolds. Each pattern defines the shape of a generated file with `/* PLACEHOLDER */` comments where LLM-generated logic is injected.

This keeps generated code structurally consistent even when the LLM output varies — the pattern is the source of truth for structure, the LLM fills in the logic.

Patterns are organized by language and framework and declared in your `prompt.md` stack config. When a stack is selected, Lysithea resolves the correct pattern set automatically.

```
Patterns/
├── Javascript/
│   └── Express/
├── Python/
│   └── FastAPI/
│   └── Django/
├── Ruby/
│   └── Rails/
├── Go/
│   └── Gin/
└── PHP/
    └── Laravel/
```

> Pattern contributions for any language and framework are welcome on the `patterns` branch. Generator support for new stacks will be added incrementally — see [CONTRIBUTING.md](./CONTRIBUTING.md).

---

## Roadmap

- [ ] Additional stack support
- [ ] Business rules declarations via `prompt.md`
- [ ] Expanded pattern library
- [ ] Import and scaffold from existing table data

---

## Contributing

Contributions are welcome. If you'd like to add a new pattern, fix a generator, or submit a demo prompt, please open an issue or PR.

---

## License

MIT © [Jon Lindholm](https://github.com/JonLindholm11)

## Acknowledgements

Built by [Jon Lindholm] | [GitHub](https://github.com/JonLindholm11) | [LinkedIn](https://www.linkedin.com/in/jon-lindholm-3507b338a/)


