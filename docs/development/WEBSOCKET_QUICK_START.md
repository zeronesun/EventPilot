# WebSocket实时通讯基础设施 - 快速入门

## 🚀 快速开始

### 1. 环境准备

确保已安装所有依赖：
```bash
pip install channels daphne channels-redis
```

### 2. 启动Redis服务

**开发环境**：
```bash
# 启动Redis (如果已在运行则跳过)
redis-server
```

**生产环境**：
```bash
# 使用Docker运行Redis
docker run -d -p 6379:6379 redis:7-alpine
```

### 3. 配置环境变量

在 `.env` 文件中添加：
```bash
# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# WebSocket配置
WEBSOCKET_CONCURRENT_DEVICES=3
WEBSOCKET_HEARTBEAT_INTERVAL=30
WEBSOCKET_HEARTBEAT_TIMEOUT=90
```

### 4. 运行Django服务器

**开发环境** (使用Daphne支持WebSocket)：
```bash
daphne config.asgi:application -b 0.0.0.0 -p 8000
```

或者使用runserver (仅用于测试，功能有限)：
```bash
python manage.py runserver
```

## 💻 前端集成

### 1. 安�始化WebSocket客户端

在Vue组件中：
```vue
<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { 
  initializeWebSocket, 
  onNotification, 
  getWebSocketClient 
} from '@/lib/websocket-client';
import { useWebSocketStore } from '@/stores/websocket';
import { useAuthStore } from '@/stores/auth';

const wsStore = useWebSocketStore();
const authStore = useAuthStore();
const connected = ref(false);

onMounted(async () => {
  try {
    // 使用JWT token连接WebSocket
    await initializeWebSocket(authStore.token);
    connected.value = true;
    
    console.log('WebSocket已连接');
  } catch (error) {
    console.error('WebSocket连接失败:', error);
  }
});

// 监听通知
onNotification((notification) => {
  console.log('收到通知:', notification);
  // 显示通知到UI
  showToast(notification.message);
});
</script>

<template>
  <div>
    <div v-if="connected" class="status-indicator">
      🟢 WebSocket已连接
    </div>
    <div v-else class="status-indicator">
      🔴 WebSocket未连接
    </div>
  </div>
</template>
```

### 2. 使用Pinia Store

```vue
<script setup lang="ts">
import { computed } from 'vue';
import { useWebSocketStore } from '@/stores/websocket';

const wsStore = useWebSocketStore();

// 响应式数据
const connected = computed(() => wsStore.connected);
const notifications = computed(() => wsStore.notifications);
const unreadCount = computed(() => wsStore.unreadCount);

// 标记通知为已读
function markAsRead(notificationId: string) {
  wsStore.markAsRead(notificationId);
}

// 获取在线用户
function getOnlineUsers() {
  return wsStore.getOnlineUsers();
}

// 更新自己的状态
function setStatus(status: 'online' | 'away' | 'busy') {
  wsStore.updateMyStatus(status);
}
</script>

<template>
  <div>
    <!-- 通知列表 -->
    <div v-for="notification in notifications" :key="notification.id">
      <div class="notification" :class="{ unread: !notification.read }">
        <h4>{{ notification.title }}</h4>
        <p>{{ notification.message }}</p>
        <small>{{ notification.created_at }}</small>
        <button @click="markAsRead(notification.id)">
          标记为已读
        </button>
      </div>
    </div>
    
    <!-- 未读计数 -->
    <div v-if="unreadCount > 0">
      🔔 {{ unreadCount }} 条未读通知
    </div>
  </div>
</template>
```

## 🔌 API使用

### 后端触发通知

```python
from apps.websocket.notification_service import (
    NotificationService, 
    NotificationType, 
    NotificationPriority
)

# 创建服务实例
notification_service = NotificationService()

# 创建通知
notification = await notification_service.create_notification(
    user_id=1,  # 接收用户ID
    title="任务分配",
    message="您被分配了新任务: 完成活动策划",
    notification_type=NotificationType.INFO,
    priority=NotificationPriority.NORMAL,
    data={
        "task_id": 123,
        "event_id": 456
    }
)

# 自动发送活动更新通知
await notification_service.send_event_notification(
    event_id=456,
    action='updated'
)

# 自动发送任务分配通知
await notification_service.send_task_notification(
    task_id=123,
    action='assigned',
    user_id=1,
    data={"task_name": "完成策划"}
)
```

