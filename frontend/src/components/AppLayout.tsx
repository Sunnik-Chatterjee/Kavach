import { NavLink, Outlet } from 'react-router-dom'
import { useLive } from '../context/live'

const links = [
  { to: '/', label: 'Overview' },
  { to: '/predictions', label: 'Predictions' },
  { to: '/alerts', label: 'Alerts' },
  { to: '/health', label: 'System' },
]

export function AppLayout({
  streamStatus,
}: {
  streamStatus: 'connecting' | 'live' | 'offline'
}) {
  const { toasts, dismissToast } = useLive()

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">KV</div>
          <div>
            <h1>Kavach</h1>
            <p>Edge OT watch floor</p>
          </div>
        </div>
        <nav className="nav">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.to === '/'}
              className={({ isActive }) => (isActive ? 'active' : undefined)}
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          Predictive maintenance and side-channel watch. Human operators remain in the loop.
        </div>
      </aside>
      <main className="content">
        <div className="topbar">
          <div />
          <div className={`status-chip ${streamStatus}`}>
            <span className="status-dot" />
            {streamStatus === 'live'
              ? 'Live feed'
              : streamStatus === 'connecting'
                ? 'Connecting'
                : 'Feed offline'}
          </div>
        </div>
        <Outlet />
      </main>
      <div className="toast-stack">
        {toasts.map((toast) => (
          <div key={toast.id} className={`toast ${toast.kind}`}>
            <strong>{toast.title}</strong>
            <div>{toast.detail}</div>
            <button type="button" onClick={() => dismissToast(toast.id)}>
              Dismiss
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
