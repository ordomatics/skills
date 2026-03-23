---
name: odoo-widget-development
description: >
  Odoo 18 OWL widget and component development — use when building custom frontend
  components, patching existing Odoo components (Thread, Composer, Chatter, Message),
  creating client actions, registering services (reactive stores), or wiring up
  SCSS + QWeb templates for a custom UI inside Odoo 18. Covers the full stack:
  OWL component lifecycle, the patch() API, reactive services, SSE streaming,
  QWeb directives, SCSS conventions, and manifest asset bundles.
  Always trigger this skill when the user mentions OWL, client actions, patching
  Composer/Thread/Chatter, custom services, reactive state, or any JS/XML/SCSS
  work inside an Odoo module.
---

# Odoo 18 Widget / Component Development

## Directory Layout

```
my_module/
└── static/
    └── src/
        ├── components/
        │   └── my_widget/
        │       ├── my_widget.js        # OWL component
        │       ├── my_widget.xml       # QWeb template
        │       └── my_widget.scss      # Scoped styles
        ├── patches/
        │   └── some_core_patch.js      # patch() overrides
        ├── services/
        │   └── my_store_service.js     # registry service
        ├── client_actions/
        │   └── my_client_action.js     # registry client action
        └── templates/
            └── extra_templates.xml     # standalone QWeb snippets
```

Declare all JS/XML/SCSS in the module manifest under `assets`:

```python
"assets": {
    "web.assets_backend": [
        "my_module/static/src/**/*.js",
        "my_module/static/src/**/*.xml",
        "my_module/static/src/**/*.scss",
    ],
},
```

---

## 1. OWL Component Skeleton

```js
/** @odoo-module **/

import { Component, useState, useRef, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class MyWidget extends Component {
    // 1. Declare child components
    static components = { SomeChild };
    // 2. Declare the QWeb template (module_name.TemplateName)
    static template = "my_module.MyWidget";
    // 3. Declare accepted props (type-checked)
    static props = {
        record: { type: Object },
        onClose: { type: Function, optional: true },
        "*": true,   // allow extra props from parent
    };

    setup() {
        // Services
        this.orm   = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");

        // Reactive state — any assignment triggers re-render
        this.state = useState({
            isLoading: false,
            items: [],
        });

        // Reactive service (must useState-wrap for reactivity)
        this.myStore = useState(useService("my.store"));

        // DOM refs — use t-ref="myRef" in template
        this.containerRef = useRef("container");

        // Lifecycle
        onMounted(() => this.load());
    }

    async load() {
        this.state.isLoading = true;
        try {
            this.state.items = await this.orm.searchRead(
                "my.model", [], ["id", "name"]
            );
        } finally {
            this.state.isLoading = false;
        }
    }

    get filteredItems() {
        return this.state.items.filter(i => i.name);
    }

    async onItemClick(itemId) {
        await this.orm.write("my.model", [itemId], { active: false });
        this.notification.add(_t("Item archived."), { type: "success" });
        await this.load();
    }
}
```

---

## 2. QWeb Template

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<templates xml:space="preserve">
    <t t-name="my_module.MyWidget">
        <div class="o-MyWidget h-100 d-flex flex-column" t-ref="container">

            <!-- Loading spinner -->
            <div t-if="state.isLoading" class="text-center p-4">
                <i class="fa fa-spinner fa-spin" />
            </div>

            <!-- Content -->
            <div t-else="" class="flex-grow-1 overflow-auto">
                <!-- Empty state -->
                <div t-if="filteredItems.length === 0" class="p-4 text-muted text-center">
                    No items found.
                </div>

                <!-- List -->
                <t t-foreach="filteredItems" t-as="item" t-key="item.id">
                    <div
                        class="o-MyWidget-item p-3 border-bottom cursor-pointer"
                        t-att-class="{ 'o-active': item.id === state.selectedId }"
                        t-on-click="() => this.onItemClick(item.id)"
                    >
                        <span t-esc="item.name" />
                    </div>
                </t>
            </div>

            <!-- Footer with OWL slot -->
            <div class="p-3 border-top">
                <t t-slot="footer">
                    <button class="btn btn-primary" t-on-click="load">
                        <i class="fa fa-refresh me-1" /> Refresh
                    </button>
                </t>
            </div>
        </div>
    </t>
