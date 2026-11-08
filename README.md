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
/plugin install odoo-module-development  # generic Odoo module patterns
/plugin install odoo-development         # Ordomatics project context
/plugin install ai-development           # plugin development toolkit
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

## `odoo-development` Plugin — Ordomatics Project Context

Project-specific context for the Ordomatics Odoo stack: infrastructure, LLM suite, and WhatsApp modules.
Pair with `odoo-module-development` for full Odoo coverage.

### Agents

| Agent | Model | Role |
|---|---|---|
| `odoo-developer` | Sonnet 4.6 | Docker, entrypoint, env, CI/CD, module setup |
| `odoo-llm-developer` | Sonnet 4.6 | odoo-llm suite expert (provider dispatch, dependency chain, 34 modules) |
| `odoo-whatsapp-developer` | Sonnet 4.6 | WhatsApp module expert (templates, messaging flows, Business API) |

### Skills

| Skill | When It Activates |
|---|---|
| `odoo-docker-ops` | Docker Compose operations, image builds, logs |
| `odoo-module-setup` | Module installation, setup_odoo_modules.sh, .env config |
| `odoo-cicd` | GitHub Actions / GitLab CI pipeline management, submodules |
| `odoo-llm-provider-dispatch` | Adding or extending an LLM provider module |
| `odoo-whatsapp-templates` | Defining templates, variable mapping, Meta approval flow |
| `odoo-whatsapp-messaging` | Sending messages, composer wizard, delivery status tracking |

---

## `odoo-module-development` Plugin — Generic Odoo Patterns

Generic Odoo 18.0 module development patterns — works with any Odoo project.

### Agents

| Agent | Model | Role |
|---|---|---|
| `odoo-module-developer` | Sonnet 4.6 | Odoo 18.0 ORM, views, model structure, module conventions |

### Commands

- **`/odoo-module-development:implement`** — Implement a feature, fix, refactor, or migration in any Odoo module
- **`/odoo-module-development:bump-version`** — Bump an Odoo module version and update changelog/docs
- **`/odoo-module-development:check-module`** — Validate an Odoo module structure and manifest
- **`/odoo-module-development:fix-app-store-html`** — Clean up and fix App Store HTML description

### Skills

| Skill | When It Activates |
|---|---|
| `odoo-feature-dev` | Modifying existing Odoo modules |
| `odoo-module-creator` | Scaffolding new Odoo modules |
| `odoo-app-landing-page` | Writing or improving Odoo App Store landing pages |
| `odoo-mail-integration` | Adding chatter, posting messages, mail subtypes, followers |
| `odoo-security-patterns` | ir.model.access.csv, ir.rule, group visibility, sudo() |
| `odoo-wizard-patterns` | TransientModel wizards, multi-record, return actions |
| `odoo-controller-patterns` | HTTP routes, JSON endpoints, webhook receivers |
| `odoo-queue-job-patterns` | OCA queue_job async execution, channels, retries |

---

## `ai-development` Plugin — Plugin Development Toolkit

Create, validate, and maintain Claude Code plugins, skills, agents, and commands following best practices. Also includes persistent cross-session memory.

### Agents

| Agent | Model | Role |
|---|---|---|
| `plugin-architect` | Opus 4.6 | Design, create, validate, and improve plugins and their components |

### Commands

- **`/ai-development:create-plugin`** — Scaffold a new plugin with agents, skills, and commands
- **`/ai-development:validate-plugin`** — Audit a plugin for structural correctness and quality
- **`/ai-development:add-component`** — Add a skill, agent, or command to an existing plugin

```bash
/ai-development:create-plugin devops-toolkit Infrastructure and deployment patterns
/ai-development:validate-plugin odoo-module-development
/ai-development:add-component skill python-development python-caching Caching strategies
```

### Skills

| Skill | When It Activates |
|---|---|
| `plugin-architecture` | Creating a new plugin, understanding plugin structure, marketplace registration |
| `skill-writing` | Writing or improving a SKILL.md file |
| `agent-writing` | Writing or improving an agent .md file |
| `command-writing` | Writing or improving a command .md workflow |
| `marketplace-management` | Adding/removing plugins, bumping versions, auditing the marketplace |
| `memory` | Storing, retrieving, or searching persistent memories across sessions |

---

## `odoo-ops` Plugin — Operational Runbooks

### Skills

| Skill | Use when |
|-------|----------|
| `odoo-env-reset` | Wiping and redeploying a K8s environment |
| `argocd-sync` | ArgoCD isn't picking up a commit |
| `supabase-recovery` | Supabase circuit breaker / too many authentication errors |
| `doks-redeploy` | Destroying and recreating the ephemeral DOKS test cluster |
| `platform-restore` | Restoring the whole platform onto a new cloud account: pause the Terraform-backed claims, adopt existing Neon/R2 resources into state, then bring every deployment back |

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
