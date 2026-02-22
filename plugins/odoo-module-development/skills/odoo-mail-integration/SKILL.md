---
name: odoo-mail-integration
description: Odoo 18 mail.thread integration — use when adding chatter to a model, defining message subtypes, posting messages programmatically, working with followers, or serializing messages via the Odoo 18 Store API.
---

# Odoo Mail Integration

## Adding Chatter to a Model

```python
class MyModel(models.Model):
    _name = "mymodule.mymodel"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "My Model"

    name = fields.Char(tracking=True)       # tracking=True → log changes in chatter
    state = fields.Selection(tracking=True)
```

Add `<chatter/>` in the form view (Odoo 18 shorthand):

```xml
<form>
    <sheet>...</sheet>
    <chatter/>
</form>
```

## Posting Messages Programmatically

```python
# Logged note (internal, not sent to followers)
record.message_post(
    body=_("Status changed to %s.") % record.state,
    message_type="comment",
    subtype_xmlid="mail.mt_note",
)

# Message sent to followers
record.message_post(
    body=_("Your order has been confirmed."),
    message_type="email",
    subtype_xmlid="mail.mt_comment",
    partner_ids=[record.partner_id.id],
)
```

## Defining Custom Subtypes

```xml
<!-- data/mail_message_subtype_data.xml -->
<record id="mt_my_event" model="mail.message.subtype">
    <field name="name">My Event</field>
    <field name="res_model">mymodule.mymodel</field>
    <field name="default" eval="True"/>
    <field name="description">My custom event occurred</field>
</record>
```

```python
record.message_post(
    body=_("Custom event triggered."),
    subtype_id=self.env.ref("mymodule.mt_my_event").id,
)
```

## Odoo 18 Store Serialization

```python
from odoo.addons.mail.tools.discuss import Store

store = Store()
message._to_store(store)
result = store.get_result()["mail.message"][0]
```

## mail_post_autofollow

Set `mail_post_autofollow = True` on the model to automatically add message authors as followers:

```python
class MyModel(models.Model):
    _inherit = "mail.thread"
    _mail_post_access = "read"          # who can post: "read" (default) or "write"
```

## Followers

```python
# Add a follower
record.message_subscribe(partner_ids=[partner.id])

# Remove a follower
record.message_unsubscribe(partner_ids=[partner.id])

# Check followers
record.message_partner_ids
```
