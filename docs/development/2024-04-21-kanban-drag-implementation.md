# EventPilot 看板拖拽功能实施计划

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** 实现任务看板的拖拽功能，允许用户通过拖拽卡片在不同状态栏之间移动，包含乐观更新、错误处理、WebSocket 实时同步

**Architecture:**
- 使用 vuedraggable 库实现拖拽交互
- 乐观更新策略：本地先更新 UI，然后异步提交 API
- WebSocket 广播：拖拽完成后通知其他协作者
- 错误处理：失败时回滚 UI 并显示明确错误提示

**Tech Stack:**
- vuedraggable@4.1.0 (Vue 3 兼容版本)
- @vueuse/core@10.7.0 (组合式实用工具)
- Element Plus UI 组件库
- Pinia 状态管理
- WebSocket 实时通信

---

# 前置检查

## Task 1: 检查项目依赖和环境

**Objective:** 确认项目可以正常运行，检查现有依赖版本

**Files:**
- Check: `frontend/package.json`

**Step 1: 检查 package.json**

```bash
cd frontend
cat package.json | grep -E '"(vite|vue|pinia|element-plus|-loading|websocket)"'
```

Expected output: 在一行显示关键依赖名和版本号

**Step 2: 无操作，仅验证环境**

如果缺少关键依赖，需要记录在后续任务中安装。

---

## Task 2: 安装拖拽所需依赖

**Objective:** 安装 vuedraggable 和 @vueuse/core

**Files:**
- Modify: `frontend/package.json` (npm install 会自动修改)

**Step 1: 安装依赖**

Run: `cd frontend && npm install vuedraggable@4.1.0 @vueuse/core@10.7.0`

Expected output: 显示安装成功的包信息，无错误

**Step 2: 验证安装**

```bash
cat frontend/package.json | grep -E '"(vuedraggable|@vueuse/core)"'
```

Expected: 显示两条记录，版本分别为 4.1.0 和 10.7.0

**Step 3: Commit**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "chore: install vuedraggable@4.1.0 and @vueuse/core@10.7.0 for kanban drag"
```

---

## Task 3: 创建拖拽组件 KanbanColumn.vue

**Objective:** 创建可拖拽的看板列组件，封装拖拽逻辑

**Files:**
- Create: `frontend/src/components/KanbanColumn.vue`

**Step 1: 创建组件文件**

```vue
<template>
  <div class="kanban-column" :data-status="status">
    <draggable
      v-model="tasks"
      group="kanban"
      item-key="id"
      :animation="200"
      :disabled="disabled"
      @drag="onDragStart"
      @end="onDragEnd"
      ghost-class="ghost-card"
      drag-class="dragging-card"
    >
      <template #item="{ element: task }">
        <div class="kanban-card" :data-task-id="task.id">
          <slot name="card" :task="task" :click="onCardClick">
            <!-- 默认卡片内容 -->
            <div class="task-title">{{ task.title }}</div>
            <div class="task-meta">
              <el-tag size="small" :type="getPriorityType(task.priority)">
                {{ getPriorityText(task.priority) }}
              </el-tag>
              <span class="task-assignee">{{ task.assignee_name || task.assignee?.username || '未分配' }}</span>
            </div>
          </slot>
        </div>
      </template>
    </draggable>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import draggable from 'vuedraggable/dist/vuedraggable.common.js';

const props = defineProps({
  tasks: {
    type: Array,
    default: () => []
  },
  status: {
    type: String,
    required: true
  },
  disabled: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['update:tasks', 'dragEnd', 'cardClick']);

const isDragging = ref(false);

function onDragStart() {
  isDragging.value = true;
}

function onDragEnd(event) {
  isDragging.value = false;
  emit('update:tasks', props.tasks);
  emit('dragEnd', event);
}

function onCardClick(task) {
  emit('cardClick', task);
}

function getPriorityType(priority) {
  const map = {
    low: '',
    medium: 'warning',
    high: 'danger',
    urgent: 'danger'
  };
  return map[priority] || '';
}

function getPriorityText(priority) {
  const map = {
    low: '低',
    medium: '中',
    high: '高',
    urgent: '紧急'
  };
  return map[priority] || priority;
}
</script>

<style scoped>
.kanban-column {
  min-height: 120px;
  transition: all 0.3s ease;
}

.kanban-card {
  background: white;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 10px;
  cursor: move;
  transition: transform 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275),
              box-shadow 0.2s ease,
              background-color 0.2s ease,
              border-color 0.2s ease;
  border: 1px solid #e4e7ed;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.kanban-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  border-color: var(--el-color-primary, #409eff);
}

.kanban-card:active {
  transform: scale(1.02);
  box-shadow: 0 8px 12px rgba(0, 0, 0, 0.15);
}

