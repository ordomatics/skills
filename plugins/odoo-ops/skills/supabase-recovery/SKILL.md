---
name: supabase-recovery
description: This skill should be used when the user encounters a Supabase Supavisor circuit breaker error, specifically 'FATAL: Circuit breaker open: Too many authentication errors'. Covers the complete recovery sequence: scale to zero, pause/restore the Supabase project, reset the DB password, update the K8s secret, and scale back up. Trigger phrases: 'circuit breaker is open', 'supabase auth errors', 'too many authentication errors', 'supabase connection refused', 'FATAL: Circuit breaker open'.
---

# /supabase-recovery

Recover from: `FATAL: Circuit breaker open: Too many authentication errors`

**STOP ALL CONNECTION ATTEMPTS FIRST.** Every failed connection resets the circuit breaker timer. Do not test, ping, or query the DB until Step 8.

> **Replace `{ENV}` with the environment name and `{SUPABASE_PROJECT_ID}` with the Supabase project ID.**
> Find the project ID in the Supabase dashboard URL (`https://supabase.com/dashboard/project/{SUPABASE_PROJECT_ID}`) or in `.env` as `SUPABASE_{ENV}_PROJECT_ID`.

---

## Step 1 — Scale all workloads to zero immediately

```bash
microk8s kubectl scale deployment --all --replicas=0 -n ordomatics-{ENV}
```

Verify no pods are running:
```bash
microk8s kubectl get pods -n ordomatics-{ENV}
# Expected: No resources found
```

## Step 2 — Pause the Supabase project

Via MCP:
```
mcp__supabase__pause_project({ project_id: "{SUPABASE_PROJECT_ID}" })
```

## Step 3 — Wait for INACTIVE status

```
mcp__supabase__get_project({ id: "{SUPABASE_PROJECT_ID}" })
# Wait until status == "INACTIVE" (takes 1-3 minutes)
```

## Step 4 — Restore the project

```
mcp__supabase__restore_project({ project_id: "{SUPABASE_PROJECT_ID}" })
```

Wait for status to return to `"ACTIVE_HEALTHY"`.

## Step 5 — Reset the DB password

In the Supabase dashboard: **Settings → Database → Reset database password**.

Alternatively, use the Supabase MCP `reset_db_password` tool if the dashboard is slow.

Update `.env`:
```
SUPABASE_{ENV}_PASSWORD=<new-password>
```

## Step 6 — Update the K8s secret

Re-create the full secret with the new password (see `odoo-env-reset` Step 3 for the complete key list per environment):

```bash
source ~/projects/ordomatics/odoo/.env

microk8s kubectl create secret generic ordomatics-{ENV}-secrets \
  -n ordomatics-{ENV} \
  --from-literal=DB_HOST="${SUPABASE_{ENV}_HOST}" \
  --from-literal=DB_PORT=6543 \
  --from-literal=DB_USER=odoo \
  --from-literal=DB_PASSWORD="<new-password>" \
  --from-literal=DB_NAME=postgres \
  --from-literal=ADMIN_PASSWD="${ADMIN_PASSWD}" \
  --from-literal=ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-}" \
  --from-literal=OPENAI_API_KEY="${OPENAI_API_KEY:-}" \
  --dry-run=client -o yaml | microk8s kubectl apply -f -
```

## Step 7 — Wait 5 minutes with ZERO connection attempts

Do not run any queries, psql, or curl to the app. Every attempt (even failed ones) resets the breaker timer.

## Step 8 — Test once with psql

```bash
PGPASSWORD=<new-password> psql \
  "postgresql://odoo.{SUPABASE_REF}.pooler.supabase.com:6543/postgres?sslmode=require"
```

- If it connects: proceed to Step 9.
- If still blocked: wait another 10 minutes. Do NOT keep retrying.

## Step 9 — Scale workloads back up

```bash
microk8s kubectl scale deployment ordomatics-{ENV} --replicas=1 -n ordomatics-{ENV}
microk8s kubectl scale deployment ordomatics-{ENV}-longpolling --replicas=1 -n ordomatics-{ENV}
```

---

## Gotchas

- **Direct host `db.{SUPABASE_REF}.supabase.co` is IPv6-only** — unreachable from IPv4-only machines. Use the pooler host `odoo.{SUPABASE_REF}.pooler.supabase.com` instead.
- **Port 5432 (session mode) and port 6543 (transaction mode) share the same circuit breaker.** Switching ports does not help.
- **Every failed attempt resets the timer** — including `pg_isready`, `psql`, health check probes, and app connection pool retries.
- **Pause/restore resets the Supavisor process state** — this is the only reliable way to clear the circuit breaker without waiting 30+ minutes.
