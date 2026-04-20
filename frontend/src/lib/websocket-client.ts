// WebSocket客户端
// 遵循fullstack-dev最佳实践实现

export interface WebSocketMessage {
  type: string;
  event?: string;
  timestamp?: string;
  data?: Record<string, unknown>;
  error?: {
    code: string;
    message: string;
  };
  notification?: NotificationData;
  broadcast?: boolean;
}

export interface NotificationData {
  id: string;
  user_id: number;
  title: string;
  message: string;
  type: 'info' | 'warning' | 'error' | 'success';
  priority: 0 | 1 | 2 | 3;
  data?: Record<string, unknown>;
  created_at: string;
  read_at?: string | null;
  read: boolean;
  aggregated?: boolean;
  compressed_data?: string;
}

export interface PresenceStatus {
  user_id: number;
  status: 'offline' | 'online' | 'away' | 'busy' | 'do_not_disturb';
  online: boolean;
  last_active?: string;
  since?: string;
  timestamp?: string;
}

export interface ConnectionConfig {
  url: string;
  autoReconnect?: boolean;
  reconnectAttempts?: number;
  reconnectInterval?: number;
  heartbeatInterval?: number;
  maxOfflineMessages?: number;
}

export type MessageHandler = (message: WebSocketMessage) => void;
export type ConnectionHandler = () => void;
export type ErrorHandler = (error: Error) => void;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private config: ConnectionConfig;
  private reconnectAttempts: number = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private offlineQueue: WebSocketMessage[] = [];
  private messageHandlers: Map<string, MessageHandler[]> = new Map();
  private connectionHandlers: ConnectionHandler[] = [];
  private disconnectHandlers: ConnectionHandler[] = [];
  private errorHandlers: ErrorHandler[] = [];
  private isConnected: boolean = false;
  private isConnecting: boolean = false;
  private authToken: string | null = null;
  private connectionId: string | null = null;

  constructor(config: ConnectionConfig) {
    this.config = {
      autoReconnect: true,
      reconnectAttempts: 10,
      reconnectInterval: 3000,
      heartbeatInterval: 30000,
      maxOfflineMessages: 100,
      ...config,
    };
  }

  connect(token?: string): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.isConnected) {
        resolve();
        return;
      }

      if (this.isConnecting) {
        reject(new Error('Connection already in progress'));
        return;
      }

      this.isConnecting = true;
      this.authToken = token || this.authToken;

      if (!this.authToken) {
        reject(new Error('Authentication token required'));
        return;
      }

      try {
        // 构建WebSocket URL
        const wsUrl = new URL(this.config.url);
        wsUrl.searchParams.append('token', this.authToken);

        this.ws = new WebSocket(wsUrl.toString());

        this.ws.onopen = () => {
          this.isConnected = true;
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.processOfflineQueue();
          this.startHeartbeat();
          
          this.connectionHandlers.forEach(handler => handler());
          console.log('[WebSocket] Connected:', wsUrl.toString());
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('[WebSocket] Failed to parse message:', error);
          }
        };

        this.ws.onerror = (error) => {
          console.error('[WebSocket] Error:', error);
          this.errorHandlers.forEach(handler => handler(
            new Error('WebSocket connection error')
          ));
        };

        this.ws.onclose = () => {
          this.isConnected = false;
          this.isConnecting = false;
          this.stopHeartbeat();
          
          this.disconnectHandlers.forEach(handler => handler());

          if (this.config.autoReconnect && this.reconnectAttempts < this.config.reconnectAttempts!) {
            this.reconnect();
          }
        };

      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  disconnect(): void {
    this.stopHeartbeat();
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.isConnected = false;
    this.isConnecting = false;
  }

  send(message: WebSocketMessage): boolean {
    if (!this.isConnected || !this.ws) {
      // 添加到离线队列
      if (this.offlineQueue.length < this.config.maxOfflineMessages!) {
        this.offlineQueue.push(message);
      }
      console.warn('[WebSocket] Not connected, message queued');
      return false;
    }

    try {
      this.ws.send(JSON.stringify(message));
      return true;
    } catch (error) {
      console.error('[WebSocket] Failed to send message:', error);
      return false;
    }
  }

  on(event: string, handler: MessageHandler): void {
    if (!this.messageHandlers.has(event)) {
      this.messageHandlers.set(event, []);
    }
    this.messageHandlers.get(event)!.push(handler);
  }

  off(event: string, handler: MessageHandler): void {
    const handlers = this.messageHandlers.get(event);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index !== -1) {
        handlers.splice(index, 1);
      }
    }
  }

  onConnect(handler: ConnectionHandler): void {
    this.connectionHandlers.push(handler);
  }

  onDisconnect(handler: ConnectionHandler): void {
    this.disconnectHandlers.push(handler);
  }

  onError(handler: ErrorHandler): void {
    this.errorHandlers.push(handler);
  }

  subscribe(topics: string[]): void {
    this.send({
      type: 'subscribe',
      data: { topics }
    });
  }

  unsubscribe(topics: string[]): void {
    this.send({
      type: 'unsubscribe',
      data: { topics }
    });
  }

  markNotificationAsRead(notificationId: string): void {
    this.send({
      type: 'notification_read',
      data: { notification_id: notificationId }
    });
  }

  updatePresence(status: PresenceStatus['status']): void {
    this.send({
      type: 'presence',
      data: {
        action: 'update_status',
        status: status
      }
    });
  }

  sendCollaborationEvent(action: string, data: Record<string, unknown>): void {
    this.send({
      type: 'collaboration',
      data: {
        action,
        ...data
      }
    });
  }

  private processOfflineQueue(): void {
    while (this.offlineQueue.length > 0) {
      const message = this.offlineQueue.shift();
      if (message) {
        this.send(message);
      }
    }
  }

  private handleMessage(message: WebSocketMessage): void {
    const { type } = message;

    // 特殊消息类型处理
    switch (type) {
      case 'ping':
        // 响应心跳
        this.send({ type: 'pong' });
        break;

      case 'pong':
        // 心跳响应，更新连接状态
        break;

      case 'connected':
        // 记录连接信息
        this.connectionId = message.data?.connection_id || null;
        console.log('[WebSocket] Connection ID:', this.connectionId);
        break;

      case 'error':
        console.error('[WebSocket] Error:', message.error);
        this.errorHandlers.forEach(handler => 
          handler(new Error(message.error?.message || 'Unknown error'))
        );
        break;

      case 'notification':
      case 'notification_read':
      case 'presence':
      case 'user_status':
      case 'collaboration':
      case 'event_update':
      case 'task_update':
        // 调用注册的处理器
        this.callHandlers(type, message);
        this.callHandlers('*', message);
        break;

      default:
        // 未知消息类型
        this.callHandlers(type, message);
    }
  }

  private callHandlers(event: string, message: WebSocketMessage): void {
    const handlers = this.messageHandlers.get(event);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(message);
        } catch (error) {
          console.error('[WebSocket] Handler error:', error);
        }
      });
    }
  }

  private reconnect(): void {
    if (this.reconnectAttempts >= this.config.reconnectAttempts!) {
      console.error('[WebSocket] Max reconnection attempts reached');
      this.errorHandlers.forEach(handler => 
        handler(new Error('WebSocket reconnection failed'))
      );
      return;
    }

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }

    this.reconnectAttempts++;

    console.log(`[WebSocket] Reconnecting (${this.reconnectAttempts}/${this.config.reconnectAttempts})...`);

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, this.config.reconnectInterval);
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    
    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected) {
        this.send({ type: 'ping' });
      }
    }, this.config.heartbeatInterval);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  getConnectionState(): {
    connected: boolean;
    connecting: boolean;
    connectionId: string | null;
  } {
    return {
      connected: this.isConnected,
      connecting: this.isConnecting,
      connectionId: this.connectionId,
    };
  }
}