</templates>
```

**Key QWeb directives:**

| Directive | Purpose |
|-----------|---------|
| `t-name` | Template name (must be `module.ClassName`) |
| `t-if / t-else` | Conditional rendering |
| `t-foreach / t-as / t-key` | List rendering — always provide `t-key` |
| `t-esc` | Safe text output (HTML-escaped) |
| `t-raw` | Raw HTML output (only for trusted server HTML) |
| `t-att-class` | Conditional classes via object literal |
| `t-att-style` | Inline style string |
| `t-ref` | Bind DOM element to `useRef` |
| `t-on-click` | Event handler (arrow function for closures) |
| `t-model` | Two-way bind input to `state.field` |
| `t-slot` | Named slot injection |
| `t-set-slot="content"` | Fill a named slot in a child |

---

## 3. Patching Core Odoo Components

Use `patch()` from `@web/core/utils/patch` to extend existing Odoo components **without forking**.  
The patch is **merged** — you only override the methods you define.

```js
/** @odoo-module **/

import { SomeComponent } from "@mail/core/common/some_component";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { useState } from "@odoo/owl";

// Patch static properties (add child components, etc.)
patch(SomeComponent, {
    components: { ...SomeComponent.components, MyNewChild },
});

// Patch prototype (methods and getters)
patch(SomeComponent.prototype, {
    setup() {
        super.setup();                              // ALWAYS call super first
        this.myStore = useState(useService("my.store"));
        Object.assign(this.state, { myFlag: false });
    },

    get isMyContext() {
        return this.props.thread?.model === "my.model";
    },

    async myNewMethod() {
        if (!this.isMyContext) return super.myNewMethod?.();
        // custom logic
    },

    // Override getter
    get placeholder() {
        if (this.isMyContext) return "Custom placeholder…";
        return super.placeholder;
    },
});
```

**Real-world patches in llm_thread:**

| File | What it patches | Why |
|------|-----------------|-----|
| `chatter_patch.js` | `Chatter` prototype | Adds AI button + LLM thread state |
| `composer_patch.js` | `Composer` prototype | Intercepts `sendMessage` for LLM threads |
| `thread_patch.js` | `Thread` prototype | Adds LLM CSS classes & streaming scroll |
| `thread_model_patch.js` | `Thread` model (data) | Fixes URL routing for `llm.thread` |
| `message_patch.js` | `Message` component + `Message` model | Adds tool-call rendering, overrides `computeIsEmpty` |

**Pattern: guard with `isMyContext`**  
Always check a discriminating condition before overriding behavior, so normal mail threads are unaffected:

```js
async sendMessage() {
    if (this.isMyContext) {
        // ... custom send
        return;
    }
    return super.sendMessage();
}
```

---

## 4. Reactive Service (Store Pattern)

Register a singleton reactive service in the Odoo registry.  
Other components consume it via `useService("my.store")` and **must wrap with `useState()`** for reactivity.

```js
/** @odoo-module **/

import { reactive } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { Deferred } from "@web/core/utils/concurrency";

export const myStoreService = {
    dependencies: ["orm", "mail.store", "notification"],

    start(env, { orm, "mail.store": mailStore, notification }) {
        const store = reactive({
            // --- State ---
            items: new Map(),
            isReady: new Deferred(),

            // --- Computed (getters) ---
            get itemList() {
                return Array.from(this.items.values());
            },

            // --- Actions ---
            async loadItems() {
                const data = await orm.searchRead("my.model", [], ["id", "name"]);
                data.forEach(item => this.items.set(item.id, item));
                this.isReady.resolve();
            },

            async createItem(values) {
                const id = await orm.create("my.model", [values]);
                await this.loadItems();
                return id;
            },
        });

        // Bootstrap after mailStore is ready
        mailStore.isReady.then(() => store.loadItems());

        return store;
    },
};

