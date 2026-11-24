---
name: platform-restore
description: "Restore the Ordomatics platform (the platform cluster and ordomatics-prod; Odoo then brings back the clusters and every deployment) onto a new or emptied cloud account, without duplicating Neon projects or R2 buckets. Use when the Linode account is suspended or replaced, when both clusters are gone, when a fresh platform cluster must take over the existing Neon/R2 data, or when asked to 'redeploy the stack on the new account', 'rebuild the platform', 'restore after the outage', 'move to another Linode account', 'disaster recovery'. Also use before ANY provision-platform run on an empty account: running it naively recreates empty databases."
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
| Neon projects and databases (the data) | per-deployment Secrets on every apps cluster: registry pull secret, app secret, storage keys (Odoo's Redeploy recreates them) |
| R2 buckets (the filestores) | Backstage's Postgres (task history; acceptable) |
| GitLab registries, deploy tokens, CI variables | per-bucket R2 access keys (their value is shown once) |
| Cloudflare zone, tunnels | ArgoCD's registration of a cluster in the platform's account (clusters in an account of their own and customers' are in the backup) |

**The one dangerous loss is the Terraform state.** Neon projects, branches,
databases, R2 buckets, tunnels and the clusters are all created by
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
| `restore:state` | decrypts the hourly backup with `TFSTATE_AGE_KEY` and applies **every** state, clusters included: a cluster that still exists matches its state, one that is gone is dropped on refresh and made anew |
| `restore:unpause` | unpauses `neon-projects/ordomatics.yaml`, waits for `np-ordomatics` Ready, **fails if Neon's project ids changed**; then unpauses every claim whose state was restored, and **fails if a cluster in an account of its own was created or removed** (`linode-creds-<name>` marks one) |
| `bootstrap:ordomatics`, `bootstrap:platform-apps` | the last stage of the same pipeline, each a **manual play (user)**: ordomatics-prod (step 9), then the storefront's and Asterisk's credentials (step 10) |

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

### 8. Backstage, then the clusters

After `bootstrap:platform` has written the right `GITLAB_TOKEN`, restart
Backstage (`kubectl -n backstage rollout restart deploy/backstage`): Secrets do
not reach running pods.

The clusters need nothing from you:
- **Customers' clusters and clusters in an account of their own** (e.g.
  `diansire`) come back registered with ArgoCD: the hourly backup holds their
  registration Secrets, and `restore:unpause` checks none was duplicated.
- **A cluster in the platform's account** that is gone is built again by its
  claim, since its state is dropped on refresh. Register it by re-running
  `create-cluster` through the API with every value explicit (the form's
  defaults are not applied to API calls):

```json
{"templateRef":"template:default/create-cluster","values":{"name":"<cluster>",
 "provider":"lke","region":"eu-central","nodeSize":"g6-standard-2","nodeCount":2,
 "kubernetesVersion":"1.35","dnsZone":"ordomatics.com","acmeEmail":"admin@ordomatics.com",
 "addons":true,"register":true,"timeoutSeconds":1800}}
```

`POST https://backstage.ordomatics.com/api/scaffolder/v2/tasks` with the
`SCAFFOLDER_SERVICE_TOKEN` from `backstage-secrets`. Then hard-refresh the
ArgoCD apps that said "there are no clusters with this name".

### 9. ordomatics-prod: `bootstrap-ordomatics`

saas runs inside ordomatics-prod, so it cannot redeploy itself while down. Play
the `bootstrap:ordomatics` job of the restore pipeline (**user**; also a mode of
its own). Fixed on
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

It builds ordomatics-prod only. n8n is not part of it (set `DEPLOY_N8N=1` only on
a brand-new platform): its database claim comes back from the platform repo and
Odoo redeploys it. It recommits a simplified `values.prod.yaml`. That's fine for
a few minutes; the next step restores it. A Pod stuck in ImagePullBackOff picks up a fixed
pull secret on its next retry: no need to delete it.

### 10. Everything else: Odoo

Once odoo.ordomatics.com answers, Odoo brings back the rest; the infra pipeline
does not know about individual clusters or apps any more.

- **n8n:** Odoo, n8n, **Redeploy**. Its encryption key and its editor login are
  restored from the copies in `ordomatics-platform` (the backup holds them);
  nothing is minted while a copy exists.
- **Storefront and Asterisk credentials:** the `bootstrap-platform-apps` pipeline
  mode, from the CI variables (it needs none of this to get Odoo live).
- **Every deployment:** Odoo itself, below.

#### Every deployment: automatic

Odoo notices the rebuild itself. Its reconcile asks Backstage which cluster the
platform runs on (the UID of `kube-system`); the first sight of a different one
flags every deployment (but ordomatics-prod's own) to redeploy, and each goes
as soon as it is live, asleep or failed, **three at a time** (GitLab refuses
more archive fetches at once). Asleep ones redeploy asleep. `deploy-branch`
recreates their registry and app Secrets from Odoo's records; GitLab deploy
tokens survive, so the stored registry credentials still work. Watch the
Deployments list: each shows the note "The platform was rebuilt: redeploying."
The **Redeploy all** button does the same on demand.

Customers' clusters come back connected: the backup holds each one's
connection (`<name>-cluster-kubeconfig`) and ArgoCD registration, and its
tunnel comes back from state. Only a cluster connected after the last backup
needs its owner to paste a token again; until then its deployments wait.
A deployment that failed on our cluster: open it in Odoo (**Retry Upgrade**
when an old upgrade Job is in the way, as ged-test's was).

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
- n8n comes back through Odoo (step 10); the storefront and Asterisk with `bootstrap-platform-apps`.
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

## The full destroy-and-rebuild drill (2026-11-24, same account)

`destroy-platform`, then `restore-platform`, on a live platform whose apps ran on
another cluster (`diansire`, another account). Platform services were down from
about 21:00 to 22:02; the apps on `diansire` never stopped. Provisioning took 2
minutes, the platform bootstrap 4, the state restore and unpause 2. Everything
after that was fixes: an uninterrupted run is about 15 minutes after the play.

What it checked and found (all fixed unless noted):
- **All 17 states restored, every claim released, Neon unchanged (3 projects),
  `diansire` registered again from the backup**, and its cluster count unchanged.
- **n8n came back with the same login and encryption key** (hashes equal before
  and after): both live as copies in `ordomatics-platform` and travel in the backup.
- **The pause skipped cluster claims**, so `diansire`'s would have synced before
  its state came back and created a second cluster. `pause-claims.py` covers them.
- **`bootstrap:ordomatics` raced Backstage's DNS and certificate** (ran 4 seconds
  after the unpause). It now waits up to 15 minutes.
- **`deploy-branch` could not build ordomatics-prod on a fresh platform:** the
  default Kubernetes client was the legacy shared clients cluster, a placeholder
  host in capitals. It now means the platform's own cluster.
- **Odoo noticed the rebuild but missed n8n and its own deployment**, and three
  redeploys at once got a GitLab 429. It now flags both, runs one redeploy at a
  time and retries a throttled one.
- **The ordomatics AppProject came out with empty destinations** (the bootstrap
  passed the wrong parameter and the skeleton did not know the platform cluster).
- **`destroy-platform` leaves orphans:** the old NodeBalancer and a PVC volume
  stay in the account (the load balancer and Backstage's database volume). Delete
  them by hand after checking they are detached. Not yet automated.
- **Not done:** `ADMIN_PASSWD` regenerates for every app that is redeployed from
  scratch; an apps cluster rebuilt in a surviving platform is not detected (only
  the platform's identity is).

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

## A planned move: remove the old account first

> Written for the 2026-11-17 move, when a shared clients cluster lived in the account
> being replaced. Today the apps clusters are managed from Odoo: a cluster in
> another account (`diansire`) is untouched by this procedure, and one in the
> platform's account is rebuilt by its claim after `restore-platform`. Read
> steps 3 and 6 below with that in mind.

Done 2026-11-17 (Linode to another Linode account), in this order. Nothing is
lost that the backup does not hold, so do it in steps and stop at each gate.

1. **Prepare while everything runs.** Run `tfstate-backup` once
   (`kubectl -n crossplane-system create job --from=cronjob/tfstate-backup <name>`),
   and copy the state Secrets out, **encrypted as they are written** (no
   plaintext on disk): `kubectl ... get secrets -o json | age -r <AGE_RECIPIENT> -o <file>.age`.
   Record a before-picture (Linode clusters, NodeBalancers, volumes, instances;
   Neon projects; DNS counts; tunnels; ArgoCD apps; workspaces) to compare after.
2. **Pause every Terraform-backed claim** (`scripts/pause-claims.py pause`, push) so a
   stray delete cannot reach Neon or R2. The claim is paused, not the Workspace.
3. **Remove the clients cluster declaratively:** delete `clusters/<name>/` in the
   platform repo. ArgoCD prunes the addon apps (the ingress Service goes first, which
   deletes its NodeBalancer), Crossplane destroys the LKE cluster. Odoo refuses this in its
   UI for the shared cluster. The sites are down from here.
4. **Destroy the platform cluster:** `platform-cluster/main.tf` has
   `lifecycle.prevent_destroy = true`, so `destroy-platform` fails its plan until it is set
   to `false` **in its own commit** (its comment says so). Create the pipeline with
   `{"ref":"linode","inputs":{"pipeline_mode":"destroy-platform","destroy_confirm":"DESTROY"}}`
   and play `destroy:platform-cluster` (user). It also deletes the argocd and backstage A
   records. Linode then deletes the CCM-created NodeBalancer and volume by itself within
   minutes: check the account against the before-picture before deleting anything by hand.
5. **Only then switch accounts:** the new `LINODE_API_TOKEN` in `infra/.env` **and** the CI
   variable (compare them by hash, never print), a **new `TF_STATE_NAME`** in the three
   platform jobs, `prevent_destroy = true` back, and revert the clients-cluster removal.
   Push, run `terraform:plan-platform-cluster` (it shows `1 to add`), then continue at step 4
   above with `restore-platform`.
6. After provisioning: replace the dead kubeconfigs (`ci/scripts/linode-kubeconfig.sh <label> <out>`),
   restart Backstage, `bootstrap-ordomatics`; Odoo redeploys the rest by itself.

## Common pitfalls

- **Odoo has to answer at `odoo.ordomatics.com`.** The bootstrap deploys
  `ordomatics-prod` with a wildcard host, so ExternalDNS creates only `*.ordomatics.com`.
  A wildcard never answers for a name that has children: stale
  `_acme-challenge.<x>.odoo.ordomatics.com` TXT records made `odoo` resolve to nothing.
  Delete such leftovers. `saas.ordomatics.com` is the **storefront**, not Odoo.
- **A `pending` deployment never redeployed** (its pods cannot pull: the registry Secret is
  one only a redeploy recreates; Backstage reports `servers: null`). Fixed in `saas`
  `3149162` (a requested redeploy fires from a `pending` deployment whose last operation
  finished over 15 minutes ago). On an older image, set it to `failed` by hand.
- **GitLab answers 429** to the template archive fetch when several redeploys run at once;
  the one that failed is retried alone (`action_redeploy`) when the others have settled.
- **The backup carries what existed:** a registration made by mistake comes back too
  (`argocd` cluster Secrets and `<name>-cluster-kubeconfig`). List `argocd` cluster Secrets after
  a restore and delete any that no app uses.
- **`restore:unpause` passing is the proof** that Neon's project list did not change; still
  compare Neon's names and ids with the before-picture, and the 19 workspaces `True/True`.
- **Local DNS:** after ExternalDNS replaces a record, a home router can cache
  an empty answer (NOERROR, no A) for up to the zone's 30-minute SOA minimum.
  Compare `dig @1.1.1.1` with `dig @192.168.1.1` before suspecting the cluster.
- **`kubectl get applications`** is ambiguous on the platform cluster: use
  `applications.argoproj.io`.
- **Untracked work in `/tmp`:** credential files written for the imports must
  be mode 600 and deleted afterwards.

## Next

A restore is: credentials and a new state name (steps 1–3), the `restore-platform`
pipeline (one play), `bootstrap-ordomatics`; Odoo redeploys everything else by itself.
A `restore-all` mode that chains the first two would turn today's separate triggers into one play.
