---
name: odoo-whatsapp-templates
description: WhatsApp template definition and management — use when creating or registering WhatsApp message templates, understanding the Meta approval workflow, mapping template variables to Odoo fields, or debugging template status issues.
---

# WhatsApp Templates

## Template Definition (XML)

```xml
<record id="whatsapp_template_mytemplate" model="whatsapp.template">
    <field name="name">my_template_name</field>
    <field name="body">Hello {{1}}, your order {{2}} is confirmed.</field>
    <field name="wa_account_id" ref="base_setup.whatsapp_account_demo"/>
    <field name="status">approved</field>
    <field name="model_id" ref="sale.model_sale_order"/>
</record>
```

## Template Fields Reference

| Field | Type | Description |
|-------|------|-------------|
| `name` | Char | Template name — must match Meta-approved name exactly |
| `body` | Text | Message body with `{{N}}` variable placeholders (1-indexed) |
| `wa_account_id` | Many2one | WhatsApp Business Account |
| `model_id` | Many2one | Odoo model this template applies to |
| `status` | Selection | `draft`, `pending`, `approved`, `rejected` |
| `lang_ids` | Many2many | Supported languages (ISO codes, e.g. `en_US`, `fr_FR`) |

## Variable Placeholders

Variables use `{{N}}` syntax (1-indexed). Map them to model fields via
`whatsapp.template.variable`:

```xml
<record id="var_1_partner_name" model="whatsapp.template.variable">
    <field name="template_id" ref="whatsapp_template_mytemplate"/>
    <field name="name">{{1}}</field>
    <field name="line_type">field</field>
    <field name="field_id" ref="base.field_res_partner__name"/>
</record>

<record id="var_2_order_name" model="whatsapp.template.variable">
    <field name="template_id" ref="whatsapp_template_mytemplate"/>
    <field name="name">{{2}}</field>
    <field name="line_type">field</field>
    <field name="field_id" ref="sale.field_sale_order__name"/>
</record>
```

`line_type` options: `field` (Odoo field), `free_text` (static), `ref_name` (related field)

## Template Status Workflow

```
draft → pending (submitted to Meta) → approved / rejected
```

- In development: set `status = "approved"` directly on demo data records
- Production: templates must be approved by Meta before sending
- Rejected templates require content revision + resubmission to Meta
- Template name must be unique per WhatsApp Business Account

## Referencing a Template in Code

```python
template = self.env.ref("my_module.whatsapp_template_mytemplate")
# Pass to whatsapp.message.create() — see odoo-whatsapp-messaging skill
```
