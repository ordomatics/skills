Validate a Claude Code plugin for structural correctness, quality, and marketplace consistency.

## Plugin: $ARGUMENTS

If no plugin name is provided, validate ALL plugins in the marketplace.

---

## Step 1 — Locate the Plugin

```bash
ls plugins/$ARGUMENTS/.claude-plugin/plugin.json
```

If the plugin doesn't exist, list available plugins and ask the user which one to validate.

## Step 2 — Structural Checks

### plugin.json

- [ ] File exists and is valid JSON
- [ ] `name` matches directory name
- [ ] `version` is valid semver (X.Y.Z)
- [ ] `description` is present and non-empty
- [ ] `author` has `name` and `email`
- [ ] `license` is present

### marketplace.json Sync

- [ ] Plugin has an entry in marketplace.json `plugins` array
- [ ] marketplace.json `version` matches plugin.json `version`
- [ ] marketplace.json `source` path resolves to the plugin directory

## Step 3 — Agent Quality Checks

For each `.md` file in `agents/`:

- [ ] Has YAML frontmatter with `---` delimiters
- [ ] `name` matches filename (minus `.md`)
- [ ] `description` is present and includes trigger phrases
- [ ] `model` is one of: `opus`, `sonnet`, `haiku`
- [ ] Opens with "You are..." persona line
- [ ] Contains prescriptive rules (not just capability lists)
- [ ] Lists available skills (if plugin has skills)
- [ ] Has "How to Approach Tasks" section
- [ ] Length: under 200 lines (flag if over, suggest trimming)

### Verbosity Assessment

Count lines dedicated to capability lists vs. behavioral rules. Flag agents
where >50% of content is capability enumeration. Suggest converting to skills
or trimming.

## Step 4 — Skill Quality Checks

For each directory in `skills/`:

- [ ] Contains `SKILL.md`
- [ ] SKILL.md has YAML frontmatter with `name` and `description`
- [ ] `name` matches directory name
- [ ] `description` includes specific trigger conditions
- [ ] Body is under 500 lines (flag with line count if over)
- [ ] Code examples use correct syntax for the target framework/version
- [ ] Cross-references point to existing skill names within the marketplace
- [ ] If `references/` exists, SKILL.md tells when to load each file
- [ ] If `scripts/` exists, SKILL.md documents invocation

## Step 5 — Command Quality Checks

For each `.md` file in `commands/`:

- [ ] First line is a descriptive sentence
- [ ] Contains `$ARGUMENTS` reference
- [ ] Defines expected argument format with examples
- [ ] Has numbered steps in imperative form
- [ ] Includes verification/cross-check step
- [ ] Defines output format

## Step 6 — Cross-Reference Integrity

Check all cross-references between components:

```bash
# Find all skill references in agents
grep -rn "skill" plugins/$ARGUMENTS/agents/ | grep -oP '`[a-z-]+`'

# Verify each referenced skill exists
for skill in $(grep -roh '`[a-z-]+`' plugins/$ARGUMENTS/agents/ | tr -d '`' | sort -u); do
  if [ -d "plugins/$ARGUMENTS/skills/$skill" ]; then
    echo "✓ $skill"
  else
    # Check other plugins too
    found=$(find plugins/*/skills -maxdepth 1 -name "$skill" -type d)
    if [ -n "$found" ]; then
      echo "✓ $skill (in another plugin: $found)"
    else
      echo "✗ $skill NOT FOUND"
    fi
  fi
done
```

## Step 7 — README Coverage

Check that the plugin is documented in README.md:

- [ ] Has a section heading matching the plugin name
- [ ] Agent table lists all agents with correct models
- [ ] Skills table lists all skills
- [ ] Commands are documented with usage examples
- [ ] No stale entries (removed components still listed)

## Output

Generate a validation report:

```
Plugin: {name} (v{version})
═══════════════════════════

Structure:     ✓ PASS (plugin.json valid, marketplace synced)
Agents:        ✓ 2/2 valid | ⚠ 1 verbose (python-pro: 158 lines, 60% capabilities)
Skills:        ✓ 8/8 valid | ⚠ 1 long (odoo-app-landing-page: 487 lines)
Commands:      ✓ 4/4 valid
Cross-refs:    ✓ All references resolve
README:        ⚠ Missing command documentation for /fix-app-store-html

Issues found: 2 warnings, 0 errors
```

Classify findings as:
- **ERROR**: broken structure, missing required files, invalid frontmatter
- **WARNING**: quality issues, verbose agents, long skills, stale documentation
- **INFO**: suggestions for improvement
