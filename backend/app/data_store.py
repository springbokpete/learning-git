"""
In-memory data store for the MK LAB Private 5G NOC Dashboard.

Seeded with realistic simulated data. A background thread refreshes
metrics every 30 seconds with small random perturbations.
"""

import time
import random
import threading
from collections import deque
from copy import deepcopy

from .models import (
    KPI, Alarm, Device, Topology, TopologyNode, TopologyEdge, TelemetryRecord,
)

SITE = "mk-lab"
MAX_TELEMETRY = 100
REFRESH_INTERVAL = 30  # seconds

# ---------------------------------------------------------------------------
# Static seed data
# ---------------------------------------------------------------------------

_DEVICES_SEED: list[dict] = [
    {"id": "fibrolan-switch-1",       "site": SITE, "domain": "network",        "type": "switch",      "status": "online", "ip": "10.0.0.1",  },
    {"id": "supermicro-server-1",     "site": SITE, "domain": "infrastructure", "type": "server",      "status": "online", "ip": "10.0.0.10", },
    {"id": "openstack-controller-1",  "site": SITE, "domain": "infrastructure", "type": "controller",  "status": "online", "ip": "10.0.0.20", },
    {"id": "druid-raemis-core-1",     "site": SITE, "domain": "core",           "type": "5g-core",     "status": "online", "ip": "10.0.1.1",  },
    {"id": "airspan-gnodeb-1",        "site": SITE, "domain": "ran",            "type": "gnodeb",      "status": "online", "ip": "10.0.2.1",  },
    {"id": "airspan-mgmt-1",          "site": SITE, "domain": "management",     "type": "mgmt-server", "status": "online", "ip": "10.0.2.2",  },
]

_ALARMS_SEED: list[dict] = [
    {
        "id": "ALM001", "site": SITE, "domain": "ran",            "device": "airspan-gnodeb-1",
        "severity": "critical", "status": "active",
        "message": "High uplink interference detected on cell 1",
        "timestamp": 0,
    },
    {
        "id": "ALM002", "site": SITE, "domain": "infrastructure", "device": "supermicro-server-1",
        "severity": "major",    "status": "active",
        "message": "CPU utilisation above 85% for more than 10 minutes",
        "timestamp": 0,
    },
    {
        "id": "ALM003", "site": SITE, "domain": "core",           "device": "druid-raemis-core-1",
        "severity": "minor",    "status": "active",
        "message": "PDU session establishment latency elevated (>50 ms)",
        "timestamp": 0,
    },
    {
        "id": "ALM004", "site": SITE, "domain": "network",        "device": "fibrolan-switch-1",
        "severity": "warning",  "status": "active",
        "message": "Port GE0/2 utilisation at 78% — approaching threshold",
        "timestamp": 0,
    },
    {
        "id": "ALM005", "site": SITE, "domain": "ran",            "device": "airspan-gnodeb-1",
        "severity": "minor",    "status": "cleared",
        "message": "Synchronisation source switchover completed successfully",
        "timestamp": 0,
    },
]

# KPI definitions: (domain, device, metric, base_value, unit, jitter_pct)
_KPI_DEFS = [
    # RAN
    ("ran",            "airspan-gnodeb-1",       "ue_connected",         5.0,   "count",   0.2),
    ("ran",            "airspan-gnodeb-1",       "rsrp_avg",            -85.0,  "dBm",     0.02),
    ("ran",            "airspan-gnodeb-1",       "throughput_dl_mbps",  120.0,  "Mbps",    0.1),
    ("ran",            "airspan-gnodeb-1",       "throughput_ul_mbps",   45.0,  "Mbps",    0.1),
    ("ran",            "airspan-gnodeb-1",       "prb_utilization_pct",  65.0,  "%",       0.05),
    ("ran",            "airspan-gnodeb-1",       "sinr_avg",             18.0,  "dB",      0.05),
    # Infrastructure
    ("infrastructure", "supermicro-server-1",    "cpu_usage_pct",        72.0,  "%",       0.08),
    ("infrastructure", "supermicro-server-1",    "memory_usage_pct",     58.0,  "%",       0.04),
    ("infrastructure", "supermicro-server-1",    "disk_usage_pct",       41.0,  "%",       0.01),
    ("infrastructure", "openstack-controller-1", "cpu_usage_pct",        35.0,  "%",       0.08),
    ("infrastructure", "openstack-controller-1", "memory_usage_pct",     62.0,  "%",       0.04),
    ("infrastructure", "openstack-controller-1", "disk_usage_pct",       55.0,  "%",       0.01),
    # Core
    ("core",           "druid-raemis-core-1",    "pdu_sessions_active",  12.0,  "count",   0.15),
    ("core",           "druid-raemis-core-1",    "amf_registrations",     8.0,  "count",   0.1),
    ("core",           "druid-raemis-core-1",    "upf_throughput_gbps",   0.9,  "Gbps",    0.08),
    # Network
    ("network",        "fibrolan-switch-1",       "port_utilization_pct", 52.0,  "%",       0.06),
    ("network",        "fibrolan-switch-1",       "packet_loss_pct",       0.02, "%",       0.5),
    ("network",        "fibrolan-switch-1",       "latency_ms",            1.4,  "ms",      0.1),
    # Management
    ("management",     "airspan-mgmt-1",          "cpu_usage_pct",        28.0,  "%",       0.08),
    ("management",     "airspan-mgmt-1",          "memory_usage_pct",     44.0,  "%",       0.04),
]

