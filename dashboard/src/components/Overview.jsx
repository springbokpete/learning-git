import { useState, useEffect, useCallback } from 'react'
import { fetchSiteStatus, fetchAlarms, fetchDevices } from '../api/client.js'

const REFRESH_INTERVAL = 30_000

function StatCard({ title, value, sub, accent }) {
  return (
    <div className="card" style={{ borderColor: accent ? 'rgba(0,212,170,0.3)' : undefined }}>
      <div className="card-title">{title}</div>
      <div className="card-value" style={{ color: accent || undefined }}>{value ?? '—'}</div>
      {sub && <div className="card-sub">{sub}</div>}
    </div>
  )
}

function SiteStatusBanner({ status }) {
  const map = {
    operational: { cls: 'status-online',  label: 'OPERATIONAL',  dot: 'online' },
    degraded:    { cls: 'status-warning', label: 'DEGRADED',     dot: 'degraded' },
    critical:    { cls: 'status-offline', label: 'CRITICAL',     dot: 'critical' },
  }
  const cfg = map[status?.site_status?.toLowerCase()] || map.operational

  return (
    <div className="card" style={{ marginBottom: 20, display: 'flex', alignItems: 'center', gap: 12 }}>
      <span className={`status-dot status-dot--${cfg.dot}`} style={{ width: 14, height: 14 }} />
      <div>
        <div className="card-title" style={{ marginBottom: 2 }}>Site Status</div>
        <span className={`card-value ${cfg.cls}`} style={{ fontSize: 22 }}>{cfg.label}</span>
      </div>
      <div style={{ marginLeft: 'auto', textAlign: 'right' }}>
        <div className="card-sub">Site</div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: 'var(--text-primary)' }}>
          {status?.site_name || 'MK LAB'}
        </div>
      </div>
    </div>
  )
}

export default function Overview() {
  const [siteStatus, setSiteStatus] = useState(null)
  const [alarms, setAlarms]         = useState([])
  const [devices, setDevices]       = useState([])
  const [loading, setLoading]       = useState(true)
  const [error, setError]           = useState(null)
  const [lastRefresh, setLastRefresh] = useState(null)

  const load = useCallback(async () => {
    try {
      const [s, a, d] = await Promise.all([
        fetchSiteStatus(),
        fetchAlarms(),
        fetchDevices(),
      ])
      setSiteStatus(s)
      setAlarms(Array.isArray(a) ? a : a?.alarms ?? [])
      setDevices(Array.isArray(d) ? d : d?.devices ?? [])
      setError(null)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
      setLastRefresh(new Date())
    }
  }, [])

  useEffect(() => {
    load()
    const id = setInterval(load, REFRESH_INTERVAL)
    return () => clearInterval(id)
  }, [load])

  const devicesOnline  = devices.filter(d => d.status?.toLowerCase() === 'online').length
  const devicesOffline = devices.filter(d => d.status?.toLowerCase() !== 'online').length
  const criticalAlarms = alarms.filter(a => a.severity?.toLowerCase() === 'critical').length
  const recentAlarms   = [...alarms].sort((a, b) =>
    new Date(b.timestamp || b.time || 0) - new Date(a.timestamp || a.time || 0)
  ).slice(0, 5)

  if (loading) return (
    <div className="state-loading"><div className="spinner" /><span>Loading overview…</span></div>
  )

  return (
    <div>
      {error && (
        <div className="state-error" style={{ marginBottom: 16, justifyContent: 'flex-start' }}>
          ⚠ {error}
        </div>
      )}

      <SiteStatusBanner status={siteStatus} />

      {/* ── Summary stats ── */}
      <div className="grid-4" style={{ marginBottom: 24 }}>
        <StatCard title="Devices Online"  value={devicesOnline}  sub="of total fleet" accent="var(--online)" />
        <StatCard title="Devices Offline" value={devicesOffline} sub="require attention" accent={devicesOffline > 0 ? 'var(--offline)' : undefined} />
        <StatCard title="Active Alarms"   value={alarms.length}  sub="all severities" />
        <StatCard title="Critical Alarms" value={criticalAlarms} sub="immediate action" accent={criticalAlarms > 0 ? 'var(--offline)' : undefined} />
      </div>

      <div className="grid-2" style={{ marginBottom: 24, alignItems: 'start' }}>
        {/* ── Recent alarms ── */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Recent Alarms</span>
            <span className="refresh-indicator">
              {lastRefresh ? `Updated ${lastRefresh.toLocaleTimeString()}` : ''}
            </span>
          </div>
          {recentAlarms.length === 0 ? (
            <div className="state-empty" style={{ padding: '24px 0' }}>No active alarms</div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Severity</th>
                  <th>Device</th>
                  <th>Message</th>
                  <th>Time</th>
                </tr>
              </thead>
              <tbody>
                {recentAlarms.map((alarm, i) => {
                  const sev = alarm.severity?.toLowerCase() || 'info'
                  const ts  = alarm.timestamp || alarm.time
                  return (
                    <tr key={alarm.id || i}>
                      <td><span className={`badge badge--${sev}`}>{sev}</span></td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>{alarm.device || alarm.source || '—'}</td>
                      <td style={{ color: 'var(--text-secondary)', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {alarm.message || alarm.description || '—'}
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                        {ts ? new Date(ts).toLocaleTimeString() : '—'}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>

        {/* ── Device quick status ── */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Device Status</span>
            <span className="tag">{devices.length} total</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 8 }}>
            {devices.slice(0, 12).map((dev, i) => {
              const st = dev.status?.toLowerCase() || 'unknown'
              return (
                <div key={dev.id || dev.name || i} style={{
                  background: 'var(--bg-tertiary)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-md)',
                  padding: '10px 12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}>
                  <span className={`status-dot status-dot--${st}`} />
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {dev.name}
                    </div>
                    <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                      {dev.domain || dev.type || ''}
                    </div>
                  </div>
                </div>
              )
            })}
            {devices.length === 0 && (
              <div className="state-empty" style={{ padding: '24px 0', gridColumn: '1/-1' }}>No devices found</div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