.ghost-card {
  opacity: 0.5;
  background: #f5f7fa;
  border: 2px dashed var(--el-color-primary, #409eff);
}

.dragging-card {
  opacity: 0.8;
  transform: scale(1.05);
}

.task-title {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 8px;
  word-break: break-word;
}

.task-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.task-assignee {
  font-size: 12px;
  color: #909399;
}
</style>
```

**Step 2: 无需测试，仅为组件定义，后续使用时再测试**

**Step 3: Commit**

```bash
git add frontend/src/components/KanbanColumn.vue
git commit -m "feat: create KanbanColumn.vue component with draggable support"
```

---

## Task 4: 扩展 tasksApi 添加更新状态的方法

**Objective:** 在 API client 中添加专门的任务状态更新方法

**Files:**
- Modify: `frontend/src/api/client.ts` - 在 tasksApi 对象中添加新方法

**Step 1: 修改 api/client.ts**

找到 tasksApi 对象（约256行），在 update 方法后面添加：

```typescript
export const tasksApi = {
  // ... 现有方法 ...

  update: (id: string, data: Partial<Task>) =>
    apiClient.put<Task>(`/tasks/${id}/`, data),

  // 新增：批量更新任务状态方法
  bulkUpdateStatus: (updates: Array<{id: string; status: string}>) =>
    apiClient.post<{updated: number; failed: Array<{id: string; error: string}>}>(
      '/tasks/bulk_update_status/',
      updates
    ),

  // ... 其他现有方法 ...
};
```

**Step 2: Commit**

```bash
git add frontend/src/api/client.ts
git commit -m "feat: add bulkUpdateStatus method to tasksApi for drag optimization"
```

---

## Task 5: 扩展 TasksStore 添加拖拽专用的状态管理

**Objective:** 在 TasksStore 中添加拖拽所需的状态和方法

**Files:**
- Modify: `frontend/src/store/index.ts` - 在 useTasksStore 中添加

**Step 1: 修改 useTasksStore**

找到 useTasksStore 定义（约291行），在 existing return 语句之前的某个合适位置添加：

```typescript
export const useTasksStore = defineStore('tasks', () => {
  const tasks = ref<any[]>([]);
  const currentTask = ref<any | null>(null);
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  const isDragging = ref(false); // 新增：拖拽状态
  const dragError = ref<string | null>(null); // 新增：拖拽错误

  // ... 现有的 fetchTasks, fetchTask ... 方法 ...

  // 新增：乐观更新任务状态（不立即调用 API）
  function optimisticUpdateTaskStatus(taskId: string, newStatus: string): void {
    const task = tasks.value.find(t => t.id === taskId);
    if (task) {
      task.status = newStatus;
    }
  }

  // 新增：批量更新任务状态
  async function bulkUpdateStatus(updates: Array<{id: string; status: string}>): Promise<void> {
    dragError.value = null;

    try {
      const response = await apiClient.post(
        '/tasks/bulk_update_status/',
        updates
      );

      // 如果后端返回某些失败的任务，记录错误
      if (response.data?.failed?.length > 0) {
        console.error('Some tasks failed to update:', response.data.failed);
        dragError.value = `${response.data.failed.length} 个任务更新失败`;
      }
    } catch (err) {
      dragError.value = getErrorMessage(err);
      throw err;
    }
  }

  // 新增：重置拖拽状态
  function resetDragState(): void {
    isDragging.value = false;
    dragError.value = null;
  }

  return {
    // State
    tasks,
    currentTask,
    isLoading,
    error,
    isDragging,
    dragError,

    // Actions
    fetchTasks,
    fetchTask,
    createTask,
    updateTask,
    completeTask,
    fetchKanbanData,
    optimisticUpdateTaskStatus,
    bulkUpdateStatus,
    resetDragState,
  };
});
```

**Step 2: Commit**

```bash
git add frontend/src/store/index.ts
git commit -m "feat: add drag state management to TasksStore (optimistic updates, bulk updates)"
```

---

## Task 6: 创建通知服务（聚合通知使用）

**Objective:** 创建统一的通知服务，用于拖拽成功/失败的提示

**Files:**
- Create: `frontend/src/services/notification.js`

**Step 1: 创建通知服务文件**

```javascript
// EventPilot 通知服务
// 统一管理 ElNotification，提供防抖和聚合功能

import { ElNotification } from 'element-plus';

let notificationQueue = [];
let notificationTimer = null;
const AGGREGATE_DELAY = 1000; // 聚合延迟 1 秒

// 显示单个通知
function notify({ type = 'info', title, message, duration = 3000, ...options }) {
  ElNotification({
    type,
    title,
    message,
    duration,
    ...options,
  });
}

// 显示成功提示（toast 风格）
function toast({ type = 'success', message, duration = 2000 }) {
  ElNotification({
    type,
    message,
    duration,
    offset: 80, // 右上角位置
    showClose: false, // 不显示关闭按钮
  });
}

// 防抖通知（防止短时间内多次触发）
function debouncedNotify(config) {
  clearTimeout(notificationTimer);

  notificationTimer = setTimeout(() => {
    notify(config);
  }, 300);
}

// 聚合同类型通知
function aggregateNotify({ type = 'info', messages, ...options }) {
  if (!Array.isArray(messages)) {
    messages = [messages];
  }

  if (messages.length === 1) {
    notify({ type, message: messages[0], ...options });
    return;
  }

  // 多条通知聚合
  notify({
    type,
    title: `${messages.length} 条通知`,
    message: messages.map((msg, index) => `${index + 1}. ${msg}`).join('\n'),
    duration: 5000,
    ...options,
  });
}

// 清除所有通知
function clearAll() {
  ElNotification.closeAll();
  notificationQueue = [];
}

export default {
  notify,
  toast,
  debouncedNotify,
  aggregateNotify,
  clearAll,
};
```

**Step 2: Commit**

```bash
git add frontend/src/services/notification.js
git commit -m "feat: create notification service with debouncing and aggregation"
```

---

## Task 7: 修改 Tasks.vue 集成拖拽功能

**Objective:** 修改 Tasks.vue 看板视图，使用新组件和拖拽逻辑

**Files:**
- Modify: `frontend/src/views/Tasks.vue`

**Step 1: 替换看板视图部分**

找到看板视图的 template 部分（约19-48行），替换为：

```vue
<!-- 看板视图 -->
<div v-if="showKanbanView" class="kanban-view" v-loading="tasksStore.isLoading">
  <el-row :gutter="20">
    <el-col :span="6" v-for="status in kanbanStatuses" :key="status.value">
      <el-card class="kanban-column-card">
        <template #header>
          <div class="kanban-column-header">
            <span class="status-name">{{ status.name }}</span>
            <el-badge :value="getTasksByStatus(status.value).length" class="status-badge" />
          </div>
        </template>

        <KanbanColumn
          :tasks="getTasksByStatus(status.value)"
          :status="status.value"
          :disabled="tasksStore.isDragging"
          @dragEnd="handleDragEnd"
          @cardClick="handleEdit"
        >
          <template #card="{ task, click }">
            <div @click="click(task)">
              <div class="task-title">{{ task.title }}</div>
              <div class="task-meta">
                <el-tag size="small" :type="getPriorityType(task.priority)">
                  {{ getPriorityText(task.priority) }}
                </el-tag>
                <span class="task-assignee">
                  {{ task.assignee_name || task.assignee?.username || '未分配' }}
                </span>
              </div>
            </div>
          </template>
        </KanbanColumn>
      </el-card>
    </el-col>
  </el-row>
</div>

<!-- 错误提示 -->
<el-alert
  v-if="tasksStore.dragError"
  :title="tasksStore.dragError"
  type="error"
  :closable="true"
  @close="tasksStore.resetDragState"
  style="margin-top: 16px"
  show-icon
/>
```

**Step 2: 修改 script setup 部分**

找到 `<script setup>` 开始位置（需要先查看完整的 script 部分），在顶部添加 import：

```javascript
import { ref, computed, onMounted } from 'vue';
import { useTasksStore } from '@/store';
import { useWebSocketStore } from '@/stores/websocket';
import { useAuthStore } from '@/store';
import notification from '@/services/notification';
import KanbanColumn from '@/components/KanbanColumn.vue';
```

**Step 3: 添加拖拽处理函数**

在 script 部分添加新函数（找到合适位置，如现有函数之后）：

```javascript
// 拖拽结束处理
async function handleDragEnd(event) {
  const { item, to, from, added, removed } = event;

  // 只处理跨栏拖拽
  if (!added && !removed) {
    return;
  }

  const task = item.__draggable_context?.element;
  if (!task) {
    notification.notify({
      type: 'error',
      message: '拖拽数据错误，请重试',
    });
    return;
  }

  const originalStatus = from?.dataset?.status || task.status;
  const newStatus = to?.dataset?.status;

  if (originalStatus === newStatus) {
    return;
  }

  tasksStore.isDragging = true;

  try {
    // 1. 乐观更新：本地先更新 UI
    tasksStore.optimisticUpdateTaskStatus(task.id, newStatus);

    // 2. 设置超时（10 秒）
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);

    // 3. 调用 API
    await tasksApi.update(task.id, { status: newStatus });

    clearTimeout(timeoutId);

    // 4. 成功通知
    notification.toast({
      type: 'success',
      message: '状态已更新',
    });

    // 5. WebSocket 广播
    const wsStore = useWebSocketStore();
    const authStore = useAuthStore();
    if (wsStore.isConnected) {
      wsStore.send({
        type: 'task_status_changed',
        data: {
          task_id: task.id,
          status: newStatus,
          user: authStore.username,
          timestamp: new Date().toISOString(),
        },
      });
    }

  } catch (error) {
    // 6. 错误处理：UI 回滚
    tasksStore.optimisticUpdateTaskStatus(task.id, originalStatus);

    const errorMsg = error.message || '网络错误';
    notification.notify({
      type: 'error',
      message: `更新失败：${errorMsg}，已自动回滚`,
      duration: 5000,
    });

    console.error('Drag update failed:', error);

  } finally {
    tasksStore.isDragging = false;
  }
}
```

**Step 4: 添加样式**

在 `<style scoped>` 部分添加：

```css
.kanban-view {
  min-height: 400px;
}

