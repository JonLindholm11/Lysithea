# Contributing to Lysithea

Thanks for your interest in contributing. This document explains how the repo is structured, where to push, and what's needed for different types of contributions.

---

## Branch Structure

| Branch | Purpose | Who pushes here |
|--------|---------|-----------------|
| `main` | Stable, release-ready | Merged from `development` only |
| `development` | Active agent and backend work | Core contributors, PRs for generator/planner/CLI changes |
| `patterns` | Pattern file contributions | Anyone adding or improving pattern files |

**If you are working on generators, planners, CLI, or any Python backend code → PR into `development`**

**If you are adding or improving pattern files → PR into `patterns`**

Never push directly to `main`.

---

## Contributing Patterns

Pattern contributions are one of the most impactful ways to help Lysithea grow. Patterns let Lysithea scaffold applications in new languages and frameworks without requiring changes to the core generation pipeline.

### How patterns work

Patterns are template files that define the structure of a generated file. The LLM fills in logic at `/* PLACEHOLDER */` markers — the pattern controls the shape, the LLM fills in the details.

```js
// Example: a route pattern stub
router.get('/', async (req, res) => {
  /* PLACEHOLDER */
});
```

Each pattern file includes a metadata header that tells Lysithea where to write the output:

```js
/**
 * @output-dir api/routes
 * @file-naming {resource}.js
 */
```

### Adding a new pattern

1. Fork the repo and check out the `patterns` branch
2. Navigate to `Patterns/` and follow the existing directory structure:
```
Patterns/
└── {Language}/
    └── {Framework}/
        └── your-pattern.js
```
3. Use `/* PLACEHOLDER */` syntax for any logic the LLM should generate
4. Include the `@output-dir` and `@file-naming` metadata header
5. Open a PR into the `patterns` branch with a short description of what the pattern generates

### A note on generator support

Lysithea's generators currently have full support for the **Javascript / Express** stack. Patterns for other languages and frameworks are welcome and encouraged — they will be wired up to generator support as it is added. If you contribute patterns for a new stack, note in your PR which stack they are intended for so they can be tracked and connected when the generator work is ready.

---

## Contributing to the Agent / Backend

If you want to work on generators, planners, the CLI, or any part of the Python orchestration pipeline, open a PR into the `development` branch.

### Setup

```bash
git clone https://github.com/JonLindholm11/Lysithea.git
cd Lysithea
pip install -r requirements.txt
pip install -e .
```

### Key files

| File | Purpose |
|------|---------|
| `Lysithea/coordinator.py` | Reads `prompt.md`, plans resources and operations → `functions.json` |
| `Lysithea/stack_planner.py` | Extracts stack config → `stack.json` |
| `Lysithea/orchestrator.py` | Runs the full planning and generation pipeline |
| `Lysithea/pattern_manager.py` | Loads pattern files, resolves placeholders |
| `Lysithea/file_manager.py` | All file I/O — source of truth for paths |
| `Lysithea/cli.py` | CLI entry point |
| `Lysithea/generators/` | One generator per output type |

### Conventions

- `stack_config` is always accessed as `stack_config['stack']['backend']` etc. — never assume a flat shape
- Pattern placeholders use `/* PLACEHOLDER */` syntax only
- Generators normalize resource names to lowercase
- Always cast `Path` objects to `str()` before passing to `save_generated_files`
- Use `LYSITHEA_PROJECT_PATH` env var for output paths — never use `Path(__file__)` relative resolution for output

### Testing

Run Lysithea end-to-end against a test `prompt.md` before opening a PR. A simple blog or book store spec is enough to validate most generator changes. Include a note in your PR about what you tested against.

---

## Community Prompts

If you have a `prompt.md` that produces a solid generated app, consider submitting it to the **[lysithea-prompts](https://github.com/JonLindholm11/lysithea-prompts)** repo. See that repo's contributing guide for details.

---

## Questions

Open an issue if you're unsure where something belongs or want to discuss a contribution before building it.
