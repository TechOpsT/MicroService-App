#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
CLUSTER_NAME="taskflow"

SERVICES=("frontend" "api-gateway" "user-service" "task-service")

echo "==> Building Docker images"
for svc in "${SERVICES[@]}"; do
  echo "    Building taskflow/$svc:latest"
  docker build -t "taskflow/$svc:latest" "$ROOT_DIR/services/$svc"
done

echo "==> Loading images into KIND cluster: $CLUSTER_NAME"
for svc in "${SERVICES[@]}"; do
  echo "    Loading taskflow/$svc:latest"
  kind load docker-image "taskflow/$svc:latest" --name "$CLUSTER_NAME"
done

echo "==> All images loaded successfully"
docker images | grep "^taskflow"