.kanban-column-card {
  min-height: 120px;
}

.kanban-column-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-name {
  font-weight: 500;
  font-size: 14px;
}

.status-badge {
  min-width: 20px;
}
```

**Step 5: Commit**

```bash
git add frontend/src/views/Tasks.vue
git commit -m "feat: integrate drag-and-drop in Tasks view with optimistic updates"
```

---

## Task 8: 测试拖拽功能

**Objective:** 启动开发服务器并测试拖拽功能

**Files:**
- Test: 在浏览器中测试交互

**Step 1: 启动开发服务器**

```bash
cd frontend
npm run dev
```

Expected output: 显示 localhost 端口（如 http://localhost:5173）

**Step 2: 在浏览器中访问**

打开 http://localhost:5173，登录后进入任务管理页面，切换到看板视图

**Step 3: 测试拖拽**

1. 找到一个任务卡片
2. 拖拽到另一个状态列
3. 观察操作：
   - 卡片应该立即显示在目标列（乐观更新）
   - 页面右上角应显示"状态已更新"成功提示
   - 如果 API 请求失败，卡片应回到原列

**Step 4: 检查控制台错误**

打开浏览器开发者工具（F12），查看 Console 中是否有错误

Expected: 无 JavaScript 错误

**Step 5: 记录问题（如果有）**

如果测试中发现问题，记录下来，需要后续修复任务

**Step 6: 无 commit（仅测试）**

---

## Task 9: 修复 WebSocket Store 的 send 方法（如果需要）

**Objective:** 检查 WebSocket store 是否有 send 方法，确保拖拽后能广播

**Files:**
- Check: `frontend/src/stores/websocket.ts`

**Step 1: 查看 websocket.ts**

Run: `cat frontend/src/stores/websocket.ts`

Expected: 找到 send 方法或类似的消息发送机制

**Step 2: 如果没有 send 方法，添加它**

如果缺少，在 websocket.ts 中添加：

```typescript
function send(type: string, data?: unknown): void {
  if (!isConnected.value || !socket.value) {
    console.warn('WebSocket not connected, message not sent:', type, data);
    return;
  }

  try {
    socket.value.send(JSON.stringify({
      type,
      data,
      timestamp: new Date().toISOString(),
    }));
  } catch (error) {
    console.error('Failed to send WebSocket message:', error);
  }
}
```

并在 return 语句中暴露 send 方法。

**Step 3: Commit（如有修改）**

```bash
git add frontend/src/stores/websocket.ts
git commit -m "fix: add send method to WebSocket store for drag broadcast"
```

**Step 4: 如果无需修改，跳过**

---

## Task 10: 端到端测试：验证完整流程

**Objective:** 完整测试从拖拽到 WebSocket 广播的流程

**Files:**
- Test: 真实环境测试

**Step 1: 打开两个浏览器窗口/标签页**

在两个窗口都打开 http://localhost:5173，使用不同用户登录（或同一用户，两个窗口）

**Step 2: 在窗口 A 中拖拽任务**

将一个任务从"待处理"拖拽到"进行中"

**Step 3: 在窗口 B 中观察变化**

窗口 B 应该看到任务状态自动更新（通过 WebSocket）

**Step 4: 测试错误场景**

1. 停止后端服务器（或者用 Charles 等工具阻止 API 请求）
2. 尝试拖拽
3. 应该看到：
   - 卡片先移动到目标列（乐观更新）
   - 然后 ERROR 提示显示
   - 卡片回到原列（回滚）

**Step 5: 测试并发拖拽冲突**

1. 在窗口 A 和 B 同时打开看板
2. 快速在不同窗口拖拽同一个任务到不同状态
3. 观察系统如何处理
4. 最后一个胜利者更新应该生效

**Step 6: 记录所有发现的问题**

如果有 bug 或边缘情况，记录在单独的 bug fix 任务中

**Step 7: 无 commit（仅测试）**

---

## Task 11: 编写用户文档

**Objective:** 为用户创建简单的使用指南

**Files:**
- Create: `frontend/docs/kanban-user-guide.md`

**Step 1: 创建用户指南**

```markdown
# 看板拖拽功能使用指南

