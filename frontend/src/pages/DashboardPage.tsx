import { useEffect, useState } from 'react'
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import { ApiError } from '../api/client'
import { getDashboardSummary, getFaultDistribution, getPredictionStats } from '../api/endpoints'
import type { DashboardSummary, FaultDistribution, PredictionStats } from '../api/types'
import { useLive } from '../context/live'
import {
  formatConfidence,
  formatDateTime,
  formatLabel,
  formatPercent,
  isHealthyLabel,
  relativeTime,
} from '../lib/format'

const CHART_COLORS = ['#3dd68c', '#e3b341', '#ff6b4a', '#7dd3b0', '#6ea8fe', '#ff3b5c']

export function DashboardPage() {
  const { latestPrediction, setLatestPrediction, liveTick } = useLive()
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [distribution, setDistribution] = useState<FaultDistribution>({})
  const [stats, setStats] = useState<PredictionStats | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading((current) => current || summary === null)
      setError(null)
      try {
        const [nextSummary, nextDistribution, nextStats] = await Promise.all([
          getDashboardSummary(),
          getFaultDistribution(),
          getPredictionStats(),
        ])
        if (cancelled) return
        setSummary(nextSummary)
        setDistribution(nextDistribution)
        setStats(nextStats.data)
        if (nextSummary.latest_prediction) {
          setLatestPrediction(nextSummary.latest_prediction)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'Unable to load dashboard')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    void load()
    return () => {
      cancelled = true
    }
  }, [liveTick, setLatestPrediction])

  const prediction = latestPrediction ?? summary?.latest_prediction ?? null
  const chartData = Object.entries(distribution).map(([name, value]) => ({
    name: formatLabel(name),
    value,
  }))

  return (
    <section>
      <p className="eyebrow">Plant overview</p>
      <h2 className="page-title">Motor health at a glance</h2>
      <p className="page-copy">
        Live inference results from the edge model, with fault mix and operator-facing KPIs.
      </p>

      {error && <div className="error">{error}</div>}
      {loading && !summary && <div className="loading">Loading plant metrics…</div>}

      <div className="grid kpi-grid">
        <article className="panel kpi">
          <div className="label">Predictions</div>
          <div className="value">{summary?.total_predictions ?? '—'}</div>
        </article>
        <article className="panel kpi">
          <div className="label">Healthy</div>
          <div className="value">{summary?.healthy_count ?? stats?.normal_predictions ?? '—'}</div>
        </article>
        <article className="panel kpi">
          <div className="label">Faults</div>
          <div className="value">{summary?.fault_count ?? stats?.fault_predictions ?? '—'}</div>
        </article>
        <article className="panel kpi">
          <div className="label">Avg confidence</div>
          <div className="value">
            {summary
              ? formatConfidence(summary.average_confidence)
              : stats
                ? formatConfidence(stats.average_confidence)
                : '—'}
          </div>
        </article>
      </div>

      {stats && (
        <p className="meta" style={{ marginTop: 12 }}>
          Fault rate {formatPercent(stats.fault_rate, false)} across {stats.total_predictions} samples.
        </p>
      )}

      <div className="grid two-col">
        <article className="panel">
          <h3>Latest inference</h3>
          {!prediction ? (
            <div className="empty">No predictions yet. Waiting for the edge service.</div>
          ) : (
            <>
              <div className="prediction-hero">
                <div>
                  <p
                    className={`fault-label ${isHealthyLabel(prediction.fault_label) ? 'healthy' : 'fault'}`}
                  >
                    {formatLabel(prediction.fault_label)}
                  </p>
                  <p className="meta">
                    Confidence {formatConfidence(prediction.confidence)} ·{' '}
                    {relativeTime(prediction.prediction_timestamp)}
                  </p>
                </div>
                <div className="meta">
                  {formatDateTime(prediction.prediction_timestamp)}
                </div>
              </div>
              <div className="prob-list">
                {Object.entries(prediction.probabilities_json)
                  .sort((a, b) => b[1] - a[1])
                  .map(([label, probability]) => (
                    <div className="prob-row" key={label}>
                      <span>{formatLabel(label)}</span>
                      <div className="bar">
                        <span style={{ width: `${Math.max(probability * 100, 1)}%` }} />
                      </div>
                      <span>{formatConfidence(probability)}</span>
                    </div>
                  ))}
              </div>
            </>
          )}
        </article>
        <article className="panel">
          <h3>Fault distribution</h3>
          {chartData.length === 0 ? (
            <div className="empty">No distribution data yet.</div>
          ) : (
            <div style={{ height: 280 }}>
              <ResponsiveContainer>
                <PieChart>
                  <Pie
                    data={chartData}
                    dataKey="value"
                    nameKey="name"
                    innerRadius={62}
                    outerRadius={96}
                    paddingAngle={2}
                  >
                    {chartData.map((entry, index) => (
                      <Cell key={entry.name} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      background: '#10202b',
                      border: '1px solid rgba(125,211,176,0.2)',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </article>
      </div>
    </section>
  )
}
