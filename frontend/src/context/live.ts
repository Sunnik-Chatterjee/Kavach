import { createContext, useContext } from 'react'
import type { Alert, Prediction } from '../api/types'

export interface Toast {
  id: string
  kind: 'fault' | 'alert' | 'escalation' | 'info'
  title: string
  detail: string
}

export interface LiveContextValue {
  latestPrediction: Prediction | null
  setLatestPrediction: (prediction: Prediction | null) => void
  toasts: Toast[]
  dismissToast: (id: string) => void
  pushToast: (toast: Omit<Toast, 'id'>) => void
  liveTick: number
  bumpLive: () => void
  applyAlertEvent: (alert: Pick<Alert, 'id' | 'title' | 'severity' | 'high_priority'> & {
    description?: string
    updated?: boolean
  }) => void
}

export const LiveContext = createContext<LiveContextValue | null>(null)

export function useLive() {
  const value = useContext(LiveContext)
  if (!value) {
    throw new Error('useLive must be used within LiveProvider')
  }
  return value
}
