#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME="taskflow"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "==> Creating KIND cluster: $CLUSTER_NAME"
if kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
  echo "    Cluster already exists, skipping."
else
  kind create cluster --config "$ROOT_DIR/kind/cluster.yaml"
fi

echo "==> Adding Traefik Helm repository"
helm repo add traefik https://traefik.github.io/charts
helm repo update

echo "==> Installing Traefik ingress controller"
helm upgrade --install traefik traefik/traefik \
  --namespace traefik \
  --create-namespace \
  --set deployment.kind=DaemonSet \
  --set service.type=NodePort \
  --set "ports.web.hostPort=80" \
  --set "ports.websecure.hostPort=443" \
  --set "nodeSelector.ingress-ready=true" \
  --set "tolerations[0].key=node-role.kubernetes.io/control-plane" \
  --set "tolerations[0].operator=Exists" \
  --set "tolerations[0].effect=NoSchedule" \
  --wait --timeout 120s

echo "==> Traefik installed successfully"
kubectl get pods -n traefik
