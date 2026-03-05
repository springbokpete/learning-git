import { useState, useEffect, useCallback, useRef } from 'react'
import { fetchTopology } from '../api/client.js'

const REFRESH_INTERVAL = 30_000

/* ── Colour helpers ─────────────────────────────────────────────────────── */
const STATUS_FILL   = { online: '#2ea043', offline: '#f85149', warning: '#d29922', degraded: '#d29922', unknown: '#30363d' }
const STATUS_STROKE = { online: '#3fb950', offline: '#ff7b72', warning: '#e3b341', degraded: '#e3b341', unknown: '#484f58' }

function statusFill(s)   { return STATUS_FILL[s?.toLowerCase()]   || STATUS_FILL.unknown }
function statusStroke(s) { return STATUS_STROKE[s?.toLowerCase()] || STATUS_STROKE.unknown }

/* ── Domain → logical zone on the SVG canvas ───────────────────────────── */
const DOMAIN_ZONE = {
  management:     { cx: 0.50, cy: 0.12 },   // top centre
  infrastructure: { cx: 0.15, cy: 0.25 },   // top left
  core:           { cx: 0.50, cy: 0.50 },   // centre
  network:        { cx: 0.82, cy: 0.25 },   // top right
  ran:            { cx: 0.50, cy: 0.82 },   // bottom centre
}

/**
 * Assign (x, y) positions to nodes.
 * Nodes of the same domain are spread in a small circle around their zone centre.
 */
function layoutNodes(nodes, W, H) {
  if (!nodes?.length) return []

  // Group by domain
  const groups = {}
  nodes.forEach(n => {
    const dom = (n.domain || n.type || 'unknown').toLowerCase()
    groups[dom] = groups[dom] || []
    groups[dom].push(n)
  })

  const positioned = []
  Object.entries(groups).forEach(([dom, members]) => {
    const zone  = DOMAIN_ZONE[dom] || { cx: 0.5, cy: 0.5 }
    const count = members.length
    const radius = Math.min(W, H) * (count === 1 ? 0 : 0.10 + count * 0.015)

    members.forEach((node, idx) => {
      const angle = (2 * Math.PI * idx) / count - Math.PI / 2
      positioned.push({
        ...node,
        x: zone.cx * W + (count === 1 ? 0 : Math.cos(angle) * radius),
        y: zone.cy * H + (count === 1 ? 0 : Math.sin(angle) * radius),
      })
    })
  })
  return positioned
}

/* ── Domain label positions for the background zones ──────────────────── */
const DOMAIN_LABELS = [
  { key: 'management',     label: 'MGMT',           cx: 0.50, cy: 0.05 },
  { key: 'infrastructure', label: 'INFRA',           cx: 0.15, cy: 0.17 },
  { key: 'core',           label: 'CORE',            cx: 0.50, cy: 0.40 },
  { key: 'network',        label: 'NETWORK',         cx: 0.82, cy: 0.17 },
  { key: 'ran',            label: 'RAN',             cx: 0.50, cy: 0.73 },
]

/* ── Tooltip ────────────────────────────────────────────────────────────── */
function NodeTooltip({ node, x, y }) {
  if (!node) return null
  return (
    <foreignObject x={x + 14} y={y - 10} width={180} height={110} style={{ pointerEvents: 'none' }}>
      <div xmlns="http://www.w3.org/1999/xhtml" style={{
        background: '#161b22',
        border: '1px solid #30363d',
        borderRadius: 6,
        padding: '8px 10px',
        fontSize: 11,
        color: '#e6edf3',
        fontFamily: 'monospace',
        lineHeight: 1.7,
        boxShadow: '0 4px 16px rgba(0,0,0,0.5)',
      }}>
        <div style={{ fontWeight: 700, color: '#00d4aa', marginBottom: 4 }}>{node.name}</div>
        <div><span style={{ color: '#6e7681' }}>type:</span>   {node.type || '—'}</div>
        <div><span style={{ color: '#6e7681' }}>domain:</span> {node.domain || '—'}</div>
        <div><span style={{ color: '#6e7681' }}>status:</span> <span style={{ color: statusFill(node.status) }}>{node.status || '—'}</span></div>
        {node.ip && <div><span style={{ color: '#6e7681' }}>ip:</span> {node.ip}</div>}
      </div>
    </foreignObject>
  )
}

