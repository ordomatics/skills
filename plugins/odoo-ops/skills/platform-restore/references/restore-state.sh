#!/usr/bin/env bash
# Put the backed-up Terraform states, and the connection secrets of customers'
# own databases, back on a (new) platform cluster, before any claim is
# unpaused. Written by platform/tfstate-backup, hourly, to the generic package
# registry of ordomatics/infra, encrypted with age.
#
# Usage: restore-state.sh <age-identity-file> <platform-kubeconfig> [--same-account]
#   --same-account  also restore tfstate-cc-* (the clusters' own state). Leave it
#                   out on a new account: there the clients cluster must be
#                   created anew, and the old state would point at the old one.
set -euo pipefail
IDENTITY="$1" KC="$2" SAME="${3:-}"
tmp=$(mktemp -d); chmod 700 "$tmp"; trap 'rm -rf "$tmp"' EXIT

glab api "projects/ordomatics%2Finfra/packages/generic/tfstate/current/tfstate.json.age" > "$tmp/state.age"
age -d -i "$IDENTITY" -o "$tmp/state.json" "$tmp/state.age"

filter='.'
[ "$SAME" = "--same-account" ] || filter='.items |= map(select((.metadata.labels.tfstateWorkspace // "") | startswith("cc-") | not))'
jq "$filter" "$tmp/state.json" > "$tmp/apply.json"
echo "restoring $(jq '.items | length' "$tmp/apply.json") secrets:"
jq -r '.items[].metadata.name' "$tmp/apply.json"
KUBECONFIG="$KC" kubectl apply -f "$tmp/apply.json"
