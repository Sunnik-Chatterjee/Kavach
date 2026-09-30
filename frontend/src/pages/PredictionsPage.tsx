import { useEffect, useState } from 'react'
import { ApiError } from '../api/client'
import { listPredictions } from '../api/endpoints'
import type { Paginated, Prediction } from '../api/types'
import { useLive } from '../context/live'
import {
  formatConfidence,
  formatDateTime,
  formatLabel,
  isHealthyLabel,
} from '../lib/format'

export function PredictionsPage() {
  const { liveTick } = useLive()
  const [page, setPage] = useState(1)
  const [faultLabel, setFaultLabel] = useState('')
  const [appliedLabel, setAppliedLabel] = useState('')
  const [data, setData] = useState<Paginated<Prediction> | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading((current) => current || data === null)
      setError(null)
      try {
        const response = await listPredictions({
          page,
          size: 20,
          fault_label: appliedLabel || undefined,
        })
        if (!cancelled) setData(response.data)
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'Unable to load predictions')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    void load()
    return () => {
      cancelled = true
    }
  }, [appliedLabel, liveTick, page])

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.size)) : 1

  return (
    <section>
      <p className="eyebrow">History</p>
      <h2 className="page-title">Inference log</h2>
      <p className="page-copy">
        Newest-first predictions from GET /predictions, with optional fault label filter.
      </p>

      <form
        className="filter-row"
        onSubmit={(event) => {
          event.preventDefault()
          setPage(1)
          setAppliedLabel(faultLabel.trim())
        }}
      >
        <input
          value={faultLabel}
          onChange={(event) => setFaultLabel(event.target.value)}
          placeholder="Filter by fault_label"
        />
        <button className="btn primary" type="submit">
          Apply
        </button>
        <button
          className="btn"
          type="button"
          onClick={() => {
            setFaultLabel('')
            setAppliedLabel('')
            setPage(1)
          }}
        >
          Clear
        </button>
      </form>

      {error && <div className="error">{error}</div>}
      {loading && <div className="loading">Fetching predictions…</div>}

      <div className="panel table-wrap">
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Label</th>
              <th>Confidence</th>
              <th>Top classes</th>
            </tr>
          </thead>
          <tbody>
            {data?.items.map((prediction) => {
              const top = Object.entries(prediction.probabilities_json)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 3)
                .map(([label, value]) => `${formatLabel(label)} ${formatConfidence(value)}`)
                .join(' · ')
              return (
                <tr key={prediction.id}>
                  <td>{formatDateTime(prediction.prediction_timestamp)}</td>
                  <td>
                    <span
                      className={`badge ${isHealthyLabel(prediction.fault_label) ? '' : 'severity-high'}`}
                    >
                      {formatLabel(prediction.fault_label)}
                    </span>
                  </td>
                  <td>{formatConfidence(prediction.confidence)}</td>
                  <td>{top || '—'}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
        {data && data.items.length === 0 && (
          <div className="empty">No predictions match this filter.</div>
        )}
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
