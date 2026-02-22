---
name: odoo-llm-provider-dispatch
description: odoo-llm provider dispatch pattern — use when adding a new LLM provider module, extending an existing provider with new methods, or debugging dispatch routing between llm.provider and service-specific implementations.
---

# odoo-llm Provider Dispatch Pattern

The core extensibility mechanism of the odoo-llm suite. Every LLM provider
module (openai, anthropic, ollama, etc.) follows this exact pattern.

## How Dispatch Works

```python
# llm (base) defines the public interface
class LLMProvider(models.Model):
    _name = "llm.provider"

    def chat(self, messages, model=None, **kwargs):
        return self._dispatch("chat", messages, model=model, **kwargs)

    def _dispatch(self, method, *args, record=None, **kwargs):
        service_method = f"{self.service}_{method}"
        record = record if record else self
        if not hasattr(record, service_method):
            raise NotImplementedError(f"{service_method} not implemented")
        return getattr(record, service_method)(*args, **kwargs)
```

## Implementing a New Provider

```python
# llm_myprovider/models/llm_provider.py
class LLMProvider(models.Model):
    _inherit = "llm.provider"

    @api.model
    def _get_available_services(self):
        return super()._get_available_services() + [("myprovider", "My Provider")]

    # Client — accessed via self.client (cached property on base)
    def myprovider_get_client(self):
        return MySDK(api_key=self.api_key, base_url=self.api_base)

    # Required: chat completion
    def myprovider_chat(self, messages, model=None, stream=False, **kwargs):
        client = self.client
        response = client.chat(model=model or self.model_id, messages=messages)
        return response.choices[0].message.content

    # Required: message formatting
    def myprovider_format_messages(self, messages, system_prompt=None, model=None):
        formatted = []
        if system_prompt:
            formatted.append({"role": "system", "content": system_prompt})
        for msg in messages:
            formatted.append({"role": msg["role"], "content": msg["content"]})
        return formatted

    # Required: model listing
    def myprovider_models(self, model_id=None):
        for m in self.client.models.list():
            yield {"name": m.id, "details": {}}
```

## Method Naming Convention

All service methods are prefixed with `{service}_`:

| Base method | Implementation |
|-------------|---------------|
| `chat(messages)` | `myprovider_chat(messages, ...)` |
| `format_messages(messages)` | `myprovider_format_messages(messages, ...)` |
| `models(model_id)` | `myprovider_models(model_id)` |
| `get_client()` | `myprovider_get_client()` |
| `embed(text)` | `myprovider_embed(text, ...)` (optional) |
| `generate_image(prompt)` | `myprovider_generate_image(prompt, ...)` (optional) |

## Minimal __manifest__.py

```python
{
    "name": "LLM My Provider",
    "version": "18.0.1.0.0",
    "category": "Technical",
    "depends": ["llm"],
    "data": [],
    "installable": True,
    "license": "LGPL-3",
}
```
