# Validation Checklist Reference

Comprehensive validation checks for Claude Code plugin components.

## Plugin-Level Checks

```bash
# Verify plugin.json exists and is valid JSON
cat plugins/{name}/.claude-plugin/plugin.json | python3 -m json.tool

# Verify name matches directory
DIRNAME=$(basename plugins/{name})
JSONNAME=$(python3 -c "import json; print(json.load(open('plugins/{name}/.claude-plugin/plugin.json'))['name'])")
[ "$DIRNAME" = "$JSONNAME" ] && echo "PASS" || echo "FAIL: dir=$DIRNAME json=$JSONNAME"

# Verify version matches marketplace.json
PLUGIN_VER=$(python3 -c "import json; print(json.load(open('plugins/{name}/.claude-plugin/plugin.json'))['version'])")
MARKET_VER=$(python3 -c "
import json
m = json.load(open('.claude-plugin/marketplace.json'))
print(next(p['version'] for p in m['plugins'] if p['name'] == '{name}'))
")
[ "$PLUGIN_VER" = "$MARKET_VER" ] && echo "PASS" || echo "FAIL: plugin=$PLUGIN_VER marketplace=$MARKET_VER"
```

## Agent Checks

For each `.md` file in `agents/`:

- [ ] Has YAML frontmatter delimited by `---`
- [ ] Frontmatter contains `name` (matches filename minus `.md`)
- [ ] Frontmatter contains `description` (1-2 sentences, starts with verb or noun)
- [ ] Frontmatter contains `model` (one of: `opus`, `sonnet`, `haiku`)
- [ ] Body starts with "You are..." persona definition
- [ ] Contains behavioral rules, not just capability lists
- [ ] Lists available skills if the plugin has skills
- [ ] Contains "How to Approach Tasks" section with actionable steps
- [ ] Total length < 200 lines (ideal: 60-120 lines)

```bash
# Check agent frontmatter
for f in plugins/{name}/agents/*.md; do
  echo "=== $(basename $f) ==="
  head -20 "$f" | grep -E "^(name|description|model):"
done
```

## Skill Checks

For each directory in `skills/`:

- [ ] Contains `SKILL.md` (required entry point)
- [ ] SKILL.md has YAML frontmatter with `name` and `description`
- [ ] `name` in frontmatter matches directory name
- [ ] `description` includes trigger conditions ("Use when...")
- [ ] Body is under 500 lines (move overflow to references/)
- [ ] Code examples are syntactically correct and use current API versions
- [ ] Cross-references to other skills point to existing skill names
- [ ] If `references/` exists, SKILL.md tells the reader when to load each file
- [ ] If `scripts/` exists, SKILL.md documents how to invoke each script

```bash
# Check skill frontmatter and line count
for d in plugins/{name}/skills/*/; do
  SKILL="$d/SKILL.md"
  if [ -f "$SKILL" ]; then
    LINES=$(wc -l < "$SKILL")
    echo "=== $(basename $d) === ($LINES lines)"
    head -10 "$SKILL" | grep -E "^(name|description):"
    [ "$LINES" -gt 500 ] && echo "WARNING: exceeds 500 line guideline"
  else
    echo "MISSING: $SKILL"
  fi
done
```

## Command Checks

For each `.md` file in `commands/`:

- [ ] First line is a descriptive sentence (no frontmatter required for commands)
- [ ] Contains `$ARGUMENTS` reference for argument parsing
- [ ] Defines expected argument format with examples
- [ ] Has numbered steps (Step 1, Step 2, etc.)
- [ ] Steps are actionable and use imperative form
- [ ] References relevant skills or agents when cross-domain knowledge is needed
- [ ] Includes output format or summary section

```bash
# Check command structure
for f in plugins/{name}/commands/*.md; do
  echo "=== $(basename $f) ==="
  grep -c '\$ARGUMENTS' "$f" | xargs -I{} echo "  \$ARGUMENTS refs: {}"
  grep -c '^## Step\|^### [0-9]' "$f" | xargs -I{} echo "  Step sections: {}"
done
```

## Marketplace Checks

```bash
# Count actual plugins vs. declared
ACTUAL=$(ls -d plugins/*/ | wc -l)
DECLARED=$(python3 -c "import json; print(len(json.load(open('.claude-plugin/marketplace.json'))['plugins']))")
echo "Actual: $ACTUAL, Declared: $DECLARED"

# List any plugins in marketplace.json that don't exist on disk
python3 -c "
import json, os
m = json.load(open('.claude-plugin/marketplace.json'))
for p in m['plugins']:
    path = p['source']
    if not os.path.isdir(path):
        print(f'MISSING: {p[\"name\"]} -> {path}')
"
```

## README Checks

- [ ] Documents every plugin with its agents, skills, and commands
- [ ] Agent table has columns: Agent, Model, Role
- [ ] Skill table has columns: Skill, When It Activates
- [ ] Command entries show usage examples
- [ ] Quick Start section has correct installation commands
- [ ] Plugin counts and names match actual directory contents