registry.category("services").add("my.store", myStoreService);
```

**Consuming the service in a component:**

```js
setup() {
    // Without useState: changes won't re-render the component
    this.myStore = useState(useService("my.store"));
}
```

---

## 5. Client Action

A client action is a full-page (or dialog) view registered in the action registry.

```js
/** @odoo-module **/

import { Component, onWillStart, onWillDestroy, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class MyClientAction extends Component {
    static components = { MyWidget };
    static template = "my_module.MyClientAction";
    static props = ["*"];   // client actions receive arbitrary props

    setup() {
        this.myStore = useState(useService("my.store"));
        this.mailStore = useState(useService("mail.store"));

        onWillStart(async () => {
            // Wait for services, then restore state from action context
            await Promise.all([this.mailStore.isReady, this.myStore.isReady]);
            const activeId = this.props.action.context?.active_id;
            if (activeId) await this.myStore.selectItem(activeId);
        });

        onWillDestroy(() => this.cleanup());
    }

    cleanup() { /* stop streams, subscriptions, etc. */ }
}

// Register — matches the tag in ir.actions.client
registry.category("actions").add("my_module.my_client_action", MyClientAction);
```

**Backend action record:**

```xml
<record id="action_my_client_action" model="ir.actions.client">
    <field name="name">My App</field>
    <field name="tag">my_module.my_client_action</field>
    <field name="target">current</field>
</record>
```

---

## 6. Responsive Layout Patterns

```js
// In component setup:
this.ui = useState(useService("ui"));   // MUST useState for reactivity

get isSmall() {
    // True on mobile OR when rendered in a narrow side-panel chatter
    return this.ui.isSmall || (this.env.inChatter?.aside ?? false);
}
```

**Mobile sidebar pattern (slide-in):**

```scss
.o-MySidebar {
    &.o-mobile {
        position: fixed;
        top: 0; left: 0; bottom: 0;
        z-index: 1055;          // above Bootstrap modal
        width: 100%;
        max-width: 300px;
        transform: translateX(-100%);
        transition: transform 300ms cubic-bezier(0.4, 0, 0.2, 1);

        &.o-visible { transform: translateX(0); }
    }
}

.o-MySidebar-backdrop {
    position: fixed; inset: 0;
    background: rgba(0,0,0,.5);
    z-index: 1050;
    opacity: 0; visibility: hidden;
    transition: opacity 300ms, visibility 0ms linear 300ms;
    &.o-visible { opacity: 1; visibility: visible; transition: opacity 300ms; }
}
```

---

## 7. Server-Sent Events (SSE / EventSource)

For streaming AI responses or real-time progress updates:

**Frontend:**

```js
startStreaming(threadId) {
    const url = `/my_module/stream?thread_id=${threadId}`;
    const es = new EventSource(url);

    es.onmessage = (event) => {
        const data = JSON.parse(event.data);
        this.handleChunk(data);
    };
    es.onerror = () => {
        this.stopStreaming();
        this.notification.add(_t("Connection lost."), { type: "danger" });
    };
    this.eventSources.set(threadId, es);
},

stopStreaming(threadId) {
    this.eventSources.get(threadId)?.close();
    this.eventSources.delete(threadId);
},

handleChunk(data) {
    switch (data.type) {
        case "message_create":
            // insert new message into mailStore
            this.mailStore.insert({ "mail.message": [data.message] }, { html: true });
            break;
        case "message_update":
            // update existing message chunk
            this.mailStore.insert({ "mail.message": [data.message] }, { html: true });
            break;
        case "done":
            this.stopStreaming(data.thread_id);
            break;
        case "error":
            this.notification.add(data.error, { type: "danger" });
            this.stopStreaming(data.thread_id);
            break;
    }
}
```

**Backend controller:**

```python
from odoo import http
from odoo.http import request
import json

class MyStreamController(http.Controller):

    @http.route("/my_module/stream", auth="user", type="http")
    def stream(self, thread_id, **kwargs):
        def generate():
            for chunk in my_generator(thread_id):
                yield f"data: {json.dumps(chunk)}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        return request.make_response(
            generate(),
            headers=[
                ("Content-Type", "text/event-stream"),
                ("Cache-Control", "no-cache"),
                ("X-Accel-Buffering", "no"),   # disable nginx buffering
            ],
        )
