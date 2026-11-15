---
name: connect-cluster
description: Use when an Ordomatics customer wants their project to run on a Kubernetes cluster they operate, or their own cluster misbehaves. Covers choosing and preparing a cluster (MicroK8s on a laptop or server, K3s without Traefik, a managed cloud cluster), running the portal's connect.sh command, and diagnosing what the portal reports afterwards. Trigger phrases: 'connect my cluster to Ordomatics', 'bring my own cluster', 'run my Odoo on my own server', 'set up microk8s for Ordomatics', 'the portal says Waiting for you', 'Can't manage your cluster', 'Your cluster refused the token', 'connector is not running', 'pods stuck in Pending', 'connect.sh failed'.
---

# Connect a cluster to Ordomatics

Ordomatics deploys and updates the customer's Odoo project on a Kubernetes cluster
they operate. The cluster needs **no public address**: a connector (`cloudflared`,
2 replicas, namespace `ordomatics-system`) dials out to Cloudflare, and Ordomatics
reaches the cluster's API and the sites through that tunnel. Sites are served at
`<address>.ordomatics.com`.

Customer docs, the source of truth if anything here disagrees:
https://docs.ordomatics.com/start/byo-cluster/ and
https://docs.ordomatics.com/start/prepare-your-server/

## Rules

- **Two secrets, never in chat or a web form by you.** The portal's command carries
  the **tunnel key**; the command prints the **cluster token**. The user copies the
  command from the portal and pastes the token into the portal themselves. Don't ask
  for either, don't repeat one that appears in output, don't type one into a page.
- **Name the cluster before changing it.** `kubectl` acts on the current context,
  often an old or dead one. Show `kubectl config current-context` and the nodes, and
  get a yes, before anything that writes.
- **Read-only checks first.** Everything in step 2 is safe; installs and `sudo`
  steps are the user's to approve.
- The connector gets **cluster-admin**. Recommend a cluster dedicated to Ordomatics.

## 1. Choose a cluster

Ask what they have. Then:

| They have | Do |
|---|---|
| A cluster already | Go to step 2 with its context |
| One Linux machine, or a laptop to try it | MicroK8s, below |
| A server and prefer K3s | K3s **without Traefik**, below |
| A cloud account | Its managed Kubernetes (LKE, DOKS, GKE, EKS, AKS…), 1.29+, nodes of 4 GB or more |

Capacity: 8 GB of memory in total, at least 4 GB on one node, for one Small
environment. A single 4 GB node leaves pods `Pending`.

MicroK8s (`ingress` must stay off: Ordomatics installs its own):

```bash
sudo snap install microk8s --classic
sudo usermod -aG microk8s "$USER"        # then log out and in again
microk8s enable dns hostpath-storage
```

K3s:

```bash
curl -sfL https://get.k3s.io | sh -s - --disable traefik
sudo k3s kubectl get nodes
```

On a **laptop**, warn now: the site is only up while the machine is on and awake, and
the machine needs a fixed address (connect.sh offers it, see step 3).

## 2. Check it (read-only)

```bash
kubectl config current-context
kubectl get nodes -o wide
kubectl version                                  # Server: v1.29 or newer
kubectl get storageclass                         # one marked "(default)"
kubectl auth can-i '*' '*' --all-namespaces      # yes
kubectl get ingressclass                         # empty, or only nginx (ours)
kubectl get nodes -o custom-columns=NODE:.metadata.name,MEM:.status.allocatable.memory
```

On MicroK8s write `microk8s kubectl`. Fix what fails:

| Fails | Fix |
|---|---|
| No answer from the API | Wrong context (`kubectl config use-context …`), or the cluster is off |
| Older than 1.29 | Upgrade the cluster |
| No default StorageClass | MicroK8s: `microk8s enable hostpath-storage`; K3s has `local-path`; cloud: mark one with `storageclass.kubernetes.io/is-default-class=true` |
| `can-i` says no | Use an admin kubeconfig for this one-time setup |
| Another ingress class (traefik…) | Remove that controller, or use another cluster |
| Not enough memory | Bigger or more nodes |

