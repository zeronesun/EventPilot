<template>
  <div class="home-page">
    <div class="welcome-section">
      <h2>欢迎回来，{{ authStore.user?.username }}</h2>
      <p>今天是实现目标的好日子</p>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #ecf5ff; color: #409eff">
              <el-icon><Calendar /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-number">{{ eventCount }}</div>
              <div class="stat-label">总活动数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #f0f9ff; color: #67c23a">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-number">{{ executingEventCount }}</div>
              <div class="stat-label">执行中</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #fef0f0; color: #f56c6c">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-number">{{ pendingTaskCount }}</div>
              <div class="stat-label">待处理任务</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #f4f4f5; color: #909399">
              <el-icon><DocumentChecked /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-number">{{ completedTaskCount }}</div>
              <div class="stat-label">已完成任务</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近活动 -->
    <el-card shadow="never" class="recent-events-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">最近活动</span>
          <el-button link @click="$router.push('/events')">查看全部</el-button>
        </div>
      </template>
      <div v-loading="isLoading">
        <el-empty v-if="recentEvents.length === 0" description="暂无活动" />
        <div v-else class="events-list">
          <div
            v-for="event in recentEvents"
            :key="event.id"
            class="event-item"
            @click="$router.push(`/events/${event.id}`)"
          >
            <div class="event-info">
              <h3>{{ event.name }}</h3>
              <p>
                <el-tag :type="getStatusType(event.status)" size="small">
                  {{ getStatusText(event.status) }}
                </el-tag>
                <span class="event-date">
                  {{ formatDate(event.start_date) }}
                </span>
              </p>
            </div>
            <div class="event-budget">
              <span>预算: ¥{{ formatNumber(event.estimated_budget) }}</span>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 待处理任务 -->
    <el-card shadow="never" class="pending-tasks-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">待处理任务</span>
          <el-button link @click="$router.push('/tasks')">查看全部</el-button>
        </div>
      </template>
      <div v-loading="isLoading">
        <el-empty v-if="pendingTasks.length === 0" description="暂无任务" />
        <div v-else class="tasks-list">
          <div
            v-for="task in pendingTasks.slice(0, 5)"
            :key="task.id"
            class="task-item"
          >
            <div class="task-info">
              <h3>{{ task.title }}</h3>
              <p><el-tag size="small">{{ task.task_type }}</el-tag></p>
            </div>
            <div class="task-progress">
              <el-progress :percentage="task.progress || 0" :status="task.progress >= 100 ? 'success' : undefined" />
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 实时动态 -->
    <el-card shadow="never" class="activity-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">实时动态</span>
        </div>
      </template>
      <el-timeline>
        <el-timeline-item
          v-for="(event, index) in recentEvents"
          :key="index"
          :timestamp="formatDateTime(event.created_at)"
        >
          <div>
            <p>{{ event.name }} 已创建</p>
          </div>
        </el-timeline-item>
      </el-timeline>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onActivated, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useEventsStore } from '@/stores/events'
import { useTasksStore } from '@/stores/tasks'
import {
  Calendar, TrendCharts, Document, DocumentChecked,
} from '@element-plus/icons-vue'

const authStore = useAuthStore()
const eventsStore = useEventsStore()
const tasksStore = useTasksStore()

const isLoading = computed(() => eventsStore.isLoading || tasksStore.isLoading)

const eventCount = computed(() => (eventsStore.events || []).length)
const executingEventCount = computed(() =>
  (eventsStore.events || []).filter(e => e.status === 'executing').length
)
const pendingTaskCount = computed(() =>
  (tasksStore.tasks || []).filter(t => t.status === 'pending').length
)
const completedTaskCount = computed(() =>
  (tasksStore.tasks || []).filter(t => t.status === 'completed').length
)

const recentEvents = computed(() => (eventsStore.events || []).slice(0, 5))
const pendingTasks = computed(() =>
  (tasksStore.tasks || []).filter(t => t.status === 'pending')
)

onMounted(async () => {
  try {
    await Promise.all([
      eventsStore.fetchEvents(),
      tasksStore.fetchTasks()
    ])
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
    // 不再显示通用错误消息，因为store内部已处理
  }
})

onActivated(async () => {
  try {
    await Promise.all([
      eventsStore.fetchEvents(),
      tasksStore.fetchTasks()
    ])
  } catch (error) {
    console.error('Failed to refresh dashboard data:', error)
  }
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

function formatDate(dateString: string) {
  if (!dateString) return ''
  return new Date(dateString).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

function formatDateTime(dateString: string) {
  if (!dateString) return ''
  return new Date(dateString).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatNumber(num: string | number | null | undefined) {
  if (num === null || num === undefined) return '0.00'
  const parsed = typeof num === 'string' ? parseFloat(num) : num
  return parsed.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}
</script>

<style scoped>
.home-page {
  padding: 20px;
}

.welcome-section {
  margin-bottom: 20px;
}

.welcome-section h2 {
  margin: 0 0 10px 0;
  font-size: 24px;
  font-weight: 600;
}

.welcome-section p {
  margin: 0;
  color: #909399;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 16px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  margin-right: 16px;
}

.stat-content {
  flex: 1;
}

.stat-number {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-weight: 600;
  font-size: 16px;
}

.events-list,
.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.event-item {
  padding: 12px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.event-item:hover {
  border-color: #409eff;
  background: #f5f7fa;
}

.event-info h3 {
  margin: 0 0 8px 0;
  font-size: 14px;
}

.event-info p {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.event-date {
  color: #909399;
  font-size: 12px;
}

.event-budget {
  margin-top: 8px;
  font-size: 12px;
  color: #606266;
}

.task-item {
  padding: 12px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
}

.task-info h3 {
  margin: 0 0 8px 0;
  font-size: 14px;
}

.task-info p {
  margin: 0;
  margin-bottom: 8px;
}

.task-progress {
  margin-top: 8px;
}

.recent-events-card,
.pending-tasks-card,
.activity-card {
  margin-bottom: 20px;
}
</style>