```

---

## 8. SCSS Conventions

```scss
// Use Odoo CSS variables, not hardcoded colours
.o-MyWidget {
    background-color: $o-view-background-color;   // matches current theme
    color: var(--primary);                        // Bootstrap variable
    border-color: var(--bs-border-color);

    // BEM-like child elements
    &-item {
        transition: background-color 0.2s ease;

        &.o-active {
            background-color: var(--primary);
            color: white;
            .text-muted { color: rgba(255,255,255,.7) !important; }
        }
    }

    // Responsive
    @media (max-width: 767px) {
        padding: 0.5rem !important;
    }
}

// Utility classes (add only if Bootstrap doesn't cover them)
.cursor-pointer { cursor: pointer; }
.min-width-0    { min-width: 0; }
```

---

## 9. Opening Dialogs / Form Views Programmatically

```js
// In setup():
this.action = useService("action");

// Open a form in a dialog
await this.action.doAction({
    type: "ir.actions.act_window",
    res_model: "my.model",
    res_id: recordId,        // omit for new record
    views: [[false, "form"]],
    target: "new",           // "new" = dialog, "current" = full page
    context: { form_view_initial_mode: "edit" },
}, {
    onClose: async () => {
        // Refresh data after dialog closes
        await this.activeThread.fetchData(["name", "state"]);
    },
});
```

---

## 10. Common Pitfalls

| Mistake | Fix |
|---------|-----|
| `useService(...)` without `useState(...)` | Wrap: `this.store = useState(useService("my.store"))` |
| Calling `useService` outside `setup()` | Move all service calls into `setup()` |
| Forgetting `super.setup()` in a patch | Always call `super.setup()` first |
| Mutating non-reactive objects | Use `Object.assign(this.state, {...})` or store in `useState` |
| EventSource not closed on destroy | Close in `onWillDestroy` / `cleanup()` |
| Missing `t-key` in `t-foreach` | Always add `t-key="item.id"` — required for diffing |
| `t-on-click="method(arg)"` | Use arrow fn: `t-on-click="() => this.method(arg)"` |
| Patch modifies unrelated threads | Guard with `if (!this.isMyModel) return super.method()` |
| Many2many update | Use command syntax: `[[6, 0, newIds]]` |

---

## 11. Integrating with Chatter (Embed in Form View)

```js
// chatter_patch.js pattern
patch(Chatter.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
        Object.assign(this.state, { isMyModeActive: false });
    },

    get shouldShowMyButton() {
        return Boolean(this.props.threadModel && this.props.threadId);
    },

    async onMyButtonClick() {
        if (this.state.isMyModeActive) {
            this.state.isMyModeActive = false;
        } else {
            const threadId = await this.ensureMyThread();
            // Insert thread into mailStore so Thread component can render it
            const thread = this.store.Thread.insert({ model: "my.model", id: threadId });
            if (!this.store.discuss) this.store.discuss = {};
            this.store.discuss.thread = thread;
            await thread.fetchData(["messages"]);
            this.state.isMyModeActive = true;
        }
    },
});

// Register component so chatter template can use it
Object.assign(Chatter.components, { MyWidget });
```

Template addition (in `templates/chatter_extra.xml`):

```xml
<t t-inherit="mail.Chatter" t-inherit-mode="extension">
    <xpath expr="//div[hasclass('o-mail-Chatter-top')]" position="before">
        <button t-if="shouldShowMyButton" t-on-click="onMyButtonClick"
                class="btn btn-sm btn-light">
            <i class="fa fa-robot" /> AI
        </button>
    </xpath>
    <xpath expr="//div[hasclass('o-mail-Chatter-content')]" position="replace">
        <t t-if="state.isMyModeActive">
            <MyWidget recordModel="props.threadModel" recordId="props.threadId" />
        </t>
        <t t-else="">
            <t t-call-super />
        </t>
    </xpath>
</t>
```