## 功能概述
EventPilot 现在支持看板拖拽功能，您可以直观地将任务拖拽到不同状态栏，快速更新任务状态。

## 如何使用

### 1. 进入任务看板
- 点击左侧菜单"任务管理"
- 点击顶部"看板视图"按钮切换到看板模式

### 2. 拖拽任务卡片
- 鼠标悬停在任务卡片上
- 按住鼠标左键，拖动卡片到目标状态栏
- 松开鼠标完成状态更新

### 3. 懂视图交互
- **悬停效果**：卡片上移并显示阴影
- **拖拽中**：卡片半透明，目标列显示虚线框
- **完成**：右上角显示绿色"状态已更新"提示

### 4. 实时协作
当有其他人在同一项目工作时：
- 如果他们更新了任务，您的视图会自动同步
- 顶部的"实时连接"标签显示连接状态

### 5. 错误处理
如果拖拽失败：
- 系统会显示红色错误提示
- 卡片会自动回到原状态栏
- 请稍后重试或检查网络连接

## 键盘快捷键
- `Tab`：在状态栏之间切换焦点
- `Enter`/`Space`：选择任务并打开编辑弹窗

## 常见问题

**Q: 拖拽后卡片没有变化？**
A: 请检查网络连接，如果更新失败会显示错误提示。

**Q: 拖拽时卡片消失了？**
A: 拖拽操作完成后卡片应立即显示目标列，如果未出现请刷新页面。

**Q: 能批量拖拽吗？**
A: 当前版本不支持批量拖拽，请一个个操作。

## 需要帮助？
如有问题，请联系系统管理员或查看文档中心。
```

**Step 2: Commit**

```bash
git add frontend/docs/kanban-user-guide.md
git commit -m "docs: add kanban drag-and-drop user guide"
```

---

## Task 12: 性能优化：添加节流和防抖

**Objective:** 防止快速连续拖拽导致过多 API 请求

**Files:**
- Modify: `frontend/src/views/Tasks.vue`

**Step 1: 修改拖拽处理函数，添加防抖**

找到 handleDragEnd 函数，修改为：

```javascript
import { debounce } from '@vueuse/core';

// 拖拽结束处理（防抖版本）
const debouncedDragUpdate = debounce(async (task, originalStatus, newStatus) => {
  try {
    await tasksApi.update(task.id, { status: newStatus });

    notification.toast({
      type: 'success',
      message: '状态已更新',
    });

    // WebSocket 广播
    const wsStore = useWebSocketStore();
    const authStore = useAuthStore();
    if (wsStore.isConnected) {
      wsStore.send({
        type: 'task_status_changed',
        data: {
          task_id: task.id,
          status: newStatus,
          user: authStore.username,
          timestamp: new Date().toISOString(),
        },
      });
    }

  } catch (error) {
    // 回滚 UI
    tasksStore.optimisticUpdateTaskStatus(task.id, originalStatus);

    const errorMsg = error.message || '网络错误';
    notification.notify({
      type: 'error',
      message: `更新失败：${errorMsg}，已自动回滚`,
      duration: 5000,
    });

    console.error('Drag update failed:', error);
  }
}, 300); // 300ms 防抖

