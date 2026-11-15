#!/usr/bin/env bash
# Proves the hourly backup restores: a throwaway one-node LKE cluster gets the
# backup through restore-state.sh, and each restored Secret is compared with the
# live platform's. The cluster is deleted on exit, whatever happened.
#
# Usage: restore-drill.sh <age-identity-file> <live-platform-kubeconfig>
# Requires: LINODE_API_TOKEN, GITLAB_TOKEN (or glab), curl, jq, age, kubectl
set -euo pipefail
IDENTITY="$1" LIVE="$2"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
api() { curl -fsS -H "Authorization: Bearer ${LINODE_API_TOKEN}" -H 'Content-Type: application/json' "$@"; }
tmp=$(mktemp -d); chmod 700 "$tmp"
id=""
cleanup() {
  [ -n "$id" ] && api -X DELETE "https://api.linode.com/v4/lke/clusters/$id" >/dev/null && echo "==> deleted drill cluster $id"
  rm -rf "$tmp"
}
trap cleanup EXIT

version=$(api https://api.linode.com/v4/lke/versions | jq -r '.data[0].id')
id=$(api -X POST https://api.linode.com/v4/lke/clusters -d "$(jq -n --arg v "$version" \
  '{label: "restore-drill-\(now | strftime("%m%d%H%M"))", region: "eu-central", k8s_version: $v,
    node_pools: [{type: "g6-standard-1", count: 1}]}')" | jq -r .id)
echo "==> drill cluster $id (k8s $version)"

export KUBECONFIG="$tmp/drill.yaml"
for _ in $(seq 1 60); do
  api "https://api.linode.com/v4/lke/clusters/$id/kubeconfig" 2>/dev/null | jq -r '.kubeconfig // empty' | base64 -d > "$KUBECONFIG" || true
  [ -s "$KUBECONFIG" ] && kubectl get ns default --request-timeout=5s >/dev/null 2>&1 && break
  sleep 10
done
kubectl get ns default >/dev/null

# Bootstrap creates these on a real restore.
kubectl create namespace crossplane-system
kubectl create namespace ordomatics-platform
bash "$HERE/restore-state.sh" "$IDENTITY" "$KUBECONFIG"

# name, then a hash of its data: the same in both, except Secrets changed in
# the hour since the backup.
digest() {
  KUBECONFIG="$1" kubectl get secrets -A -o json \
    | jq -r '.items[] | select(.metadata.namespace == "crossplane-system" or .metadata.namespace == "ordomatics-platform")
        | select((.metadata.labels.tfstate // "") == "true" or ((.metadata.labels["platform.ordomatics.com/kind"] // "") | test("^(external-postgres|repo-credentials)$")))
        | select((.metadata.labels.tfstateWorkspace // "") | (startswith("cc-") or . == "default") | not)
        | "\(.metadata.namespace)/\(.metadata.name) \(.data | tostring | @base64)"' \
    | while read -r name data; do echo "$name $(printf %s "$data" | sha256sum | cut -c1-12)"; done | sort
}
digest "$KUBECONFIG" > "$tmp/restored"
digest "$LIVE" > "$tmp/live"
echo "==> restored $(wc -l < "$tmp/restored"), live $(wc -l < "$tmp/live")"
echo "--- only live (created since the backup):";  comm -13 <(cut -d' ' -f1 "$tmp/restored") <(cut -d' ' -f1 "$tmp/live")
echo "--- only restored (gone since the backup):"; comm -23 <(cut -d' ' -f1 "$tmp/restored") <(cut -d' ' -f1 "$tmp/live")
echo "--- data differs (changed since the backup):"
join "$tmp/restored" "$tmp/live" | awk '$2 != $3 {print $1}'
