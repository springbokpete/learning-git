"""
Private 5G NOC Dashboard — Telemetry Collector
Simulates device metrics for MK LAB and POSTs them to the backend API.
"""

import logging
import os
import random
import time
from dataclasses import dataclass, field
from typing import Generator

import requests
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "30"))
SITE = "mk-lab"

TELEMETRY_ENDPOINT = f"{BACKEND_URL}/telemetry"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger(__name__)


@dataclass
class MetricReading:
    site: str
    domain: str
    device: str
    metric: str
    value: float
    timestamp: int = field(default_factory=lambda: int(time.time()))


class Collector:
    """Generates simulated telemetry for all MK LAB devices."""

    # ------------------------------------------------------------------
    # Network
    # ------------------------------------------------------------------
    def collect_fibrolan_switch_1(self) -> list[MetricReading]:
        device = "fibrolan-switch-1"
        domain = "network"
        return [
            MetricReading(SITE, domain, device, "port_utilization_pct", round(random.uniform(5.0, 85.0), 2)),
            MetricReading(SITE, domain, device, "packet_rate_rx_pps",   round(random.uniform(1_000, 500_000), 0)),
            MetricReading(SITE, domain, device, "packet_rate_tx_pps",   round(random.uniform(1_000, 500_000), 0)),
            MetricReading(SITE, domain, device, "rx_errors",            random.randint(0, 50)),
            MetricReading(SITE, domain, device, "tx_errors",            random.randint(0, 10)),
        ]

    # ------------------------------------------------------------------
    # Infrastructure
    # ------------------------------------------------------------------
    def collect_supermicro_server_1(self) -> list[MetricReading]:
        device = "supermicro-server-1"
        domain = "infrastructure"
        return [
            MetricReading(SITE, domain, device, "cpu_usage_pct",    round(random.uniform(5.0, 90.0), 2)),
            MetricReading(SITE, domain, device, "memory_usage_pct", round(random.uniform(30.0, 95.0), 2)),
            MetricReading(SITE, domain, device, "disk_usage_pct",   round(random.uniform(20.0, 80.0), 2)),
        ]

    def collect_openstack_controller_1(self) -> list[MetricReading]:
        device = "openstack-controller-1"
        domain = "infrastructure"
        vm_active = random.randint(10, 40)
        vm_error  = random.randint(0, 3)
        vm_count  = vm_active + vm_error + random.randint(0, 5)
        return [
            MetricReading(SITE, domain, device, "vm_count",  vm_count),
            MetricReading(SITE, domain, device, "vm_active", vm_active),
            MetricReading(SITE, domain, device, "vm_error",  vm_error),
        ]

    # ------------------------------------------------------------------
    # Core
    # ------------------------------------------------------------------
    def collect_druid_raemis_core_1(self) -> list[MetricReading]:
        device = "druid-raemis-core-1"
        domain = "core"
        return [
            MetricReading(SITE, domain, device, "registered_ues",         random.randint(50, 500)),
            MetricReading(SITE, domain, device, "active_sessions",         random.randint(20, 400)),
            MetricReading(SITE, domain, device, "s1ap_messages_per_sec",   round(random.uniform(10.0, 300.0), 2)),
        ]

    # ------------------------------------------------------------------
    # RAN
    # ------------------------------------------------------------------
    def collect_airspan_gnodeb_1(self) -> list[MetricReading]:
        device = "airspan-gnodeb-1"
        domain = "ran"
        return [
            MetricReading(SITE, domain, device, "ue_connected",          random.randint(0, 32)),
            MetricReading(SITE, domain, device, "rsrp_avg",              round(random.uniform(-110.0, -70.0), 2)),
            MetricReading(SITE, domain, device, "throughput_dl_mbps",    round(random.uniform(0.5, 150.0), 2)),
            MetricReading(SITE, domain, device, "throughput_ul_mbps",    round(random.uniform(0.5, 75.0), 2)),
            MetricReading(SITE, domain, device, "prb_utilization_pct",   round(random.uniform(1.0, 95.0), 2)),
        ]

    # ------------------------------------------------------------------
    # Management
    # ------------------------------------------------------------------
    def collect_airspan_mgmt_1(self) -> list[MetricReading]:
        device = "airspan-mgmt-1"
        domain = "management"
        return [
            MetricReading(SITE, domain, device, "managed_gnodebs", random.randint(1, 8)),
            MetricReading(SITE, domain, device, "active_alarms",   random.randint(0, 15)),
        ]

    # ------------------------------------------------------------------
    # Aggregate
    # ------------------------------------------------------------------
    def collect_all(self) -> Generator[MetricReading, None, None]:
        collectors = [
            self.collect_fibrolan_switch_1,
            self.collect_supermicro_server_1,
            self.collect_openstack_controller_1,
            self.collect_druid_raemis_core_1,
            self.collect_airspan_gnodeb_1,
            self.collect_airspan_mgmt_1,
        ]
        for fn in collectors:
            yield from fn()


def post_metric(session: requests.Session, reading: MetricReading, max_retries: int = 3) -> bool:
    """POST a single metric reading to the backend with exponential back-off."""
    payload = {
        "site":      reading.site,
        "domain":    reading.domain,
        "device":    reading.device,
        "metric":    reading.metric,
        "value":     reading.value,
        "timestamp": reading.timestamp,
    }

    for attempt in range(1, max_retries + 1):
        try:
            response = session.post(TELEMETRY_ENDPOINT, json=payload, timeout=10)
            response.raise_for_status()
            log.debug(
                "Posted %s/%s=%s  →  HTTP %s",
                reading.device, reading.metric, reading.value, response.status_code,
            )
            return True
        except requests.exceptions.ConnectionError:
            wait = 2 ** attempt
            log.warning(
                "Backend unreachable (attempt %d/%d). Retrying in %ds…",
                attempt, max_retries, wait,
            )
            time.sleep(wait)
        except requests.exceptions.Timeout:
            wait = 2 ** attempt
            log.warning("Request timed out for %s/%s (attempt %d/%d). Retrying in %ds…", reading.device, reading.metric, attempt, max_retries, wait)
            time.sleep(wait)
        except requests.exceptions.HTTPError as exc:
            log.error("HTTP error for %s/%s: %s", reading.device, reading.metric, exc)
            return False

    log.error(
        "Failed to post %s/%s after %d attempts — backend may be down.",
        reading.device, reading.metric, max_retries,
    )
    return False


def run() -> None:
    log.info("Collector starting — site=%s  backend=%s  interval=%ds", SITE, BACKEND_URL, POLL_INTERVAL)
    collector = Collector()

    with requests.Session() as session:
        while True:
            cycle_start = time.time()
            log.info("── Collection cycle starting ──────────────────────────────────")

            readings = list(collector.collect_all())
            log.info("Collected %d metric readings across all devices.", len(readings))

            ok = fail = 0
            for reading in readings:
                if post_metric(session, reading):
                    ok += 1
                else:
                    fail += 1

            elapsed = time.time() - cycle_start
            log.info(
                "── Cycle complete in %.1fs  ✓ %d posted  ✗ %d failed ──────────",
                elapsed, ok, fail,
            )

            sleep_for = max(0, POLL_INTERVAL - elapsed)
            log.info("Next collection in %.0fs.", sleep_for)
            time.sleep(sleep_for)


if __name__ == "__main__":
    run()
