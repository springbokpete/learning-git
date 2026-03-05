# System Architecture – Private 5G NOC Dashboard (MK LAB)

## Overview

The Private 5G NOC Dashboard is a containerised platform that collects telemetry, alarms, and KPIs from the MK LAB network infrastructure and presents them in a centralised operational dashboard.

## Components

### 1. Dashboard Frontend (React)
- React 18 + Vite build tooling
- Chart.js for KPI visualisations
- Pure SVG network topology
- Dark NOC theme
- Auto-refreshing panels (15–30 s intervals)
- Served via nginx at port 80 (mapped to 3000 on host)

### 2. Backend API (FastAPI)
- Python 3.11 + FastAPI
- In-memory data store (Phase 1; swap for PostgreSQL/InfluxDB in Phase 2)
- Background thread refreshes simulated metrics every 30 s
- REST JSON API at port 8000
- Swagger UI at `/docs`

### 3. Collector Service (Python)
- Polls or receives data from each device domain
- Phase 1: generates realistic simulated telemetry
- Phase 2: integrates real device APIs
- Posts normalised telemetry to backend `/telemetry` endpoint
- Configurable poll interval (default 30 s)

## Container Architecture

```
┌────────────────────────────────────────────────────┐
│  Docker Network: noc-net                            │
│                                                     │
│  ┌────────────┐  REST   ┌──────────────────────┐   │
│  │  dashboard │◄───────►│      backend          │   │
│  │  (nginx:80)│         │  (uvicorn:8000)       │   │
│  └────────────┘         └──────────┬───────────┘   │
│       │                            │ in-memory store│
│       │ port 3000            ┌─────▼────────────┐  │
│  host │                      │    collector     │  │
│       │ port 8000            │  (python:30s)    │  │
│       │                      └──────────────────┘  │
└───────┴─────────────────────────────────────────────┘
```

## Data Flow

```
Device / Simulated Collector
         │
         │ POST /telemetry
         ▼
    Backend API (in-memory store)
         │
         │ GET /site-status, /kpis, /alarms, /devices, /topology
         ▼
    Dashboard Frontend
         │
         │ Rendered in browser
         ▼
    NOC Operator
```

## Unified Data Model

All telemetry records conform to this schema:

| Field | Type | Description |
|-------|------|-------------|
| site | string | Site identifier (e.g. `mk-lab`) |
| domain | string | Device domain (`ran`, `core`, `infrastructure`, `network`, `management`) |
| device | string | Device identifier |
| metric | string | Metric name |
| value | number | Metric value |
| timestamp | integer | Unix epoch seconds |
| severity | string (optional) | `critical`, `major`, `minor`, `warning` |
| status | string (optional) | `active`, `acknowledged`, `cleared` |

## Security Principles

- CORS origins restricted to known frontends (configurable via `ALLOWED_ORIGINS`)
- All inter-service communication via internal Docker network
- No credentials or secrets in source code
- Phase 3 will add JWT authentication and RBAC

## Scalability

- Stateless backend can be horizontally scaled
- Collector service is independently deployable per site
- Phase 2 replaces in-memory store with InfluxDB (metrics) + PostgreSQL (alarms/inventory)
- Phase 3 adds multi-site aggregation layer

## Device Domains

| Domain | Devices | Protocols (Phase 2) |
|--------|---------|---------------------|
| network | fibrolan-switch-1 | SNMP v2c/v3 |
| infrastructure | supermicro-server-1, openstack-controller-1 | Prometheus, OpenStack API |
| core | druid-raemis-core-1 | Raemis REST API |
| ran | airspan-gnodeb-1 | Airspan NMS API, O1 interface |
| management | airspan-mgmt-1 | Airspan Management API |
