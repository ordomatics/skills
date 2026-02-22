---
name: odoo-whatsapp-messaging
description: WhatsApp messaging patterns — use when adding WhatsApp message tracking to an Odoo model, sending templated messages programmatically, opening the WhatsApp composer wizard from an action button, or tracking message delivery status.
---

# WhatsApp Messaging

## Add Message Tracking to a Model

```python
class SaleOrder(models.Model):
    _inherit = "sale.order"

    whatsapp_message_ids = fields.One2many(
        "whatsapp.message", "res_id",
        domain=[("model", "=", "sale.order")],
        string="WhatsApp Messages",
    )
```

## Send a Templated Message Programmatically

```python
def action_send_whatsapp_notification(self):
    self.ensure_one()
    account = self.env["whatsapp.account"].search([], limit=1)
    if not account:
        raise UserError(_("No WhatsApp account configured."))
    template = self.env.ref("my_module.whatsapp_template_mytemplate")
    self.env["whatsapp.message"].create({
        "mobile_number": self.partner_id.mobile,
        "wa_account_id": account.id,
        "whatsapp_template_id": template.id,
        "res_id": self.id,
        "model": self._name,
    })
```

## Open the Composer Wizard from a Button

```python
def action_open_whatsapp_composer(self):
    self.ensure_one()
    return {
        "type": "ir.actions.act_window",
        "res_model": "whatsapp.composer",
        "view_mode": "form",
        "target": "new",
        "context": {
            "default_res_model": self._name,
            "default_res_id": self.id,
        },
    }
```

```xml
<button name="action_open_whatsapp_composer" type="object"
        string="Send WhatsApp" class="oe_highlight"/>
```

## Message Status Tracking

`whatsapp.message` delivery states:

| State | Meaning |
|-------|---------|
| `outgoing` | Queued for sending |
| `sent` | Delivered to WhatsApp servers |
| `delivered` | Delivered to recipient's device |
| `read` | Read by recipient |
| `failed` | Delivery failure (check `failure_reason`) |

```python
# Check if a record has unread messages
unread = self.whatsapp_message_ids.filtered(
    lambda m: m.state not in ("delivered", "read", "failed")
)
```

## Extending the Composer

To pre-fill or restrict the composer for your model:

```python
class WhatsappComposer(models.TransientModel):
    _inherit = "whatsapp.composer"

    def _get_default_template(self):
        if self.res_model == "mymodule.mymodel":
            return self.env.ref("my_module.whatsapp_template_mytemplate")
        return super()._get_default_template()
```
