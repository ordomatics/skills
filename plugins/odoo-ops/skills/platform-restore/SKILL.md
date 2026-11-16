---
name: platform-restore
description: "Restore the whole Ordomatics platform (platform cluster, clients cluster, every production deployment) onto a new or emptied cloud account, without duplicating Neon projects or R2 buckets. Use when the Linode account is suspended or replaced, when both clusters are gone, when a fresh platform cluster must take over the existing Neon/R2 data, or when asked to 'redeploy the stack on the new account', 'rebuild the platform', 'restore after the outage', 'move to another Linode account', 'disaster recovery'. Also use before ANY provision-platform run on an empty account: running it naively recreates empty databases."
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Platform restore

Brings the platform back on a new cloud account from git, GitLab and the data
that lives outside the clusters (Neon, R2, Cloudflare, GitLab registries).
First done for real on 2026-11-08, after the old Linode account was suspended;
every pitfall below was hit then.

`<skill>` below is `~/projects/ordomatics/skills/plugins/odoo-ops/skills/platform-restore`.

## What survives and what does not

| Survives (outside the clusters) | Lost with the clusters |
|---|---|
| git: platform, infra, client repos, values files | Terraform state of every Crossplane workspace (Secrets in `crossplane-system`) |
| Neon projects and databases (the data) | per-deployment Secrets on the clients cluster: registry pull secret, app secret, storage keys |
| R2 buckets (the filestores) | Backstage's Postgres (task history; acceptable) |
| GitLab registries, deploy tokens, CI variables | per-bucket R2 access keys (their value is shown once) |
| Cloudflare zone, tunnels | ArgoCD's registration of our clients cluster (customers' clusters are in the backup) |

**The one dangerous loss is the Terraform state.** Neon projects, branches,
databases, R2 buckets, tunnels and the clients cluster are all created by
provider-terraform Workspaces, whose state is a Secret named
`tfstate-<workspace>-state` on the platform cluster. On a fresh platform every
Workspace starts with empty state and **creates new, empty resources**:
production would come back on blank databases (same failure class as the
2026-10-02 smartacus duplicate). Hence: pause first, adopt, then unpause.

**Since 2026-11 the state is backed up:** `platform/tfstate-backup` uploads every
workspace's state hourly, age-encrypted, to the generic package registry of
`ordomatics/infra` (package `tfstate`, version `current`). With that backup,
the `restore-platform` pipeline restores it (steps 4–7). The age key is the
user's (their password manager), also held by CI as `TFSTATE_AGE_KEY`.

If the old control plane still answers (`kubectl -n crossplane-system get
secrets -l tfstate=true` on the old kubeconfig: LKE kept answering for ~2 days
after the nodes died), **copy those Secrets out first** and skip step 5's
imports by applying them as-is. Read-only on the old account.

## Workspace naming (deterministic, from the claim name)

| Claim kind | Composition | Workspace | Adoptable? |
|---|---|---|---|
| NeonProject | neon-project-tf | `np-<claim>` | yes: `neon_project` + `neon_database.default` |
| Database | database-neon-tf | `db-<claim>` | yes: `neon_database.db` |
| Database | database-neon-ref-tf | `db-<claim>` | nothing to import (data sources only) |
| NeonBranch | neon-branch-tf | `nb-<claim>` | yes: `neon_branch` + `neon_endpoint` |
| Storage | storage-r2-tf | `st-<claim>` | bucket + CORS yes; the Cloudflare token is minted anew |
| Storage | storage-linode-tf (no selector) | `st-<claim>` | no: belongs to the old Linode account; keep paused |
| ClusterTunnel | cluster-tunnel-tf | `tun-<claim>` | in the backup; without it, no: the tunnel secret is unrecoverable, recreate it and re-run the connector |
| ClientCluster | client-cluster-lke-tf | `cc-<claim>` | must NOT be adopted: the new account needs a new cluster |

## Procedure

Steps marked **(user)** were refused to the agent by Claude Code's auto-mode
classifier on 2026-11-08 (manual pipeline jobs, `terraform apply`, writing CI
secrets, platform-cluster mutations). Hand the user the exact `!` command.

### 1. Inputs

- New cloud API key in `infra/.env` (`LINODE_API_TOKEN=`). Check it:
  `curl -H "Authorization: Bearer $TOKEN" https://api.linode.com/v4/profile` → 200.