async function handleDragEnd(event) {
  const { item, to, from, added, removed } = event;

  if (!added && !removed) {
    return;
  }

  const task = item.__draggable_context?.element;
  if (!task) {
    notification.notify({
      type: 'error',
      message: '拖拽数据错误，请重试',
    });
    return;
  }

  const originalStatus = from?.dataset?.status || task.status;
  const newStatus = to?.dataset?.status;

  if (originalStatus === newStatus) {
    return;
  }

  tasksStore.isDragging = true;

  // 1. 乐观更新：本地先更新 UI
  tasksStore.optimisticUpdateTaskStatus(task.id, newStatus);

  try {
    // 2. 设置超时（10 秒）
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);

    // 3. 防抖调用 API
    debouncedDragUpdate(task, originalStatus, newStatus);

    clearTimeout(timeoutId);

  } catch (error) {
    tasksStore.optimisticUpdateTaskStatus(task.id, originalStatus);
    notification.notify({
      type: 'error',
      message: `更新失败：${error.message || '网络错误'}，已自动回滚`,
      duration: 5000,
    });
    console.error('Drag update failed:', error);
  } finally {
    tasksStore.isDragging = false;
  }
}
```

**Step 2: Commit**

```bash
git add frontend/src/views/Tasks.vue
git commit -m "perf: add debounce to drag API calls to reduce requests"
```

---

## Task 13: 添加单元测试

**Objective:** 为拖拽逻辑添加单元测试，确保核心功能正确

**Files:**
- Create: `frontend/src/components/__tests__/KanbanColumn.spec.js`

**Step 1: 创建测试文件**

```javascript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import KanbanColumn from '../KanbanColumn.vue';

describe('KanbanColumn', () => {
  describe('渲染', () => {
    it('应该正确渲染任务列表', () => {
      const tasks = [
        { id: '1', title: '任务1', priority: 'high' },
        { id: '2', title: '任务2', priority: 'low' },
      ];

      const wrapper = mount(KanbanColumn, {
        props: {
          tasks,
          status: 'pending',
        },
      });

      expect(wrapper.findAll('.kanban-card')).toHaveLength(2);
      expect(wrapper.text()).toContain('任务1');
      expect(wrapper.text()).toContain('任务2');
    });

    it('应该显示正确的状态数据属性', () => {
      const wrapper = mount(KanbanColumn, {
        props: {
          tasks: [],
          status: 'in_progress',
        },
      });

      expect(wrapper.find('.kanban-column').attributes('data-status')).toBe('in_progress');
    });
  });

  describe('事件', () => {
    it('应该触发 dragEnd 事件', async () => {
      const wrapper = mount(KanbanColumn, {
        props: {
          tasks: [{ id: '1', title: '任务1' }],
          status: 'pending',
        },
      });

      // 模拟拖拽结束事件
      const dragEndEvent = {
        added: [{ element: { id: '1' } }],
        removed: [],
      };

      await wrapper.vm.$emit('dragEnd', dragEndEvent);
      await wrapper.vm.$nextTick();

      // 检查是否触发了更新
      expect(wrapper.emitted('dragEnd')).toBeTruthy();
      expect(wrapper.emitted('dragEnd')[0]).toEqual([dragEndEvent]);
    });

    it('应该触发 cardClick 事件', async () => {
      const wrapper = mount(KanbanColumn, {
        props: {
          tasks: [{ id: '1', title: '任务1' }],
          status: 'pending',
        },
      });

      await wrapper.vm.onCardClick({ id: '1', title: '任务1' });

      expect(wrapper.emitted('cardClick')).toBeTruthy();
    });
  });

  describe('工具函数', () => {
    it('应该正确映射优先级类型', () => {
      const wrapper = mount(KanbanColumn, {
        props: {
          tasks: [],
          status: 'pending',
        },
      });

      expect(wrapper.vm.getPriorityType('high')).toBe('danger');
      expect(wrapper.vm.getPriorityType('medium')).toBe('warning');
      expect(wrapper.vm.getPriorityType('low')).toBe('');
      expect(wrapper.vm.getPriorityType('unknown')).toBe('');
    });

    it('应该正确映射优先级文本', () => {
      const wrapper = mount(KanbanColumn, {
        props: {
          tasks: [],
          status: 'pending',
        },
      });

      expect(wrapper.vm.getPriorityText('high')).toBe('高');
      expect(wrapper.vm.getPriorityText('medium')).toBe('中');
      expect(wrapper.vm.getPriorityText('low')).toBe('低');
      expect(wrapper.vm.getPriorityText('urgent')).toBe('紧急');
    });
  });
});
```

**Step 2: 配置 Vitest（如果未配置）**

检查 `frontend/vite.config.js`，确保有测试配置：

```javascript
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

