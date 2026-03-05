# API Contracts – Private 5G NOC Dashboard

Base URL: `http://localhost:8000`

All responses are `application/json`. All timestamps are Unix epoch seconds.

---

## GET /health

Returns service health information.

**Response 200:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "uptime_seconds": 120,
  "telemetry_records": 42
}
```

---

## GET /site-status

Returns overall operational status of MK LAB.

**Response 200:**
```json
{
  "site": "mk-lab",
  "status": "operational",
  "timestamp": 1741147370,
  "summary": {
    "devices_total": 6,
    "devices_online": 6,
    "devices_offline": 0,
    "active_alarms": 3,
    "critical_alarms": 1
  }
}
```

`status` values: `operational` | `degraded` | `critical`

---

## GET /kpis

Returns all KPI metrics across all domains.

**Query parameters:**
- `domain` (optional) – filter by domain (e.g. `ran`, `core`, `infrastructure`)
- `device` (optional) – filter by device ID

**Response 200:**
```json
[
  {
    "site": "mk-lab",
    "domain": "ran",
    "device": "airspan-gnodeb-1",
    "metric": "ue_connected",
    "value": 5,
    "timestamp": 1741147370,
    "unit": "count"
  },
  {
    "site": "mk-lab",
    "domain": "ran",
    "device": "airspan-gnodeb-1",
    "metric": "rsrp_avg",
    "value": -85.3,
    "timestamp": 1741147370,
    "unit": "dBm"
  }
]
```

**Key metrics by domain:**

| Domain | Metric | Unit | Typical Range |
|--------|--------|------|---------------|
| ran | ue_connected | count | 0–100 |
| ran | rsrp_avg | dBm | -110 to -70 |
| ran | throughput_dl_mbps | Mbps | 0–1000 |
| ran | throughput_ul_mbps | Mbps | 0–500 |
| ran | prb_utilization_pct | % | 0–100 |
| core | registered_ues | count | 0–1000 |
| core | active_sessions | count | 0–500 |
| core | s1ap_messages_per_sec | msg/s | 0–1000 |
| infrastructure | cpu_usage_pct | % | 0–100 |
| infrastructure | memory_usage_pct | % | 0–100 |
| infrastructure | disk_usage_pct | % | 0–100 |
| network | port_utilization_pct | % | 0–100 |
| network | packet_rate_pps | pps | 0–1000000 |
| network | error_rate_pct | % | 0–100 |
| management | managed_gnodebs | count | 0–100 |
| management | active_alarms | count | 0–1000 |

---

## GET /alarms

Returns all active alarms.

**Query parameters:**
- `severity` (optional) – filter by severity (`critical`, `major`, `minor`, `warning`)
- `domain` (optional) – filter by domain
- `status` (optional) – filter by status (`active`, `acknowledged`, `cleared`)

**Response 200:**
```json
[
  {
    "id": "ALM001",
    "site": "mk-lab",
    "domain": "ran",
    "device": "airspan-gnodeb-1",
    "severity": "critical",
    "status": "active",
    "message": "High interference detected on cell",
    "timestamp": 1741147370
  }
]
```

`severity` values: `critical` | `major` | `minor` | `warning`
`status` values: `active` | `acknowledged` | `cleared`

---

## GET /devices

Returns device inventory and status.

**Response 200:**
```json
[
  {
    "id": "fibrolan-switch-1",
    "site": "mk-lab",
    "domain": "network",
    "type": "switch",
    "status": "online",
    "ip": "10.0.0.1",
    "last_seen": 1741147370
  }
]
```

`status` values: `online` | `offline` | `degraded`

---

## GET /topology

Returns network topology for visualisation.

**Response 200:**
```json
{
  "nodes": [
    {
      "id": "fibrolan-switch-1",
      "label": "Fibrolan Switch",
      "domain": "network",
      "type": "switch",
      "status": "online"
    }
  ],
  "edges": [
    {
      "source": "fibrolan-switch-1",
      "target": "supermicro-server-1",
      "label": "10GbE"
    }
  ]
}
```

---

## POST /telemetry

Ingest a telemetry record from a collector.

**Request body:**
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

**Response 202 Accepted:**
```json
{
  "status": "accepted",
  "id": "tel_1741147370_airspan-gnodeb-1_ue_connected"
}
```

---

## GET /telemetry

Returns recent telemetry records (last 100).

**Response 200:**
```json
[
  {
    "site": "mk-lab",
    "domain": "ran",
    "device": "airspan-gnodeb-1",
    "metric": "ue_connected",
    "value": 5,
    "timestamp": 1741147370
  }
]
```
