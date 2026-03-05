from pydantic import BaseModel
from typing import Any, Optional


class KPI(BaseModel):
    site: str
    domain: str
    device: str
    metric: str
    value: float
    timestamp: int
    unit: str


class Alarm(BaseModel):
    id: str
    site: str
    domain: str
    device: str
    severity: str  # critical | major | minor | warning
    status: str    # active | cleared
    message: str
    timestamp: int


class Device(BaseModel):
    id: str
    site: str
    domain: str
    type: str
    status: str    # online | offline | degraded
    ip: str
    last_seen: int


class TopologyNode(BaseModel):
    id: str
    label: str
    domain: str
    type: str
    status: str


class TopologyEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str


class Topology(BaseModel):
    nodes: list[TopologyNode]
    edges: list[TopologyEdge]


class SiteStatusSummary(BaseModel):
    devices_total: int
    devices_online: int
    devices_offline: int
    active_alarms: int
    critical_alarms: int


class SiteStatus(BaseModel):
    site: str
    status: str   # operational | degraded | critical | offline
    timestamp: int
    summary: SiteStatusSummary


class TelemetryRecord(BaseModel):
    site: str
    domain: str
    device: str
    metric: str
    value: float
    timestamp: int
    severity: Optional[str] = None
    status: Optional[str] = None
    unit: Optional[str] = None
    meta: Optional[dict[str, Any]] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: float
    telemetry_records: int