_TOPOLOGY_EDGES = [
    ("fibrolan-switch-1",      "supermicro-server-1",    "1GbE uplink"),
    ("fibrolan-switch-1",      "openstack-controller-1", "1GbE uplink"),
    ("fibrolan-switch-1",      "druid-raemis-core-1",    "10GbE core link"),
    ("fibrolan-switch-1",      "airspan-gnodeb-1",       "1GbE fronthaul"),
    ("fibrolan-switch-1",      "airspan-mgmt-1",         "1GbE mgmt"),
    ("druid-raemis-core-1",    "openstack-controller-1", "10GbE virt fabric"),
    ("airspan-gnodeb-1",       "airspan-mgmt-1",         "mgmt plane"),
]


def _now() -> int:
    return int(time.time())


def _jitter(base: float, pct: float) -> float:
    """Return base value ± pct * |base|.  Only clamps to 0 for naturally non-negative metrics."""
    delta = abs(base) * pct * random.uniform(-1.0, 1.0)
    result = base + delta
    # Only apply floor for metrics whose base is ≥ 0 (e.g. percentages, counts)
    if base >= 0:
        result = max(0.0, result)
    return round(result, 3)


class DataStore:
    """Thread-safe in-memory store with periodic metric refresh."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._start_time = time.time()

        # Mutable live state
        self._kpi_state: dict[tuple, float] = {}   # key → current value
        self._devices: list[dict] = []
        self._alarms: list[dict] = []
        self._topology: Topology | None = None
        self._telemetry: deque[TelemetryRecord] = deque(maxlen=MAX_TELEMETRY)

        self._seed()
        self._refresh_kpis()

        # Start background refresh thread
        self._thread = threading.Thread(target=self._background_refresh, daemon=True)
        self._thread.start()

    # ------------------------------------------------------------------
    # Seeding
    # ------------------------------------------------------------------

    def _seed(self) -> None:
        now = _now()

        # Devices
        self._devices = [
            {**d, "last_seen": now} for d in _DEVICES_SEED
        ]

        # Alarms — spread timestamps over last hour
        self._alarms = []
        for i, alarm in enumerate(_ALARMS_SEED):
            a = deepcopy(alarm)
            a["timestamp"] = now - (i * 720)   # 12-minute spacing
            self._alarms.append(a)

        # Topology
        nodes = [
            TopologyNode(
                id=d["id"],
                label=d["id"],
                domain=d["domain"],
                type=d["type"],
                status=d["status"],
            )
            for d in _DEVICES_SEED
        ]
        edges = [
            TopologyEdge(
                id=f"edge-{i}",
                source=src,
                target=dst,
                label=lbl,
            )
            for i, (src, dst, lbl) in enumerate(_TOPOLOGY_EDGES)
        ]
        self._topology = Topology(nodes=nodes, edges=edges)

        # Initialise KPI state with base values
        for domain, device, metric, base, _unit, _jitter_pct in _KPI_DEFS:
            self._kpi_state[(domain, device, metric)] = base

    # ------------------------------------------------------------------
    # KPI refresh
    # ------------------------------------------------------------------

    def _refresh_kpis(self) -> None:
        """Apply random jitter to all KPI values in-place."""
        for domain, device, metric, base, _unit, jitter_pct in _KPI_DEFS:
            current = self._kpi_state[(domain, device, metric)]
            # Drift toward base slowly, then apply jitter
            drifted = current + (base - current) * 0.1
            self._kpi_state[(domain, device, metric)] = _jitter(drifted, jitter_pct)

        # Also update device last_seen timestamps
        now = _now()
        for device in self._devices:
            if device["status"] == "online":
                device["last_seen"] = now

    def _background_refresh(self) -> None:
        while True:
            time.sleep(REFRESH_INTERVAL)
            with self._lock:
                self._refresh_kpis()

    # ------------------------------------------------------------------
    # Public read API
    # ------------------------------------------------------------------

    def get_kpis(self) -> list[KPI]:
        now = _now()
        with self._lock:
            result = []
            for domain, device, metric, _base, unit, _j in _KPI_DEFS:
                result.append(KPI(
                    site=SITE,
                    domain=domain,
                    device=device,
                    metric=metric,
                    value=self._kpi_state[(domain, device, metric)],
                    timestamp=now,
                    unit=unit,
                ))
            return result

    def get_alarms(self) -> list[Alarm]:
        with self._lock:
            return [Alarm(**a) for a in self._alarms]

    def get_devices(self) -> list[Device]:
        with self._lock:
            return [Device(**d) for d in self._devices]

    def get_topology(self) -> Topology:
        with self._lock:
            assert self._topology is not None
            return self._topology

    def get_site_status(self):
        with self._lock:
            devices = self._devices
            alarms = self._alarms

            total = len(devices)
            online = sum(1 for d in devices if d["status"] == "online")
            offline = total - online
            active = [a for a in alarms if a["status"] == "active"]
            critical = sum(1 for a in active if a["severity"] == "critical")

            if critical > 0:
                site_status = "critical"
            elif offline > 0 or any(a["severity"] == "major" for a in active):
                site_status = "degraded"
            else:
                site_status = "operational"

            return {
                "site": SITE,
                "status": site_status,
                "timestamp": _now(),
                "summary": {
                    "devices_total": total,
                    "devices_online": online,
                    "devices_offline": offline,
                    "active_alarms": len(active),
                    "critical_alarms": critical,
                },
            }

    def get_telemetry(self) -> list[TelemetryRecord]:
        with self._lock:
            return list(self._telemetry)

    # ------------------------------------------------------------------
    # Public write API
    # ------------------------------------------------------------------

    def ingest_telemetry(self, record: TelemetryRecord) -> None:
        with self._lock:
            self._telemetry.append(record)

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    def uptime(self) -> float:
        return time.time() - self._start_time

    def telemetry_count(self) -> int:
        with self._lock:
            return len(self._telemetry)


# Singleton instance used by routes
store = DataStore()
