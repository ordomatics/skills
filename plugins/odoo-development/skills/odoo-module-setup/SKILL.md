---
name: odoo-module-setup
description: Odoo module installation and setup using setup_odoo_modules.sh. Use when the user asks to install, update, verify, or troubleshoot module installation in the Odoo project.
allowed-tools: Bash, Read, Glob, Grep
---

# Odoo Module Setup

This skill covers module installation orchestration via `setup_odoo_modules.sh`
and direct `odoo-bin` commands in the Ordomatics Odoo project.

## setup_odoo_modules.sh

The script at `/home/moctardiallo/projects/ordomatics/odoo/setup_odoo_modules.sh`
handles the full module installation flow.

### Usage

```bash
# Run via Docker Compose (recommended)
docker compose run --rm odoo-setup

# Or with flags
docker compose exec odoo /setup_odoo_modules.sh --check-only
docker compose exec odoo /setup_odoo_modules.sh --core-only
docker compose exec odoo /setup_odoo_modules.sh --verify
docker compose exec odoo /setup_odoo_modules.sh --debug
```

### Flags

| Flag | What it does |
|------|-------------|
| `--check-only` | Report installed/missing modules, no changes |
| `--core-only` | Install only core modules (base, web, mail, queue_job, fastapi...) |
| `--verify` | Verify all expected modules are installed |
| `--debug` | Show module location analysis and verbose output |
| `--help` | Show usage |

### What it installs

Core (in dependency order):
```
base → web → contacts → product → account → mail → queue_job → fastapi → endpoint_route_handler
```

Then custom modules (whatsapp suite, llm suite) in dependency order.

### How it works

1. Waits for PostgreSQL (30 retries, 2s apart)
2. Checks if database exists and is initialized
3. For each module: installs with `odoo-bin -i`, verifies in `ir_module_module`, retries up to 3 times
4. Reports pass/fail for each module

## Direct Module Operations

### Install a module

```bash
docker compose exec odoo odoo-bin -d odoo -i my_module --stop-after-init
```

### Update a module

```bash
docker compose exec odoo odoo-bin -d odoo -u my_module --stop-after-init
```

### Install multiple modules

```bash
docker compose exec odoo odoo-bin -d odoo -i module_a,module_b,module_c --stop-after-init
```

### Check module status via SQL

```bash
docker compose exec odoo psql -h db -U odoo -d odoo -c "
    SELECT name, state, latest_version
    FROM ir_module_module
    WHERE name LIKE 'llm%'
    ORDER BY name;
"
```

### Run tests for a module

```bash
docker compose exec odoo odoo-bin -d odoo \
    --test-enable \
    --stop-after-init \
    --test-tags=my_module
```

## Troubleshooting

### Module not found during install

```bash
# Check if module exists in addons path
docker compose exec odoo odoo-bin --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/enterprise,/mnt/oca,/mnt/whatsapp,/mnt/odoo-llm \
    -d odoo --stop-after-init 2>&1 | grep "my_module"

# Verify the module has __manifest__.py
docker compose exec odoo ls /mnt/odoo-llm/my_module/__manifest__.py
```

### Module stuck in 'to upgrade' state

```bash
docker compose exec odoo psql -h db -U odoo -d odoo -c "
    UPDATE ir_module_module SET state = 'installed'
    WHERE name = 'my_module' AND state = 'to upgrade';
"
docker compose exec odoo odoo-bin -d odoo -u my_module --stop-after-init
```

### XML/Python error during update

Read the logs immediately after the failed update:

```bash
docker compose logs --tail=50 odoo
```

Common causes:
- Missing `__init__.py` import for a new `.py` file
- New `.xml` file not listed in `__manifest__.py` `"data"`
- Syntax error in Python or XML
- Missing dependency in `depends`
