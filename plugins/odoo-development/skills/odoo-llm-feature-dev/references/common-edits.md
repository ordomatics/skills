# Common In-Place Edits Reference

Ready-to-use snippets for the most frequent modifications to existing modules.

## Table of Contents

1. [Add a plain field](#1-add-a-plain-field)
2. [Add a computed field](#2-add-a-computed-field)
3. [Add a relational field](#3-add-a-relational-field)
4. [Add a selection option](#4-add-a-selection-option)
5. [Patch create()](#5-patch-create)
6. [Patch write()](#6-patch-write)
7. [Add a constraint](#7-add-a-constraint)
8. [Add a public action method](#8-add-a-public-action-method)
9. [Add xpath to an existing view](#9-add-xpath-to-an-existing-view)
10. [Add a field to a list view](#10-add-a-field-to-a-list-view)
11. [Add a field to a form group](#11-add-a-field-to-a-form-group)
12. [Add a notebook page](#12-add-a-notebook-page)
13. [Add an ir.model.access.csv row](#13-add-an-irmodelaccess-csv-row)
14. [Add an ir.rule](#14-add-an-irrule)
15. [Add a new dependency](#15-add-a-new-dependency)
16. [Add a new data file to manifest](#16-add-a-new-data-file-to-manifest)
17. [Add a Many2many field with tag widget](#17-add-a-many2many-field-with-tag-widget)
18. [Add a stat button](#18-add-a-stat-button)
19. [Fix a selection field default](#19-fix-a-selection-field-default)
20. [Add index to an existing field](#20-add-index-to-an-existing-field)

---

## 1. Add a plain field

Add after the last field of the same type. Keep field definitions grouped:
scalars first, then relational, then computed.

```python
# Scalar fields
my_field = fields.Char(string="My Field")
my_flag = fields.Boolean(string="Enabled", default=False)
my_count = fields.Integer(string="Count", default=0)
my_date = fields.Date(string="Due Date")
my_datetime = fields.Datetime(string="Processed At")
my_amount = fields.Float(string="Amount", digits=(16, 2))
my_text = fields.Text(string="Notes")
my_html = fields.Html(string="Content")
my_json = fields.Json(string="Details")
```

---

## 2. Add a computed field

```python
# Field definition (near other computed fields at the bottom of the field block)
my_computed = fields.Integer(
    string="Item Count",
    compute="_compute_my_computed",
    store=True,   # add if used in domain filters or sorted on
    index=True,   # add only when store=True and used in search
)

# Compute method (after field definitions, before create/write)
@api.depends("item_ids")
def _compute_my_computed(self):
    for record in self:
        record.my_computed = len(record.item_ids)
```

**Rules:**
- Always iterate `for record in self:` — never assume `self` is a single record in compute methods.
- `store=True` triggers recompute on dependency change and makes the value available in SQL.
- If the compute touches many records, use `read_group` for performance instead of iterating.

---

## 3. Add a relational field

```python
# Many2one (FK)
provider_id = fields.Many2one(
    "llm.provider",
    string="Provider",
    required=True,
    ondelete="cascade",  # or "set null" / "restrict"
    index=True,
)

# One2many (inverse of Many2one)
item_ids = fields.One2many(
    "llm.item",           # the child model
    "parent_id",          # the Many2one field on the child
    string="Items",
)

# Many2many
tag_ids = fields.Many2many(
    "llm.tag",
    string="Tags",
)

# Many2many with explicit relation table (needed when >1 M2M between same models)
tool_ids = fields.Many2many(
    "llm.tool",
    "llm_feature_tool_rel",   # relation table name
    "feature_id",             # column for this model
    "tool_id",                # column for the other model
    string="Tools",
)
```

---

## 4. Add a selection option

Locate the `Selection` field definition. Append the new tuple:

```python
# Before
state = fields.Selection([
    ("draft", "Draft"),
    ("active", "Active"),
], default="draft")

# After — add new option at the logical position
state = fields.Selection([
    ("draft", "Draft"),
    ("active", "Active"),
    ("archived", "Archived"),   # ← new
], default="draft")
```

If the selection drives a `statusbar_visible` attribute in a view, update that too:
```xml
<field name="state" widget="statusbar" statusbar_visible="draft,active,archived"/>
```

---

## 5. Patch create()

If `create()` already exists, add your logic inside it. If it doesn't, add it
after the field definitions and before any `write()` override.

```python
@api.model_create_multi
def create(self, vals_list):
    records = super().create(vals_list)
    for record in records:
        # your post-create logic
        record._my_post_create_hook()
    return records
```

**Don't** add a second `create()` — only one can exist per class in Python.

---

## 6. Patch write()

```python
def write(self, vals):
    # Capture state before the write if needed
    old_states = {r.id: r.state for r in self} if "state" in vals else {}

    result = super().write(vals)

    if "state" in vals:
        for record in self:
            record._on_state_changed(old_states.get(record.id))

    return result

def _on_state_changed(self, old_state):
    _logger.info("Record %s: %s → %s", self.id, old_state, self.state)
```

---

## 7. Add a constraint

```python
@api.constrains("name", "provider_id")
def _check_unique_name_per_provider(self):
    for record in self:
        duplicate = self.search([
            ("name", "=", record.name),
            ("provider_id", "=", record.provider_id.id),
            ("id", "!=", record.id),
        ], limit=1)
        if duplicate:
            raise ValidationError(
                _("A record named '%s' already exists for this provider.") % record.name
            )
```

---

## 8. Add a public action method

Action methods return an `ir.actions` dict or `None`. Always call `ensure_one()`
unless the method is explicitly designed for multi-record operation.

```python
def action_do_something(self):
    self.ensure_one()
    if self.state != "draft":
        raise UserError(_("Only draft records can be processed."))

    # business logic
    self.state = "active"

    # Return an action to open a related view, or nothing
    return {
        "type": "ir.actions.act_window",
        "res_model": "llm.result",
        "view_mode": "list,form",
        "domain": [("source_id", "=", self.id)],
        "target": "current",
    }

# Multi-record version (no ensure_one)
def action_bulk_activate(self):
    self.filtered(lambda r: r.state == "draft").write({"state": "active"})
```

---

## 9. Add xpath to an existing view

Use this when you need to add something to a view defined in another module.
Put this record in your module's view XML file.

```xml
<!-- position="after" — insert immediately after the target element -->
<xpath expr="//field[@name='model_id']" position="after">
    <field name="my_new_field" />
</xpath>

<!-- position="before" — insert before -->
<xpath expr="//field[@name='name']" position="before">
    <field name="code" />
</xpath>

<!-- position="inside" — insert as last child of the target -->
<xpath expr="//group[@name='left_group']" position="inside">
    <field name="my_field" />
</xpath>

<!-- position="replace" — replace the target entirely -->
<xpath expr="//field[@name='old_field']" position="replace">
    <field name="new_field" />
</xpath>

<!-- position="attributes" — modify attributes of the target -->
<xpath expr="//field[@name='name']" position="attributes">
    <attribute name="readonly">state != 'draft'</attribute>
</xpath>

<!-- Targeting by element type + position -->
<xpath expr="//sheet/group[1]" position="before">
    <div class="alert alert-warning" invisible="active">
        This record is archived.
    </div>
</xpath>
```

---

## 10. Add a field to a list view

```xml
<!-- Inside an existing <list> — add after the field you want it next to -->
<field name="my_new_field" />

<!-- With decoration -->
<field name="state"
       decoration-success="state == 'active'"
       decoration-warning="state == 'draft'"
       decoration-muted="state == 'done'" />

<!-- Optional column with widget -->
<field name="amount" widget="monetary" optional="show" />
```

---

## 11. Add a field to a form group

```xml
<!-- Inside a <group> -->
<field name="my_new_field" />

<!-- With inline attrs (Odoo 18 — no attrs= needed) -->
<field name="my_field"
       invisible="state != 'active'"
       required="state == 'active'"
       readonly="state == 'done'" />

<!-- With a widget -->
<field name="details" widget="json" />
<field name="tag_ids" widget="many2many_tags" options="{'no_create': True}" />
```

---

## 12. Add a notebook page

```xml
<!-- Inside an existing <notebook> element -->
<page string="My New Tab" invisible="not my_field">
    <group>
        <field name="my_field" />
    </group>
</page>
```

If the `<notebook>` doesn't exist yet, add it after the last `<group>` inside `<sheet>`.

---

## 13. Add an ir.model.access.csv row

Append a new line to the CSV. Never reorder existing lines — Odoo uses the
`id` column for upgrades.

```csv
# New line — user read/write/create, no unlink
access_llm_mymodel_user,llm.mymodel user,model_llm_mymodel,base.group_user,1,1,1,0

# New line — manager full access
access_llm_mymodel_manager,llm.mymodel manager,model_llm_mymodel,base.group_system,1,1,1,1

# Portal user — read only
access_llm_mymodel_portal,llm.mymodel portal,model_llm_mymodel,base.group_portal,1,0,0,0
```

Column order: `id, name, model_id:id, group_id:id, perm_read, perm_write, perm_create, perm_unlink`

The `model_id:id` value is always `model_` + the model's `_name` with dots replaced by underscores.
For `llm.my.model` → `model_llm_my_model`.

---

## 14. Add an ir.rule

Add inside the `<data noupdate="1">` block in the security XML:

```xml
<record id="rule_llm_mymodel_own" model="ir.rule">
    <field name="name">LLM My Model: own records</field>
    <field name="model_id" ref="model_llm_mymodel" />
    <field name="domain_force">[('create_uid', '=', user.id)]</field>
    <field name="perm_read" eval="True" />
    <field name="perm_write" eval="True" />
    <field name="perm_create" eval="True" />
    <field name="perm_unlink" eval="False" />
    <field name="groups" eval="[(4, ref('base.group_user'))]" />
</record>
```

---

## 15. Add a new dependency

In `__manifest__.py`:

```python
# Odoo module dependency
"depends": ["llm", "llm_thread", "mail"],   # add the module name

# Python package dependency
"external_dependencies": {"python": ["new-package>=2.0"]},
```

After adding a Python package, it must be installed in the container:
```bash
docker compose exec odoo pip install new-package
# or rebuild the image if it's a permanent dependency
```

---

## 16. Add a new data file to manifest

```python
"data": [
    "security/ir.model.access.csv",
    "security/llm_feature_security.xml",
    "data/llm_feature_data.xml",      # ← new data file
    "views/llm_feature_views.xml",
    "wizards/llm_feature_wizard_views.xml",  # ← new wizard view
],
```

Order matters: security files must come before views; data files that reference
records from views should come after.

---

## 17. Add a Many2many field with tag widget

```python
# Model
tag_ids = fields.Many2many("llm.tag", string="Tags")
```

```xml
<!-- View -->
<field name="tag_ids"
       widget="many2many_tags"
       options="{'color_field': 'color', 'no_create': True}" />
```

---

## 18. Add a stat button

Requires a computed count field on the model:

```python
# Model
related_count = fields.Integer(
    compute="_compute_related_count", string="Related"
)

@api.depends("related_ids")
def _compute_related_count(self):
    for record in self:
        record.related_count = len(record.related_ids)

def action_view_related(self):
    self.ensure_one()
    return {
        "type": "ir.actions.act_window",
        "res_model": "llm.related",
        "view_mode": "list,form",
        "domain": [("parent_id", "=", self.id)],
    }
```

```xml
<!-- View — inside <div class="oe_button_box" name="button_box"> -->
<button name="action_view_related"
        type="object"
        class="oe_stat_button"
        icon="fa-list"
        invisible="related_count == 0">
    <field name="related_count" widget="statinfo" string="Related" />
</button>
```

---

## 19. Fix a selection field default

```python
# Wrong default that doesn't match any option
state = fields.Selection([("draft","Draft"),("done","Done")], default="pending")

# Fixed
state = fields.Selection([("draft","Draft"),("done","Done")], default="draft")
```

After fixing, run a migration or update query if the DB already has invalid values:
```sql
UPDATE llm_mymodel SET state = 'draft' WHERE state NOT IN ('draft', 'done');
```

---

## 20. Add index to an existing field

When a field is frequently used in `search()` domain filters or `order=` clauses,
add `index=True`. This requires a module update to apply the DB index.

```python
# Before
name = fields.Char(required=True)

# After
name = fields.Char(required=True, index=True)
```

```bash
# Apply the index with a module update
docker compose exec odoo odoo-bin -d <db> -u <module> --stop-after-init
```