- GitLab CLI signed in: `glab auth login --hostname gitlab.com --web` **(user)**
  (the non-web form fails in a `!` prompt: it is not interactive).

### 2. GitLab CI variables on `ordomatics/infra`

Set from `infra/.env` without printing them (`glab api -X PUT
projects/ordomatics%2Finfra/variables/<KEY> -f "value=$V" -F masked=true`).
Read each variable's `masked`/`protected` first and keep them.

| Variable | Pitfall seen |
|---|---|
| `LINODE_API_TOKEN` | the new account's key |
| `GITLAB_TOKEN` | needs **`api`, `read_registry`, `write_repository`**. A `ci-deploy` token with only repository scopes broke the registry pull secret (403 on `jwt/auth`) and Backstage's GitLab API. Check: `curl -H "PRIVATE-TOKEN: $T" https://gitlab.com/api/v4/personal_access_tokens/self` |
| `CF_TOKENS_TOKEN` | without it `cloudflare-r2-creds` is never created and every `st-*` Workspace waits forever |
| `CF_TUNNELS_TOKEN`, `CF_ZONE_ID` | same, for `cloudflare-tunnel-creds` |
| `STOREFRONT_RESEND_API_KEY`, `STOREFRONT_GOOGLE_CLIENT_ID`, `STOREFRONT_GOOGLE_CLIENT_SECRET` | `storefront-email` was once made by hand; without these the storefront server stays in CreateContainerConfigError |
| `TFSTATE_BACKUP_USER`, `TFSTATE_BACKUP_TOKEN` | deploy token on `ordomatics/infra` with `write_package_registry`; without them `tfstate-backup` has no Secret and nothing is backed up |
| `ODOO_RESTORE_LOGIN`, `ODOO_RESTORE_API_KEY` | an Odoo user with rights on deployments and its API key, for `restore-deployments` |
| `TFSTATE_AGE_KEY` | File variable, protected, masked and hidden: only the `AGE-SECRET-KEY-…` line (a multi-line value cannot be masked). `restore:key-check` proves on every push that it matches the backup's recipient |

Compare what `ci/scripts/bootstrap-argocd.sh` reads with what GitLab has:
`grep -oE '\$\{?[A-Z][A-Z0-9_]+' ci/scripts/bootstrap-argocd.sh | sort -u`
against the variables list. Ignore script-internal names.

### 3. Point the infra repo at the new account (branch `linode`)

- `.gitlab-ci.yml`: a **new** `TF_STATE_NAME` (e.g. `platform-cluster-2026-11`)
  in every job, so the old account's state stays intact for its cleanup.
- `platform-cluster/variables.tf`: `node_type = "g6-standard-4"` (8 GB; 4 GB
  stalled Backstage rollouts).

### 4–7. Pause, provision, restore, unpause: the `restore-platform` pipeline

One pipeline does what used to be four manual steps (infra, since 2026-11-16):

| Job | Does |
|---|---|
| `restore:pause` | pauses every Terraform-backed claim in the platform repo (`platform/scripts/pause-claims.py`) and pushes: nothing can create on empty state |
| `provision:platform-cluster` | **the one manual play (user)** |
| `bootstrap:platform` | follows automatically |
| `restore:state` | decrypts the hourly backup with `TFSTATE_AGE_KEY` and applies it; leaves out `tfstate-cc-*` unless the input `restore_same_account` is `yes` |
| `restore:unpause` | unpauses `neon-projects/ordomatics.yaml`, waits for `np-ordomatics` Ready, **fails if Neon's project ids changed**; then unpauses every claim whose state was restored |

```bash
glab api -X POST projects/ordomatics%2Finfra/pipeline -H 'Content-Type: application/json' \
  --input - <<<'{"ref":"linode","inputs":{"pipeline_mode":"restore-platform"}}'
glab api projects/ordomatics%2Finfra/pipelines/<id>/jobs      # provision:platform-cluster is manual
glab api -X POST projects/ordomatics%2Finfra/jobs/<job>/play   # (user)
```

`TFSTATE_AGE_KEY` is a protected, masked and hidden **File** variable on
`ordomatics/infra` holding the age identity. Plain `provision-platform` now
refuses (`restore:guard`) to build a missing platform cluster under unpaused
claims, which is the case that recreates empty databases.

**`restore:unpause` fails, listing claims, when some have no state in the
backup** (created in the hour before the loss). They stay paused; adopt each,
then unpause it (`python3 scripts/pause-claims.py unpause <file>` in the
platform repo, push).

