import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ApiError } from '../api/client'
import { acknowledgeAlert, getAlert, resolveAlert } from '../api/endpoints'
import type { Alert } from '../api/types'
import { formatConfidence, formatDateTime, formatLabel, severityClass } from '../lib/format'

export function AlertDetailPage() {
  const { alertId } = useParams()
  const [alert, setAlert] = useState<Alert | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (!alertId) return
    const id = alertId
    let cancelled = false
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const response = await getAlert(id)
        if (!cancelled) setAlert(response.data)
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'Unable to load alert')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    void load()
    return () => {
      cancelled = true
    }
  }, [alertId])

  async function mutate(action: 'ack' | 'resolve') {
    if (!alertId) return
    setBusy(true)
    try {
      const response =
        action === 'ack' ? await acknowledgeAlert(alertId) : await resolveAlert(alertId)
      setAlert(response.data)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Action failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section>
      <p className="eyebrow">Alert record</p>
      <h2 className="page-title">{alert?.title ?? 'Alert'}</h2>
      <p className="page-copy">
        <Link to="/alerts">Back to queue</Link>
      </p>

      {loading && <div className="loading">Loading alert…</div>}
      {error && <div className="error">{error}</div>}

      {alert && (
        <article className="panel alert-detail">
          <div>
            <span className={`badge ${severityClass(alert.severity)}`}>{alert.severity}</span>
            {alert.high_priority && (
              <span className="badge severity-critical" style={{ marginLeft: 8 }}>
                High priority
              </span>
            )}
          </div>
          <p>{alert.description}</p>
          <p className="meta">Event: {formatLabel(alert.event_type)}</p>
          <p className="meta">
            Device: {alert.source_device_id ?? 'unspecified'} · Confidence{' '}
            {formatConfidence(alert.confidence)}
          </p>
          <p className="meta">Created {formatDateTime(alert.created_at)}</p>
          <p className="meta">
            {alert.resolved
              ? 'Resolved'
              : alert.acknowledged
                ? 'Acknowledged, still open'
                : 'Awaiting operator action'}
          </p>
          <div className="actions">
            <button
              className="btn"
              disabled={busy || alert.acknowledged}
              onClick={() => void mutate('ack')}
            >
              Acknowledge
            </button>
            <button
              className="btn primary"
              disabled={busy || alert.resolved}
              onClick={() => void mutate('resolve')}
            >
              Resolve
            </button>
          </div>
        </article>
      )}
    </section>
  )
}
