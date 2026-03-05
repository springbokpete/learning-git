const BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')

async function apiFetch(path) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Accept': 'application/json' },
  })
  if (!res.ok) {
    throw new Error(`API ${path} responded ${res.status} ${res.statusText}`)
  }
  return res.json()
}

/** GET /status  — overall site status */
export async function fetchSiteStatus() {
  return apiFetch('/status')
}

/** GET /kpis  — all KPI metrics */
export async function fetchKPIs() {
  return apiFetch('/kpis')
}

/** GET /alarms  — active alarms */
export async function fetchAlarms() {
  return apiFetch('/alarms')
}

/** GET /devices  — device inventory with live status */
export async function fetchDevices() {
  return apiFetch('/devices')
}

/** GET /topology  — network topology (nodes + edges) */
export async function fetchTopology() {
  return apiFetch('/topology')
}
