import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import type { Alert, Prediction, RealtimeEvent } from '../api/types'
import { isHealthyLabel } from '../lib/format'
import { LiveContext, type Toast } from './live'
import { useRealtime } from '../hooks/useRealtime'

export function LiveProvider({
  children,
  onStatus,
}: {
  children: ReactNode
  onStatus: (status: 'connecting' | 'live' | 'offline') => void
}) {
  const [latestPrediction, setLatestPrediction] = useState<Prediction | null>(null)
  const [toasts, setToasts] = useState<Toast[]>([])
  const [liveTick, setLiveTick] = useState(0)

  const pushToast = useCallback((toast: Omit<Toast, 'id'>) => {
    const id = crypto.randomUUID()
    setToasts((current) => [...current.slice(-4), { ...toast, id }])
    window.setTimeout(() => {
      setToasts((current) => current.filter((item) => item.id !== id))
    }, 7000)
  }, [])

  const dismissToast = useCallback((id: string) => {
    setToasts((current) => current.filter((item) => item.id !== id))
  }, [])

  const bumpLive = useCallback(() => {
    setLiveTick((tick) => tick + 1)
  }, [])

  const applyAlertEvent = useCallback(
    (
      alert: Pick<Alert, 'id' | 'title' | 'severity' | 'high_priority'> & {
        description?: string
        updated?: boolean
      },
    ) => {
      pushToast({
        kind: alert.updated ? 'escalation' : 'alert',
        title: alert.updated ? 'Alert escalated' : alert.title,
        detail: `${alert.severity}${alert.high_priority ? ' · high priority' : ''}${
          alert.description ? ` — ${alert.description}` : ''
        }`,
      })
      bumpLive()
    },
    [bumpLive, pushToast],
  )

  const onEvent = useCallback(
    (event: RealtimeEvent) => {
      if ('event' in event && event.event === 'PREDICTION_CREATED') {
        setLatestPrediction(event.data)
        bumpLive()
        if (!isHealthyLabel(event.data.fault_label)) {
          pushToast({
            kind: 'fault',
            title: 'Fault detected',
            detail: `${event.data.fault_label.replace(/_/g, ' ')} at ${(event.data.confidence * 100).toFixed(1)}% confidence`,
          })
        }
        return
      }
      if ('type' in event && event.type === 'alert') {
        applyAlertEvent({
          id: event.id,
          title: event.title,
          severity: event.severity,
          high_priority: event.high_priority,
          description: event.description,
        })
        return
      }
      if ('type' in event && event.type === 'alert_updated') {
        applyAlertEvent({
          id: event.id,
          title: event.title,
          severity: event.severity,
          high_priority: event.high_priority,
          description: event.description,
          updated: true,
        })
      }
    },
    [applyAlertEvent, bumpLive, pushToast],
  )

  const status = useRealtime(onEvent)

  useEffect(() => {
    onStatus(status)
  }, [onStatus, status])

  const value = useMemo(
    () => ({
      latestPrediction,
      setLatestPrediction,
      toasts,
      dismissToast,
      pushToast,
      liveTick,
      bumpLive,
      applyAlertEvent,
    }),
    [
      applyAlertEvent,
      bumpLive,
      dismissToast,
      latestPrediction,
      liveTick,
      pushToast,
      toasts,
    ],
  )

  return <LiveContext.Provider value={value}>{children}</LiveContext.Provider>
}