**By import: claims with no state in the backup.**

```bash
cd ~/projects/ordomatics/platform
python3 <skill>/references/adopt-state.py $WORK     # one dir per np-/db-/nb-/st- workspace
for d in $WORK/*/; do (cd $d && terraform init -input=false >/dev/null && terraform plan -no-color | grep -E '^Plan:'); done
```

Expected plans:
- `np-*`: `2 to import, 0 to add, 0 to change, 0 to destroy`. The project's
  password comes back from Neon on import.
- `db-*`: `1 to import, 0 to add, 0 to change, 0 to destroy`
- `nb-*`: `2 to import, 0 to add, 0 to change, 0 to destroy` (the branch and its
  endpoint). A branch whose project is gone is skipped: remove its claim instead.
- `st-*`: `1 (or 2 with CORS) to import, 1 to add, 1 to change`. The add is the
  bucket's new Cloudflare token; the change is only `force_destroy`, which is
  Terraform-side.

**Anything else (a destroy, a replace, a create of a project) → stop and ask.**
Then apply them **(user)**: imports only for Neon, plus new tokens for R2:

```bash
cd $WORK && for d in np-* db-* nb-* st-*; do (cd $d && printf '%s: ' $d && terraform apply -auto-approve -input=false -no-color | grep -E '^Apply complete|^Error'; chmod 600 terraform.tfstate); done
```

Upload them under their workspace names:
`bash <skill>/references/push-state.sh $WORK ~/.kube/ordomatics-platform-new.yaml`.
The Secrets carry the same labels Terraform gives them in-cluster.
Afterwards delete `$WORK`: it holds credential files and states with passwords.

Keep paused whatever is not adoptable (table above), and any claim whose
resource no longer exists: remove it from git instead.

If the old control plane still answers, its states can be applied as they are
instead of the backup (see "What survives" above), before the unpause job.

Kubeconfigs come straight from the cloud API, no Terraform needed:

```bash
ID=$(curl -s -H "Authorization: Bearer $L" https://api.linode.com/v4/lke/clusters \
  | jq -r '.data[] | select(.label=="ordomatics-platform") | .id')
curl -s -H "Authorization: Bearer $L" https://api.linode.com/v4/lke/clusters/$ID/kubeconfig \
  | jq -r .kubeconfig | base64 -d > ~/.kube/ordomatics-platform-new.yaml   # umask 077
```

### 8. Backstage, then the clients cluster

After `bootstrap:platform` has written the right `GITLAB_TOKEN`, restart
Backstage (`kubectl -n backstage rollout restart deploy/backstage`): Secrets do
not reach running pods.

Register the clients cluster through `create-cluster`. Its claim already
exists in git and the Workspace has already built the cluster. The template
re-renders identical files, then registers it with ArgoCD, gives Backstage
credentials there, and seeds the Cloudflare tokens. **Call it through the API
with every value explicit:** the form's defaults are not applied to API
calls, and a first call with only `name` skipped every step behind `addons`
and `register`.

```json
{"templateRef":"template:default/create-cluster","values":{"name":"ordomatics-clients",
 "provider":"lke","region":"eu-central","nodeSize":"g6-standard-4","nodeCount":2,
 "kubernetesVersion":"1.35","dnsZone":"ordomatics.com","acmeEmail":"admin@ordomatics.com",
 "addons":true,"register":true,"timeoutSeconds":1800}}
```

`POST https://backstage.ordomatics.com/api/scaffolder/v2/tasks` with the
`SCAFFOLDER_SERVICE_TOKEN` from `backstage-secrets`. Then hard-refresh the
ArgoCD apps that said "there are no clusters with this name".

### 9. ordomatics-prod: `bootstrap-ordomatics`

saas runs inside ordomatics-prod, so it cannot redeploy itself while down. Run
the `bootstrap-ordomatics` pipeline mode (play the job: **user**). Fixed on
2026-11-08 (infra `b370d83`, `d5c3404`, `c1e1340`). Before running an older
copy, check it has all three:
- R2 bucket by default (`ordomatics-r2-filestore`, provider `r2`), with the
  claim's `endpoint`/`region`/keys Secret passed to `deploy-branch`. The old
  default recommitted the Linode bucket claim and would have pointed
  production at an empty bucket.