### 查询在线状态

```python
from apps.websocket.status_manager import StatusManager, UserStatus

status_manager = StatusManager()
presence_service = status_manager.get_presence_service()

# 检查用户是否在线
is_online = presence_service.is_user_online(user_id=1)

# 获取所有在线用户
online_users = presence_service.get_online_users()

# 更新用户状态
await presence_service.update_user_status(
    user_id=1,
    status=UserStatus.BUSY,
    device_id="device_123"
)

# 获取用户状态详情
status = presence_service.get_user_status(user_id=1)
```

### 协作功能

```python
# 用户进入活动详情页
await status_manager.update_event_state(
    event_id=1,
    user_id=1,
    action='enter'
)

# 用户离开活动详情页
await status_manager.update_event_state(
    event_id=1,
    user_id=1,
    action='exit'
)

# 查看谁正在查看活动
event_state = status_manager.get_event_state(event_id=1)
active_users = event_state['active_users']  # 查看活动的用户ID列表
```

## 📱 前端监听事件

### 监听通知
```typescript
import { onNotification } from '@/lib/websocket-client';

onNotification((notification) => {
  // 处理通知
  showToast({
    title: notification.title,
    message: notification.message,
    type: notification.type // 'info' | 'warning' | 'error' | 'success'
  });
});
```

### 监听在线状态更新
```typescript
import { onPresenceUpdate } from '@/lib/websocket-client';

onPresenceUpdate((status) => {
  // 更新用户在线状态
  console.log(`用户 ${status.user_id} 状态变更为: ${status.status}`);
  
  if (status.online) {
    // 显示在线指示器
  }
});
```

### 监听协作事件
```typescript
import { onCollaborationEvent } from '@/lib/websocket-client';

onCollaborationEvent((data) => {
  if (data.action === 'enter_event') {
    // 显示"其他人正在查看此活动"提示
    showCollaboratorInfo(data.user_id);
  } else if (data.action === 'view_task') {
    // 显示任务协作信息
  }
});
```

### 连接状态监听
```typescript
import { getWebSocketClient } from '@/lib/websocket-client';

const client = getWebSocketClient();

// 监听连接事件
client.onConnect(() => {
  console.log('WebSocket已连接');
});

// 监听断开事件
client.onDisconnect(() => {
  console.log('WebSocket已断开，尝试重连...');
});

// 监听错误事件
client.onError((error) => {
  console.error('WebSocket错误:', error);
});
```

## 🎯 常用场景

### 场景1：实时任务分配

**后端** (当任务被分配时)：
```python
# 在任务创建/更新的信号处理器中
@receiver(post_save, sender=Task)
def task_assigned(sender, instance, created, **kwargs):
    if instance.assignee_id:
        notification_service = NotificationService()
        await notification_service.send_task_notification(
            task_id=instance.id,
            action='assigned',
            user_id=instance.assignee_id
        )
```

**前端** (实时接收)：
```typescript
onNotification((notification) => {
  if (notification.type === 'info' && 'task' in notification.message) {
    // 显示任务分配通知
    showToast(`新任务分配: ${notification.message}`);
    // 刷新任务列表
    refreshTasks();
  }
});
```

### 场景2：协作编辑活动详情

**前端 (进入活动详情页)：
```typescript
import { sendCollaboration } from '@/lib/websocket-client';

// 进入活动详情
sendCollaboration('enter_event', { event_id: eventId });

// 离开活动详情
onUnmounted(() => {
  sendCollaboration('exit_event', { event_id: eventId });
});
```

**前端 (显示协作者)：
```typescript
const collaborators = ref<User[]>([]);

onCollaborationEvent((data) => {
  if (data.action === 'enter_event' && data.event_id === eventId) {
    // 获取用户信息并添加到协作者列表
    loadUserInfo(data.user_id).then(user => {
      collaborators.value.push(user);
    });
  } else if (data.action === 'exit_event') {
    // 从协作者列表中移除
    collaborators.value = collaborators.value.filter(
      u => u.id !== data.user_id
    );
  }
});
```

### 场景3：在线状态显示