Outbound internet is required from the nodes, including **port 7844 TCP and UDP**
to Cloudflare, plus pulls from Docker Hub and registry.gitlab.com.

## 3. Run the portal's command

In the portal (https://odoo.ordomatics.com): **Your infrastructure** (or the project's
**Your own clusters** card) → type a cluster name → **Connect a cluster**. The cluster
shows **Waiting for you** with one command:

```bash
curl -fsSL https://odoo.ordomatics.com/saas_portal/static/k8s/connect.sh | bash -s -- <tunnel key>
```

The user copies it from the portal and runs it in their own terminal (in Claude Code,
`! <command>` also works, though the token then shows in the transcript). Options:
`KUBECTL='microk8s kubectl'` before `bash` to pick the client, `--yes` after the key
where nothing can answer prompts.

It names the cluster and asks, checks step 2 again, offers the fixed address on a
MicroK8s laptop (`sudo`), installs the connector, waits until it reaches Cloudflare,
and prints the cluster token last. What its messages mean:

| connect.sh says | Do |
|---|---|
| That cluster does not answer | Wrong context or cluster off; for local MicroK8s, use `KUBECTL='microk8s kubectl'` |
| PROBLEM: … (then "Nothing changed") | Fix each as in step 2, run again |
| The connector did not start | `kubectl -n ordomatics-system get pods`, then `describe` the pod (image pulls, memory) |
| runs but cannot reach Cloudflare | Open outbound 7844 TCP/UDP; or the key is stale: copy the command from the portal again |
| has not issued our token yet | Wait a minute, run again |

Then the user pastes the printed token in the portal's **token** box and clicks
**Connect**. The badge turns **Connected** with the Kubernetes version, and Ordomatics
installs `ingress-nginx` on the cluster.

## 4. When the portal reports a problem

| The portal says | Meaning | Do |
|---|---|---|
| Your cluster's connector is not running, or cannot reach us | Tunnel down | `kubectl -n ordomatics-system logs deploy/cloudflared --tail=50`; run the command again |
| Your cluster refused the token | Wrong secret pasted | Paste the token connect.sh printed last, not the key inside the command |
| We could not reach your cluster | Off, dropped, or a laptop moved | Check it's on; on a laptop see below; run the command again, **Try again** |
| Can't manage your cluster (site still answers) | The API is unreachable through the tunnel, nearly always a laptop that changed networks | See below |
| Pods stay `Pending` | Memory or storage | `kubectl describe pod <pod> -n <ns>`: read Events |

**Laptop that changed networks.** MicroK8s advertises the address the machine had when
it started. Check:

```bash
microk8s kubectl get endpoints kubernetes -o jsonpath='{.subsets[*].addresses[*].ip}'
```

Anything other than `10.250.0.1` means the address was never pinned. Pin it once
(asks for `sudo`; restarts MicroK8s; the site blinks for a minute):

```bash
curl -fsSL https://odoo.ordomatics.com/saas_portal/static/k8s/pin-address.sh -o pin-address.sh
sudo bash pin-address.sh
```

Until then, after each move: `sudo microk8s refresh-certs --cert server.crt && sudo snap
restart microk8s.daemon-kubelite`.

**What should run once connected:**

```bash
kubectl get pods -A | grep -v kube-system
```

The connector in `ordomatics-system`, `ingress-nginx`, and per application a namespace
with server, worker, longpolling and Redis pods.

## Their own database on the same cluster

Optional. The laptop Postgres recipe (pgvector image, extensions `pg_trgm`, `unaccent`,
`vector`) is in https://docs.ordomatics.com/start/prepare-your-server/#try-it-on-a-laptop;
the portal then takes host, port, database, role and password under **On your own
database server**. The user types the password into the portal, not into chat.

## Disconnecting

The portal's **Disconnect** removes the connector, the ingress add-on and the
cluster-admin binding once nothing runs there. Confirm afterwards:

```bash
kubectl get ns ordomatics-system
kubectl get clusterrolebinding ordomatics
```