// 创建全局WebSocket客户端实例
let wsClient: WebSocketClient | null = null;

export function getWebSocketClient(): WebSocketClient {
  if (!wsClient) {
    // 从环境变量获取WebSocket URL
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = window.location.host;
    const wsUrl = `${wsProtocol}//${wsHost}/ws/events/`;
    
    wsClient = new WebSocketClient({
      url: wsUrl,
      autoReconnect: true,
      reconnectAttempts: 10,
      reconnectInterval: 3000,
      heartbeatInterval: 30000,
    });
  }
  return wsClient;
}

export function initializeWebSocket(token?: string): Promise<void> {
  const client = getWebSocketClient();
  return client.connect(token);
}

export function disconnectWebSocket(): void {
  if (wsClient) {
    wsClient.disconnect();
  }
}

// 事件监听器包装函数
let notificationCallback: ((notification: NotificationData) => void) | null = null;
let presenceCallback: ((status: PresenceStatus) => void) | null = null;
let collaborationCallback: ((data: Record<string, unknown>) => void) | null = null;

export function onNotification(callback: (notification: NotificationData) => void): void {
  notificationCallback = callback;
  const client = getWebSocketClient();
  client.on('notification', (message: WebSocketMessage) => {
    if (message.notification && notificationCallback) {
      notificationCallback(message.notification);
    }
  });
}

export function onPresenceUpdate(callback: (status: PresenceStatus) => void): void {
  presenceCallback = callback;
  const client = getWebSocketClient();
  client.on('presence', (message: WebSocketMessage) => {
    if (message.data && presenceCallback) {
      presenceCallback(message.data as PresenceStatus);
    }
  });
}

export function onCollaborationEvent(callback: (data: Record<string, unknown>) => void): void {
  collaborationCallback = callback;
  const client = getWebSocketClient();
  client.on('collaboration', (message: WebSocketMessage) => {
    if (message.data && collaborationCallback) {
      collaborationCallback(message.data as Record<string, unknown>);
    }
  });
}

export function resetWebSocketClient(): void {
  if (wsClient) {
    wsClient.disconnect();
    wsClient = null;
  }
  notificationCallback = null;
  presenceCallback = null;
  collaborationCallback = null;
}