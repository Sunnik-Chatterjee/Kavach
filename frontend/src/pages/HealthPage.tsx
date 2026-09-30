import { useEffect, useState } from 'react'
import { ApiError } from '../api/client'
import { getHealth, getLatestPrediction } from '../api/endpoints'
import type { HealthData, Prediction } from '../api/types'
import { formatConfidence, formatDateTime, formatLabel } from '../lib/format'

export function HealthPage() {
  const [health, setHealth] = useState<HealthData | null>(null)
  const [latest, setLatest] = useState<Prediction | null>(null)
  const [latestError, setLatestError] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      setError(null)
      setLatestError(null)
      try {
        const healthResponse = await getHealth()
        if (!cancelled) setHealth(healthResponse.data)
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'Backend health check failed')
        }
      }

      try {
        const latestResponse = await getLatestPrediction()
        if (!cancelled) setLatest(latestResponse.data)
      } catch (err) {
        if (!cancelled) {
          setLatestError(
            err instanceof ApiError ? err.message : 'Latest prediction is unavailable',
          )
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    void load()
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <section>
      <p className="eyebrow">Connectivity</p>
      <h2 className="page-title">System status</h2>
      <p className="page-copy">
        Health ping against GET /health, plus the latest stored inference as a pipeline sanity check.
      </p>

      {loading && <div className="loading">Checking backend…</div>}
      {error && <div className="error">{error}</div>}

      <div className="grid two-col">
        <article className="panel health-card">
          <h3>API</h3>
          <div className="value">{health?.status ?? 'DOWN'}</div>
          <p className="meta">Kavach backend {health?.version ?? 'unknown'}</p>
          {health?.timestamp && (
            <p className="meta">Reported {formatDateTime(health.timestamp)}</p>
          )}
        </article>
        <article className="panel">
          <h3>Latest stored prediction</h3>
          {latestError && <div className="empty">{latestError}</div>}
          {latest && (
            <>
              <p className="fault-label">{formatLabel(latest.fault_label)}</p>
              <p className="meta">
                {formatConfidence(latest.confidence)} · {formatDateTime(latest.prediction_timestamp)}
              </p>
              <p className="meta">id {latest.id}</p>
            </>
          )}
        </article>
      </div>
    </section>
  )
}
