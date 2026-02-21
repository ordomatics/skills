---
name: odoo-module-creator
description: "Create complete, production-ready Odoo 18.0 modules. Use this skill proactively whenever the user asks to create a new Odoo module, scaffold a feature, build a wizard, add a controller/webhook, or start a new module from scratch."
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Odoo Module Creator

This skill generates complete, properly structured Odoo 18.0 modules ready to
install without modification.

## Step 1 — Clarify the Module Type

Before generating anything, determine which module type best fits the request:

| Type | When to use | Key pattern |
|------|-------------|-------------|
| **Base model** | New standalone resource | `models.Model`, security, views, menus |
| **Feature module** | Extending existing functionality | `_inherit`, view inheritance with xpath |
| **Wizard** | Multi-step user workflow | `TransientModel`, form with footer buttons |
| **Controller** | Webhook or external HTTP endpoint | `http.Controller`, `@http.route` |

Also confirm:
- **Module name** (snake_case, e.g. `myapp_feature`)
- **Model prefix** (e.g. `myapp.feature`)
- **Dependencies** (e.g. `["base", "mail"]`)
- **External Python packages** needed, if any

## Step 2 — Generate All Files

Create every file the module needs. Never create a partial module — always include
security, views, and the manifest.

### File checklist

```
{module_name}/
├── __manifest__.py          ← always
├── __init__.py              ← always
├── models/
│   ├── __init__.py          ← always
│   └── {module_name}.py     ← at least one model file
├── views/
│   └── {module_name}_views.xml  ← always (list + form + action + menu)
├── security/
│   ├── {module_name}_security.xml  ← always
│   └── ir.model.access.csv         ← always
├── wizards/                 ← if wizard type
├── controllers/             ← if controller type
└── tests/
    ├── __init__.py
    └── test_{module_name}.py  ← at least setUp + 2 test methods
```

## Step 3 — Apply the Right Patterns

### Manifest

```python
{
    "name": "Module Display Name",
    "version": "18.0.1.0.0",
    "category": "Technical",
    "summary": "One-line description",
    "author": "Your Company",
    "website": "https://yourcompany.com",
    "license": "LGPL-3",
    "depends": ["base"],
    # "external_dependencies": {"python": ["package-name"]},
    "data": [
        "security/{module_name}_security.xml",
        "security/ir.model.access.csv",
        "views/{module_name}_views.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
}
```

### Base model

```python
import logging
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class MyModel(models.Model):
    _name = "myapp.mymodel"
    _description = "My Model"
    _order = "name"

    name = fields.Char(string="Name", required=True, index=True)
    active = fields.Boolean(default=True)
    state = fields.Selection(
        [("draft", "Draft"), ("active", "Active"), ("done", "Done")],
        default="draft", required=True, index=True,
    )

    @api.depends("name")
    def _compute_display_name(self):
        for record in self:
            record.display_name = record.name or ""

    @api.model_create_multi
    def create(self, vals_list):
        return super().create(vals_list)

    def action_activate(self):
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft records can be activated."))
        self.state = "active"
```

### Views

```xml
<?xml version="1.0" encoding="utf-8" ?>
<odoo>
    <record id="view_mymodel_list" model="ir.ui.view">
        <field name="name">myapp.mymodel.list</field>
        <field name="model">myapp.mymodel</field>
        <field name="arch" type="xml">
            <list string="My Models" default_order="name">
                <field name="name"/>
                <field name="state"
                       decoration-success="state == 'active'"
                       decoration-muted="state == 'done'"/>
            </list>
        </field>
    </record>

    <record id="view_mymodel_form" model="ir.ui.view">
        <field name="name">myapp.mymodel.form</field>
        <field name="model">myapp.mymodel</field>
        <field name="arch" type="xml">
            <form>
                <header>
                    <button name="action_activate" type="object" string="Activate"
                            class="oe_highlight" invisible="state != 'draft'"/>
                    <field name="state" widget="statusbar"
                           statusbar_visible="draft,active,done"/>
                </header>
                <sheet>
                    <div class="oe_title"><h1><field name="name"/></h1></div>
                    <group>
                        <field name="active" widget="boolean_toggle"/>
                    </group>
                </sheet>
            </form>
        </field>
    </record>

    <record id="action_mymodel" model="ir.actions.act_window">
        <field name="name">My Models</field>
        <field name="res_model">myapp.mymodel</field>
        <field name="view_mode">list,form</field>
    </record>

    <menuitem id="menu_mymodel"
              name="My Models"
              parent="base.next_id_9"
              action="action_mymodel"
              sequence="10"/>
</odoo>
```

### Security

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_mymodel_user,myapp.mymodel user,model_myapp_mymodel,base.group_user,1,1,1,0
access_mymodel_manager,myapp.mymodel manager,model_myapp_mymodel,base.group_system,1,1,1,1
```

### Version string

Always `"18.0.1.0.0"` for new modules.

## Step 4 — Present the Output

After writing all files, print a brief summary:

```
Created {module_name}/:
  ✓ __manifest__.py
  ✓ __init__.py
  ✓ models/{module_name}.py
  ✓ views/{module_name}_views.xml
  ✓ security/ir.model.access.csv
  ✓ security/{module_name}_security.xml
  ✓ tests/test_{module_name}.py

Install with:
  odoo-bin -d {db} -u {module_name} --stop-after-init
```
