import { defineStore } from 'pinia';
import { ref, computed, watch } from 'vue';
import {
  WebSocketClient,
  WebSocketMessage,
  NotificationData,
  PresenceStatus,
  getWebSocketClient,
  initializeWebSocket,
  disconnectWebSocket,
  onNotification,
  onPresenceUpdate,
  onCollaborationEvent,
} from '@/lib/websocket-client';

interface WebSocketState {
  connected: boolean;
  connecting: boolean;
  connectionId: string | null;
  notifications: NotificationData[];
  unreadCount: number;
  presence: Map<number, PresenceStatus>;
  collaborationEvents: Map<string, unknown[]>;
}

const initialState: WebSocketState = {
  connected: false,
  connecting: false,
  connectionId: null,
  notifications: [],
  unreadCount: 0,
  presence: new Map(),
  collaborationEvents: new Map(),
};

export const useWebSocketStore = defineStore('websocket', () => {
  // State
  const state = ref<WebSocketState>(JSON.parse(JSON.stringify(initialState)));
  
  // Getters
  const connected = computed(() => state.value.connected);
  const connecting = computed(() => state.value.connecting);
  const connectionId = computed(() => state.value.connectionId);
  const notifications = computed(() => state.value.notifications);
  const unreadCount = computed(() => state.value.unreadCount);
  const presenceList = computed(() => Array.from(state.value.presence.values()));
  
  // Actions
  async function connect(token: string) {
    const client = getWebSocketClient();
    
    // 设置事件处理器
    setupEventHandlers(client);
    
    try {
      state.value.connecting = true;
      await initializeWebSocket(token);
    } catch (error) {
      state.value.connecting = false;
      throw error;
    }
  }
  
  function disconnect() {
    disconnectWebSocket();
    resetState();
  }
  
  function resetState() {
    state.value = JSON.parse(JSON.stringify(initialState));
  }
  
  function setupEventHandlers(client: WebSocketClient) {
    // 连接状态
    client.onConnect(() => {
      const connectionState = client.getConnectionState();
      state.value.connected = connectionState.connected;
      state.value.connecting = connectionState.connecting;
      state.value.connectionId = connectionState.connectionId;
    });
    
    client.onDisconnect(() => {
      state.value.connected = false;
      state.value.connecting = false;
    });
    
    client.onError((error) => {
      console.error('[WebSocket Store] Error:', error);
    });
  }
  
  // 通知相关
  function addNotification(notification: NotificationData) {
    state.value.notifications.unshift(notification);
    
    if (!notification.read) {
      state.value.unreadCount++;
    }
    
    // 限制存储的通知数量
    if (state.value.notifications.length > 100) {
      state.value.notifications = state.value.notifications.slice(0, 100);
    }
  }
  
  function markAsRead(notificationId: string) {
    const notification = state.value.notifications.find(n => n.id === notificationId);
    if (notification && !notification.read) {
      notification.read = true;
      notification.read_at = new Date().toISOString();
      state.value.unreadCount = Math.max(0, state.value.unreadCount - 1);
      
      // 发送到服务器
      const client = getWebSocketClient();
      client.markNotificationAsRead(notificationId);
    }
  }
  
  function markAllAsRead() {
    state.value.notifications.forEach(notification => {
      if (!notification.read) {
        notification.read = true;
        notification.read_at = new Date().toISOString();
      }
    });
    state.value.unreadCount = 0;
  }
  
  function clearNotifications() {
    state.value.notifications = [];
    state.value.unreadCount = 0;
  }
  
  // 在线状态相关
  function updatePresence(userId: number, status: PresenceStatus) {
    state.value.presence.set(userId, status);
  }
  
  function removePresence(userId: number) {
    state.value.presence.delete(userId);
  }
  
  function getUserPresence(userId: number): PresenceStatus | undefined {
    return state.value.presence.get(userId);
  }
  
  function getOnlineUsers(): PresenceStatus[] {
    return presenceList.value.filter(p => p.online);
  }
  
  // 协作事件相关
  function addCollaborationEvent(eventId: string, data: unknown) {
    if (!state.value.collaborationEvents.has(eventId)) {
      state.value.collaborationEvents.set(eventId, []);
    }
    
    const events = state.value.collaborationEvents.get(eventId)!;
    events.push(data);
    
    // 限制存储的事件数量
    if (events.length > 50) {
      events.shift();
    }
  }
  
  function getCollaborationEvents(eventId: string): unknown[] {
    return state.value.collaborationEvents.get(eventId) || [];
  }
  
  function clearCollaborationEvents(eventId: string) {
    state.value.collaborationEvents.delete(eventId);
  }
  
  // 订阅主题
  function subscribe(topics: string[]) {
    const client = getWebSocketClient();
    client.subscribe(topics);
  }
  
  function unsubscribe(topics: string[]) {
    const client = getWebSocketClient();
    client.unsubscribe(topics);
  }
  
  // 更新自己的在线状态
  function updateMyStatus(status: PresenceStatus['status']) {
    const client = getWebSocketClient();
    client.updatePresence(status);
  }
  
  // 发送协作事件
  function sendCollaboration(action: string, data: Record<string, unknown>) {
    const client = getWebSocketClient();
    client.sendCollaborationEvent(action, data);
  }

  // 发送消息
  function send(message: WebSocketMessage) {
    const client = getWebSocketClient();
    client.send(message);
  }

  return {
    state,
    connected,
    connecting,
    connectionId,
    notifications,
    unreadCount,
    presenceList,
    connect,
    disconnect,
    resetState,
    addNotification,
    markAsRead,
    markAllAsRead,
    clearNotifications,
    updatePresence,
    removePresence,
    getUserPresence,
    getOnlineUsers,
    addCollaborationEvent,
    getCollaborationEvents,
    clearCollaborationEvents,
    subscribe,
    unsubscribe,
    updateMyStatus,
    sendCollaboration,
    send,
  };
}, {
  persist: true // 持久化到localStorage
});

// 设置通知监听器
export function setupNotificationHandlers(store: ReturnType<typeof useWebSocketStore>) {
  onNotification((notification) => {
    store.addNotification(notification);
  });
  
  onPresenceUpdate((status) => {
    store.updatePresence(status.user_id, status);
  });
  
  onCollaborationEvent((data) => {
    if (data.action === 'enter_event' && data.event_id) {
      store.addCollaborationEvent(`event_${data.event_id}`, data);
    } else if (data.action === 'view_task' && data.task_id) {
      store.addCollaborationEvent(`task_${data.task_id}`, data);
    }
  });
}