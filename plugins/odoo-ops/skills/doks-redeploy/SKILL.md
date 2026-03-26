---
name: doks-redeploy
description: This skill should be used when the user needs to destroy and recreate the ephemeral DOKS test cluster from scratch, including tearing down the old cluster via Terraform, provisioning a new one, and running Ansible to bootstrap ArgoCD and deploy Odoo. Trigger phrases: 'redeploy the test cluster', 'destroy and recreate test', 'full cycle on test', 'reset the DOKS cluster', 'rebuild the cluster from scratch', 'tear down and redeploy'.
---

# /doks-redeploy

Full destroy → create → deploy cycle for the ephemeral DOKS test cluster.

This covers: `destroy.sh` teardown → Terraform cluster creation → kubeconfig export → Ansible bootstrap (ingress, cert-manager, ArgoCD, secrets, ArgoCD app) → upgrade job runs → pods healthy.

> **Total time: ~25 min** (5 min cluster create + 20 min Ansible + module install)

---

## Step 1 — Destroy existing cluster

```bash
cd ~/projects/ordomatics/helm/terraform && ./destroy.sh
```

This script: patches ArgoCD finalizers → deletes the ArgoCD app → deletes the namespace → waits 30s → cleans up DO volumes/LBs → runs `terraform destroy`.

---

## Step 2 — Create new cluster

```bash
cd ~/projects/ordomatics/helm/terraform/cluster
export TF_VAR_do_token=$(grep DIGITALOCEAN_API_TOKEN ~/projects/ordomatics/odoo/.env | cut -d= -f2)
terraform apply -auto-approve
```

Then export the kubeconfig:

```bash
terraform output -raw kubeconfig > ~/.kube/ordomatics-test.yaml
```

---

## Step 3 — Run Ansible

```bash
cd ~/projects/ordomatics/helm/ansible
ansible-playbook -i inventory.ini playbook.yml -e env=test
```

Ansible will:
1. Install ingress-nginx → wait for LB IP
2. Install cert-manager + ClusterIssuer
3. Install ArgoCD + configure GitLab repo credentials
4. Create namespace + secrets (`gitlab-registry`, `ordomatics-test-secrets`)
5. Update `values.test.yaml` with the new LB IP and push to GitLab
6. Apply the ArgoCD Application and wait up to 30 min for sync

### If Ansible push is rejected (non-fast-forward)

CI may have pushed to the helm repo between your last pull and Ansible's push. Fix:

```bash
cd ~/projects/ordomatics/helm
git stash
git pull --rebase origin main
git stash pop
git push
```

Then resume Ansible from the ArgoCD app task:

```bash
cd ~/projects/ordomatics/helm/ansible
ansible-playbook -i inventory.ini playbook.yml -e env=test \
  --start-at-task="Apply ArgoCD Application for test env"
```

> **Note:** The final "Display final status" task will fail with `'loadbalancer_ip' is undefined` when resuming mid-playbook — this is harmless. The sync succeeds regardless.

---

## Step 4 — Monitor upgrade job

The ArgoCD Sync phase runs:
1. **Wave -2 (Sync hook):** configmap created
2. **Wave -1 (Sync hook):** upgrade job runs (~18 min, installs ~100 modules)
3. **Wave 0+:** deployments, PVCs, services, ingress

```bash
kubectl get pods -n ordomatics-test -w
kubectl logs -f <upgrade-pod-name> -n ordomatics-test
```

Job completion looks like:
```
✨ Module setup complete!
```

---

## Step 5 — Verify

```bash
kubectl get pods -n ordomatics-test
kubectl get ingress -n ordomatics-test
```

Expected pods: `ordomatics-test-*` (Running), `ordomatics-test-longpolling-*` (Running), `ordomatics-test-redis-*` (Running), upgrade pod (Completed).

App URL: `https://test.<LB-IP>.sslip.io`

---

## Gotchas

| Symptom | Cause | Fix |
|---|---|---|
| Ansible push rejected (non-fast-forward) | CI pushed to helm repo between local commit and Ansible push | `git stash && git pull --rebase origin main && git stash pop && git push`, then resume from `Apply ArgoCD Application for test env` |
| Upgrade job `CreateContainerConfigError` — configmap not found | Both configmap and job must be `argocd.argoproj.io/hook: Sync` | Check `configmap.yaml` has the hook annotation |
| `FileNotFoundError` for `/var/lib/odoo/filestore/...` on fresh cluster | Stale `ir_attachment` records from old cluster pointing to local PVC path (no `fs_storage_id`) | **Only run if the user explicitly asks.** Exec into pod: `PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "DELETE FROM ir_attachment WHERE store_fname IS NOT NULL AND fs_storage_id IS NULL;"` |
| ArgoCD stuck: `waiting for completion of hook` + pod has `CreateContainerConfigError` | Old stuck job; ArgoCD operation not cleared | `kubectl delete job <name> -n ordomatics-test --force`, then patch: `kubectl patch application ordomatics-test -n argocd --type=json -p='[{"op":"remove","path":"/status/operationState"},{"op":"remove","path":"/operation"}]'`, then re-sync |
| Invalid Kubernetes version slug | New DO account has different available versions | Check available slugs: `doctl kubernetes options versions`, update `terraform/cluster/variables.tf` |
| `kubectl` connects to wrong cluster | `KUBECONFIG` not set to DOKS config | `export KUBECONFIG=~/.kube/ordomatics-test.yaml` |

---

## Key architecture notes

- **DO Spaces bucket** (`ordomatics-test-filestore`) is NOT destroyed — it persists across cycles. Odoo attachments survive cluster recreates.
- **Supabase DB** is persistent — module state, records, and users survive cluster recreates.
- **ArgoCD upgrade job hook ordering:** Both configmap (`sync-wave: "-2"`) and upgrade job (`sync-wave: "-1"`) are `Sync` hooks. ArgoCD does not order hooks relative to non-hook resources — both must be hooks for wave ordering to work.
- **KUBECONFIG for cloud:** Use plain `kubectl` with `KUBECONFIG=~/.kube/ordomatics-test.yaml`, not `microk8s kubectl` (that's local only).
