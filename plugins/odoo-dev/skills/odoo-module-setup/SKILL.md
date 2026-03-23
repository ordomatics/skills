---
name: odoo-module-setup
description: Odoo module setup and environment — use when running setup_odoo_modules.sh, checking installed module status, configuring .env variables, or troubleshooting module installation failures.
---

# Odoo Module Setup

## setup_odoo_modules.sh

Installs modules in dependency order. Supports:

```bash
# Full setup
./setup_odoo_modules.sh

# Check what's installed without making changes
./setup_odoo_modules.sh --check-only

# Install core modules only (base, web, mail, queue_job, fastapi...)
./setup_odoo_modules.sh --core-only

# Verify installed module status
./setup_odoo_modules.sh --verify

# Debug mode — show module locations
./setup_odoo_modules.sh --debug
```

Module installation is verified against `ir_module_module` table with 3 retry
attempts per module and 30 PostgreSQL connection retries on startup.

## Environment Variables (.env)

```bash
# Database
DB_HOST=db
DB_PORT=5432
DB_USER=odoo
DB_PASSWORD=odoo
DB_NAME=odoo

# Odoo
ODOO_DEV_MODE=true        # true = dev mode, false = prod
ADMIN_PASSWD=...           # master password

# Queue jobs
ODOO_QUEUE_JOB_CHANNELS=root:2,whatsapp:1

# LLM providers
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...

# WhatsApp / Meta
META_ACCESS_TOKEN=...
WHATSAPP_PHONE_NUMBER_ID=...
```
