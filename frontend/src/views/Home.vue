<template>
  <div class="home-container">
    <el-container>
      <el-aside width="250px" class="sidebar">
        <div class="user-info">
          <el-avatar :size="60" :src="authStore.currentUser?.avatar_url">
            {{ authStore.username.charAt(0).toUpperCase() }}
          </el-avatar>
          <div class="user-details">
            <p class="user-name">{{ authStore.username }}</p>
            <p class="user-role">{{ getRoleText(authStore.userRole) }}</p>
          </div>
        </div>
        
        <el-menu
          :default-active="activeMenu"
          class="sidebar-menu"
          @select="handleMenuSelect"
        >
          <el-menu-item index="dashboard">
            <el-icon><DataLine /></el-icon>
            <span>工作台</span>
          </el-menu-item>
          <el-menu-item index="activities">
            <el-icon><HomeFilled /></el-icon>
            <span>活动管理</span>
          </el-menu-item>
          <el-menu-item index="tasks">
            <el-icon><List /></el-icon>
            <span>任务管理</span>
          </el-menu-item>
          <el-menu-item index="users">
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </el-menu-item>
          <el-menu-item index="files">
            <el-icon><Folder /></el-icon>
            <span>文件管理</span>
          </el-menu-item>
          <el-menu-item index="checklists">
            <el-icon><DocumentChecked /></el-icon>
            <span>清单管理</span>
          </el-menu-item>
          <el-menu-item index="profiles">
            <el-icon><UserFilled /></el-icon>
            <span>关联方档案</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-container>
        <el-header class="header">
          <div class="header-left">
            <h2>工作台</h2>
          </div>
          <div class="header-right">
            <el-badge :value="notificationCount" class="notification-badge">
              <el-button circle @click="showNotifications">
                <el-icon><Bell /></el-icon>
              </el-button>
            </el-badge>
            <el-button circle @click="handleLogout" type="danger">
              <el-icon><SwitchButton /></el-icon>
            </el-button>
          </div>
        </el-header>

        <el-main class="main-content">
          <el-row :gutter="20">
            <!-- 统计卡片 -->
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
                    <el-button type="primary" link @click="router.push('/activities')">
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
        </el-main>

        <el-footer height="40px" class="footer">
          <div class="footer-content">
            <span>© 2026 EventPilot - 活动领航系统</span>
            <span>v1.2 Phase 2</span>
          </div>
        </el-footer>
      </el-container>
    </el-container>
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
  User,
  Folder,
  DocumentChecked,
  Bell,
  SwitchButton,
  Calendar,
  Document,
  Loading
} from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()
const eventsStore = useEventsStore()
const tasksStore = useTasksStore()
const webSocketStore = useWebSocketStore()

const activeMenu = ref('dashboard')
const notificationCount = ref(0)

const statistics = [
  {
    label: '活动总数',
    value: computed(() => eventsStore.events.length),
    icon: 'HomeFilled',
    color: '#409EFF'
  },
  {
    label: '进行中活动',
    value: computed(() => eventsStore.events.filter(e => e.status === 'executing').length),
    icon: 'DataLine',
    color: '#67C23A'
  },
  {
    label: '待处理任务',
    value: computed(() => tasksStore.tasks.filter(t => t.status === 'pending').length),
    icon: 'List',
    color: '#E6A23C'
  },
  {
    label: '已完成任务',
    value: computed(() => tasksStore.tasks.filter(t => t.status === 'completed').length),
    icon: 'DocumentChecked',
    color: '#909399'
  }
]

const recentEvents = computed(() => eventsStore.events.slice(0, 5))
const pendingTasks = computed(() => tasksStore.tasks.filter(t => t.status === 'pending'))
const notifications = computed(() => webSocketStore.notifications.slice(0, 10))

onMounted(async () => {
  try {
    authStore.initialize()
    
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

function handleMenuSelect(index) {
  activeMenu.value = index
  
  switch(index) {
    case 'dashboard':
      router.push('/')
      break
    case 'activities':
      router.push('/events')
      break
    case 'tasks':
      router.push('/tasks')
      break
    case 'users':
      router.push('/users')
      break
    case 'files':
      router.push('/files')
      break
    case 'checklists':
      router.push('/checklists')
      break
    case 'profiles':
      router.push('/profiles')
      break
  }
}

function showNotifications() {
  const unreadNotifications = notifications.value.filter(n => !n.read)
  if (unreadNotifications.length === 0) {
    ElMessage.info('暂未读通知')
  } else {
    ElMessage.success(`有 ${unreadNotifications.length} 条未读通知`)
  }
}

async function handleLogout() {
  try {
    await authStore.logout()
    webSocketStore.disconnect()
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch (error) {
    console.error('Logout error:', error)
    ElMessage.error('退出登录失败')
  }
}

function getRoleText(role) {
  const roles = {
    admin: '管理员',
    project_owner: '项目负责人',
    executor: '执行者',
    observer: '观察者'
  }
  return roles[role] || '用户'
}

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
  height: 100vh;
  overflow: hidden;
}

.user-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 30px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.avatar {
  margin-bottom: 10px;
}

.user-details {
  text-align: center;
}

.user-name {
  margin: 0;
  color: white;
  font-size: 16px;
  font-weight: 500;
}

.user-role {
  margin: 5px 0 0;
  color: rgba(255, 255, 255, 0.8);
  font-size: 12px;
}

.sidebar {
  background: #fff;
  border-right: 1px solid #e4e7ed;
  height: 100%;
}

.sidebar-menu {
  border-right: none;
}

.sidebar-menu .el-menu-item {
  margin: 5px 0;
  border-radius: 4px;
}

.sidebar-menu .el-menu-item.is-active {
  background: #ecf5ff;
  color: #409eff;
}

.header {
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.header-left h2 {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.header-right {
  display: flex;
  gap: 15px;
  align-items: center;
}

.notification-badge {
  --el-badge-bg-color: #f56c6c;
}

.notification-badge :deep(.el-badge__content) {
  top: 0;
  right: 0;
}

.main-content {
  background: #f5f7fa;
  padding: 20px;
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

.footer {
  background: #fff;
  border-top: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 20px;
  font-size: 12px;
  color: #999;
}

.footer-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
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