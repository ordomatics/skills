---
name: odoo-llm-module-creator
description: >
  Create complete, production-ready Odoo 18.0 modules following the patterns
  established in this project's odoo-llm suite. Use this skill proactively
  whenever the user asks to create a new Odoo module, add a new provider
  integration, scaffold a feature, build a wizard, add a controller/webhook,
  or extend an existing module with new models or views. Even partial requests
  like "add a model for X" or "make a new llm_ module" should trigger this skill.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Odoo Module Creator

This skill generates complete, properly structured Odoo 18.0 modules that follow
the conventions of this project's `addons/odoo-llm` suite. All generated code is
ready to install without modification.

## Step 1 — Clarify the Module Type

Before generating anything, determine which module type best fits the request.
Ask the user if it isn't obvious from their description:

| Type | When to use | Key pattern |
|------|-------------|-------------|
| **Base model** | New standalone resource (not a provider) | `models.Model`, security, views, menus |
| **Provider extension** | Adding a new LLM/API service | `_inherit = "llm.provider"`, dispatch pattern |
| **Feature module** | Extending existing llm.* functionality | `_inherit`, view inheritance with xpath |
| **Wizard** | Multi-step user workflow | `TransientModel`, form with footer buttons |
| **Controller** | Webhook or external HTTP endpoint | `http.Controller`, `@http.route` |
| **Tool module** | LLM function-calling tool | `_inherit = "llm.tool"` |

Also confirm:
- **Module name** (suggest `llm_<feature>` format)
- **Dependencies** (default: `["llm"]`; add `mail`, `queue_job`, etc. as needed)
- **External Python packages** needed, if any

## Step 2 — Generate All Files

Create every file the module needs. Never create a partial module — always include
security, views, and the manifest. Use the patterns in `references/patterns.md`.

### File checklist

```
llm_<name>/
├── __manifest__.py          ← always
├── __init__.py              ← always
├── models/
│   ├── __init__.py          ← always
│   └── llm_<name>.py        ← at least one model file
├── views/
│   └── llm_<name>_views.xml ← always (list + form + action + menu)
├── security/
│   ├── llm_<name>_security.xml  ← always (even if just a placeholder)
│   └── ir.model.access.csv      ← always
├── wizards/                 ← if wizard type
├── controllers/             ← if controller type
└── tests/
    ├── __init__.py
    └── test_llm_<name>.py   ← include at least setUp + 2 test methods
```

## Step 3 — Apply the Right Patterns

Read `references/patterns.md` for complete, copy-paste-ready code for every
pattern. Key rules to apply in every module:

### Naming
- Module directory: `llm_<feature>` (snake_case)
- Model `_name`: `"llm.<feature>"` (dotted)
- XML ids: `view_llm_<feature>_list`, `action_llm_<feature>`, `menu_llm_<feature>`
- Private methods: prefix with `_`
- Provider service methods: prefix with `<service>_` (e.g., `openai_chat`)

### Odoo 18.0 specifics — these are easy to get wrong
- Use `<list>` **not** `<tree>` in XML views
- Use `invisible="condition"` directly on elements, **not** `attrs=`
- Use `_compute_display_name` **not** `name_get()`
- Use `from odoo.addons.mail.tools.discuss import Store` for mail serialization
- Use `@api.model_create_multi` for `create()` overrides
- `<chatter/>` only when model inherits `mail.thread`

### Security
Every new model needs both files:
1. `security/llm_<name>_security.xml` — ir.rules if record-level access needed
2. `security/ir.model.access.csv` — at minimum user read + manager full access

### Version string
Always `"18.0.1.0.0"` for new modules.

## Step 4 — Provider Extension Pattern (if applicable)

When the module type is "provider extension", follow this exact structure:

```python
# models/llm_<service>_provider.py
class LLMProvider(models.Model):
    _inherit = "llm.provider"

    @api.model
    def _get_available_services(self):
        return super()._get_available_services() + [("<service>", "Display Name")]

    def <service>_get_client(self):
        """Called via self.client property"""
        return MySDK(api_key=self.api_key)

    def <service>_chat(self, messages, model=None, stream=False, **kwargs):
        model = self.get_model(model, "chat")
        formatted = self.format_messages(messages, model=model)
        response = self.client.chat(messages=formatted, model=model.name)
        if not stream:
            return self._<service>_process_response(response)
        return self._<service>_stream_response(response)

    def <service>_format_messages(self, messages, system_prompt=None, model=None):
        """Transform mail.message records into provider API format"""
        result = []
        if system_prompt:
            result.append({"role": "system", "content": system_prompt})
        for msg in messages:
            result.append({"role": msg.llm_role, "content": msg.body})
        return result

    def <service>_models(self, model_id=None):
        """Yield model dicts for the fetch-models wizard"""
        for m in self.client.list_models():
            yield {"name": m.id, "details": {}}
```

No `__manifest__.py` section for `external_dependencies` is needed unless
there's a pip package. If there is, include:
```python
"external_dependencies": {"python": ["package-name"]},
```

## Step 5 — Present the Output

After writing all files, print a brief summary:

```
Created llm_<name>/:
  ✓ __manifest__.py
  ✓ __init__.py
  ✓ models/llm_<name>.py
  ✓ views/llm_<name>_views.xml
  ✓ security/ir.model.access.csv
  ✓ security/llm_<name>_security.xml
  ✓ tests/test_llm_<name>.py

Install with:
  docker compose exec odoo odoo-bin -d <db> -u llm_<name> --stop-after-init

Test with:
  docker compose exec odoo ./run_tests.sh llm_<name>
```

## Reference

All patterns with complete code examples are in `references/patterns.md`.
Load that file when you need a specific pattern (manifest, model, view, wizard,
controller, security, test). It is organized by section so you can search
for exactly what you need.
