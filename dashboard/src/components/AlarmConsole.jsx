import { useState, useEffect, useCallback } from 'react'
import { fetchAlarms } from '../api/client.js'

const REFRESH_INTERVAL = 15_000

const SEVERITIES = ['all', 'critical', 'major', 'minor', 'warning', 'info']

function severityOrder(s) {
  const order = { critical: 0, major: 1, minor: 2, warning: 3, info: 4 }
  return order[s?.toLowerCase()] ?? 99
}

export default function AlarmConsole() {
  const [alarms, setAlarms]         = useState([])
  const [filter, setFilter]         = useState('all')
  const [loading, setLoading]       = useState(true)
  const [error, setError]           = useState(null)
  const [lastRefresh, setLastRefresh] = useState(null)

  const load = useCallback(async () => {
    try {
      const data = await fetchAlarms()
      const list = Array.isArray(data) ? data : data?.alarms ?? []
      // Sort by severity then timestamp (newest first within severity)
      list.sort((a, b) => {
        const sevDiff = severityOrder(a.severity) - severityOrder(b.severity)
        if (sevDiff !== 0) return sevDiff
        return new Date(b.timestamp || b.time || 0) - new Date(a.timestamp || a.time || 0)
      })
      setAlarms(list)
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

  const filtered = filter === 'all'
    ? alarms
    : alarms.filter(a => a.severity?.toLowerCase() === filter)

  const counts = SEVERITIES.reduce((acc, sev) => {
    acc[sev] = sev === 'all'
      ? alarms.length
      : alarms.filter(a => a.severity?.toLowerCase() === sev).length
    return acc
  }, {})

  if (loading) return (
    <div className="state-loading"><div className="spinner" /><span>Loading alarms…</span></div>
  )

  return (
    <div>
      {error && (
        <div className="state-error" style={{ marginBottom: 12, justifyContent: 'flex-start' }}>
          ⚠ {error}
        </div>
      )}

      {/* ── Filter bar ── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div className="filter-bar" style={{ marginBottom: 0 }}>
          {SEVERITIES.map(sev => (
            <button
              key={sev}
              className={`filter-btn ${filter === sev ? 'filter-btn--active' : ''}`}
              onClick={() => setFilter(sev)}
            >
              {sev.charAt(0).toUpperCase() + sev.slice(1)}
              {counts[sev] > 0 && (
                <span style={{
                  marginLeft: 5,
                  background: sev === 'all' ? 'var(--bg-tertiary)' : `var(--${sev === 'critical' ? 'offline' : sev}-dim, var(--bg-tertiary))`,
                  borderRadius: '100px',
                  padding: '0 5px',
                  fontSize: 10,
                  fontFamily: 'var(--font-mono)',
                }}>
                  {counts[sev]}
                </span>
              )}
            </button>
          ))}
        </div>
        <span className="refresh-indicator">
          Refresh: 15s {lastRefresh ? `· ${lastRefresh.toLocaleTimeString()}` : ''}
        </span>
      </div>

      {/* ── Alarms table ── */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {filtered.length === 0 ? (
          <div className="state-empty">No alarms match the selected filter.</div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Severity</th>
                  <th>Device</th>
                  <th>Domain</th>
                  <th>Message</th>
                  <th>Time</th>
                  <th>ID</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((alarm, i) => {
                  const sev = alarm.severity?.toLowerCase() || 'info'
                  const ts  = alarm.timestamp || alarm.time
                  return (
                    <tr key={alarm.id || i}>
                      <td>
                        <span className={`badge badge--${sev}`}>{sev}</span>
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>
                        {alarm.device || alarm.source || '—'}
                      </td>
                      <td>
                        <span className="tag">{alarm.domain || '—'}</span>
                      </td>
                      <td style={{ color: 'var(--text-secondary)', maxWidth: 320, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {alarm.message || alarm.description || '—'}
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                        {ts
                          ? new Date(ts).toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'medium' })
                          : '—'}
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)' }}>
                        {alarm.id || '—'}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div style={{ marginTop: 10, textAlign: 'right', fontSize: 11, color: 'var(--text-muted)' }}>
        Showing {filtered.length} of {alarms.length} alarms
      </div>
    </div>
  )
}
