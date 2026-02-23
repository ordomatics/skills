Create a new Claude Code plugin in the moctarjallo/skills marketplace.

## Arguments: $ARGUMENTS

Expected format: `{plugin-name} [description]`

Examples:
- `devops-toolkit Infrastructure, CI/CD, and deployment patterns`
- `react-development`
- `data-engineering ETL pipelines, data quality, and warehouse patterns`

If no description is provided, ask the user what the plugin should cover.

---

## Step 1 — Clarify Scope

Before creating anything, determine:

1. **Plugin name** (kebab-case, e.g. `devops-toolkit`)
2. **Domain** — what area does it cover?
3. **Components planned**:
   - Agents: how many, what personas, which models?
   - Skills: what domain knowledge packs?
   - Commands: what workflows?
4. **Generic or project-specific?** — generic plugins are reusable by anyone; project-specific plugins encode your unique stack context
5. **Category**: `languages`, `frameworks`, `ai`, `tools`, or `devops`

If the user already provided enough context, proceed. Otherwise ask.

## Step 2 — Create Plugin Structure

Load the `plugin-architecture` skill and create all required files:

```
plugins/{plugin-name}/
├── .claude-plugin/
│   └── plugin.json
├── agents/
│   └── (at least one agent .md)
├── commands/
│   └── (optional command .md files)
└── skills/
    └── (at least one skill directory with SKILL.md)
```

### Create plugin.json

```json
{
  "name": "{plugin-name}",
  "version": "1.0.0",
  "description": "{description}",
  "author": {
    "name": "Moctar Diallo",
    "email": "moctarjallo@gmail.com"
  },
  "license": "MIT"
}
```

### Create the Agent

Load the `agent-writing` skill for patterns. Create the primary agent following
the behavioral-rules-over-capability-lists principle. Target 60-120 lines.

### Create the Skills

Load the `skill-writing` skill for patterns. Create each skill with:
- Valid frontmatter (name matching directory, pushy description)
- Body under 500 lines
- Code-first reference or step-by-step procedure pattern

### Create Commands (if any)

Load the `command-writing` skill for patterns. Create each command with:
- `$ARGUMENTS` handling
- Numbered steps in imperative form
- Verification checklist

## Step 3 — Register in Marketplace

Add the plugin entry to `.claude-plugin/marketplace.json`:

1. Read the current marketplace.json
2. Add the new plugin to the `plugins` array
3. Bump `metadata.version` (minor bump for new plugin)
4. Verify the entry version matches plugin.json version

## Step 4 — Update README.md

Add a section for the new plugin in README.md following the existing format:
- Plugin heading with brief description
- Agent table (Agent, Model, Role)
- Commands list with usage examples
- Skills table (Skill, When It Activates)

## Step 5 — Validate

Run the validation checklist from the `plugin-architecture` skill:

- [ ] plugin.json name matches directory name
- [ ] plugin.json version matches marketplace.json entry version
- [ ] All agent .md files have valid frontmatter (name, description, model)
- [ ] All SKILL.md files have valid frontmatter (name, description)
- [ ] All commands reference $ARGUMENTS
- [ ] README.md documents the new plugin

## Output

Present a summary:

```
Created {plugin-name}/:
  ✓ .claude-plugin/plugin.json (v1.0.0)
  ✓ agents/{agent}.md ({model})
  ✓ skills/{skill}/SKILL.md
  ✓ commands/{command}.md (if any)
  ✓ marketplace.json updated (v{new-version})
  ✓ README.md updated

Install with:
  /plugin install {plugin-name}
```
