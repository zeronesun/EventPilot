<template>
  <div class="home-container">
    <!-- 统计卡片 -->
    <el-row :gutter="20">
      <el-col :span="6" v-for="(stat, index) in statistics" :key="index">
        <el-card class="stat-card" :body-style="{ padding: '20px' }">
          <div class="stat-content">
            <div class="stat-icon" :style="{ backgroundColor: stat.color }">
              <el-icon :size="24"><component :is="stat.icon" /></el-icon>
            </div>
            <div class="stat-details">
              <div class="stat-value">{{ stat.value }}</div>
              <div class="stat-label">{{ stat.label }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>最近活动</h3>
              <el-button type="primary" link @click="router.push('/events')">
                查看全部
              </el-button>
            </div>
          </template>

          <el-skeleton :loading="eventsStore.isLoading" :rows="3" animated>
            <el-empty v-if="!eventsStore.isLoading && recentEvents.length === 0"
              description="暂无活动" />
            <div v-else class="event-list">
              <div v-for="event in recentEvents" :key="event.id" class="event-item">
                <div class="event-header">
                  <h4>{{ event.name }}</h4>
                  <el-tag :type="getStatusType(event.status)" size="small">
                    {{ getStatusText(event.status) }}
                  </el-tag>
                </div>
                <div class="event-meta">
                  <span class="event-date">
                    <el-icon><Calendar /></el-icon>
                    {{ formatDate(event.start_date) }}
                  </span>
                  <span class="event-type">
                    <el-icon><Document /></el-icon>
                    {{ getTypeText(event.type) }}
                  </span>
                </div>
              </div>
            </div>
          </el-skeleton>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card>
          <template #header>
            <h3>待处理任务</h3>
          </template>

          <el-skeleton :loading="tasksStore.isLoading" :rows="3" animated>
            <el-empty v-if="!tasksStore.isLoading && pendingTasks.length === 0"
              description="暂无待处理任务" />
            <div v-else class="task-list">
              <div v-for="task in pendingTasks.slice(0, 5)" :key="task.id" class="task-item">
                <div class="task-header">
                  <h4>{{ task.title }}</h4>
                  <el-tag :type="getPriorityType(task.priority)" size="small">
                    {{ getPriorityText(task.priority) }}
                  </el-tag>
                </div>
                <div class="task-meta">
                  <span class="task-progress">
                    <el-progress :percentage="task.progress || 0" :stroke-width="4" />
                  </span>
                </div>
              </div>
            </div>
          </el-skeleton>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>实时动态</h3>
              <el-tag type="success" size="small">
                <el-icon class="is-loading"><Loading /></el-icon>
                实时连接
              </el-tag>
            </div>
          </template>

          <div v-if="notifications.length === 0" class="empty-notifications">
            <el-empty description="暂无最新动态" />
          </div>
          <div v-else class="notifications-list">
            <div v-for="notification in notifications" :key="notification.id"
                 class="notification-item">
              <div class="notification-content">
                <div class="notification-title">{{ notification.title }}</div>
                <div class="notification-message">{{ notification.message }}</div>
                <div class="notification-time">{{ formatTime(notification.timestamp) }}</div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore, useEventsStore, useTasksStore } from '../store'
import { useWebSocketStore } from '../stores/websocket'
import { ElMessage } from 'element-plus'
import {
  DataLine,
  HomeFilled,
  List,
  DocumentChecked,
  Calendar,
  Document,
  Loading
} from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()
const eventsStore = useEventsStore()
const tasksStore = useTasksStore()
const webSocketStore = useWebSocketStore()

const notificationCount = ref(0)

const eventCount = computed(() => eventsStore.events.length)
const executingEventCount = computed(() => eventsStore.events.filter(e => e.status === 'executing').length)
const pendingTaskCount = computed(() => tasksStore.tasks.filter(t => t.status === 'pending').length)
const completedTaskCount = computed(() => tasksStore.tasks.filter(t => t.status === 'completed').length)

const statistics = [
  {
    label: '活动总数',
    value: eventCount,
    icon: 'HomeFilled',
    color: '#409EFF'
  },
  {
    label: '进行中活动',
    value: executingEventCount,
    icon: 'DataLine',
    color: '#67C23A'
  },
  {
    label: '待处理任务',
    value: pendingTaskCount,
    icon: 'List',
    color: '#E6A23C'
  },
  {
    label: '已完成任务',
    value: completedTaskCount,
    icon: 'DocumentChecked',
    color: '#909399'
  }
]

const recentEvents = computed(() => eventsStore.events.slice(0, 5))
const pendingTasks = computed(() => tasksStore.tasks.filter(t => t.status === 'pending'))
const notifications = computed(() => webSocketStore.notifications.slice(0, 10))

onMounted(async () => {
  try {
    // Load initial data
    await Promise.all([
      eventsStore.fetchEvents(),
      tasksStore.fetchTasks(),
      webSocketStore.connect()
    ])

    // Update notification count
    notificationCount.value = notificationCount.value + notificationCount.value

  } catch (error) {
    console.error('Failed to load dashboard data:', error)
    ElMessage.error('加载数据失败')
  }
})

onUnmounted(() => {
  webSocketStore.disconnect()
})

function getStatusType(status) {
  const types = {
    planning: 'info',
    executing: 'warning',
    completed: 'success',
    reviewed: 'info',
    cancelled: 'danger'
  }
  return types[status] || 'info'
}

function getStatusText(status) {
  const texts = {
    planning: '策划中',
    executing: '执行中',
    completed: '已完成',
    reviewed: '已复盘',
    cancelled: '已取消'
  }
  return texts[status] || status
}

function getPriorityType(priority) {
  const types = {
    low: 'info',
    medium: 'warning',
    high: 'danger',
    urgent: 'danger'
  }
  return types[priority] || 'info'
}

function getPriorityText(priority) {
  const texts = {
    low: '低',
    medium: '中',
    high: '高',
    urgent: '紧急'
  }
  return texts[priority] || priority
}

function getTypeText(type) {
  const texts = {
    corporate_event: '企业活动',
    exhibition: '展会',
    conference: '会议',
    training: '培训',
    party: '聚会',
    other: '其他'
  }
  return texts[type] || type
}

function formatDate(dateString) {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}

function formatTime(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleTimeString('zh-CN')
}
</script>

<style scoped>
.home-container {
  padding: 0;
}

.stat-card {
  border-radius: 8px;
  overflow: hidden;
}

.stat-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-top: 5px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.event-list, .task-list, .notifications-list {
  max-height: 400px;
  overflow-y: auto;
}

.event-item, .task-item, .notification-item {
  padding: 15px 0;
  border-bottom: 1px solid #f0f0f0;
}

.event-item:last-child, .task-item:last-child, .notification-item:last-child {
  border-bottom: none;
}

.event-header, .task-header, .notification-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.event-header h4, .task-header h4, .notification-title {
  margin: 0;
  font-size: 15px;
  color: #333;
  font-weight: 500;
}

.event-meta, .task-meta {
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: #666;
  align-items: center;
}

.event-meta span, .task-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.task-progress {
  width: 100%;
  margin-top: 10px;
}

.notification-message {
  font-size: 14px;
  color: #666;
  margin-bottom: 5px;
}

.notification-time {
  font-size: 12px;
  color: #999;
}

.empty-notifications {
  text-align: center;
  padding: 40px 0;
}

.is-loading {
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
