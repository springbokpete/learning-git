import { useState, useEffect, useCallback } from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'
import { Bar, Line } from 'react-chartjs-2'
import { fetchKPIs } from '../api/client.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

const REFRESH_INTERVAL = 30_000

/** Common chart options — dark theme */
function chartOpts(title, yLabel = '') {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: { color: '#8b949e', font: { size: 11 }, boxWidth: 12 },
      },
      tooltip: {
        backgroundColor: '#161b22',
        titleColor: '#e6edf3',
        bodyColor: '#8b949e',
        borderColor: '#30363d',
        borderWidth: 1,
      },
    },
    scales: {
      x: {
        ticks:  { color: '#6e7681', font: { size: 10, family: 'monospace' } },
        grid:   { color: 'rgba(48,54,61,0.6)' },
        border: { color: '#30363d' },
      },
      y: {
        title:  { display: !!yLabel, text: yLabel, color: '#6e7681', font: { size: 10 } },
        ticks:  { color: '#6e7681', font: { size: 10, family: 'monospace' } },
        grid:   { color: 'rgba(48,54,61,0.6)' },
        border: { color: '#30363d' },
      },
    },
  }
}

/** Build a colour palette of n colours cycling through accent shades */
const PALETTE = [
  '#00d4aa', '#388bfd', '#e3611c', '#d29922',
  '#2ea043', '#f85149', '#8b949e', '#79c0ff',
]

function buildBarData(labels, datasets) {
  return {
    labels,
    datasets: datasets.map((ds, i) => ({
      label: ds.label,
      data: ds.data,
      backgroundColor: PALETTE[i % PALETTE.length] + 'cc',
      borderColor:     PALETTE[i % PALETTE.length],
      borderWidth: 1,
      borderRadius: 3,
    })),
  }
}

function buildLineData(labels, datasets) {
  return {
    labels,
    datasets: datasets.map((ds, i) => ({
      label: ds.label,
      data: ds.data,
      borderColor:     PALETTE[i % PALETTE.length],
      backgroundColor: PALETTE[i % PALETTE.length] + '20',
      pointRadius: 3,
      pointHoverRadius: 5,
      tension: 0.35,
      fill: false,
    })),
  }
}

/** Extract KPI values for a domain, returns { labels, metrics } */
function extractDomain(kpis, domain) {
  if (!kpis) return { labels: [], metrics: {} }

  // Support both array and object API shapes
  if (Array.isArray(kpis)) {
    const domainKpis = kpis.filter(k =>
      k.domain?.toLowerCase() === domain.toLowerCase()
    )
    const metrics = {}
    domainKpis.forEach(k => {
      metrics[k.name] = metrics[k.name] || []
      metrics[k.name].push(k.value)
    })
    const labels = domainKpis
      .filter((k, i, a) => a.findIndex(x => x.name === k.name) === i)
      .map(k => k.name)
    return { labels, metrics }
  }

  // Object shape: { ran: { ue_connected: 42, ... }, core: {...}, ... }
  const domainData = kpis[domain.toLowerCase()] || kpis[domain] || {}
  const labels  = Object.keys(domainData)
  const metrics = { values: Object.values(domainData) }
  return { labels, metrics }
}

/** A single KPI bar chart card */
function KPIBarCard({ title, labels, values, yLabel }) {
  if (!labels?.length) return (
    <div className="card">
      <div className="card-header"><span className="card-title">{title}</span></div>
      <div className="state-empty">No data</div>
    </div>
  )
  return (
    <div className="card">
      <div className="card-header"><span className="card-title">{title}</span></div>
      <div style={{ height: 200 }}>
        <Bar
          data={buildBarData(labels, [{ label: title, data: values }])}
          options={chartOpts(title, yLabel)}
        />
      </div>
    </div>
  )
}

