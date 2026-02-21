---
name: odoo-feature-dev
description: "Add fields, fix bugs, extend views, and modify business logic inside existing Odoo modules. Use this skill proactively when the user asks to add a field, fix a bug, add a method, extend a view, change business logic, update security, or modify anything in an already-existing module."
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Odoo Feature Developer

This skill handles modifications to existing Odoo modules: adding fields, fixing bugs,
extending views, updating security, changing business logic — anything that touches
files that already exist.

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
grep -r "_name = \"mymodule.mymodel\"" {addons_path}/

# Find all views for a model
grep -rl "model.*mymodule.mymodel" {addons_path}/ --include="*.xml"

# Find a field definition
grep -rn "field_name" {addons_path}/{module}/

# Find all files that import a class
grep -rn "from.*mymodule" {addons_path}/
```

## Step 2 — Classify the Change

| Change | Right approach |
|--------|---------------|
| New field on an existing model | Edit the model's `.py` file directly |
| New field exposed in a view | Edit the `.xml` file; add inside the right `<group>` or use xpath if inheriting |
| Bug in a method | Edit the method in place; keep the fix minimal |
| New method on existing model | Append to the model's `.py` file in the correct section |
| Extend a view from another module | Add an `inherit_id` view record with xpath — do NOT edit the original |
| New computed field | Add field + `@api.depends` compute method; add `store=True` + `index=True` if filtered on |
| New dependency (pip package) | Add to `external_dependencies` in `__manifest__.py` |
| New data file | Add path to `"data"` list in `__manifest__.py` |
| Fix access rights | Edit `ir.model.access.csv` or the security XML |
| Add a selection option | Edit the `Selection` field definition + any related domain/filter |

## Step 3 — Apply the Change

### Method order in model files

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

### Odoo 18 rules — easy to get wrong

- `<list>` not `<tree>` in view XML
- `invisible="condition"` directly on the element, **not** `attrs=`
- `_compute_display_name` **not** `name_get()`
- `@api.model_create_multi` for `create()`, not `@api.model`
- `from odoo.addons.mail.tools.discuss import Store` for mail serialization

### Extending a view (from another module)

Never edit the original view XML. Add an inherit record:

```xml
<record id="view_mymodel_form_inherit_myfeature" model="ir.ui.view">
    <field name="name">mymodel.form.inherit.myfeature</field>
    <field name="model">mymodule.mymodel</field>
    <field name="inherit_id" ref="other_module.view_mymodel_form" />
    <field name="arch" type="xml">
        <xpath expr="//field[@name='name']" position="after">
            <field name="my_new_field" />
        </xpath>
    </field>
</record>
```

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
odoo-bin -d {db} -u {module_name} --stop-after-init

# Run module tests
odoo-bin -d {db} --test-enable --stop-after-init --test-tags={module_name}
```

Adjust the command to match your project's setup (docker compose, direct, etc.).
