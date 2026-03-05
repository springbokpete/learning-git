# Private 5G NOC Dashboard – MK LAB

A Network Operations Centre dashboard for monitoring Private 5G infrastructure and network components in MK LAB.

## Monitored Components

| Device | Domain | Type |
|--------|--------|------|
| fibrolan-switch-1 | Network | Ethernet Switch |
| supermicro-server-1 | Infrastructure | Bare-Metal Server |
| openstack-controller-1 | Infrastructure | OpenStack Controller |
| druid-raemis-core-1 | Core | 5G Core Network |
| airspan-gnodeb-1 | RAN | gNodeB Radio |
| airspan-mgmt-1 | Management | Radio Management Platform |

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     NOC Dashboard                        │
│  ┌──────────┐   ┌──────────┐   ┌───────────────────┐   │
│  │ Overview │   │   KPIs   │   │   Alarm Console   │   │
│  └──────────┘   └──────────┘   └───────────────────┘   │
│  ┌──────────┐   ┌──────────────────────────────────┐   │
│  │ Topology │   │         Device Status             │   │
│  └──────────┘   └──────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────┘
                         │ REST API
              ┌──────────▼──────────┐
              │    Backend (8000)   │
              │  FastAPI + In-Memory│
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │  Collector Service  │
              │  Simulated Telemetry│
              └─────────────────────┘
```

See [docs/architecture.md](docs/architecture.md) for full architecture documentation.
See [docs/api-contracts.md](docs/api-contracts.md) for API contract documentation.

## Quick Start

### Prerequisites
- Docker and Docker Compose

### Run the Platform

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

The dashboard will be available at **http://localhost:3000**

The backend API will be available at **http://localhost:8000**

API documentation (Swagger UI) at **http://localhost:8000/docs**

## Development

### Backend (FastAPI)

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Collector

```bash
cd collector
pip install -r requirements.txt
BACKEND_URL=http://localhost:8000 python collector.py
```

### Dashboard (React/Vite)

```bash
cd dashboard
npm install
npm run dev
```

The dev server will be available at **http://localhost:5173**

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service health check |
| `/site-status` | GET | Overall site operational status |
| `/kpis` | GET | KPI metrics for all domains |
| `/alarms` | GET | Active alarms list |
| `/devices` | GET | Device inventory and status |
| `/topology` | GET | Network topology nodes and edges |
| `/telemetry` | POST | Ingest telemetry from collectors |
| `/telemetry` | GET | Recent telemetry records |

## Dashboard Pages

- **Operations Overview** – Site status, alarm summary, device health
- **KPI Analytics** – Charts for RAN, Core, Infrastructure metrics
- **Alarm Console** – Filterable alarm table with severity colour-coding
- **Network Topology** – SVG visualisation of device connectivity
- **Device Status** – Grid of device cards with status indicators

## Development Phases

- **Phase 1 (POC)** ✅ – Single site, simulated data, all dashboard pages
- **Phase 2** – Real telemetry integration (Raemis, Airspan, OpenStack, Fibrolan APIs)
- **Phase 3** – Alarm correlation, historical analytics, multi-site, authentication

## Data Model

All telemetry follows a unified model:

```json
{
  "site": "mk-lab",
  "domain": "ran",
  "device": "airspan-gnodeb-1",
  "metric": "ue_connected",
  "value": 5,
  "timestamp": 1741147370
}
```
