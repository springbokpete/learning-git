import { useState, useEffect, useCallback } from 'react'
import { fetchDevices } from '../api/client.js'

const REFRESH_INTERVAL = 30_000

function DeviceCard({ device }) {
  const status = device.status?.toLowerCase() || 'unknown'
  const lastSeen = device.last_seen || device.lastSeen || device.updated_at

  return (
    <div style={{
      background: 'var(--bg-secondary)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius-lg)',
      padding: '16px',
      display: 'flex',
      flexDirection: 'column',
      gap: 8,
      transition: 'border-color 0.15s',
      borderLeft: `3px solid var(--${status === 'online' ? 'online' : status === 'offline' ? 'offline' : 'warning'})`,
    }}>
      {/* Header row */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}>
          <span className={`status-dot status-dot--${status}`} />
          <span style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 13,
            fontWeight: 600,
            color: 'var(--text-primary)',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}>
            {device.name}
          </span>
        </div>
        <span className={`badge badge--${status === 'online' ? 'info' : status === 'offline' ? 'critical' : 'warning'}`}
          style={{ flexShrink: 0, fontSize: 9 }}>
          {status}
        </span>
      </div>

      {/* Meta rows */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px 12px', fontSize: 11 }}>
        <MetaRow label="Type"   value={device.type} />
        <MetaRow label="Domain" value={device.domain} />
        <MetaRow label="IP"     value={device.ip || device.ip_address} mono />
        <MetaRow label="Model"  value={device.model || device.vendor} />
      </div>

      {/* Last seen */}
      {lastSeen && (
        <div style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', borderTop: '1px solid var(--border-muted)', paddingTop: 6, marginTop: 2 }}>
          Last seen: {new Date(lastSeen).toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'short' })}
        </div>
      )}
    </div>
  )
}

function MetaRow({ label, value, mono }) {
  if (!value) return null
  return (
    <div>
      <span style={{ color: 'var(--text-muted)', marginRight: 4 }}>{label}:</span>
      <span style={{ color: 'var(--text-secondary)', fontFamily: mono ? 'var(--font-mono)' : undefined }}>
        {value}
      </span>
    </div>
  )
}

const DOMAIN_FILTERS = ['all', 'ran', 'core', 'infrastructure', 'network', 'management']

export default function DeviceStatus() {
  const [devices, setDevices]       = useState([])
  const [domainFilter, setDomainFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')
  const [loading, setLoading]       = useState(true)
  const [error, setError]           = useState(null)
  const [lastRefresh, setLastRefresh] = useState(null)

  const load = useCallback(async () => {
    try {
      const data = await fetchDevices()
      const list = Array.isArray(data) ? data : data?.devices ?? []
      setDevices(list)
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

  // Derive available domains from actual device data
  const availableDomains = ['all', ...new Set(devices.map(d => d.domain?.toLowerCase()).filter(Boolean))]

  const filtered = devices.filter(d => {
    const domOk = domainFilter === 'all' || d.domain?.toLowerCase() === domainFilter
    const stOk  = statusFilter === 'all' || d.status?.toLowerCase() === statusFilter
    return domOk && stOk
  })

  const online  = devices.filter(d => d.status?.toLowerCase() === 'online').length
  const offline = devices.filter(d => d.status?.toLowerCase() === 'offline').length
  const other   = devices.length - online - offline

  if (loading) return (
    <div className="state-loading"><div className="spinner" /><span>Loading devices…</span></div>
  )

  return (
    <div>
      {error && (
        <div className="state-error" style={{ marginBottom: 12, justifyContent: 'flex-start' }}>
          ⚠ {error}
        </div>
      )}

      {/* ── Summary strip ── */}
      <div className="grid-3" style={{ marginBottom: 20 }}>
        <div className="card" style={{ padding: '12px 16px' }}>
          <div className="card-title">Online</div>
          <div className="card-value" style={{ color: 'var(--online)', fontSize: 22 }}>{online}</div>
        </div>
        <div className="card" style={{ padding: '12px 16px' }}>
          <div className="card-title">Offline</div>
          <div className="card-value" style={{ color: online === devices.length ? 'var(--text-muted)' : 'var(--offline)', fontSize: 22 }}>{offline}</div>
        </div>
        <div className="card" style={{ padding: '12px 16px' }}>
          <div className="card-title">Other / Degraded</div>
          <div className="card-value" style={{ color: 'var(--warning)', fontSize: 22 }}>{other}</div>
        </div>
      </div>

      {/* ── Filters ── */}
      <div style={{ display: 'flex', gap: 24, marginBottom: 16, flexWrap: 'wrap', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontSize: 10, color: 'var(--text-muted)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Domain</div>
          <div className="filter-bar" style={{ marginBottom: 0 }}>
            {availableDomains.map(d => (
              <button
                key={d}
                className={`filter-btn ${domainFilter === d ? 'filter-btn--active' : ''}`}
                onClick={() => setDomainFilter(d)}
              >
                {d.charAt(0).toUpperCase() + d.slice(1)}
              </button>
            ))}
          </div>
        </div>

        <div>
          <div style={{ fontSize: 10, color: 'var(--text-muted)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Status</div>
          <div className="filter-bar" style={{ marginBottom: 0 }}>
            {['all', 'online', 'offline', 'degraded'].map(s => (
              <button
                key={s}
                className={`filter-btn ${statusFilter === s ? 'filter-btn--active' : ''}`}
                onClick={() => setStatusFilter(s)}
              >
                {s.charAt(0).toUpperCase() + s.slice(1)}
              </button>
            ))}
          </div>
        </div>

        <div style={{ marginLeft: 'auto', alignSelf: 'flex-end' }}>
          <span className="refresh-indicator">
            {filtered.length} of {devices.length} devices
            {lastRefresh ? ` · ${lastRefresh.toLocaleTimeString()}` : ''}
          </span>
        </div>
      </div>

      {/* ── Device grid ── */}
      {filtered.length === 0 ? (
        <div className="state-empty">No devices match the selected filters.</div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 14 }}>
          {filtered.map((dev, i) => (
            <DeviceCard key={dev.id || dev.name || i} device={dev} />
          ))}
        </div>
      )}
    </div>
  )
}
