import { buildQuery, request } from './client'
import type {
  Alert,
  DashboardSummary,
  FaultDistribution,
  HealthData,
  Paginated,
  Prediction,
  PredictionStats,
  Severity,
  SuccessResponse,
} from './types'

export function getHealth() {
  return request<SuccessResponse<HealthData>>('/api/v1/health')
}

export function getLatestPrediction() {
  return request<SuccessResponse<Prediction>>('/api/v1/predictions/latest')
}

export function listPredictions(params: {
  page?: number
  size?: number
  fault_label?: string
}) {
  return request<SuccessResponse<Paginated<Prediction>>>(
    `/api/v1/predictions${buildQuery(params)}`,
  )
}

export function getPredictionStats() {
  return request<SuccessResponse<PredictionStats>>('/api/v1/predictions/stats')
}

export function getDashboardSummary() {
  return request<DashboardSummary>('/api/v1/dashboard/summary')
}

export function getFaultDistribution() {
  return request<FaultDistribution>('/api/v1/dashboard/fault-distribution')
}

export function listAlerts(params: {
  page?: number
  size?: number
  severity?: Severity | ''
  acknowledged?: boolean | ''
  resolved?: boolean | ''
}) {
  return request<SuccessResponse<Paginated<Alert>>>(
    `/api/v1/alerts${buildQuery(params)}`,
  )
}

export function getAlert(alertId: string) {
  return request<SuccessResponse<Alert>>(`/api/v1/alerts/${alertId}`)
}

export function acknowledgeAlert(alertId: string) {
  return request<SuccessResponse<Alert>>(`/api/v1/alerts/${alertId}/acknowledge`, {
    method: 'PATCH',
  })
}

export function resolveAlert(alertId: string) {
  return request<SuccessResponse<Alert>>(`/api/v1/alerts/${alertId}/resolve`, {
    method: 'PATCH',
  })
}
