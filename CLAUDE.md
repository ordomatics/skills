# CLAUDE.md — moctarjallo/skills

This is a Claude Code plugin marketplace. It contains installable plugins that provide
specialized AI agents, skills (domain knowledge), and commands (workflows) for Claude Code.

## Repository Structure

```
.claude-plugin/marketplace.json   ← plugin registry (source of truth for catalog)
plugins/
  {plugin-name}/
    .claude-plugin/plugin.json    ← plugin metadata
    agents/*.md                   ← AI persona definitions
    commands/*.md                 ← slash-command workflows
    skills/{name}/SKILL.md        ← domain knowledge packs
```

## Key Rules

### Before Any Change

1. **Install the ai-development plugin** — it contains the authoritative patterns:
   ```
   /plugin install ai-development
   ```
2. Load the relevant skill before writing:
   - Creating a plugin → `plugin-architecture`
   - Writing a SKILL.md → `skill-writing`
   - Writing an agent → `agent-writing`
   - Writing a command → `command-writing`
   - Updating the marketplace → `marketplace-management`

### Naming Conventions

- Plugin directories: `kebab-case`
- Agent files: `kebab-case.md`
- Command files: `kebab-case.md`
- Skill directories: `kebab-case`
- SKILL.md `name` field: must match its directory name
- Agent `name` field: must match its filename (minus `.md`)

### Version Rules

- `plugin.json` version must always match the corresponding `marketplace.json` entry version
- Adding a new plugin or component → bump marketplace `metadata.version` (minor)
- Fixing existing components → bump marketplace `metadata.version` (patch)
- `marketplace.json` `metadata.description` must accurately reflect actual plugin/component counts

### Component Quality Standards

**Skills:**
- SKILL.md must have YAML frontmatter with `name` and `description`
- `description` must include specific trigger conditions (action verbs, filenames, error types)
- Body under 500 lines — push overflow into `references/`
- Code examples must be syntactically correct for the target framework version
- No duplicated content — cross-reference other skills instead

**Agents:**
- Must have YAML frontmatter with `name`, `description`, and `model` (opus/sonnet/haiku)
- `description` must include "Use PROACTIVELY for..." trigger phrases
- Encode behavioral rules and code patterns, not capability lists
- Target 60-120 lines, max 200
- List available skills in an "Available Skills" section
- Include "How to Approach Tasks" section

**Commands:**
- First line is a brief description (no YAML frontmatter)
- Must reference `$ARGUMENTS` and document expected format with examples
- Numbered steps in imperative form
- Include a verification/cross-check step
- Define output format

### Commit Convention

```
[TAG] component-type plugin-name: description

Tags: [ADD], [FIX], [IMP], [REM], [REF], [BREAKING]
```

Examples:
```
[ADD] ai-development v2.0.0 — plugin development toolkit
[ADD] skill odoo-module-development: odoo-cron-patterns
[FIX] agent python-development: trim python-pro verbosity
[IMP] command odoo-module-development: add migration step to implement
```

### After Any Change

1. Verify `plugin.json` version matches `marketplace.json` entry
2. Verify README.md documents the change
3. Run: `git add . && git status` to review before committing
