#!/usr/bin/env bash
# Upload each adopted state into the platform cluster as provider-terraform
# expects it: Secret tfstate-<workspace>-state in crossplane-system.
# Usage: push-state.sh <workdir> <platform-kubeconfig>
# Uses Terraform's own kubernetes backend, so the Secret's format and labels
# are exactly what the in-cluster workspaces read.
set -euo pipefail
W="$1" KC="$2"
cd "$W"
for ws in $(ls -d np-* db-* st-* 2>/dev/null); do
  [ -f "$ws/terraform.tfstate" ] || { echo "$ws: no local state, skipped"; continue; }
  P="$W/push/$ws"; rm -rf "$P"; mkdir -p "$P"
  cat > "$P/main.tf" <<EOF
terraform {
  backend "kubernetes" {
    config_path   = "$KC"
    namespace     = "crossplane-system"
    secret_suffix = "state"
  }
}
EOF
  ( cd "$P" && terraform init -input=false -no-color >/dev/null \
      && terraform workspace new "$ws" -no-color >/dev/null \
      && terraform state push -no-color "$W/$ws/terraform.tfstate" >/dev/null \
      && echo "$ws pushed" ) || echo "$ws FAILED"
done
KUBECONFIG="$KC" kubectl -n crossplane-system get secrets -l tfstate=true --no-headers | awk '{print $1}'
