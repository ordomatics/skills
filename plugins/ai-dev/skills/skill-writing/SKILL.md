---
name: skill-writing
description: "Write high-quality SKILL.md files for Claude Code plugins. Covers frontmatter schema, progressive disclosure, writing style, bundled resources, and common patterns. Use when creating a new skill, improving an existing skill, or reviewing skill quality — even if the user doesn't explicitly mention 'skill', trigger this when they ask to add domain knowledge to a plugin."
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Skill Writing Guide

Skills are domain knowledge packs that load into Claude's context on demand. A good
skill turns hours of debugging into a 30-second lookup.

## SKILL.md Anatomy

```markdown
---
name: skill-name
description: "What this skill does and WHEN to use it. Be specific about trigger conditions."
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Skill Title

Brief overview of what this skill covers (1-2 sentences).

## When to Use This Skill

Bullet list of trigger conditions.

## Core Content

The actual knowledge — patterns, templates, code examples, procedures.

## Common Pitfalls

Non-obvious gotchas that save time.
```

### Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | yes | Must match the directory name exactly |
| `description` | yes | Trigger description — what it does + when to use it |
| `allowed-tools` | no | Tools the skill needs (Read, Write, Edit, Bash, Glob, Grep) |
| `compatibility` | no | Dependencies or requirements (rarely needed) |

### Writing Effective Descriptions

The `description` is the primary trigger mechanism. Claude decides whether to load
a skill based on this field alone. Make it specific and slightly "pushy":

**Weak:**
```yaml
description: Odoo security patterns
```

**Strong:**
```yaml
description: "Odoo 18 security patterns — use when writing ir.model.access.csv, defining ir.rule record-level security, restricting fields to groups, applying sudo() correctly, or debugging access rights errors."
```

The strong version lists specific trigger contexts. Include action verbs and
concrete artifacts (filenames, class names, error types) that a user would mention.

## Progressive Disclosure

Skills use a three-level loading system to manage token budget:

| Level | What loads | Size target | When |
|-------|-----------|-------------|------|
| **Metadata** | name + description | ~100 words | Always in context |
| **SKILL.md body** | Full markdown | <500 lines | When skill triggers |
| **Bundled resources** | references/, scripts/, assets/ | Unlimited | On demand from SKILL.md |

This matters because every token in context competes with the user's conversation.
Keep SKILL.md focused. Push deep documentation into references/.

### When to use references/

Move content to `references/` when:
- The SKILL.md body exceeds 400 lines
- Content is domain-specific (e.g., AWS vs GCP vs Azure variants)
- Content is rarely needed but essential when it is
- You have large code examples or templates

Always include a pointer in SKILL.md telling the reader when to load the reference:

```markdown
## Cloud Deployment

Read `references/aws.md` for AWS-specific patterns, or `references/gcp.md`
for Google Cloud. Only load the one you need.
```

### When to use scripts/

Bundle scripts when:
- A task is repetitive and deterministic (validation, formatting, scaffolding)
- The script saves the model from reinventing a multi-step process each time
- Multiple skills or commands would benefit from the same tool

Scripts can be invoked without loading their full content into context.

## Writing Patterns

### Pattern 1: Code-First Reference

Best for: API patterns, ORM patterns, framework conventions.

Lead with a working code example, then explain the rules:

```markdown
## Basic Wizard

\```python
class MyWizard(models.TransientModel):
    _name = "mymodule.mywizard"
    _description = "My Wizard"
    ...
\```

Rules:
- Always inherit TransientModel, never Model
- Use `ensure_one()` in action methods
- Return `{"type": "ir.actions.act_window_close"}` to close the dialog
```

### Pattern 2: Step-by-Step Procedure

Best for: multi-step workflows, setup procedures, debugging guides.

Number the steps. Use imperative form. Include verification:

```markdown
## Step 1 — Locate the Right Files

Use Grep to find the model definition before assuming its path:
\```bash
grep -rn "_name = \"sale.order\"" addons/
\```

## Step 2 — Read Before Editing

Read the full file. Check for _inherit chains that depend on it.

## Step 3 — Apply the Change

[specific instructions]

## Step 4 — Verify

Update the module and run tests:
\```bash
odoo-bin -d mydb -u mymodule --stop-after-init
\```
```

### Pattern 3: Decision Table

Best for: choosing between alternatives, classifying inputs.

```markdown
| Change Type | Right Approach |
|-------------|----------------|
| New field on existing model | Edit the model's .py file directly |
| New field in UI | Edit .xml; use xpath if inheriting |
| Bug in a method | Minimal targeted fix; add a regression test |
```

### Pattern 4: Gotcha List

Best for: encoding hard-won debugging knowledge.

```markdown
## Common Pitfalls

### rgba() colors are stripped by Odoo App Store
Use hex colors only: `#875A7B` not `rgba(135,90,123,0.1)`.

### `<tree>` was renamed to `<list>` in Odoo 18
Your view XML will silently fail if you use the old tag.
```

## Writing Style

1. **Imperative form**: "Read the file", "Check for violations" — not "The skill reads the file"
2. **Explain the why**: "Always iterate in compute methods — never assume single record, because Odoo calls compute on recordsets, not individual records"
3. **Concrete over abstract**: show the actual code, the actual command, the actual filename
4. **Short paragraphs**: 1-3 sentences. Skills are reference material, not essays.
5. **Tables for structured choices**: when the reader needs to pick between options
6. **Code blocks with comments**: explain non-obvious lines inline

## Skill Quality Checklist

Before finalizing a skill, verify:

- [ ] `name` in frontmatter matches directory name
- [ ] `description` lists specific trigger conditions with action verbs
- [ ] Body is under 500 lines (use references/ for overflow)
- [ ] Starts with a 1-2 sentence overview
- [ ] Code examples are syntactically correct and tested
- [ ] Code examples use the correct API version (e.g., Odoo 18 syntax, not 16)
- [ ] Cross-references point to existing skills by their exact names
- [ ] If references/ exist, SKILL.md explains when to load each one
- [ ] Common pitfalls section captures non-obvious gotchas
- [ ] No duplicated content that exists in another skill — cross-reference instead
