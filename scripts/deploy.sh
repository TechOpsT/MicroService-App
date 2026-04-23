#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
RELEASE_NAME="taskflow"
NAMESPACE="taskflow"
CHART_DIR="$ROOT_DIR/helm/taskflow"

echo "==> Creating namespace: $NAMESPACE"
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

echo "==> Deploying TaskFlow via Helm"
helm upgrade --install "$RELEASE_NAME" "$CHART_DIR" \
  --namespace "$NAMESPACE" \
  --wait \
  --timeout 300s

echo ""
echo "==> Deployment complete!"
echo ""
echo "Add this to your hosts file (C:\\Windows\\System32\\drivers\\etc\\hosts):"
echo "    127.0.0.1  taskflow.local"
echo ""
echo "Then open: http://taskflow.local"
echo ""
kubectl get pods -n "$NAMESPACE"
