---
name: argocd-sync
description: This skill should be used when the user needs to trigger an ArgoCD application sync or hard refresh via the REST API. Applies when the argocd CLI is unavailable, the app is showing stale manifests after a commit, or a forced sync with prune is required. Trigger phrases: 'sync the ArgoCD app', 'force a sync on staging', 'ArgoCD isn't picking up my commit', 'hard refresh dev', 'app is out of sync'.
---

# /argocd-sync

Trigger a hard refresh and sync for an ArgoCD application via the REST API.

Ask the user which app/environment to sync if not specified.

> **Replace `{ENV}` with the ArgoCD application name (e.g. `ordomatics-dev`, `ordomatics-test`).**

---

## Full sequence

```bash
# Kill any existing port-forward on 8889, then start a new one
kill $(lsof -ti:8889) 2>/dev/null
microk8s kubectl port-forward svc/argocd-server -n argocd 8889:80 &>/dev/null &
sleep 2

# Get the admin password
PASS=$(microk8s kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath='{.data.password}' | base64 -d)

# Authenticate — endpoint is /api/v1/session (SINGULAR, not "sessions")
TOKEN=$(curl -sk -X POST http://localhost:8889/api/v1/session \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"admin\",\"password\":\"$PASS\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

# Hard refresh (clears stale manifest cache from git)
curl -sk "http://localhost:8889/api/v1/applications/ordomatics-{ENV}?refresh=hard" \
  -H "Authorization: Bearer $TOKEN" -o /dev/null
sleep 3

# Sync with prune
curl -sk -X POST "http://localhost:8889/api/v1/applications/ordomatics-{ENV}/sync" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prune":true}' -o /dev/null

# Kill port-forward
kill $(lsof -ti:8889) 2>/dev/null
```

## Check sync status

Reuse the same port-forward and token steps from above, then:

```bash
curl -sk "http://localhost:8889/api/v1/applications/ordomatics-{ENV}" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json
d=json.load(sys.stdin)
s=d.get('status',{})
print('Sync:', s.get('sync',{}).get('status'))
print('Health:', s.get('health',{}).get('status'))
print('Op phase:', s.get('operationState',{}).get('phase'))
print('Message:', s.get('operationState',{}).get('message','')[:120])
"
```

---

## Gotchas

- **`/api/v1/sessions` (plural) → 404.** The correct endpoint is `/api/v1/session` (singular).
- **ArgoCD serves HTTP on port 80**, not HTTPS — port-forward to 80, not 443.
- **Tokens expire quickly** — get the token and make the request in one shell session without sleeping in between.
- **After namespace delete**, ArgoCD shows `Synced` from stale cache. Always hard-refresh before sync.
- **If `ComparisonError: connection refused`** — the repo server is crash-looping. Fix: `kubectl rollout restart deployment argocd-repo-server -n argocd` and wait for it to be Running before retrying.
