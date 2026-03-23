---
name: agent-writing
description: "Write effective Claude Code agent definitions (.md files). Covers frontmatter schema, model selection, persona design, behavioral rules vs capability lists, and cross-agent delegation. Use when creating a new agent, improving an existing agent's quality, choosing which model to assign, or reviewing agent verbosity."
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Agent Writing Guide

Agents are AI persona definitions that tell Claude *how to behave* in a specific
domain. A good agent is prescriptive and tight. A bad agent is a resume.

## Agent .md Anatomy

```markdown
---
name: agent-name
description: What this agent does and WHEN to use it. Include "Use PROACTIVELY for..." trigger phrases.
model: sonnet
---

You are an expert in [domain]. You [key behavioral trait].

## [Domain] Rules

Prescriptive rules with code examples.

## Available Skills

- **`skill-name`** — one-line description of when to load it

## How to Approach Tasks

1. Read before writing
2. Grep to locate
3. Minimal changes
4. Check side effects
```

### Frontmatter Fields

| Field | Required | Values | Description |
|-------|----------|--------|-------------|
| `name` | yes | `kebab-case` | Must match filename minus `.md` |
| `description` | yes | string | What + when. Include "Use PROACTIVELY" |
| `model` | yes | `opus`, `sonnet`, `haiku` | Model to power this agent |

## Model Selection Strategy

Choose the model based on the agent's cognitive demands:

| Model | Cost | Best for | Examples |
|-------|------|----------|----------|
| **opus** | $$$ | Deep reasoning, architecture decisions, complex code generation, multi-step analysis | `python-pro`, `django-pro` |
| **sonnet** | $$ | Pattern matching, infrastructure ops, framework-specific rules, code that follows established patterns | `odoo-module-developer`, `odoo-developer` |
| **haiku** | $ | Simple lookups, formatting, template-based tasks, validation | Linting agents, scaffolding agents |

Rule of thumb:
- If the agent needs to *think through novel problems* → opus
- If the agent needs to *apply known patterns correctly* → sonnet
- If the agent does *repetitive, well-defined tasks* → haiku

## Persona Design

### The Opening Line

Start with "You are..." and immediately establish the domain boundary:

```markdown
You are an expert Odoo 18.0 developer with deep knowledge of the ORM,
XML view system, and module conventions.
```

Don't say:
```markdown
You are a helpful AI assistant that can help with Odoo development.
```

### Behavioral Rules > Capability Lists

The most common mistake is writing agents that list capabilities instead of
encoding behavior. Compare:

**Bad — capability resume (150 lines, low signal):**
```markdown
## Capabilities
- Django 5.x features including async views
- Model design with proper relationships
- Class-based views and function-based views
- Django ORM optimization
- Custom model managers
- Django signals
- Django admin customization
[... 50 more bullet points ...]
```

**Good — behavioral rules (30 lines, high signal):**
```markdown
## Odoo 18.0 Rules — Easy to Get Wrong

- `<list>` not `<tree>` in XML views
- `invisible="condition"` directly on elements, **never** `attrs=`
- `_compute_display_name` instead of `name_get()`
- `@api.model_create_multi` for `create()` overrides

## Method Order in Model Files

1. `_name`, `_description`, `_inherit`, `_order`
2. Field definitions (scalars → relational → computed)
3. `@api.depends` compute methods
4. `@api.constrains` validation methods
5. CRUD overrides
6. Public action methods
7. Private helpers
```

The behavioral rules version tells the model *exactly how to write code*. The
capability list just says the model knows things it already knows.

### What to Include in an Agent

| Section | Include? | Purpose |
|---------|----------|---------|
| Opening persona line | Always | Set domain boundary |
| Domain-specific rules | Always | The core value — prescriptive patterns |
| Code examples | When rules need illustration | Show the correct pattern |
| Available Skills | When plugin has skills | Tell agent what knowledge exists |
| How to Approach Tasks | Always | Step-by-step methodology |
| Capabilities list | Avoid | Low signal-to-noise ratio |
| Example Interactions | Optional, keep short | 3-5 one-liners max |

### Ideal Agent Length

- **Target**: 60-120 lines
- **Maximum**: 200 lines
- **If longer**: extract domain knowledge into skills and reference them

## Cross-Agent Delegation

When an agent's domain overlaps with another, delegate rather than duplicate:

```markdown
For generic Odoo 18 ORM rules, XML views, and security conventions,
defer to the `odoo-module-developer` agent.
```

This keeps agents focused. The `odoo-llm-developer` knows LLM-specific patterns;
it defers to `odoo-module-developer` for generic Odoo rules.

## Agent Quality Checklist

- [ ] `name` matches filename minus `.md`
- [ ] `description` includes "Use PROACTIVELY for..." with specific triggers
- [ ] `model` is appropriate for the cognitive demands
- [ ] Opens with "You are..." persona definition
- [ ] Contains prescriptive rules with code examples (not capability lists)
- [ ] Lists available skills (if plugin has skills)
- [ ] Has "How to Approach Tasks" section with actionable steps
- [ ] Cross-references other agents for out-of-scope knowledge
- [ ] Total length under 200 lines (target: 60-120)
- [ ] No duplicated content that exists in a skill — reference the skill instead