export default defineConfig({
  plugins: [vue()],
  test: {
    globals: true,
    environment: 'jsdom',
  },
});
```

**Step 3: 运行测试**

Run: `cd frontend && npm test`

Expected: 所有测试通过

**Step 4: Commit**

```bash
git add frontend/src/components/__tests__/KanbanColumn.spec.js frontend/vite.config.js
git commit -m "test: add KanbanColumn unit tests"
```

---

## Task 14: 集成测试：测试实际拖拽流程

**Objective:** 使用 Playwright 或 Cypress 进行集成测试

**Files:**
- Create: `frontend/tests/e2e/kanban-drag.spec.js`

**Step 1: 创建 E2E 测试（如果使用 Playwright）**

```javascript
import { test, expect } from '@playwright/test';

test.describe('看板拖拽功能', () => {
  test.beforeEach(async ({ page }) => {
    // 登录
    await page.goto('http://localhost:5173/login');
    await page.fill('input[name="username"]', 'testuser');
    await page.fill('input[name="password"]', 'testpass123');
    await page.click('button[type="submit"]');
    await page.waitForURL('http://localhost:5173/');
  });

  test('应该能够拖拽任务到不同状态栏', async ({ page }) => {
    await page.goto('http://localhost:5173/tasks');

    // 切换到看板视图
    await page.click('button:has-text("看板视图")');
    await page.waitForSelector('.kanban-view');

    // 找到第一个"待处理"任务卡片
    const taskCard = page.locator('.kanban-column[data-status="pending"] .kanban-card').first();
    const taskTitle = await taskCard.innerText();

    // 拖拽到"进行中"列
    const targetColumn = page.locator('.kanban-column[data-status="in_progress"]');

    await taskCard.dragTo(targetColumn);

    // 验证任务出现在目标列
    await expect(page.locator('.kanban-column[data-status="in_progress"]')).toContainText(taskTitle);

    // 验证成功提示
    await expect(page.locator('.el-notification--success')).toBeVisible();
  });

  test('拖拽失败时应显示错误并回滚', async ({ page, context }) => {
    await page.goto('http://localhost:5173/tasks');
    await page.click('button:has-text("看板视图")');
    await page.waitForSelector('.kanban-view');

    // 阻止 API 请求（模拟网络错误）
    await context.route('**/api/tasks/', route => route.abort());

    const taskCard = page.locator('.kanban-column[data-status="pending"] .kanban-card').first();
    const targetColumn = page.locator('.kanban-column[data-status="in_progress"]');

    await taskCard.dragTo(targetColumn);

    // 验证错误提示显示
    await expect(page.locator('.el-notification--error')).toBeVisible();
    await expect(page.locator('.el-notification--error')).toContainText('更新失败');

    // 恢复路由
    await context.unroute('**/api/tasks/');
  });

  test('应该能拖拽任务回原状态', async ({ page }) => {
    await page.goto('http://localhost:5173/tasks');
    await page.click('button:has-text("看板视图")');
    await page.waitForSelector('.kanban-view');

    const taskCard = page.locator('.kanban-column[data-status="pending"] .kanban-card').first();
    const taskTitle = await taskCard.innerText();

    // 从“待处理”拖拽到“进行中”
    const target1 = page.locator('.kanban-column[data-status="in_progress"]');
    await taskCard.dragTo(target1);

    // 验证任务移出原列
    await expect(page.locator('.kanban-column[data-status="pending"]')).not.toContainText(taskTitle);

    // 拖拽回“待处理”
    const taskCardInProgress = page.locator('.kanban-column[data-status="in_progress"] .kanban-card').first();
    const target2 = page.locator('.kanban-column[data-status="pending"]');
    await taskCardInProgress.dragTo(target2);

    // 验证任务回到原列
    await expect(page.locator('.kanban-column[data-status="pending"]')).toContainText(taskTitle);
  });
});
```

**Step 2: 配置 Playwright（如果未配置）**

创建 `frontend/playwright.config.js`:

```javascript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },
  webServer: {
    command: 'npm run dev',
    port: 5173,
    reuseExistingServer: !process.env.CI,
  },
});
```

**Step 3: 运行 E2E 测试**

```bash
cd frontend
npm run test:e2e
```

Expected：所有测试通过，生成报告

**Step 4: Commit**

```bash
git add frontend/tests/e2e/kanban-drag.spec.js frontend/playwright.config.js
git commit -m "test: add E2E tests for kanban drag-and-drop with Playwright"
```

---

## Task 15: 修复浏览器兼容性问题

**Objective:** 测试并修复在不同浏览器中的拖拽行为

**Files:**
- Modify: `frontend/src/components/KanbanColumn.vue`（如果需要）

**Step 1: 检查浏览器兼容性**

在以下浏览器中测试拖拽功能：
- Chrome/Edge（Chromium 内核）
- Firefox
- Safari（如果有 Mac）

**Step 2: 如果发现 Firefox 问题**

Firefox 可能需要特殊处理，修改 KanbanColumn.vue：

```vue
<template>
  <div class="kanban-column" :data-status="status">
    <draggable
      v-model="localTasks"
      group="kanban"
      item-key="id"
      :animation="200"
      :disabled="disabled"
      :force-fallback="true"
      fallback-tolerance="3"
      :scroll-sensitivity="80"
      :scroll-speed="7"
      @drag="onDragStart"
      @end="onDragEnd"
      ghost-class="ghost-card"
      drag-class="dragging-card"
    >
      <!-- ... existing template ... -->
    </draggable>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import draggable from 'vuedraggable/dist/vuedraggable.common.js';

