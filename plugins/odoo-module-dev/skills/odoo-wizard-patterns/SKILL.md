---
name: odoo-wizard-patterns
description: Odoo 18 wizard patterns — use when creating a TransientModel wizard, launching it from a button or action, handling multi-record selection, or returning an action from a wizard method.
---

# Odoo Wizard Patterns

## Basic Wizard

```python
class MyWizard(models.TransientModel):
    _name = "mymodule.mywizard"
    _description = "My Wizard"

    record_id = fields.Many2one("mymodule.mymodel", required=True)
    note = fields.Text()

    def action_confirm(self):
        self.ensure_one()
        self.record_id.write({"state": "done", "note": self.note})
        return {"type": "ir.actions.act_window_close"}
```

## Multi-Record Wizard (launched from list action)

```python
class MyBatchWizard(models.TransientModel):
    _name = "mymodule.batch.wizard"
    _description = "Batch Wizard"

    line_ids = fields.Many2many(
        "mymodule.mymodel",
        default=lambda self: self._default_lines(),
    )

    @api.model
    def _default_lines(self):
        return self.env.context.get("active_ids", [])

    def action_confirm(self):
        self.line_ids.write({"state": "done"})
        return {"type": "ir.actions.act_window_close"}
```

## Launching a Wizard from a Button

```python
# On the model
def action_open_wizard(self):
    self.ensure_one()
    return {
        "type": "ir.actions.act_window",
        "res_model": "mymodule.mywizard",
        "view_mode": "form",
        "target": "new",
        "context": {"default_record_id": self.id},
    }
```

```xml
<button name="action_open_wizard" type="object" string="Open Wizard"
        invisible="state != 'draft'"/>
```

## Return Actions from Wizard

```python
# Close the dialog
return {"type": "ir.actions.act_window_close"}

# Open a record after creation
return {
    "type": "ir.actions.act_window",
    "res_model": "mymodule.mymodel",
    "res_id": new_record.id,
    "view_mode": "form",
}

# Open a filtered list
return {
    "type": "ir.actions.act_window",
    "res_model": "mymodule.mymodel",
    "view_mode": "list,form",
    "domain": [("origin_id", "=", self.record_id.id)],
}
```

## Wizard View

```xml
<record id="view_mywizard_form" model="ir.ui.view">
    <field name="name">mymodule.mywizard.form</field>
    <field name="model">mymodule.mywizard</field>
    <field name="arch" type="xml">
        <form string="My Wizard">
            <group>
                <field name="record_id"/>
                <field name="note"/>
            </group>
            <footer>
                <button name="action_confirm" type="object"
                        string="Confirm" class="btn-primary"/>
                <button string="Cancel" class="btn-secondary"
                        special="cancel"/>
            </footer>
        </form>
    </field>
</record>
```