**前端 (用户列表)：
```vue
<script setup lang="ts">
import { useWebSocketStore } from '@/stores/websocket';

const wsStore = useWebSocketStore();
const users = ref<User[]>([]);

// 加载用户列表
loadUsers().then(data => {
  users.value = data;
});

// 获取在线状态
function getUserStatus(userId: number) {
  const status = wsStore.getUserPresence(userId);
  return status?.online ? '🟢 在线' : '🔴 离线';
}
</script>

<template>
  <div>
    <div v-for="user in users" :key="user.id">
      <span>{{ user.username }}</span>
      <span>{{ getUserStatus(user.id) }}</span>
    </div>
  </div>
</template>
```

## 🧪 测试

### 使用测试脚本
```bash
# 运行WebSocket基础设施测试
python3 test_websocket_infrastructure.py
```

### 手动测试

1. **启动服务器**：
```bash
daphne config.asgi:application -b 0.0.0.0 -p 8000
```

2. **前端连接**：
```typescript
// 在浏览器控制台测试
const client = getWebSocketClient();
await client.connect('your-jwt-token');
```

3. **发送测试消息**：
```typescript
client.send({
  type: 'ping',
  timestamp: new Date().toISOString()
});
```

## 🐛 调试

### 启用详细日志

在 `config/settings/base.py` 中：
```python
DJANGO_LOG_LEVEL = 'DEBUG'
```

### 监控Redis

```bash
# 连接到Redis CLI
redis-cli

# 查看Channel层活动
MONITOR

# 查看所有键
KEYS eventpilot:*

# 查看特定组的消息
PUBLISH eventpilot:websocket "test-message"
```

### WebSocket调试工具

在浏览器控制台：
```javascript
// 查看连接状态
const client = getWebSocketClient();
console.log('Connection state:', client.getConnectionState());

// 监听所有消息
client.on('*', (message) => {
  console.log('All messages:', message);
});
```

## 📊 监控

### 查看连接统计

```python
from apps.websocket.consumer import EventPilotConsumer

connection_manager = EventPilotConsumer.get_connection_manager()
stats = connection_manager.get_stats()

print(f"活跃连接数: {stats['active_connections']}")
print(f"总连接数: {stats['total_connections']}")
print(f"唯一用户数: {stats['unique_users']}")
print(f"消息已发送: {stats['messages_sent']}")
```

### 查看通知队列

```python
from apps.websocket.notification_service import NotificationService

notification_service = NotificationService()
queue_stats = notification_service.get_queue_stats()

print(f"队列中的通知数: {queue_stats['total_queued']}")
print(f"按优先级分布: {queue_stats['by_priority']}")
```

## 🚨 常见问题

### Q1: WebSocket连接失败

**检查**：
1. Redis服务是否运行
2. JWT token是否有效
3. 端口8000是否被占用
4. 防火墙是否允许WebSocket

**解决**：
```bash
# 检查Redis
redis-cli ping  # 应返回PONG

# 检查JWT
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/auth/verify/

# 检查端口
netstat -tuln | grep 8000
```

### Q2: 通知不显示

**检查**：
1. 前端是否已连接WebSocket
2. 是否正确订阅了事件
3. 用户ID是否匹配

**调试**：
```typescript
// 添加日志
onNotification((notification) => {
  console.log('Received notification:', notification);
  showToast(notification.message);
});
```

### Q3: 状态不同步

**检查**：
1. 心跳是否正常工作
2. 超时设置是否合理
3. 网络连接是否稳定

**解决**：
- 检查WSGI日志中的心跳消息
- 增加超时时间：`WEBSOCKET_HEARTBEAT_TIMEOUT`
- 使用重连机制

## 📚 更多资源

- **完整实现报告**: `PHASE2_WEBSOCKET_IMPLEMENTATION_REPORT.md`
- **后端代码**: `apps/websocket/`
- **前端代码**: `frontend/src/lib/websocket-client.ts`
- **Pinia Store**: `frontend/src/stores/websocket.ts`
- **测试**: `tests/test_websocket/`

## 🤝 获取帮助

遇到问题？
1. 查看实现报告了解架构细节
2. 检查日志文件 `logs/django.log`
3. 参考测试用例了解使用模式
4. 运行验证脚本检查配置：`./verify_websocket_setup.sh`

---

**祝您使用愉快！如有问题，请查看完整文档或联系开发团队。** 🎉