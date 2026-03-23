---
name: odoo-controller-patterns
description: Odoo 18 HTTP controller and webhook patterns — use when writing HTTP routes, JSON-RPC endpoints, webhook receivers, or QWeb page controllers.
---

# Odoo Controller Patterns

## Route Options

```python
@http.route(
    "/mymodule/endpoint",   # URL — supports <type:param> variables
    type="json",            # "json" (auto-parse body) or "http" (raw)
    auth="user",            # "user", "public", or "none"
    methods=["POST"],       # HTTP methods to accept
    csrf=False,             # Disable CSRF for external webhooks
)
```

| `auth` | Session required | Use for |
|--------|-----------------|---------|
| `user` | Yes | Authenticated internal endpoints |
| `public` | No | Public pages, external webhooks |
| `none` | No | Low-level, handle auth yourself |

## JSON Endpoint (authenticated)

```python
from odoo import http
from odoo.http import request

class MyController(http.Controller):

    @http.route("/mymodule/api/action", type="json", auth="user", methods=["POST"])
    def my_action(self, record_id, **kwargs):
        record = request.env["mymodule.model"].browse(record_id)
        record.check_access_rights("write")
        record._do_action()
        return {"status": "success", "id": record.id}
```

## Webhook Receiver (external POST, public)

```python
import logging
_logger = logging.getLogger(__name__)

class MyController(http.Controller):

    @http.route("/mymodule/webhook/<int:record_id>", type="json",
                auth="public", methods=["POST"], csrf=False)
    def webhook(self, record_id, **kwargs):
        try:
            record = request.env["mymodule.model"].sudo().browse(record_id)
            if not record.exists():
                return {"status": "error", "message": "Not found"}
            payload = request.get_json_data()
            record._process_webhook(payload)
            return {"status": "success"}
        except Exception as e:
            _logger.error("Webhook error: %s", e, exc_info=True)
            return {"status": "error", "message": str(e)}
```

## QWeb Page Controller (public HTML page)

```python
@http.route("/mymodule/page/<int:record_id>", type="http", auth="public")
def public_page(self, record_id, **kwargs):
    record = request.env["mymodule.model"].sudo().browse(record_id)
    if not record.exists():
        return request.not_found()
    return request.render("mymodule.template_public_page", {"record": record})
```

## URL Parameter Types

```python
# Integer
@http.route("/mymodule/<int:record_id>", ...)

# String
@http.route("/mymodule/<string:slug>", ...)

# Path (captures slashes)
@http.route("/mymodule/<path:subpath>", ...)
```
