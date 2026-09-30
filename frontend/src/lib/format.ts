const HEALTHY_LABELS = new Set(['healthy', 'normal'])

export function isHealthyLabel(label: string) {
  return HEALTHY_LABELS.has(label.trim().toLowerCase())
}

export function formatPercent(value: number, fromRatio = true) {
  const percent = fromRatio ? value * 100 : value
  return `${percent.toFixed(1)}%`
}

export function formatConfidence(value: number) {
  return `${(value * 100).toFixed(1)}%`
}

export function formatLabel(label: string) {
  return label.replace(/_/g, ' ')
}

export function formatDateTime(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'medium',
  }).format(date)
}

export function relativeTime(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  const delta = Date.now() - date.getTime()
  const seconds = Math.round(delta / 1000)
  if (seconds < 45) return 'just now'
  if (seconds < 90) return '1 min ago'
  const minutes = Math.round(seconds / 60)
  if (minutes < 60) return `${minutes} min ago`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.round(hours / 24)
  return `${days}d ago`
}

export function severityClass(severity: string) {
  return `severity-${severity.toLowerCase()}`
}
