# TaskFlow — Kubernetes + Helm Practice App

A microservices task management app built for practicing Kubernetes management and Helm chart authoring, deployed locally on [KIND](https://kind.sigs.k8s.io/) with [Traefik](https://traefik.io/) as the ingress controller.

## Architecture

```
                    ┌─────────────┐
       Browser ────▶│   Traefik   │  (port 80, KIND host mapping)
                    └──────┬──────┘
                           │  IngressRoute
              ┌────────────┴────────────┐
              │                         │
        /api/* ▼                        ▼ /*
     ┌─────────────┐           ┌──────────────┐
     │ api-gateway │           │   frontend   │
     └──────┬──────┘           └──────────────┘
            │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
┌──────────┐   ┌──────────────┐
│  user-   │   │    task-     │
│  service │   │    service   │
└────┬─────┘   └──────┬───────┘
     │                │
     └───────┬─────────┘
             ▼
       ┌──────────┐
       │ postgres │
       └──────────┘
```

| Service | Language | Port (internal) |
|---|---|---|
| frontend | Node.js/Express | 8080 |
| api-gateway | Node.js/Express | 3000 |
| user-service | Python/Flask | 5000 |
| task-service | Python/Flask | 5000 |
| postgres | PostgreSQL 15 | 5432 |

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (running)
- [KIND](https://kind.sigs.k8s.io/docs/user/quick-start/#installation) v0.20+
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [Helm](https://helm.sh/docs/intro/install/) v3.12+

## Quick Start

### 1. Create the KIND cluster + install Traefik

```bash
bash scripts/setup-cluster.sh
```

### 2. Build images and load into KIND

```bash
bash scripts/build-images.sh
```

### 3. Deploy with Helm

```bash
bash scripts/deploy.sh
```

### 4. Add hosts entry

Add the following line to `C:\Windows\System32\drivers\etc\hosts` (run editor as Administrator):

```
127.0.0.1  taskflow.local
```

### 5. Open the app

Navigate to **http://taskflow.local** in your browser.

## Helm Chart Structure

```
helm/taskflow/               ← Umbrella chart
├── Chart.yaml               ← Declares sub-chart dependencies
├── values.yaml              ← Top-level values (overrides sub-chart defaults)
├── templates/
│   ├── NOTES.txt            ← Post-install instructions
│   ├── jwt-secret.yaml      ← Shared JWT secret
│   └── ingressroute.yaml    ← Traefik IngressRoute
└── charts/
    ├── postgres/            ← Sub-chart: Deployment, Service, PVC, Secret
    ├── user-service/        ← Sub-chart: Deployment, Service
    ├── task-service/        ← Sub-chart: Deployment, Service, HPA
    ├── api-gateway/         ← Sub-chart: Deployment, Service, HPA
    └── frontend/            ← Sub-chart: Deployment, Service
```

## Useful Commands

```bash
# Watch pods come up
kubectl get pods -n taskflow -w

# View Traefik dashboard (port-forward)
kubectl port-forward -n traefik svc/traefik 9000:9000

# Check IngressRoutes
kubectl get ingressroutes -n taskflow

# View HPA status
kubectl get hpa -n taskflow

# Upgrade after changes
helm upgrade taskflow helm/taskflow -n taskflow

# Render templates without deploying (dry run)
helm template taskflow helm/taskflow

# Uninstall
helm uninstall taskflow -n taskflow

# Destroy cluster
bash scripts/teardown.sh
```

## Overriding Values

```bash
# Set a custom JWT secret
helm upgrade taskflow helm/taskflow -n taskflow \
  --set global.jwtSecret=my-super-secret

# Scale the task-service
helm upgrade taskflow helm/taskflow -n taskflow \
  --set task-service.replicaCount=3

# Disable HPA and use fixed replicas
helm upgrade taskflow helm/taskflow -n taskflow \
  --set task-service.autoscaling.enabled=false \
  --set task-service.replicaCount=4
```