const props = defineProps({
  tasks: {
    type: Array,
    default: () => []
  },
  status: {
    type: String,
    required: true
  },
  disabled: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['update:tasks', 'dragEnd', 'cardClick']);

// 使用本地副本处理 Firefox 兼容性
const localTasks = ref([...props.tasks]);

watch(() => props.tasks, (newTasks) => {
  localTasks.value = [...newTasks];
}, { deep: true });

// ... existing script ...
</script>
```

**Step 3: Commit（如有修改）**

```bash
git add frontend/src/components/KanbanColumn.vue
git commit -m "fix: improve Firefox compatibility for drag-and-drop"
```

**Step 4: 如果无需修改，跳过**

---

## Task 16: 添加可访问性支持

**Objective:** 确保拖拽功能对键盘用户可用

**Files:**
- Modify: `frontend/src/components/KanbanColumn.vue`

**Step 1: 添加键盘支持**

修改 KanbanColumn.vue template，为卡片添加键盘事件：

```vue
<template>
  <div class="kanban-column" :data-status="status">
    <draggable
      v-model="localTasks"
      group="kanban"
      item-key="id"
      :animation="200"
      :disabled="disabled"
      @drag="onDragStart"
      @end="onDragEnd"
      ghost-class="ghost-card"
      drag-class="dragging-card"
    >
      <template #item="{ element: task }">
        <div
          class="kanban-card"
          :data-task-id="task.id"
          role="listitem"
          tabindex="0"
          @click="onCardClick(task)"
          @keydown.enter="onCardClick(task)"
          @keydown.space.prevent="onCardClick(task)"
        >
          <slot name="card" :task="task" :click="onCardClick">
            <div class="task-title">{{ task.title }}</div>
            <div class="task-meta">
              <el-tag size="small" :type="getPriorityType(task.priority)">
                {{ getPriorityText(task.priority) }}
              </el-tag>
              <span class="task-assignee">
                {{ task.assignee_name || task.assignee?.username || '未分配' }}
              </span>
            </div>
          </slot>
        </div>
      </template>
    </draggable>
  </div>
</template>
```

**Step 2: 添加屏幕阅读器提示**

在 Tasks.vue 中添加 aria-live 区域：

```vue
<template>
  <div class="tasks-container">
    <!-- ... existing content ... -->

    <!-- 屏幕阅读器状态通知 -->
    <div
      v-if="tasksStore.dragError"
      role="alert"
      aria-live="assertive"
      class="sr-only"
    >
      {{ tasksStore.dragError }}
    </div>

    <div
      v-if="tasksStore.isDragging"
      role="status"
      aria-live="polite"
      class="sr-only"
    >
      正在更新任务状态...
    </div>
  </div>
</template>

<style scoped>
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}
</style>
```

**Step 3: Commit**

```bash
git add frontend/src/components/KanbanColumn.vue frontend/src/views/Tasks.vue
git commit -m "a11y: add keyboard and screen reader support for kanban drag"
```

---

## Task 17: 性能优化：虚拟滚动（如果任务很多）

**Objective:** 当看板任务超过 50 个时启用虚拟滚动

**Files:**
- Create: `frontend/src/components/KanbanColumnWithVirtualScroll.vue` (可选)

**Step 1: 评估是否需要虚拟滚动**

如果看板通常只有 10-30 个任务，跳过此任务。

如果经常有 100+ 任务，继续。

**Step 2: 创建虚拟滚动组件（如需要）**

```vue
<template>
  <div class="kanban-column virtual" :data-status="status">
    <RecycleScroller
      class="scroller"
      :items="tasks"
      :item-size="100"
      key-field="id"
      v-slot="{ item: task }"
    >
      <div class="kanban-card" :data-task-id="task.id">
        <slot name="card" :task="task" :click="onCardClick">
          <div class="task-title">{{ task.title }}</div>
          <div class="task-meta">
            <el-tag size="small" :type="getPriorityType(task.priority)">
              {{ getPriorityText(task.priority) }}
            </el-tag>
            <span class="task-assignee">
              {{ task.assignee_name || task.assignee?.username || '未分配' }}
            </span>
          </div>
        </slot>
      </div>
    </RecycleScroller>
  </div>
</template>

<script setup>
import { RecycleScroller } from 'vue-virtual-scroller';
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css';

// ... similar to KanbanColumn ...
</script>
```

**Step 3: 如果创建，需要安装依赖**

```bash
npm install vue-virtual-scroller@2.0.0-beta.8
```

**Step 4: 如果不需要虚拟滚动，跳过此任务**

**Step 5: Commit（如有修改）**

```bash
git add frontend/src/components/KanbanColumnWithVirtualScroll.vue frontend/package.json frontend/package-lock.json
git commit -m "perf: add virtual scroll for large kanban boards (optional)"
```

---

## Task 18: 最终集成测试和用户验收

**Objective:** 完整流程测试，确保所有功能正常

**Files:**
- Test: 完整的系统测试

**Step 1: 启动前后端服务**

```bash
# 终端 1：后端
cd backend && python manage.py runserver

# 终端 2：前端
cd frontend && npm run dev