export default function Topology() {
  const [topology, setTopology]     = useState(null)
  const [loading, setLoading]       = useState(true)
  const [error, setError]           = useState(null)
  const [lastRefresh, setLastRefresh] = useState(null)
  const [hovered, setHovered]       = useState(null)
  const svgRef = useRef(null)

  const W = 900, H = 560   // SVG viewport

  const load = useCallback(async () => {
    try {
      const data = await fetchTopology()
      setTopology(data)
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
    <div className="state-loading"><div className="spinner" /><span>Loading topology…</span></div>
  )

  // Normalise API shape — support { nodes, edges/links } or { devices, connections }
  const rawNodes = topology?.nodes || topology?.devices || []
  const rawEdges = topology?.edges || topology?.links  || topology?.connections || []

  const nodes = layoutNodes(rawNodes, W, H)
  const nodeById = Object.fromEntries(nodes.map(n => [n.id || n.name, n]))

  // Build legend entries from actual domains present
  const domainsPresent = [...new Set(nodes.map(n => (n.domain || 'unknown').toLowerCase()))]

  return (
    <div>
      {error && (
        <div className="state-error" style={{ marginBottom: 12, justifyContent: 'flex-start' }}>
          ⚠ {error} — showing placeholder layout
        </div>
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
          {[['online','#2ea043'],['offline','#f85149'],['warning','#d29922']].map(([s, c]) => (
            <span key={s} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11, color: 'var(--text-secondary)' }}>
              <span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: '50%', background: c }} />
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </span>
          ))}
        </div>
        <span className="refresh-indicator">
          {lastRefresh ? `Updated ${lastRefresh.toLocaleTimeString()}` : ''}
          &nbsp;· {nodes.length} nodes · {rawEdges.length} links
        </span>
      </div>

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <svg
          ref={svgRef}
          viewBox={`0 0 ${W} ${H}`}
          style={{ width: '100%', display: 'block', background: 'var(--bg-primary)', borderRadius: 'var(--radius-lg)' }}
        >
          {/* ── Background domain zones ── */}
          {DOMAIN_LABELS
            .filter(z => domainsPresent.includes(z.key) || nodes.length === 0)
            .map(z => (
              <g key={z.key}>
                <circle
                  cx={z.cx * W} cy={z.cy * H + 40}
                  r={Math.min(W, H) * 0.13}
                  fill="rgba(22,27,34,0.6)"
                  stroke="rgba(48,54,61,0.5)"
                  strokeWidth={1}
                  strokeDasharray="4 3"
                />
                <text
                  x={z.cx * W} y={z.cy * H + 4}
                  textAnchor="middle"
                  fontSize={9}
                  fontFamily="monospace"
                  fontWeight={700}
                  letterSpacing="0.12em"
                  fill="rgba(110,118,129,0.7)"
                >
                  {z.label}
                </text>
              </g>
            ))}

          {/* ── Edges ── */}
          {rawEdges.map((edge, i) => {
            const src = nodeById[edge.source || edge.from || edge.src]
            const dst = nodeById[edge.target || edge.to  || edge.dst]
            if (!src || !dst) return null
            const active = edge.status?.toLowerCase() === 'active' || edge.status?.toLowerCase() === 'up'
            return (
              <line
                key={i}
                x1={src.x} y1={src.y}
                x2={dst.x} y2={dst.y}
                stroke={active ? 'rgba(0,212,170,0.35)' : 'rgba(48,54,61,0.6)'}
                strokeWidth={active ? 1.5 : 1}
                strokeDasharray={active ? undefined : '4 3'}
              />
            )
          })}

          {/* ── Nodes ── */}
          {nodes.map(node => {
            const id   = node.id || node.name
            const isHov = hovered?.id === id || hovered?.name === id
            const r    = isHov ? 18 : 14
            const fill = statusFill(node.status)
            const stroke = statusStroke(node.status)

            return (
              <g
                key={id}
                style={{ cursor: 'pointer' }}
                onMouseEnter={() => setHovered(node)}
                onMouseLeave={() => setHovered(null)}
              >
                {/* Glow ring */}
                <circle cx={node.x} cy={node.y} r={r + 6}
                  fill={fill + '22'} stroke="none" />
                {/* Main node circle */}
                <circle cx={node.x} cy={node.y} r={r}
                  fill={fill + '33'}
                  stroke={stroke}
                  strokeWidth={isHov ? 2.5 : 1.5}
                />
                {/* Inner dot */}
                <circle cx={node.x} cy={node.y} r={5}
                  fill={fill} stroke="none" />
                {/* Label */}
                <text
                  x={node.x} y={node.y + r + 14}
                  textAnchor="middle"
                  fontSize={9}
                  fontFamily="monospace"
                  fill={isHov ? '#e6edf3' : '#8b949e'}
                  fontWeight={isHov ? 700 : 400}
                >
                  {node.name}
                </text>
                {/* Tooltip on hover */}
                {isHov && (
                  <NodeTooltip node={node} x={node.x} y={node.y} />
                )}
              </g>
            )
          })}

          {/* Empty state */}
          {nodes.length === 0 && (
            <text x={W / 2} y={H / 2} textAnchor="middle" fill="#6e7681" fontSize={13} fontFamily="monospace">
              No topology data available from the API
            </text>
          )}
        </svg>
      </div>
    </div>
  )
}
