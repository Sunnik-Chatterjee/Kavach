import { useCallback, useState } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { AppLayout } from './components/AppLayout'
import { LiveProvider } from './context/LiveProvider'
import { AlertDetailPage } from './pages/AlertDetailPage'
import { AlertsPage } from './pages/AlertsPage'
import { DashboardPage } from './pages/DashboardPage'
import { HealthPage } from './pages/HealthPage'
import { PredictionsPage } from './pages/PredictionsPage'

export default function App() {
  const [streamStatus, setStreamStatus] = useState<'connecting' | 'live' | 'offline'>(
    'connecting',
  )
  const onStatus = useCallback((status: 'connecting' | 'live' | 'offline') => {
    setStreamStatus(status)
  }, [])

  return (
    <LiveProvider onStatus={onStatus}>
      <Routes>
        <Route element={<AppLayout streamStatus={streamStatus} />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/predictions" element={<PredictionsPage />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/alerts/:alertId" element={<AlertDetailPage />} />
          <Route path="/health" element={<HealthPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </LiveProvider>
  )
}
