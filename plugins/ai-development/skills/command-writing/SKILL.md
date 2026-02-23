---
name: command-writing
description: "Write Claude Code slash-command workflows (.md files in commands/). Covers argument parsing, multi-step procedures, cross-referencing skills, and output formatting. Use when creating a new command, improving an existing command workflow, or adding argument handling to a plugin."
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Command Writing Guide

Commands are user-invocable workflows triggered via `/plugin-name:command-name`.
They define multi-step procedures with argument parsing.

## Command .md Anatomy

```markdown
Brief description of what this command does (first line).

## Arguments: $ARGUMENTS

Expected format and examples.

## Step 1 — [Action]

Instructions for the first step.

## Step 2 — [Action]

Instructions for the second step.

## Output

What to show the user when done.
```

Commands do NOT use YAML frontmatter (unlike agents and skills). The first
line is the description, and the structure is the instruction set.

## Argument Handling

Commands receive user input through `$ARGUMENTS`. Always:

1. Define the expected format
2. Provide examples of valid arguments
3. Handle missing or ambiguous arguments gracefully

```markdown
## Arguments: $ARGUMENTS

Expected format: `[type] [module] [description]`

Examples:
- `add sale_custom support for custom pricing per partner`
- `fix whatsapp_connector message status not updating`

If type is missing, infer it from the description or ask.
```

## Step Design

### Imperative, sequential steps

Number the steps. Start each with a verb. Make each step a complete unit:

```markdown
## Step 1 — Locate & Read

Find and read the relevant files before writing anything.

\```bash
grep -rn "_name = \"mymodule.mymodel\"" addons/
\```

Read in full:
- Every Python file you will edit
- The view file if touching UI
- `__manifest__.py`

Do not edit anything you have not read.
```

### Branching logic

When the procedure branches based on input, use a decision table:

```markdown
## Step 2 — Implement by Type

### ADD — New feature

1. Model fields / methods in .py
2. View changes in .xml
3. Security rows in ir.model.access.csv
4. Register new files in __init__.py and __manifest__.py

### FIX — Bug fix

1. Reproduce the bug mentally by reading the code path
2. Identify the root cause
3. Apply the minimal targeted fix
4. Add a regression test
```

### Cross-referencing skills and commands

When a step needs domain knowledge from a skill, reference it:

```markdown
### ADD — New module

If the change requires a new module, use the `odoo-module-creator` skill.
```

When a step chains to another command:

```markdown
## Step 4 — Bump Version

Run `/bump-version {module}` to update the version and changelog.
```

## Verification Steps

End with a verification checklist that ensures completeness:

```markdown
## Step 3 — Cross-Check

After implementing, verify:

- [ ] Every new .py file is imported in __init__.py
- [ ] Every new .xml file is listed in __manifest__.py
- [ ] No inheriting model is broken by the change
- [ ] If a stored field was added/removed: migration script exists
```

## Output Format

Tell the command what to produce at the end:

```markdown
## Output

Provide a summary of:
- Files modified
- New version number
- Changelog entries added
- Any documentation that may need manual review
```

## Command Patterns

### Scaffold Command

Creates files from a template. Examples: `python-scaffold`, `odoo-module-creator`.

Structure:
1. Clarify what to create (project type, module type)
2. Generate all files (never partial output)
3. Present a summary with file list

### Transform Command

Modifies existing code. Examples: `implement`, `fix-app-store-html`.

Structure:
1. Locate and read the target files
2. Classify the change type
3. Apply the transformation
4. Cross-check for side effects
5. Verify the result

### Validate Command

Checks code for issues. Examples: `check-module`.

Structure:
1. Define what to check (list of checks)
2. Run each check with pass/fail criteria
3. Report findings with file:line references
4. Suggest fixes for each issue

### Metadata Command

Updates project metadata. Examples: `bump-version`.

Structure:
1. Read current state
2. Ask user for input (version type, changelog entries)
3. Update the metadata files
4. Check documentation for staleness
5. Summarize changes

## Command Quality Checklist

- [ ] First line is a brief description of the command
- [ ] `$ARGUMENTS` is referenced and format is documented with examples
- [ ] Steps are numbered and use imperative form
- [ ] Each step is a complete, actionable unit
- [ ] Cross-references to skills/commands point to existing components
- [ ] Verification/cross-check step exists
- [ ] Output format is defined
- [ ] Missing/ambiguous arguments are handled (infer or ask)
