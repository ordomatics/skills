---
name: odoo-security-patterns
description: Odoo 18 security patterns — use when writing ir.model.access.csv, defining ir.rule record-level security, restricting fields to groups, applying sudo() correctly, or debugging access rights errors.
---

# Odoo Security Patterns

## ir.model.access.csv

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_mymodel_user,mymodel user,model_mymodule_mymodel,base.group_user,1,1,1,0
access_mymodel_manager,mymodel manager,model_mymodule_mymodel,base.group_system,1,1,1,1
```

Rules:
- `model_id:id` = `model_` + model `_name` with dots → underscores
- Regular users: `1,1,1,0` (no unlink)
- Managers: `1,1,1,1`
- Read-only public: `1,0,0,0`

## ir.rule — Record-Level Security

```xml
<!-- Restrict records to the owner -->
<record id="rule_mymodel_own" model="ir.rule">
    <field name="name">My Model: own records only</field>
    <field name="model_id" ref="model_mymodule_mymodel"/>
    <field name="groups" eval="[(4, ref('base.group_user'))]"/>
    <field name="domain_force">[('user_id', '=', user.id)]</field>
    <field name="perm_read" eval="True"/>
    <field name="perm_write" eval="True"/>
    <field name="perm_create" eval="True"/>
    <field name="perm_unlink" eval="False"/>
</record>

<!-- Managers bypass the rule — no rule needed, CSV gives full access -->
```

## Group-Based Field Visibility

```xml
<!-- Hide field from non-managers in view -->
<field name="cost_price" groups="base.group_system"/>

<!-- In Python: restrict field definition -->
<field name="internal_notes" groups="base.group_system"/>
```

## Restricting Menus and Actions

```xml
<menuitem id="menu_mymodel_admin"
          name="Admin Settings"
          groups="base.group_system"/>
```

## sudo() Patterns

```python
# Use sudo() when crossing model boundaries internally
record.sudo().write({"state": "done"})

# Avoid sudo() on user-facing operations — respect access rights
# Use sudo() only for:
#   - Background jobs / cron
#   - Internal system records (mail, ir.config_parameter)
#   - Crossing to models the user shouldn't directly access
```

## Debugging Access Errors

When a user gets `AccessError`:

1. Check `ir.model.access.csv` — does the group have the required permission?
2. Check `ir.rule` — does a domain filter exclude this record?
3. Use `record.check_access_rights('write')` and `record.check_access_rule('write')` in a shell to pinpoint which layer rejects
