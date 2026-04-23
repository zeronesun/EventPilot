/**
 * WebSocket 心跳检测 composable
 * 实现双向心跳机制，及时发现连接问题
 */

export interface HeartbeatOptions {
  interval: number; // 心跳间隔（毫秒）
  timeout: number; // 超时时间（毫秒）
  onHeartbeatMissed: () => void;
  onConnectionLost: () => void;
  onConnectionRestored: () => void;
}

export function useWebSocketHeartbeat(options: Partial<HeartbeatOptions> = {}) {
  const defaultOptions: HeartbeatOptions = {
    interval: 30000, // 30秒
    timeout: 10000,  // 10秒
    onHeartbeatMissed: () => {},
    onConnectionLost: () => {},
    onConnectionRestored: () => {},
    ...options,
  }

  let heartbeatTimer: ReturnType<typeof setInterval> | null = null
  let pongTimer: ReturnType<typeof setTimeout> | null = null
  let isRunning = false
  let missedBeats = 0
  const MAX_MISSED_BEATS = 3

  // 保存回调函数引用，用于 reset 时重新使用
  let currentSendPing: (() => void | boolean) | null = null

  function start(
    sendPing: () => void | boolean
  ): void {
    if (isRunning) {
      return
    }

    // 保存回调函数引用
    currentSendPing = sendPing
    isRunning = true
    missedBeats = 0

    const intervalId = setInterval(() => {
      try {
        // 发送 PING
        // 注意：使用保存的 currentSendPing 而不是参数中的 sendPing
        if (!currentSendPing) {
          console.error('[Heartbeat] No sendPing callback available')
          handleConnectionLost()
          return
        }

        const result = currentSendPing()

        if (result === false) {
          // 发送失败，连接可能已断开
          handleConnectionLost()
          return
        }

        // 等待 PONG 响应
        startPongTimer()

      } catch (error) {
        console.error('[Heartbeat] Send ping failed:', error)
        handleConnectionLost()
      }
    }, defaultOptions.interval)

    heartbeatTimer = intervalId
  }

  function startPongTimer(): void {
    if (pongTimer) {
      clearTimeout(pongTimer)
    }

    pongTimer = setTimeout(() => {
      // PONG 超时
      missedBeats++
      console.warn(`[Heartbeat] Missed beat (${missedBeats}/${MAX_MISSED_BEATS})`)
      defaultOptions.onHeartbeatMissed()

      if (missedBeats >= MAX_MISSED_BEATS) {
        handleConnectionLost()
      }
    }, defaultOptions.timeout)
  }

  function handlePong(): void {
    if (!isRunning) {
      return
    }

    // 收到 PONG，重置计数器
    if (missedBeats > 0) {
      missedBeats = 0
      defaultOptions.onConnectionRestored()
      console.log('[Heartbeat] Connection restored')
    }

    // 清除 PONG 计时器
    if (pongTimer) {
      clearTimeout(pongTimer)
      pongTimer = null
    }
  }

  function handleConnectionLost(): void {
    if (!isRunning) {
      return
    }

    console.error('[Heartbeat] Connection lost')
    defaultOptions.onConnectionLost()
    stop()
  }

  function stop(): void {
    isRunning = false
    missedBeats = 0

    if (heartbeatTimer) {
      clearInterval(heartbeatTimer)
      heartbeatTimer = null
    }

    if (pongTimer) {
      clearTimeout(pongTimer)
      pongTimer = null
    }
  }

  function reset(): void {
    if (!currentSendPing) {
      console.warn('[Heartbeat] Cannot reset: no sendPing callback stored, call start() first')
      return
    }

    // 停止旧的心跳
    stop()

    // 使用保存的回调函数重启
    start(currentSendPing)
  }

  function getMissedBeats(): number {
    return missedBeats
  }

  return {
    start,
    stop,
    reset,
    handlePong,
    getMissedBeats,
    isRunning: () => isRunning,
  }
}
