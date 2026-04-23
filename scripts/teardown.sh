#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME="taskflow"

echo "==> Deleting KIND cluster: $CLUSTER_NAME"
kind delete cluster --name "$CLUSTER_NAME"
echo "==> Done"