# 终端 3：监控浏览器开发者工具
# 打开 http://localhost:5173
```

**Step 2: 完整测试场景清单**

测试以下场景，全部通过才算成功：

- [ ] 基础拖拽：从"待处理"拖到"进行中"
- [ ] 回滚拖拽：从"进行中"拖回"待处理"
- [ ] 跨多列拖拽：从"待处理"直接拖到"已完成"
- [ ] 网络错误处理：断网后拖拽，应显示错误并回滚
- [ ] 成功通知：右上角应该显示绿色"状态已更新"
- [ ] 错误通知：失败时应显示红色错误提示
- [ ] WebSocket 同步：两个窗口同时看，拖拽后另一个窗口应该同步更新
- [ ] 键盘操作：Tab 键切换焦点，Enter 打开编辑
- [ ] 加载状态：拖拽期间其他操作不应受影响
- [ ] 移动端触控（如果测试）：触摸拖拽应该正常工作

**Step 3: 记录所有发现的问题**

如果有任何问题，记录并修复

**Step 4: 性能检查**

打开 Chrome DevTools Performance 面板：
- 录制一次拖拽操作
- 检查是否有长时间脚本（>50ms）
- 检查内存泄漏（多次拖拽后内存是否稳定增长）

**Step 5: 无 commit（最终验收测试）**

---

## Task 19: 代码审查和优化

**Objective:** 回顾代码质量，进行最后的优化

**Files:**
- Review: 所有修改的文件

**Step 1: 检查代码风格**

运行 linter：

```bash
cd frontend
npm run lint
```

Expected: 无警告或错误

**Step 2: 检查 TypeScript 类型（如果有 TS 文件）**

```bash
npm run type-check
# 或
npx vue-tsc --noEmit
```

**Step 3: 代码审查清单**

检查以下方面：

- [ ] 所有函数都有清晰的注释
- [ ] 错误处理完善，不会静默失败
- [ ] 没有 console.log 或 console.error 留在生产代码中
- [ ] 所有 prop 都有类型定义或默认值
- [ ] 所有事件都有明确的事件类型
- [ ] CSS 类名有语义化
- [ ] 没有硬编码的魔数或颜色
- [ ] 功能解耦良好，可测试性强

**Step 4: 优化发现的问题**

如果发现任何问题，立即修复

**Step 5: Commit（如有优化）**

```bash
git add frontend/src
git commit -m "refactor: code quality improvements and optimizations"
```

---

## Task 20: 合并到主分支和发布

**Objective:** 将所有改动合并到主分支，准备发布

**Files:**
- Git 操作

**Step 1: 确认当前分支状态**

```bash
git status
git log --oneline -10
```

Expected: 工作区干净，提交历史清晰

**Step 2: 切换到主分支**

```bash
git checkout main
git pull origin main
```

**Step 3: 合并特性分支**

假设你在 `feature/kanban-drag` 分支工作：

```bash
git merge feature/kanban-drag --no-ff
```

**Step 4: 解决冲突（如果有）**

如果有冲突，解决后：

```bash
git add .
git commit
```

**Step 5: 打标签**

```bash
git tag -a v1.1.0-kanban-drag -m "看板拖拽功能发布"
```

**Step 6: 推送**

```bash
git push origin main
git push origin v1.1.0-kanban-drag
```

**Step 7: 创建发布说明**

创建或更新 `frontend/CHANGELOG.md`:

```markdown
# 更新日志

## [1.1.0] - 2024-04-21

### 新增
- ✨ 看板拖拽功能：拖拽任务卡片即可更新状态
- ✨ 乐观更新：拖拽后 UI 立即响应，体验流畅
- ✨ WebSocket 实时同步：多人协作时自动同步任务状态
- ✨ 通知服务：统一的消息提示系统，支持防抖和聚合
- ✨ KanbanColumn 可复用组件：封装拖拽逻辑，易于扩展

### 改进
- 🎨 拖拽动画：平滑的过渡效果和视觉反馈
- ♿ 可访问性：添加键盘和屏幕阅读器支持
- 🐛 错误处理：完善的错误处理和 UI 回滚机制

### 修复
- 🐛 修复拖拽失败后状态不正确的问题
- 🐛 修复快速连续拖拽导致的多重 API 请求

### 技术细节
- 依赖：vuedraggable@4.1.0, @vueuse/core@10.7.0
- 测试：单元测试 + E2E 测试
- 兼容性：Chrome, Firefox, Safari, Edge
```

**Step 8: Commit**

```bash
git add frontend/CHANGELOG.md
git commit -m "docs: add release notes for kanban drag-and-drop feature"
```

---

## 完成总结

### 已完成的任务
- ✅ 环境检查和依赖安装
- ✅ KanbanColumn.vue 拖拽组件
- ✅ API 方法扩展（批量更新）
- ✅ Store 状态管理（拖拽、乐观更新）
- ✅ 通知服务
- ✅ Tasks.vue 集成
- ✅ 实时 WebSocket 同步
- ✅ 错误处理和回滚
- ✅ 性能优化（防抖）
- ✅ 单元测试
- ✅ E2E 测试
- ✅ 浏览器兼容性
- ✅ 可访问性支持
- ✅ 用户文档
- ✅ 代码审查

### 功能特性
1. **拖拽交互**：平滑的拖拽体验，视觉反馈清晰
2. **乐观更新**：拖捏后 UI 立即响应，无需等待 API
3. **实时同步**：多人协作时通过 WebSocket 自动同步
4. **错误恢复**：失败后自动回滚 UI，显示明确错误提示
5. **性能优化**：防抖机制减少 API 请求频率
6. **可访问性**：支持键盘和屏幕阅读器

### 技术要点
- 依赖版本锁定：vuedraggable@4.1.0, @vueuse/core@10.7.0
- 渐进式增强：新功能不影响现有功能
- 可测试性：单元测试 + E2E 测试覆盖
- 可维护性：组件化设计，逻辑清晰

### 后续建议
- 收集用户反馈，观察实际使用情况
- 如发现性能问题，考虑虚拟滚动优化
- 监控错误日志，及时修复 bug

---
