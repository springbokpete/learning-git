import { useState } from 'react'
import Overview from './components/Overview.jsx'
import KPIPanel from './components/KPIPanel.jsx'
import AlarmConsole from './components/AlarmConsole.jsx'
import Topology from './components/Topology.jsx'
import DeviceStatus from './components/DeviceStatus.jsx'

const NAV_ITEMS = [
  { id: 'overview',  label: 'Overview',  icon: '⬡' },
  { id: 'kpis',      label: 'KPIs',      icon: '◈' },
  { id: 'alarms',    label: 'Alarms',    icon: '⚠' },
  { id: 'topology',  label: 'Topology',  icon: '⬢' },
  { id: 'devices',   label: 'Devices',   icon: '▣' },
]

export default function App() {
  const [activePage, setActivePage] = useState('overview')

  const renderPage = () => {
    switch (activePage) {
      case 'overview':  return <Overview />
      case 'kpis':      return <KPIPanel />
      case 'alarms':    return <AlarmConsole />
      case 'topology':  return <Topology />
      case 'devices':   return <DeviceStatus />
      default:          return <Overview />
    }
  }

  return (
    <div className="app-shell">
      {/* ── Sidebar ──────────────────────────────────────────── */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <span className="brand-icon">◈</span>
          <div className="brand-text">
            <span className="brand-title">MK LAB</span>
            <span className="brand-sub">Private 5G NOC</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          {NAV_ITEMS.map(item => (
            <button
              key={item.id}
              className={`nav-item ${activePage === item.id ? 'nav-item--active' : ''}`}
              onClick={() => setActivePage(item.id)}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <span className="system-label">System</span>
          <span className="system-status status-online">● OPERATIONAL</span>
        </div>
      </aside>

      {/* ── Main content ─────────────────────────────────────── */}
      <main className="main-content">
        <header className="topbar">
          <div className="topbar-left">
            <h1 className="page-title">
              {NAV_ITEMS.find(i => i.id === activePage)?.label}
            </h1>
          </div>
          <div className="topbar-right">
            <span className="topbar-time" suppressHydrationWarning>
              {new Date().toUTCString().replace(' GMT', ' UTC')}
            </span>
            <span className="topbar-badge">5G NR</span>
          </div>
        </header>

        <div className="page-body">
          {renderPage()}
        </div>
      </main>
    </div>
  )
}
