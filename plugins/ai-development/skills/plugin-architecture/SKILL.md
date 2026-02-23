---
name: plugin-architecture
description: "Claude Code plugin architecture patterns — plugin structure, marketplace registration, naming conventions, versioning, and component organization. Use when creating a new plugin from scratch, restructuring an existing plugin, adding a plugin to the marketplace, or understanding how plugins, skills, agents, and commands fit together."
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Plugin Architecture

This skill defines the structural patterns for Claude Code plugins in the
moctarjallo/skills marketplace.

## Plugin Structure

Every plugin is a directory under `plugins/` with this layout:

```
{plugin-name}/
├── .claude-plugin/
│   └── plugin.json          ← required: metadata
├── agents/                   ← optional: AI persona definitions
│   └── {agent-name}.md
├── commands/                 ← optional: slash-command workflows
│   └── {command-name}.md
└── skills/                   ← optional: domain knowledge packs
    └── {skill-name}/
        ├── SKILL.md          ← required: entry point
        ├── references/       ← optional: deep documentation
        ├── scripts/          ← optional: executable tools
        └── assets/           ← optional: templates, icons, fonts
```

A plugin must have at least one agent, command, or skill to be useful.

## plugin.json Schema

```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "description": "One-line description of what this plugin provides",
  "author": {
    "name": "Author Name",
    "email": "author@example.com"
  },
  "license": "MIT"
}
```

Rules:
- `name` must match the directory name exactly
- `version` uses semver: `MAJOR.MINOR.PATCH`
  - MAJOR: breaking changes to agents, commands, or skill interfaces
  - MINOR: new agents, commands, or skills added
  - PATCH: fixes, improvements to existing components
- `description` should say *what the plugin provides*, not list every component

## marketplace.json Schema

The marketplace registry at `.claude-plugin/marketplace.json`:

```json
{
  "name": "moctarjallo-skills",
  "owner": {
    "name": "Moctar Diallo",
    "email": "moctarjallo@gmail.com",
    "url": "https://github.com/moctarjallo"
  },
  "metadata": {
    "description": "Short marketplace description",
    "version": "1.6.0"
  },
  "plugins": [
    {
      "name": "plugin-name",
      "source": "./plugins/plugin-name",
      "description": "Plugin description for the catalog",
      "version": "1.0.0",
      "author": { "name": "...", "email": "..." },
      "homepage": "https://github.com/moctarjallo/skills",
      "license": "MIT",
      "category": "frameworks"
    }
  ]
}
```

Rules:
- Each plugin entry's `version` must match its `plugin.json` version
- `source` is always `./plugins/{name}` (relative path)
- `category` is one of: `languages`, `frameworks`, `ai`, `tools`, `devops`
- The `metadata.version` is the marketplace release version — bump it when any plugin changes

## Naming Conventions

| Thing | Convention | Example |
|-------|-----------|---------|
| Plugin directory | `kebab-case` | `python-development` |
| Agent file | `kebab-case.md` | `python-pro.md` |
| Command file | `kebab-case.md` | `bump-version.md` |
| Skill directory | `kebab-case` | `python-design-patterns` |
| SKILL.md `name` | matches directory | `python-design-patterns` |
| Agent `name` | matches filename (minus .md) | `python-pro` |

## Component Organization Guidelines

### When to create a new plugin vs. add to existing

Create a **new plugin** when:
- The domain is fundamentally different (Python vs. Odoo vs. DevOps)
- A user would want to install it independently
- It has no dependency on other plugins in the marketplace

Add to an **existing plugin** when:
- The component belongs to the same domain
- It shares agents or cross-references skills within the plugin
- Installing it separately wouldn't make sense

### When to use agents vs. skills vs. commands

| Component | Use when... | Example |
|-----------|-------------|---------|
| **Agent** | You need a persistent persona with model assignment and behavioral rules | `odoo-module-developer` (Sonnet, Odoo 18 rules) |
| **Skill** | You need domain knowledge that loads on demand | `odoo-security-patterns` (ir.model.access patterns) |
| **Command** | You need a user-invocable multi-step workflow with arguments | `/implement add sale_custom partner pricing` |

### Agent → Skill relationship

Agents reference skills they can use:
```markdown
## Available Skills
- **`odoo-security-patterns`** — ir.model.access, ir.rule, sudo()
- **`odoo-wizard-patterns`** — TransientModel, multi-record, return actions
```

This tells the agent *which knowledge packs exist* without loading their content.
The skill content loads only when the agent or user triggers it.

## Creating a New Plugin — Checklist

1. Create directory: `plugins/{plugin-name}/`
2. Create `.claude-plugin/plugin.json` with valid metadata
3. Create at least one component (agent, skill, or command)
4. Add plugin entry to `marketplace.json` plugins array
5. Bump `marketplace.json` `metadata.version`
6. Update `README.md` with plugin documentation

## Validating a Plugin

Check these after any change:

- [ ] `plugin.json` `name` matches directory name
- [ ] `plugin.json` `version` matches `marketplace.json` entry version
- [ ] Every `.md` agent file has valid YAML frontmatter (`name`, `description`, `model`)
- [ ] Every `SKILL.md` has valid YAML frontmatter (`name`, `description`)
- [ ] Every command `.md` references `$ARGUMENTS` for argument handling
- [ ] No orphaned files (every .py is imported, every .xml is registered)
- [ ] Cross-references between skills/agents point to existing components
- [ ] README.md documents the plugin's agents, skills, and commands

For detailed validation, read `references/validation-checklist.md`.
