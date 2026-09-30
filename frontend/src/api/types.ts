export type Severity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

export interface SuccessResponse<T> {
  success: boolean
  message: string
  data: T
}

export interface ErrorResponse {
  success: false
  message: string
  error_code?: string
}

export interface Paginated<T> {
  total: number
  page: number
  size: number
  items: T[]
}

export interface Prediction {
  id: string
  fault_label: string
  confidence: number
  probabilities_json: Record<string, number>
  prediction_timestamp: string
  created_at: string
}

export interface PredictionStats {
  total_predictions: number
  normal_predictions: number
  fault_predictions: number
  fault_rate: number
  average_confidence: number
}

export interface DashboardSummary {
  total_predictions: number
  healthy_count: number
  fault_count: number
  average_confidence: number
  latest_prediction: Prediction | null
}

export type FaultDistribution = Record<string, number>

export interface Alert {
  id: string
  title: string
  description: string
  severity: Severity
  source_device_id: string | null
  event_type: string
  confidence: number
  created_at: string
  acknowledged: boolean
  resolved: boolean
  high_priority: boolean
}

export interface HealthData {
  status: string
  version: string
  timestamp?: string
}

export interface PredictionCreatedEvent {
  event: 'PREDICTION_CREATED'
  data: Prediction
}

export interface AlertCreatedEvent {
  type: 'alert'
  id: string
  severity: Severity
  title: string
  description: string
  timestamp: string
  high_priority: boolean
}

export interface AlertUpdatedEvent {
  type: 'alert_updated'
  id: string
  severity: Severity
  title: string
  description: string
  timestamp: string
  high_priority: boolean
}

export type RealtimeEvent =
  | PredictionCreatedEvent
  | AlertCreatedEvent
  | AlertUpdatedEvent
