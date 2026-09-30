import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ApiError } from '../api/client'
import { acknowledgeAlert, listAlerts, resolveAlert } from '../api/endpoints'
import type { Alert, Paginated, Severity } from '../api/types'
import { useLive } from '../context/live'
import { formatConfidence, formatDateTime, formatLabel, severityClass } from '../lib/format'

export function AlertsPage() {
  const { liveTick } = useLive()
  const [page, setPage] = useState(1)
  const [severity, setSeverity] = useState<Severity | ''>('')
  const [acknowledged, setAcknowledged] = useState<'' | 'true' | 'false'>('')
  const [resolved, setResolved] = useState<'' | 'true' | 'false'>('')
  const [data, setData] = useState<Paginated<Alert> | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [busyId, setBusyId] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading((current) => current || data === null)
      setError(null)
      try {
        const response = await listAlerts({
          page,
          size: 20,
          severity,
          acknowledged: acknowledged === '' ? '' : acknowledged === 'true',
          resolved: resolved === '' ? '' : resolved === 'true',
        })
        if (!cancelled) setData(response.data)
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'Unable to load alerts')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    void load()
    return () => {
      cancelled = true
    }
  }, [acknowledged, liveTick, page, resolved, severity])

  async function mutate(id: string, action: 'ack' | 'resolve') {
    setBusyId(id)
    try {
      const response =
        action === 'ack' ? await acknowledgeAlert(id) : await resolveAlert(id)
      setData((current) =>
        current
          ? {
              ...current,
              items: current.items.map((item) =>
                item.id === id ? response.data : item,
              ),
            }
          : current,
      )
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Action failed')
    } finally {
      setBusyId(null)
    }
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.size)) : 1

  return (
    <section>
      <p className="eyebrow">Operator queue</p>
      <h2 className="page-title">Alerts</h2>
      <p className="page-copy">
        MEDIUM and above events from the live pipeline. Acknowledge or resolve without leaving
        the floor.
      </p>

      <div className="filter-row">
        <select
          value={severity}
          onChange={(event) => {
            setPage(1)
            setSeverity(event.target.value as Severity | '')
          }}
        >
          <option value="">All severities</option>
          <option value="MEDIUM">MEDIUM</option>
          <option value="HIGH">HIGH</option>
          <option value="CRITICAL">CRITICAL</option>
        </select>
        <select
          value={acknowledged}
          onChange={(event) => {
            setPage(1)
            setAcknowledged(event.target.value as '' | 'true' | 'false')
          }}
        >
          <option value="">Acknowledged: any</option>
          <option value="false">Unacknowledged</option>
          <option value="true">Acknowledged</option>
        </select>
        <select
          value={resolved}
          onChange={(event) => {
            setPage(1)
            setResolved(event.target.value as '' | 'true' | 'false')
          }}
        >
          <option value="">Resolved: any</option>
          <option value="false">Open</option>
          <option value="true">Resolved</option>
        </select>
      </div>

      {error && <div className="error">{error}</div>}
      {loading && <div className="loading">Fetching alerts…</div>}

      <div className="panel table-wrap">
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Alert</th>
              <th>Severity</th>
              <th>Event</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {data?.items.map((alert) => (
              <tr key={alert.id}>
                <td>{formatDateTime(alert.created_at)}</td>
                <td>
                  <Link to={`/alerts/${alert.id}`}>{alert.title}</Link>
                  {alert.high_priority && (
                    <span className="badge severity-critical" style={{ marginLeft: 8 }}>
                      Priority
                    </span>
                  )}
                </td>
                <td>
                  <span className={`badge ${severityClass(alert.severity)}`}>
                    {alert.severity}
                  </span>
                </td>
                <td>
                  {formatLabel(alert.event_type)}
                  <div className="meta">{formatConfidence(alert.confidence)}</div>
                </td>
                <td>
                  {alert.resolved ? 'Resolved' : alert.acknowledged ? 'Acknowledged' : 'Open'}
                </td>
                <td>
                  <button
                    className="btn"
                    disabled={busyId === alert.id || alert.acknowledged}
                    onClick={() => void mutate(alert.id, 'ack')}
                  >
                    Ack
                  </button>{' '}
                  <button
                    className="btn"
                    disabled={busyId === alert.id || alert.resolved}
                    onClick={() => void mutate(alert.id, 'resolve')}
                  >
                    Resolve
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {data && data.items.length === 0 && <div className="empty">No alerts in this view.</div>}
      </div>

      <div className="pager">
        <button className="btn" disabled={page <= 1} onClick={() => setPage((value) => value - 1)}>
          Previous
        </button>
        <span className="meta">
          Page {page} of {totalPages} · {data?.total ?? 0} total
        </span>
        <button
          className="btn"
          disabled={page >= totalPages}
          onClick={() => setPage((value) => value + 1)}
        >
          Next
        </button>
      </div>
    </section>
  )
}
