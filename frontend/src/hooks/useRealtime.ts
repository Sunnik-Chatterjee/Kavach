import { useCallback, useEffect, useRef, useState } from 'react'
import { websocketUrl } from '../api/client'
import type { RealtimeEvent } from '../api/types'

type ConnectionState = 'connecting' | 'live' | 'offline'

export function useRealtime(onEvent: (event: RealtimeEvent) => void) {
  const [status, setStatus] = useState<ConnectionState>('connecting')
  const handlerRef = useRef(onEvent)

  useEffect(() => {
    handlerRef.current = onEvent
  }, [onEvent])

  const connect = useCallback(() => {
    let socket: WebSocket | null = null
    let closedByUs = false
    let retryTimer: number | undefined

    const open = () => {
      setStatus('connecting')
      socket = new WebSocket(websocketUrl())

      socket.onopen = () => setStatus('live')
      socket.onerror = () => setStatus('offline')
      socket.onclose = () => {
        setStatus('offline')
        if (!closedByUs) {
          retryTimer = window.setTimeout(open, 3000)
        }
      }
      socket.onmessage = (message) => {
        try {
          const payload = JSON.parse(message.data) as RealtimeEvent
          handlerRef.current(payload)
        } catch {
          // Ignore echo/keepalive text frames from the backend.
        }
      }
    }

    open()

    return () => {
      closedByUs = true
      if (retryTimer) window.clearTimeout(retryTimer)
      socket?.close()
    }
  }, [])

  useEffect(() => connect(), [connect])

  return status
}
