# Claude Code Plugins

> **⚡ Powered by Opus 4.6, Sonnet 4.6 & Haiku 4.5**

A modular plugin system for [Claude Code](https://docs.claude.com/en/docs/claude-code/overview) providing specialized AI agents, workflow tools, and domain knowledge packages.

## Quick Start

### Step 1: Add the Marketplace

```bash
/plugin marketplace add moctarjallo/skills
```

### Step 2: Install a Plugin

```bash
/plugin install python-development
/plugin install odoo-development
```

---

## `python-development` Plugin

### Agents

| Agent | Model | Role |
|---|---|---|
| `python-pro` | Opus 4.6 | General Python expertise |
| `django-pro` | Opus 4.6 | Django web development |
| `fastapi-pro` | Opus 4.6 | FastAPI microservices |

### Commands

- **`/python-development:python-scaffold`** — Scaffold production-ready Python projects

```bash
/python-development:python-scaffold fastapi-microservice
```

### Skills (16 specialized)

Skills use progressive disclosure — they load knowledge only when activated:

| Skill | When It Activates |
|---|---|
| `async-python-patterns` | AsyncIO and concurrency work |
| `python-testing-patterns` | pytest, fixtures, test design |
| `python-packaging` | Package setup, distribution |
| `python-performance` | Profiling, optimization |
| `uv-package-manager` | Fast dependency management |

---

## `odoo-development` Plugin

### Commands

- **`/odoo-development:bump-version`** — Bump an Odoo module version and update changelog/docs

```bash
/odoo-development:bump-version my_module
```

- **`/odoo-development:check-module`** — Validate an Odoo module structure and manifest

```bash
/odoo-development:check-module my_module
```

- **`/odoo-development:fix-app-store-html`** — Clean up and fix App Store HTML description

```bash
/odoo-development:fix-app-store-html my_module
```

### Skills

| Skill | When It Activates |
|---|---|
| `odoo-app-landing-page` | Writing or improving Odoo App Store landing pages |

---

## Example Workflow

```bash
# Scaffold a new FastAPI project
/python-development:python-scaffold fastapi-microservice

# Then just talk to Claude naturally — agents and skills activate automatically
"Add async database connection pooling"
"Write pytest fixtures for the auth module"
"Optimize this endpoint for high throughput"
```

---

## Troubleshooting

**"Plugin not found"** → Make sure to add the marketplace first (Step 1).

**Plugin not loading** → Clear cache and reinstall:

```bash
rm -rf ~/.claude/plugins/cache/claude-code-workflows && rm ~/.claude/plugins/installed_plugins.json
```

---

## Resources

- [Claude Code Documentation](https://docs.claude.com/en/docs/claude-code/overview)
- [Plugins Guide](https://docs.claude.com/en/docs/claude-code/plugins)
- [Agent Skills Guide](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview)

## License

MIT License — see [LICENSE](LICENSE) for details.
