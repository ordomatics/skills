# Odoo Module Patterns Reference

Complete copy-paste-ready patterns for every file type in an odoo-llm module.

## Table of Contents

1. [__manifest__.py](#1-manifestpy)
2. [__init__.py files](#2-initpy-files)
3. [Model — base model](#3-model--base-model)
4. [Model — provider extension](#4-model--provider-extension)
5. [Model — feature module (inherit)](#5-model--feature-module-inherit)
6. [Model — mail.message extension](#6-model--mailmessage-extension)
7. [Views — list + form + search + action + menu](#7-views--list--form--search--action--menu)
8. [Views — inheritance with xpath](#8-views--inheritance-with-xpath)
9. [Security — ir.model.access.csv](#9-security--irmodelaccess-csv)
10. [Security — XML rules](#10-security--xml-rules)
11. [Wizard](#11-wizard)
12. [Controller / Webhook](#12-controller--webhook)
13. [Tests](#13-tests)
14. [Data — mail message subtypes](#14-data--mail-message-subtypes)

---

## 1. __manifest__.py

```python
{
    "name": "LLM Feature Name",
    "version": "18.0.1.0.0",
    "category": "Technical",
    "summary": "One-line description of what this module adds",
    "description": """
LLM Feature Name
================
Longer description of the module. What it does, what problem it solves.

Features:
- Feature 1
- Feature 2
    """,
    "author": "Ordomatics",
    "website": "https://ordomatics.com",
    "license": "LGPL-3",
    "depends": [
        "llm",
        # Add as needed: "llm_thread", "llm_tool", "llm_assistant", "mail", "queue_job"
    ],
    # Only needed if module requires pip packages
    # "external_dependencies": {"python": ["package-name>=1.0"]},
    "data": [
        "security/llm_feature_security.xml",
        "security/ir.model.access.csv",
        "views/llm_feature_views.xml",
        # "views/llm_feature_menu.xml",  # if menus are in a separate file
        # "data/llm_feature_data.xml",
        # "wizards/llm_feature_wizard_views.xml",
    ],
    # "assets": {
    #     "web.assets_backend": [
    #         "llm_feature/static/src/components/**/*.js",
    #         "llm_feature/static/src/components/**/*.xml",
    #     ],
    # },
    "installable": True,
    "auto_install": False,
    "application": False,
}
```

---

## 2. __init__.py files

**Root `__init__.py`:**
```python
from . import models
# from . import wizards
# from . import controllers
```

**`models/__init__.py`:**
```python
from . import llm_feature
# from . import mail_message  # if extending mail.message
```

**`wizards/__init__.py`** (if applicable):
```python
from . import llm_feature_wizard
```

**`controllers/__init__.py`** (if applicable):
```python
from . import main
```

**`tests/__init__.py`:**
```python
from . import test_llm_feature
```

---

## 3. Model — base model

```python
# models/llm_feature.py
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class LLMFeature(models.Model):
    _name = "llm.feature"
    _description = "LLM Feature"
    _inherit = ["mail.thread"]   # remove if chatter not needed
    _order = "name"
    _rec_name = "name"

    name = fields.Char(string="Name", required=True, index=True)
    active = fields.Boolean(default=True)
    provider_id = fields.Many2one(
        "llm.provider",
        string="Provider",
        required=True,
        ondelete="cascade",
        index=True,
    )
    description = fields.Text(string="Description")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("done", "Done"),
        ],
        default="draft",
        required=True,
        index=True,
    )
    details = fields.Json(string="Details")

    # ── Computed ──────────────────────────────────────────────────────────────

    @api.depends("provider_id", "name")
    def _compute_display_name(self):
        for record in self:
            if record.provider_id:
                record.display_name = f"{record.provider_id.name} / {record.name}"
            else:
                record.display_name = record.name or ""

    # ── Constraints ───────────────────────────────────────────────────────────

    @api.constrains("name", "provider_id")
    def _check_unique_name_per_provider(self):
        for record in self:
            duplicate = self.search([
                ("name", "=", record.name),
                ("provider_id", "=", record.provider_id.id),
                ("id", "!=", record.id),
            ])
            if duplicate:
                raise ValidationError(
                    _("A feature named '%s' already exists for this provider.") % record.name
                )

    # ── CRUD hooks ────────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            record._on_create()
        return records

    def write(self, vals):
        result = super().write(vals)
        if "state" in vals:
            self._on_state_changed()
        return result

    # ── Actions ───────────────────────────────────────────────────────────────

    def action_activate(self):
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft features can be activated."))
        self.state = "active"

    def action_reset_to_draft(self):
        for record in self:
            record.state = "draft"

    # ── Private helpers ───────────────────────────────────────────────────────

    def _on_create(self):
        _logger.info("LLM feature created: %s (id=%s)", self.name, self.id)

    def _on_state_changed(self):
        for record in self:
            _logger.info("Feature %s state → %s", record.id, record.state)
```

---

## 4. Model — provider extension

```python
# models/llm_myservice_provider.py
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Install with: pip install myservice-sdk
try:
    from myservice import Client as MyServiceClient
except ImportError:
    MyServiceClient = None


class LLMProvider(models.Model):
    _inherit = "llm.provider"

    # ── Service registration ──────────────────────────────────────────────────

    @api.model
    def _get_available_services(self):
        return super()._get_available_services() + [("myservice", "My Service")]

    # ── Client ────────────────────────────────────────────────────────────────

    def myservice_get_client(self):
        """Called via self.client property — return the SDK client."""
        if MyServiceClient is None:
            raise UserError(_("myservice-sdk is not installed. Run: pip install myservice-sdk"))
        return MyServiceClient(api_key=self.api_key, base_url=self.api_base or None)

    # ── Core API methods ──────────────────────────────────────────────────────

    def myservice_chat(self, messages, model=None, stream=False, tools=None,
                       prepend_messages=None, **kwargs):
        model = self.get_model(model, "chat")
        if not model:
            raise UserError(_("No chat model configured for this provider."))

        formatted = self.format_messages(messages, model=model)
        if prepend_messages:
            formatted = prepend_messages + formatted

        params = {"model": model.name, "messages": formatted, "stream": stream}

        if tools:
            formatted_tools = self.format_tools(tools)
            if formatted_tools:
                params["tools"] = formatted_tools

        response = self.client.chat.completions.create(**params)

        if not stream:
            return self._myservice_process_response(response)
        return self._myservice_stream_response(response)

    def myservice_embedding(self, texts, model=None):
        model = self.get_model(model, "embedding")
        if not model:
            raise UserError(_("No embedding model configured for this provider."))
        response = self.client.embeddings.create(model=model.name, input=texts)
        return [r.embedding for r in response.data]

    def myservice_models(self, model_id=None):
        """Yield model dicts — used by the fetch-models wizard."""
        if model_id:
            m = self.client.models.retrieve(model_id)
            yield self._myservice_parse_model(m)
        else:
            for m in self.client.models.list().data:
                yield self._myservice_parse_model(m)

    def myservice_format_messages(self, messages, system_prompt=None, model=None):
        result = []
        if system_prompt:
            result.append({"role": "system", "content": system_prompt})
        for msg in messages:
            result.append({"role": msg.llm_role, "content": msg.body or ""})
        return result

    def myservice_format_tools(self, tools):
        """Convert llm.tool records to provider API format."""
        result = []
        for tool in tools:
            result.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.parameters or {},
                },
            })
        return result

    def myservice_normalize_prepend_messages(self, messages):
        """Convert prepend messages to provider format (passthrough by default)."""
        return messages

    # ── Private helpers ───────────────────────────────────────────────────────

    def _myservice_parse_model(self, model):
        return {
            "name": model.id,
            "details": {"id": model.id},
        }

    def _myservice_process_response(self, response):
        result = {}
        choice = response.choices[0]
        if choice.message.content:
            result["content"] = choice.message.content
        if getattr(choice.message, "tool_calls", None):
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in choice.message.tool_calls
            ]
        return result

    def _myservice_stream_response(self, stream):
        for chunk in stream:
            choice = chunk.choices[0] if chunk.choices else None
            delta = choice.delta if choice else None
            if not delta:
                continue
            if delta.content:
                yield {"content": delta.content}
```

---

## 5. Model — feature module (inherit)

```python
# models/llm_thread.py  (example: extending llm.thread from another module)
import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class LLMThread(models.Model):
    """Extends llm.thread with feature-specific fields."""
    _inherit = "llm.thread"

    feature_id = fields.Many2one(
        "llm.feature",
        string="Feature",
        ondelete="set null",
        index=True,
    )
    feature_enabled = fields.Boolean(
        string="Feature Enabled",
        default=False,
    )

    def _get_system_prompt(self):
        """Hook: prepend feature context to system prompt."""
        prompt = super()._get_system_prompt() if hasattr(super(), "_get_system_prompt") else ""
        if self.feature_id and self.feature_enabled:
            prompt = f"{self.feature_id.description}\n\n{prompt}"
        return prompt
```

---

## 6. Model — mail.message extension

```python
# models/mail_message.py
import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class MailMessage(models.Model):
    _inherit = "mail.message"

    feature_data = fields.Json(string="Feature Data")

    def myservice_format_message(self, is_multimodal=False):
        """Convert this mail.message to myservice API format.

        Called via provider._dispatch("format_message", record=message).
        """
        self.ensure_one()

        content = self.body or ""

        # Basic text message
        formatted = {
            "role": self.llm_role or "user",
            "content": content,
        }

        # Multimodal: attach images
        if is_multimodal:
            images = self._get_image_attachments()
            if images:
                formatted["content"] = [{"type": "text", "text": content}] + [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{img['mimetype']};base64,{img['data']}"
                        },
                    }
                    for img in images
                ]

        return formatted
```

---

## 7. Views — list + form + search + action + menu

```xml
<?xml version="1.0" encoding="utf-8" ?>
<odoo>

    <!-- ── List view ──────────────────────────────────────────────── -->
    <record id="view_llm_feature_list" model="ir.ui.view">
        <field name="name">llm.feature.list</field>
        <field name="model">llm.feature</field>
        <field name="arch" type="xml">
            <list string="Features" default_order="name">
                <field name="name" />
                <field name="provider_id" />
                <field name="state"
                       decoration-success="state == 'active'"
                       decoration-muted="state == 'done'" />
            </list>
        </field>
    </record>

    <!-- ── Form view ──────────────────────────────────────────────── -->
    <record id="view_llm_feature_form" model="ir.ui.view">
        <field name="name">llm.feature.form</field>
        <field name="model">llm.feature</field>
        <field name="arch" type="xml">
            <form>
                <header>
                    <button name="action_activate"
                            type="object"
                            string="Activate"
                            class="oe_highlight"
                            invisible="state != 'draft'" />
                    <button name="action_reset_to_draft"
                            type="object"
                            string="Reset to Draft"
                            invisible="state == 'draft'" />
                    <field name="state"
                           widget="statusbar"
                           statusbar_visible="draft,active,done" />
                </header>

                <sheet>
                    <div class="oe_title">
                        <h1>
                            <field name="name" placeholder="Feature name…" />
                        </h1>
                    </div>

                    <group>
                        <group string="Configuration">
                            <field name="provider_id" />
                        </group>
                        <group string="Status">
                            <field name="active" widget="boolean_toggle" />
                        </group>
                    </group>

                    <notebook>
                        <page string="Description">
                            <field name="description" placeholder="Describe this feature…" />
                        </page>
                        <page string="Details"
                              invisible="not details">
                            <field name="details" widget="json" />
                        </page>
                    </notebook>
                </sheet>

                <chatter />
            </form>
        </field>
    </record>

    <!-- ── Search view ────────────────────────────────────────────── -->
    <record id="view_llm_feature_search" model="ir.ui.view">
        <field name="name">llm.feature.search</field>
        <field name="model">llm.feature</field>
        <field name="arch" type="xml">
            <search>
                <field name="name" />
                <field name="provider_id" />
                <separator />
                <filter name="active" string="Active" domain="[('state', '=', 'active')]" />
                <filter name="my_features"
                        string="Mine"
                        domain="[('create_uid', '=', uid)]" />
                <group expand="0" string="Group By">
                    <filter name="group_provider"
                            string="Provider"
                            context="{'group_by': 'provider_id'}" />
                </group>
            </search>
        </field>
    </record>

    <!-- ── Action ─────────────────────────────────────────────────── -->
    <record id="action_llm_feature" model="ir.actions.act_window">
        <field name="name">Features</field>
        <field name="res_model">llm.feature</field>
        <field name="view_mode">list,form</field>
        <field name="context">{}</field>
        <field name="help" type="html">
            <p class="o_view_nocontent_smiling_face">
                Create your first feature!
            </p>
        </field>
    </record>

    <!-- ── Menu ───────────────────────────────────────────────────── -->
    <!-- Add under the LLM root menu (defined in llm module) -->
    <menuitem id="menu_llm_feature"
              name="Features"
              parent="llm.menu_llm_root"
              action="action_llm_feature"
              sequence="30" />

</odoo>
```

---

## 8. Views — inheritance with xpath

```xml
<?xml version="1.0" encoding="utf-8" ?>
<odoo>

    <!-- Add a field to an existing form view -->
    <record id="view_llm_thread_form_inherit_feature" model="ir.ui.view">
        <field name="name">llm.thread.form.inherit.feature</field>
        <field name="model">llm.thread</field>
        <field name="inherit_id" ref="llm_thread.view_llm_thread_form" />
        <field name="arch" type="xml">
            <!-- Insert after an existing field -->
            <xpath expr="//field[@name='model_id']" position="after">
                <field name="feature_id" />
                <field name="feature_enabled" />
            </xpath>
        </field>
    </record>

    <!-- Add a stat button to an existing form -->
    <record id="view_llm_provider_form_inherit_feature" model="ir.ui.view">
        <field name="name">llm.provider.form.inherit.feature</field>
        <field name="model">llm.provider</field>
        <field name="inherit_id" ref="llm.llm_provider_view_form" />
        <field name="arch" type="xml">
            <xpath expr="//div[@name='button_box']" position="inside">
                <button name="action_view_features"
                        type="object"
                        class="oe_stat_button"
                        icon="fa-cogs">
                    <field name="feature_count" widget="statinfo" string="Features" />
                </button>
            </xpath>
        </field>
    </record>

</odoo>
```

---

## 9. Security — ir.model.access.csv

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_llm_feature_user,llm.feature user,model_llm_feature,base.group_user,1,1,1,0
access_llm_feature_manager,llm.feature manager,model_llm_feature,base.group_system,1,1,1,1
```

Rules of thumb:
- Regular users: read + write + create, **no unlink** (set to 0)
- Managers (group_system or a custom group): full access (all 1)
- Public / portal users: read only (1,0,0,0) or no access at all (omit row)

---

## 10. Security — XML rules

```xml
<?xml version="1.0" encoding="utf-8" ?>
<odoo>
    <data noupdate="1">

        <!-- Optional: create a dedicated group -->
        <!--
        <record id="group_llm_feature_manager" model="res.groups">
            <field name="name">LLM Feature Manager</field>
            <field name="category_id" ref="llm.module_category_llm"/>
            <field name="implied_ids" eval="[(4, ref('base.group_user'))]"/>
        </record>
        <record id="base.group_system" model="res.groups">
            <field name="implied_ids" eval="[(4, ref('group_llm_feature_manager'))]"/>
        </record>
        -->

        <!-- Record rule: users only see their own records -->
        <record id="rule_llm_feature_own" model="ir.rule">
            <field name="name">LLM Feature: own records only</field>
            <field name="model_id" ref="model_llm_feature" />
            <field name="domain_force">[('create_uid', '=', user.id)]</field>
            <field name="perm_read" eval="True" />
            <field name="perm_write" eval="True" />
            <field name="perm_create" eval="True" />
            <field name="perm_unlink" eval="False" />
            <field name="groups" eval="[(4, ref('base.group_user'))]" />
        </record>

        <!-- Record rule: managers see everything -->
        <record id="rule_llm_feature_manager_all" model="ir.rule">
            <field name="name">LLM Feature: managers see all</field>
            <field name="model_id" ref="model_llm_feature" />
            <field name="domain_force">[(1, '=', 1)]</field>
            <field name="groups" eval="[(4, ref('base.group_system'))]" />
        </record>

    </data>
</odoo>
```

---

## 11. Wizard

### Python model

```python
# wizards/llm_feature_wizard.py
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class LLMFeatureWizardLine(models.TransientModel):
    """One selectable item in the wizard."""
    _name = "llm.feature.wizard.line"
    _description = "Feature Wizard Line"
    _rec_name = "name"

    wizard_id = fields.Many2one(
        "llm.feature.wizard", required=True, ondelete="cascade"
    )
    name = fields.Char(required=True)
    selected = fields.Boolean(default=True)
    status = fields.Selection(
        [("new", "New"), ("existing", "Existing")],
        readonly=True,
    )


class LLMFeatureWizard(models.TransientModel):
    """Multi-step wizard for bulk feature operations."""
    _name = "llm.feature.wizard"
    _description = "Feature Wizard"

    provider_id = fields.Many2one(
        "llm.provider", required=True, readonly=True
    )
    line_ids = fields.One2many("llm.feature.wizard.line", "wizard_id")
    line_count = fields.Integer(compute="_compute_line_count")

    @api.depends("line_ids")
    def _compute_line_count(self):
        for wizard in self:
            wizard.line_count = len(wizard.line_ids)

    def action_confirm(self):
        self.ensure_one()
        selected = self.line_ids.filtered(lambda l: l.selected)
        if not selected:
            raise UserError(_("Please select at least one item."))

        created = self.env["llm.feature"]
        for line in selected:
            created |= self._process_line(line)

        if not created:
            return {"type": "ir.actions.act_window_close"}

        return {
            "type": "ir.actions.act_window",
            "res_model": "llm.feature",
            "view_mode": "list,form",
            "domain": [("id", "in", created.ids)],
        }

    def _process_line(self, line):
        return self.env["llm.feature"].create({
            "name": line.name,
            "provider_id": self.provider_id.id,
        })
```

### Wizard view

```xml
<!-- wizards/llm_feature_wizard_views.xml -->
<?xml version="1.0" encoding="utf-8" ?>
<odoo>

    <record id="view_llm_feature_wizard_form" model="ir.ui.view">
        <field name="name">llm.feature.wizard.form</field>
        <field name="model">llm.feature.wizard</field>
        <field name="arch" type="xml">
            <form>
                <sheet>
                    <h2>
                        Import features for
                        <field name="provider_id" readonly="1" />
                    </h2>

                    <div class="alert alert-info"
                         role="alert"
                         invisible="line_count == 0">
                        Found <field name="line_count" /> item(s).
                        Select those you want to import.
                    </div>

                    <field name="line_ids">
                        <list editable="top">
                            <field name="selected" />
                            <field name="name" readonly="1" />
                            <field name="status" readonly="1" />
                        </list>
                    </field>
                </sheet>

                <footer>
                    <button string="Import Selected"
                            type="object"
                            name="action_confirm"
                            class="oe_highlight"
                            invisible="line_count == 0" />
                    <button string="Cancel"
                            special="cancel"
                            class="btn-secondary" />
                </footer>
            </form>
        </field>
    </record>

    <record id="action_llm_feature_wizard" model="ir.actions.act_window">
        <field name="name">Import Features</field>
        <field name="res_model">llm.feature.wizard</field>
        <field name="view_mode">form</field>
        <field name="target">new</field>
    </record>

</odoo>
```

---

## 12. Controller / Webhook

```python
# controllers/main.py
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class LLMFeatureController(http.Controller):

    @http.route(
        "/llm/feature/webhook/<int:record_id>",
        type="json",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def feature_webhook(self, record_id, **kwargs):
        """Handle async callback from external service."""
        try:
            record = request.env["llm.feature"].sudo().browse(record_id)
            if not record.exists():
                _logger.error("Feature %s not found for webhook", record_id)
                return {"status": "error", "message": "Not found"}

            payload = request.get_json_data()
            if not payload:
                return {"status": "error", "message": "Empty payload"}

            record._process_webhook(payload)

            return {"status": "success"}

        except Exception as e:
            _logger.error("Webhook error for feature %s: %s", record_id, e, exc_info=True)
            return {"status": "error", "message": str(e)}
```

---

## 13. Tests

```python
# tests/test_llm_feature.py
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestLLMFeature(TransactionCase):

    def setUp(self):
        super().setUp()
        self.provider = self.env["llm.provider"].create({
            "name": "Test Provider",
            "service": "openai",  # adjust to whatever service exists
        })

    # ── Basic CRUD ────────────────────────────────────────────────────────────

    def test_create_feature(self):
        """A feature can be created with required fields."""
        feature = self.env["llm.feature"].create({
            "name": "My Feature",
            "provider_id": self.provider.id,
        })
        self.assertEqual(feature.name, "My Feature")
        self.assertEqual(feature.state, "draft")
        self.assertTrue(feature.active)

    def test_display_name_includes_provider(self):
        """display_name shows provider / feature."""
        feature = self.env["llm.feature"].create({
            "name": "Test",
            "provider_id": self.provider.id,
        })
        self.assertIn(self.provider.name, feature.display_name)
        self.assertIn("Test", feature.display_name)

    # ── Business logic ────────────────────────────────────────────────────────

    def test_activate_from_draft(self):
        """Activating a draft feature transitions it to active."""
        feature = self.env["llm.feature"].create({
            "name": "Activatable",
            "provider_id": self.provider.id,
        })
        feature.action_activate()
        self.assertEqual(feature.state, "active")

    def test_activate_non_draft_raises(self):
        """Activating a non-draft feature raises UserError."""
        feature = self.env["llm.feature"].create({
            "name": "Already Active",
            "provider_id": self.provider.id,
            "state": "active",
        })
        with self.assertRaises(UserError):
            feature.action_activate()

    # ── Constraints ───────────────────────────────────────────────────────────

    def test_unique_name_per_provider(self):
        """Two features with the same name under the same provider raise ValidationError."""
        self.env["llm.feature"].create({
            "name": "Duplicate",
            "provider_id": self.provider.id,
        })
        with self.assertRaises(ValidationError):
            self.env["llm.feature"].create({
                "name": "Duplicate",
                "provider_id": self.provider.id,
            })
```

---

## 14. Data — mail message subtypes

```xml
<!-- data/mail_message_subtype.xml -->
<?xml version="1.0" encoding="utf-8" ?>
<odoo>
    <data noupdate="1">

        <!-- Subtype for user messages in this module's threads -->
        <record id="mt_llm_feature_user" model="mail.message.subtype">
            <field name="name">User Message</field>
            <field name="res_model">llm.feature</field>
            <field name="default" eval="False" />
            <field name="internal" eval="False" />
            <field name="sequence">10</field>
        </record>

    </data>
</odoo>
```

---

## Error handling quick-reference

```python
# Expected / user-facing error
try:
    result = self.client.do_something()
except SpecificSDKException as e:
    _logger.warning("Expected SDK error: %s", e)
    raise UserError(_("Could not complete the operation: %s") % str(e))

# Unexpected error — always log with exc_info
except Exception as e:
    _logger.error("Unexpected error in llm.feature: %s", e, exc_info=True)
    raise UserError(_("An unexpected error occurred. Check the server logs."))
```

## Import order

```python
# 1. Standard library
import json
import logging
from datetime import datetime

# 2. Third-party
from some_sdk import Client

# 3. Odoo
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.addons.mail.tools.discuss import Store

_logger = logging.getLogger(__name__)
```
