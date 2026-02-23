---
name: marketplace-management
description: "Manage the moctarjallo/skills marketplace — add/remove plugins, bump versions, validate marketplace.json, update README.md, and ensure consistency between plugin.json files and the marketplace registry. Use when adding a new plugin to the marketplace, releasing a new version, auditing marketplace accuracy, or updating the README."
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Marketplace Management

This skill covers maintaining the moctarjallo/skills marketplace registry,
ensuring consistency between plugins and the catalog, and keeping documentation
current.

## Adding a New Plugin

### Step 1 — Verify Plugin Structure

Before adding to the marketplace, verify the plugin is complete:

```bash
# Check required files
ls plugins/{name}/.claude-plugin/plugin.json
ls plugins/{name}/skills/*/SKILL.md 2>/dev/null
ls plugins/{name}/agents/*.md 2>/dev/null
ls plugins/{name}/commands/*.md 2>/dev/null
```

Read `plugin.json` and verify it has valid name, version, description, author,
and license fields.

### Step 2 — Add to marketplace.json

Add a new entry to the `plugins` array in `.claude-plugin/marketplace.json`:

```json
{
  "name": "new-plugin",
  "source": "./plugins/new-plugin",
  "description": "What this plugin provides",
  "version": "1.0.0",
  "author": {
    "name": "Moctar Diallo",
    "email": "moctarjallo@gmail.com"
  },
  "homepage": "https://github.com/moctarjallo/skills",
  "license": "MIT",
  "category": "frameworks"
}
```

Categories: `languages`, `frameworks`, `ai`, `tools`, `devops`

### Step 3 — Bump Marketplace Version

Increment `metadata.version` in marketplace.json. Use semver:
- Adding a new plugin → minor bump (1.5.3 → 1.6.0)
- Updating existing plugins → patch bump (1.5.3 → 1.5.4)
- Breaking changes (renamed plugins, removed components) → major bump

### Step 4 — Update README.md

Add a section for the new plugin in README.md following this template:

```markdown
## `{plugin-name}` Plugin

### Agents

| Agent | Model | Role |
|---|---|---|
| `agent-name` | Opus/Sonnet/Haiku | One-line role description |

### Commands

- **`/plugin-name:command-name`** — What it does

### Skills

| Skill | When It Activates |
|---|---|
| `skill-name` | Trigger condition description |
```

## Bumping a Plugin Version

### Step 1 — Determine Bump Type

| Change | Bump |
|--------|------|
| New agent, skill, or command | Minor (x.Y.0) |
| Fix or improvement to existing component | Patch (x.y.Z) |
| Renamed/removed component, changed interfaces | Major (X.0.0) |

### Step 2 — Update plugin.json

```bash
# Edit plugins/{name}/.claude-plugin/plugin.json
# Change "version": "1.0.0" → "version": "1.1.0"
```

### Step 3 — Update marketplace.json

The plugin's version in marketplace.json must match plugin.json:

```bash
# Find and update the version in marketplace.json plugins array
```

Also bump `metadata.version` (patch for plugin updates, minor for new plugins).

### Step 4 — Update README if Needed

If the change adds or removes components, update the relevant plugin section
in README.md.

## Auditing the Marketplace

Run these checks to verify marketplace consistency:

### 1. Plugin Count

```bash
ACTUAL=$(ls -d plugins/*/ 2>/dev/null | wc -l)
DECLARED=$(python3 -c "
import json
m = json.load(open('.claude-plugin/marketplace.json'))
print(len(m['plugins']))
")
echo "Directories: $ACTUAL, In marketplace.json: $DECLARED"
```

Every plugin directory should have a marketplace.json entry and vice versa.

### 2. Version Sync

```bash
python3 -c "
import json, os
m = json.load(open('.claude-plugin/marketplace.json'))
for p in m['plugins']:
    pj_path = os.path.join(p['source'], '.claude-plugin', 'plugin.json')
    if os.path.exists(pj_path):
        pj = json.load(open(pj_path))
        match = '✓' if pj['version'] == p['version'] else '✗'
        print(f'{match} {p[\"name\"]}: marketplace={p[\"version\"]} plugin.json={pj[\"version\"]}')
    else:
        print(f'✗ {p[\"name\"]}: plugin.json NOT FOUND at {pj_path}')
"
```

### 3. README Accuracy

Check that every plugin listed in marketplace.json has a corresponding section
in README.md, and that agent/skill/command tables match the actual files on disk.

### 4. Description Accuracy

Verify that `marketplace.json` `metadata.description` accurately reflects the
actual plugin count and scope. Update if inflated or outdated.

## Removing a Plugin

1. Remove the directory: `rm -rf plugins/{name}/`
2. Remove the entry from marketplace.json `plugins` array
3. Bump marketplace version (minor if the plugin had users, patch otherwise)
4. Remove the plugin section from README.md
5. Check if other plugins cross-reference the removed plugin's skills or agents
