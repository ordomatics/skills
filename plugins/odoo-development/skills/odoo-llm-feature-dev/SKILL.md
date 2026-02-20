---
name: odoo-llm-feature-dev
description: "Add fields, fix bugs, extend views, and modify business logic inside existing odoo-llm modules. Use this skill proactively when the user asks to add a field, fix a bug, add a method, extend a view, change business logic, update security, or modify anything in an already-existing module — any change that touches existing files rather than scaffolding a new module."
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Odoo LLM Feature Developer

This skill handles modifications to existing modules in the `addons/odoo-llm`
suite: adding fields, fixing bugs, extending views, updating security, changing
business logic — anything that lives inside files that already exist.

## Core Principle: Read Before You Write

Never modify a file you haven't read in full (or at least the relevant section).
Odoo modules have load-order dependencies, field definitions that span multiple
files, and view inheritance chains. A blind edit breaks things in non-obvious ways.

**Minimum reading before any edit:**
- The full model file being changed
- The view file if adding/moving a field to the UI
- `ir.model.access.csv` if adding a new model or field with special access
- `__manifest__.py` if adding a new file or dependency

## Step 1 — Locate the Right Files

Use Glob and Grep to find exactly what to change before touching anything.

```bash
# Find which module owns a model
grep -r "_name = \"llm.thread\"" addons/odoo-llm/

# Find all views for a model
grep -rl "model.*llm.thread" addons/odoo-llm/ --include="*.xml"

# Find a field definition
grep -rn "field_name" addons/odoo-llm/llm_thread/

# Find all files that import a class
grep -rn "from.*llm_thread" addons/odoo-llm/
```

## Step 2 — Classify the Change

Pick the right approach from the table below. Using the wrong one causes
duplicated logic, broken upgrades, or hard-to-debug view conflicts.

| Change | Right approach |
|--------|---------------|
| New field on an existing model | Edit the model's `.py` file directly |
| New field exposed in a view | Edit the `.xml` file; add inside the right `<group>` or use xpath if inheriting |
| Bug in a method | Edit the method in place; keep the fix minimal |
| New method on existing model | Append to the model's `.py` file in the correct section (see method order below) |
| Extend a view from another module | Add an `inherit_id` view record with xpath — do NOT edit the original |
| New computed field | Add field + `@api.depends` compute method; add `store=True` + `index=True` if filtered on |
| New dependency (pip package) | Add to `external_dependencies` in `__manifest__.py` |
| New data file | Add path to `"data"` list in `__manifest__.py` |
| Fix access rights | Edit `ir.model.access.csv` or the security XML |
| Add a selection option | Edit the `Selection` field definition + any related domain/filter |

## Step 3 — Apply the Change

### Adding a field

1. Read the model file to find the right position (group fields by type: Char/Int/Bool first, then relational, then computed).
2. Add the field definition.
3. If it needs a view: add it to the form/list XML in the appropriate `<group>`.
4. If it has access implications: update `ir.model.access.csv`.
5. If it is stored+indexed and used in domains: add `index=True`.

```python
# Correct: add after existing fields of the same type
my_new_field = fields.Char(string="My Field", index=True)

# Computed field: always include store=True if filtered/sorted on
computed_value = fields.Integer(
    string="Count",
    compute="_compute_computed_value",
    store=True,
)

@api.depends("related_ids")
def _compute_computed_value(self):
    for record in self:
        record.computed_value = len(record.related_ids)
```

### Adding a method

Respect the existing method order in the file — this is a strong convention:

```
1. _name, _description, _inherit, _order, _rec_name   (class attrs)
2. Field definitions
3. @api.depends / @api.constrains computed fields
4. @api.constrains validation
5. @api.model_create_multi  create()
6. write() / unlink() overrides
7. Public action methods (action_*)
8. Public API methods (called from other models)
9. Private helpers (_method_name)
```

### Fixing a bug

- Read the full method, not just the line that looks wrong.
- Check callers with Grep before changing a method signature.
- If fixing error handling, use the project's pattern:
  ```python
  except SpecificError as e:
      _logger.warning("Expected: %s", e)
      raise UserError(_("User-friendly message")) from e
  except Exception as e:
      _logger.error("Unexpected: %s", e, exc_info=True)
      raise UserError(_("Unexpected error occurred.")) from e
  ```
- Do not add extra error handling around code that can't fail.

### Extending a view (from another module)

Never edit the original view XML. Add an inherit record:

```xml
<record id="view_llm_thread_form_inherit_myfeature" model="ir.ui.view">
    <field name="name">llm.thread.form.inherit.myfeature</field>
    <field name="model">llm.thread</field>
    <field name="inherit_id" ref="llm_thread.view_llm_thread_form" />
    <field name="arch" type="xml">
        <xpath expr="//field[@name='model_id']" position="after">
            <field name="my_new_field" />
        </xpath>
    </field>
</record>
```

Common xpath positions: `after`, `before`, `inside`, `replace`, `attributes`.

### Odoo 18 rules — easy to get wrong

- `<list>` not `<tree>` in view XML
- `invisible="condition"` directly on the element, **not** `attrs=`
- `_compute_display_name` **not** `name_get()`
- `@api.model_create_multi` for `create()`, not `@api.model`
- `from odoo.addons.mail.tools.discuss import Store` for mail serialization
- Field `required=` / `readonly=` can be set in XML as domain strings: `required="state == 'draft'"`

## Step 4 — Check for Side Effects

After every edit, think through:

- **Other models** that `_inherit` this model — does your change break their assumptions?
- **Existing tests** — does any test assert the old behavior?
- **Demo data** — is there data in `data/` that references removed/renamed fields?
- **Manifest** — if you added a new `.xml` data file, is it listed in `"data"`?
- **`__init__.py`** — if you added a new `.py` file, is it imported?

## Step 5 — Run a Quick Sanity Check

After editing, verify the module can still be updated cleanly:

```bash
# Update the module (checks XML validity, model changes, security)
docker compose exec odoo odoo-bin -d <db> -u <module_name> --stop-after-init

# Run module tests
docker compose exec odoo ./run_tests.sh <module_name>
```

If the change is trivial (typo, comment, minor logic fix) and you're confident,
you can skip the update step and just inform the user how to verify.

## Reference

`references/common-edits.md` contains ready-to-use snippets for the most
frequent in-place changes: adding computed fields, fixing selection fields,
patching write/create hooks, adding xpath positions, updating access CSV rows.
