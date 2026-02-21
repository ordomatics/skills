---
name: odoo-docker-ops
description: Docker Compose operations for the Ordomatics Odoo stack — build, run, logs, exec, restart, rebuild. Use when the user asks to start/stop/restart Odoo, view logs, rebuild the image, exec into the container, or troubleshoot Docker issues.
allowed-tools: Bash, Read, Glob, Grep
---

# Odoo Docker Operations

This skill handles all Docker Compose operations for the Odoo project at
`/home/moctardiallo/projects/ordomatics/odoo`.

## Project Root

```bash
cd /home/moctardiallo/projects/ordomatics/odoo
```

## Common Operations

### Start / Stop

```bash
# Start all services (local dev — includes db via override)
docker compose up -d

# Start Odoo only (if db is already running)
docker compose up -d odoo

# Stop everything
docker compose down

# Stop and remove volumes (full reset — DESTRUCTIVE)
docker compose down -v
```

### Logs

```bash
# Follow Odoo logs
docker compose logs -f odoo

# Last 100 lines
docker compose logs --tail=100 odoo

# All services
docker compose logs -f
```

### Restart

```bash
# Restart Odoo (picks up config changes)
docker compose restart odoo

# Full restart with rebuild
docker compose up -d --build odoo
```

### Rebuild Image

```bash
# Rebuild using cache
docker compose build odoo

# Rebuild from scratch (use when requirements.txt changed)
docker compose build --no-cache odoo

# Build and start
docker compose up -d --build odoo
```

### Exec into Container

```bash
# Interactive shell
docker compose exec odoo bash

# Odoo shell (Python REPL with Odoo env)
docker compose exec odoo odoo shell -d odoo

# Run a one-off command
docker compose exec odoo odoo-bin -d odoo -u my_module --stop-after-init
```

### Health Check

```bash
# Check if Odoo is responding
curl -s http://localhost:8069/web/health

# Check service status
docker compose ps
```

## Troubleshooting

### Container won't start

```bash
# Check logs for errors
docker compose logs odoo

# Check if db is healthy
docker compose ps db

# Try starting db first
docker compose up -d db && sleep 5 && docker compose up -d odoo
```

### Module not found

```bash
# Verify addons path inside container
docker compose exec odoo python3 -c "import odoo; print(odoo.addons.__path__)"

# Check module exists at expected path
docker compose exec odoo ls /mnt/odoo-llm/
docker compose exec odoo ls /mnt/whatsapp/
```

### Permission errors on logs/filestore

The entrypoint fixes permissions automatically. If issues persist:

```bash
docker compose exec odoo chown -R odoo:odoo /var/lib/odoo /var/log/odoo
```

### Database connection refused

```bash
# Check db is running and healthy
docker compose ps db
docker compose logs db

# Test connection manually
docker compose exec odoo psql -h db -U odoo -d odoo -c "SELECT 1"
```

## Dev Mode Toggle

Dev mode is controlled by `.env`:

```bash
# Enable dev mode (file watching, sync queue jobs)
# In .env:
ODOO_DEV_MODE=true

# Then restart
docker compose restart odoo
```