- `registryPassword`/`backupToken` sent as **`secrets`**, not values. Otherwise
  the pull secret holds the literal `undefined` (9 characters) and pulls 401.
- The kubeconfig read from the cloud API, not `terraform init`. GitHub refused
  the provider download on shared runners twice in a row.

It recommits a simplified `values.prod.yaml`. That's fine for a few minutes;
the next step restores it. A Pod stuck in ImagePullBackOff picks up a fixed
pull secret on its next retry: no need to delete it.

### 10. Every other deployment: `restore-deployments`

Once odoo.ordomatics.com answers, create a `restore-deployments` pipeline (no
manual play). It calls Odoo's **Redeploy all** (also a button on the back
office's Deployments list) and reports until every deployment has settled.
Each one redeploys as soon as it is live, asleep or failed, which is where a
restore leaves them; asleep ones redeploy asleep. `deploy-branch` recreates their
registry and app Secrets from Odoo's records; GitLab deploy tokens survive, so
the stored registry credentials still work.

Customers' clusters come back connected: the backup holds each one's
connection (`<name>-cluster-kubeconfig`) and ArgoCD registration, and its
tunnel comes back from state. Only a cluster connected after the last backup
needs its owner to paste a token again; until then its deployments wait, and
the job lists them without failing on them.
The job fails on a deployment that failed on our cluster: open it in Odoo
(**Retry Upgrade** when an old upgrade Job is in the way, as ged-test's was).

Needs `ODOO_RESTORE_LOGIN` and `ODOO_RESTORE_API_KEY` on `ordomatics/infra`:
an Odoo user with rights on deployments, and an API key of that user.

### 11. Verify, then clean up

- **Own-server databases** (`*-ext-conn` Secrets in `ordomatics-platform`)
  come back with `restore-state.sh` too since 2026-11-12. If one is still
  missing, a redeploy fails with "connection secret … is missing from the
  platform", and Odoo repairs it by itself: it registers the database again
  with the server's admin login it holds, then retries the deployment.
  Without an admin login, the database turns `failed` and its owner enters the
  password again.
- Each production namespace: pods Running, upgrade Jobs Complete, site 200.
- Neon project count unchanged; `kubectl get workspaces.tf.upbound.io` all True.
- n8n comes back with `bootstrap-ordomatics`; storefront with the variables above.
- **Asterisk** (`hostNetwork`) reads its node's public IP at start
  (`rtp.externalAddressFromNode`, since 2026-11-16), so it comes back on any
  node of the new cluster with nothing to edit. Its log says "Discovered
  external RTP address from node". A plain GET on `https://asterisk.<zone>/ws`
  answering 426 means its WebSocket is up.
- `cross-cluster` Secrets: `kubectl get objects.kubernetes.crossplane.io` on the
  platform; any not Synced names the missing source Secret.
- Revoke the old per-bucket R2 tokens (`r2-<bucket>`, duplicated names).
  Deploy tokens no longer pile up: since 2026-11-15 create-app-repo reuses
  each repo's pair kept in `<group>-<repo>-repo-creds`, which the backup holds.
- Restore anything temporarily rerouted during the outage.

## Drill: prove the backup restores

Without touching the live platform, on a throwaway one-node cluster that is
deleted on exit (a few cents):

```bash
export LINODE_API_TOKEN=… GITLAB_TOKEN=…        # from infra/.env
bash <skill>/references/restore-drill.sh ~/.config/ordomatics-tfstate.age ~/.kube/ordomatics-platform-new.yaml
```

It restores the latest backup with `restore-state.sh`, then lists Secrets only
live, only restored, or with different data. Anything there should be younger
than an hour. First run, 2026-11-15: 21 restored, 21 live, none differing.

## Common pitfalls

- **Local DNS:** after ExternalDNS replaces a record, a home router can cache
  an empty answer (NOERROR, no A) for up to the zone's 30-minute SOA minimum.
  Compare `dig @1.1.1.1` with `dig @192.168.1.1` before suspecting the cluster.
- **`kubectl get applications`** is ambiguous on the platform cluster: use
  `applications.argoproj.io`.
- **Untracked work in `/tmp`:** credential files written for the imports must
  be mode 600 and deleted afterwards.

## Next

Nothing on the list. A restore is: credentials and a new state name (steps
1–3), the `restore-platform` pipeline (one play), `create-cluster` for the
clients cluster, `bootstrap-ordomatics`, then `restore-deployments`.
