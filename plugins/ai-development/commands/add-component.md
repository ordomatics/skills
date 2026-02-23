Add a new component (skill, agent, or command) to an existing plugin.

## Arguments: $ARGUMENTS

Expected format: `{component-type} {plugin-name} {component-name} [description]`

Examples:
- `skill odoo-module-development odoo-cron-patterns Cron job and ir.cron patterns for scheduled actions`
- `agent python-development flask-pro Flask web development expert`
- `command odoo-module-development migrate Run database migrations for an Odoo module`

Component types: `skill`, `agent`, `command`

If the format is incomplete, infer what you can from context and ask for the rest.

---

## Step 1 — Locate the Target Plugin

```bash
ls plugins/{plugin-name}/.claude-plugin/plugin.json
```

If the plugin doesn't exist, list available plugins. If the user meant to create
a new plugin, redirect to `/ai-development:create-plugin`.

Read the plugin's current structure to understand what already exists.

## Step 2 — Create the Component

### Adding a Skill

Load the `skill-writing` skill for patterns.

1. Create the directory: `plugins/{plugin-name}/skills/{skill-name}/`
2. Create `SKILL.md` with:
   - Valid frontmatter (`name` matching directory, pushy `description`)
   - Body following the appropriate pattern (code-first, step-by-step, or decision table)
   - Under 500 lines
3. Create `references/` if the skill needs deep documentation
4. Create `scripts/` if the skill needs executable tools

### Adding an Agent

Load the `agent-writing` skill for patterns.

1. Create the file: `plugins/{plugin-name}/agents/{agent-name}.md`
2. Write with:
   - Valid frontmatter (`name`, `description` with "Use PROACTIVELY", `model`)
   - Opening "You are..." persona line
   - Behavioral rules with code examples
   - Available Skills section listing this plugin's skills
   - How to Approach Tasks section
   - Target 60-120 lines

Choose the model based on cognitive demands:
- Deep reasoning → opus
- Pattern application → sonnet
- Repetitive tasks → haiku

### Adding a Command

Load the `command-writing` skill for patterns.

1. Create the file: `plugins/{plugin-name}/commands/{command-name}.md`
2. Write with:
   - First line description
   - `$ARGUMENTS` handling with format and examples
   - Numbered steps in imperative form
   - Verification checklist
   - Output format

## Step 3 — Update Existing Agents

If adding a **skill**, check if existing agents in the plugin should reference it.
Update their "Available Skills" section:

```markdown
## Available Skills

- **`existing-skill`** — existing description
- **`new-skill`** — new skill description   ← ADD THIS
```

## Step 4 — Bump Plugin Version

Adding a component is a minor version bump:

1. Read `plugins/{plugin-name}/.claude-plugin/plugin.json`
2. Increment the minor version (e.g., `1.0.0` → `1.1.0`)
3. Update the matching entry in `.claude-plugin/marketplace.json`
4. Bump `marketplace.json` `metadata.version` (patch bump)

## Step 5 — Update README.md

Add the new component to the plugin's section in README.md:
- New agent → add row to agent table
- New skill → add row to skills table
- New command → add entry to commands list

## Step 6 — Validate

Run a quick validation:

- [ ] New component has valid structure (frontmatter, required sections)
- [ ] Name conventions followed (kebab-case throughout)
- [ ] Cross-references resolve
- [ ] Plugin version bumped in both plugin.json and marketplace.json
- [ ] README updated

## Output

```
Added {type} '{component-name}' to {plugin-name}:
  ✓ {path-to-new-file}
  ✓ Plugin version: {old} → {new}
  ✓ marketplace.json updated
  ✓ README.md updated
  ✓ Agent cross-references updated (if applicable)
```
