import { describe, it, expect, beforeEach, vi } from 'vitest'
import { WebSocketClient, WebSocketMessage } from '../lib/websocket-client'

// Mock WebSocket
class MockWebSocket {
  url: string
  onopen: (() => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  onclose: (() => void) | null = null
  readyState: number = 0

  constructor(url: string) {
    this.url = url
    this.readyState = WebSocket.CONNECTING
    setTimeout(() => {
      this.readyState = WebSocket.OPEN
      if (this.onopen) this.onopen()
    }, 10)
  }

  send(data: string): void {
    // Simulate successful send
    setTimeout(() => {
      if (this.onmessage) {
        this.onmessage(new MessageEvent('message', { data }))
      }
    }, 5)
  }

  close(): void {
    this.readyState = WebSocket.CLOSED
    if (this.onclose) this.onclose()
  }
}

// Mock global WebSocket
global.WebSocket = MockWebSocket as any

describe('WebSocketClient', () => {
  let client: WebSocketClient
  const mockUrl = 'ws://localhost:8000/ws/test'
  const mockToken = 'test-token'

  beforeEach(() => {
    client = new WebSocketClient({
      url: mockUrl,
      autoReconnect: false, // Disable auto-reconnect for tests
    })
  })

  describe('Connection', () => {
    it('should connect successfully', async () => {
      await client.connect(mockToken)
      const state = client.getConnectionState()
      expect(state.connected).toBe(true)
    })

    it('should reject connection without token', async () => {
      await expect(client.connect(undefined as any)).rejects.toThrow(
        'Authentication token required'
      )
    })

    it('should handle connection errors', async () => {
      // Test connection error handling
      const errorClient = new WebSocketClient({
        url: 'ws://invalid-test-url',
        autoReconnect: false,
      })

      await expect(errorClient.connect(mockToken)).resolves.not.toThrow()
    })
  })

  describe('Message Handling', () => {
    beforeEach(async () => {
      await client.connect(mockToken)
    })

    it('should send and receive messages', (done) => {
      const testMessage: WebSocketMessage = {
        type: 'test',
        data: { hello: 'world' },
      }

      client.on('test', (message) => {
        expect(message.data).toEqual(testMessage.data)
        done()
      })

      client.send(testMessage)
    })

    it('should handle ping/pong messages', (done) => {
      client.on('pong', (message) => {
        expect(message.type).toBe('pong')
        done()
      })

      client.send({ type: 'ping' })
    })

    it('should handle errors', (done) => {
      const errorMessage: WebSocketMessage = {
        type: 'error',
        error: {
          code: 'TEST_ERROR',
          message: 'Test error message',
        },
      }

      client.onError((error: Error) => {
        expect(error.message).toContain('Unknown error')
        done()
      })

      // Trigger error handler
      const handlers: any = client['messageHandlers']
      const errorHandler = handlers.get('error')
      if (errorHandler) {
        errorHandler(errorMessage)
      }
    })
  })

  describe('Disconnection', () => {
    it('should disconnect properly', async () => {
      await client.connect(mockToken)
      client.disconnect()
      const state = client.getConnectionState()
      expect(state.connected).toBe(false)
    })
  })

  describe('Subscription', () => {
    it('should subscribe to topics', () => {
      const spy = vi.spyOn(client, 'send')
      client.subscribe(['topic1', 'topic2'])
      expect(spy).toHaveBeenCalledWith({
        type: 'subscribe',
        data: { topics: ['topic1', 'topic2'] },
      })
    })

    it('should unsubscribe from topics', () => {
      const spy = vi.spyOn(client, 'send')
      client.unsubscribe(['topic1'])
      expect(spy).toHaveBeenCalledWith({
        type: 'unsubscribe',
        data: { topics: ['topic1'] },
      })
    })
  })

  describe('Offline Queue', () => {
    it('should queue messages when disconnected', () => {
      const offlineClient = new WebSocketClient({
        url: mockUrl,
        autoReconnect: false,
        maxOfflineMessages: 5,
      })

      // Send messages without connecting
      offlineClient.send({ type: 'test1' })
      offlineClient.send({ type: 'test2' })

      // Messages should be queued
      const queue = (offlineClient as any).offlineQueue
      expect(queue.length).toBe(2)
    })

    it('should process offline queue on reconnect', async () => {
      const reconnectClient = new WebSocketClient({
        url: mockUrl,
        autoReconnect: true,
        reconnectAttempts: 1,
        reconnectInterval: 100,
      })

      // Send messages first
      reconnectClient.send({ type: 'test1' })
      reconnectClient.send({ type: 'test2' })

      // Connect
      await reconnectClient.connect(mockToken)

      // Queue should be processed
      const queue = (reconnectClient as any).offlineQueue
      expect(queue.length).toBe(0)
    })
  })
})
