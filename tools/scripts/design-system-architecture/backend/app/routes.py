from fastapi import APIRouter, HTTPException, status
from .data_store import store
from .models import TelemetryRecord, HealthResponse

router = APIRouter()

VERSION = "1.0.0"


@router.get("/health", response_model=HealthResponse, tags=["ops"])
def health():
    """Liveness / readiness probe."""
    return HealthResponse(
        status="ok",
        version=VERSION,
        uptime_seconds=round(store.uptime(), 2),
        telemetry_records=store.telemetry_count(),
    )


@router.get("/site-status", tags=["noc"])
def site_status():
    """Overall site health summary for the MK LAB deployment."""
    return store.get_site_status()


@router.get("/kpis", tags=["noc"])
def kpis():
    """All live KPI metrics across RAN, core, infrastructure and network domains."""
    return store.get_kpis()


@router.get("/alarms", tags=["noc"])
def alarms():
    """All active and recently cleared alarms."""
    return store.get_alarms()


@router.get("/devices", tags=["noc"])
def devices():
    """Inventory and live status of all managed devices."""
    return store.get_devices()


@router.get("/topology", tags=["noc"])
def topology():
    """Network topology — nodes and directed edges."""
    return store.get_topology()


@router.post(
    "/telemetry",
    status_code=status.HTTP_202_ACCEPTED,
    tags=["collector"],
)
def ingest_telemetry(record: TelemetryRecord):
    """
    Receive a single telemetry record from a collector agent.

    The record is appended to the in-memory ring buffer (last 100 entries).
    """
    store.ingest_telemetry(record)
    return {"accepted": True, "timestamp": record.timestamp}


@router.get("/telemetry", tags=["collector"])
def get_telemetry():
    """Retrieve buffered telemetry records (up to last 100)."""
    return store.get_telemetry()