/** RAN-specific chart with multiple metrics as grouped bars */
function RANChart({ kpis }) {
  const ranDomainData = kpis
    ? (Array.isArray(kpis)
        ? null  // handled separately below
        : (kpis.ran || kpis.RAN || {}))
    : {}

  const ranMetrics = [
    'ue_connected', 'rsrp_avg', 'throughput_dl_mbps',
    'throughput_ul_mbps', 'prb_utilization_pct',
  ]

  if (Array.isArray(kpis)) {
    // Array shape — build datasets from separate entries
    const byName = {}
    kpis
      .filter(k => k.domain?.toLowerCase() === 'ran' && ranMetrics.includes(k.name))
      .forEach(k => {
        byName[k.name] = byName[k.name] || []
        byName[k.name].push(k.value)
      })

    const present = ranMetrics.filter(m => byName[m]?.length)
    if (!present.length) return null

    const maxLen = Math.max(...present.map(m => byName[m].length))
    const labels = Array.from({ length: maxLen }, (_, i) => `T-${maxLen - i}`)

    return (
      <div className="card" style={{ gridColumn: '1 / -1' }}>
        <div className="card-header">
          <span className="card-title">RAN — Key Metrics (time series)</span>
        </div>
        <div style={{ height: 260 }}>
          <Line
            data={buildLineData(labels, present.map(name => ({
              label: name, data: byName[name],
            })))}
            options={chartOpts('RAN Metrics')}
          />
        </div>
      </div>
    )
  }

  // Object shape
  const present = ranMetrics.filter(m => ranDomainData[m] !== undefined)
  if (!present.length) return null

  return (
    <div className="card" style={{ gridColumn: '1 / -1' }}>
      <div className="card-header">
        <span className="card-title">RAN — Key Metrics</span>
      </div>
      <div style={{ height: 260 }}>
        <Bar
          data={buildBarData(present, [{ label: 'Current', data: present.map(m => ranDomainData[m]) }])}
          options={chartOpts('RAN Metrics')}
        />
      </div>
    </div>
  )
}

export default function KPIPanel() {
  const [kpis, setKpis]     = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)
  const [lastRefresh, setLastRefresh] = useState(null)

  const load = useCallback(async () => {
    try {
      const data = await fetchKPIs()
      setKpis(data)
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

  if (loading) return (
    <div className="state-loading"><div className="spinner" /><span>Loading KPIs…</span></div>
  )
  if (error) return (
    <div className="state-error">⚠ {error}</div>
  )

  // Determine domains available
  const domains = Array.isArray(kpis)
    ? [...new Set(kpis.map(k => k.domain).filter(Boolean))]
    : Object.keys(kpis || {})

  const domainColours = {
    ran:            '#00d4aa',
    core:           '#388bfd',
    infrastructure: '#e3611c',
    network:        '#d29922',
    management:     '#8b949e',
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
        <span className="refresh-indicator">
          {lastRefresh ? `Last updated: ${lastRefresh.toLocaleTimeString()}` : ''}
        </span>
      </div>

      {/* RAN detail chart */}
      <div className="grid-2" style={{ marginBottom: 20 }}>
        <RANChart kpis={kpis} />
      </div>

      {/* Per-domain summary cards */}
      {domains.map(domain => {
        const { labels, metrics } = extractDomain(kpis, domain)
        const colour = domainColours[domain.toLowerCase()] || '#8b949e'
        const values = metrics.values || (labels.length ? labels.map(l => metrics[l]?.[0] ?? 0) : [])

        return (
          <div key={domain} style={{ marginBottom: 24 }}>
            <div className="section-heading" style={{ color: colour }}>
              {domain.toUpperCase()}
            </div>
            <KPIBarCard
              title={`${domain.charAt(0).toUpperCase() + domain.slice(1)} KPIs`}
              labels={labels}
              values={values}
              yLabel="Value"
            />
          </div>
        )
      })}

      {domains.length === 0 && (
        <div className="state-empty">No KPI data available from the API.</div>
      )}
    </div>
  )
}
