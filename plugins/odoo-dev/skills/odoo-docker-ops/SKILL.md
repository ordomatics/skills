---
name: odoo-docker-ops
description: Odoo Docker Compose operations — use when running, restarting, or rebuilding the Odoo stack, reading container logs, opening an Odoo shell, updating or testing a module, or rebuilding Docker images.
---

# Odoo Docker Ops

## Execution Modes (entrypoint.sh)

| Mode | How to trigger | What it does |
|------|---------------|--------------|
| `odoo` (default) | `docker compose up odoo` | Starts Odoo, optionally runs module setup |
| `setup-modules-only` | CMD override | Runs `setup_odoo_modules.sh` only |
| `setup-core-only` | CMD override | Installs core modules only |
| `bash` / `sh` | CMD override | Interactive shell |

## Common Commands

```bash
# Start full stack (local dev)
docker compose up -d

# View Odoo logs
docker compose logs -f odoo

# Restart Odoo only
docker compose restart odoo

# Run module setup separately
docker compose run --rm odoo-setup

# Open Odoo shell
docker compose exec odoo odoo shell -d odoo

# Update a module
docker compose exec odoo odoo-bin -d odoo -u my_module --stop-after-init

# Run tests
docker compose exec odoo odoo-bin -d odoo --test-enable --stop-after-init --test-tags=my_module

# Lint (Ruff)
docker compose exec odoo ruff check /mnt/odoo-llm/my_module --fix

# Rebuild image
docker compose build odoo

# Rebuild without cache
docker compose build --no-cache odoo
```

## Dev vs Prod

| | Dev (`ODOO_DEV_MODE=true`) | Prod (`ODOO_DEV_MODE=false`) |
|---|---|---|
| Workers | 0 (single process) | 2 |
| File watching | `--dev=reload` | — |
| Queue jobs | Synchronous | Async (`queue_job` runner) |
