<template>
  <div class="notifications-page">
    <div class="page-header">
      <h1>通知中心</h1>
      <div class="header-actions">
        <el-button
          v-if="notificationsStore.unreadCount > 0"
          type="primary"
          plain
          @click="handleMarkAllRead"
        >
          全部标记已读
        </el-button>
        <el-dropdown @command="handleFilterCommand">
          <el-button>
            {{ currentFilterText }}
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="all">全部</el-dropdown-item>
              <el-dropdown-item command="unread">未读</el-dropdown-item>
              <el-dropdown-item command="read">已读</el-dropdown-item>
              <el-dropdown-item command="info">信息</el-dropdown-item>
              <el-dropdown-item command="success">成功</el-dropdown-item>
              <el-dropdown-item command="warning">警告</el-dropdown-item>
              <el-dropdown-item command="error">错误</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <el-card class="stats-card" v-if="stats">
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-value">{{ stats.total }}</div>
            <div class="stat-label">总通知数</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item warning">
            <div class="stat-value">{{ stats.unread }}</div>
            <div class="stat-label">未读</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item success">
            <div class="stat-value">{{ stats.read }}</div>
            <div class="stat-label">已读</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-value">类型数</div>
            <div class="stat-label">{{ stats.by_type?.length || 0 }}</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <el-card class="notifications-card">
      <el-empty
        v-if="!notificationsStore.loading && notificationsStore.notifications.length === 0"
        description="暂无通知"
      />

      <div v-else>
        <div
          v-for="notification in notificationsStore.notifications"
          :key="notification.id"
          class="notification-item"
          :class="{
            unread: !notification.read,
            [`type-${notification.type}`]: true
          }"
        >
          <div class="notification-icon" :class="notification.type">
            <el-icon v-if="notification.type === 'success'" :size="24">
              <CircleCheck />
            </el-icon>
            <el-icon v-else-if="notification.type === 'error'" :size="24">
              <CircleClose />
            </el-icon>
            <el-icon v-else-if="notification.type === 'warning'" :size="24">
              <Warning />
            </el-icon>
            <el-icon v-else :size="24">
              <InfoFilled />
            </el-icon>
          </div>

          <div class="notification-body">
            <div class="notification-header-row">
              <h3 class="notification-title">{{ notification.title }}</h3>
              <span class="notification-time">{{ notification.relative_time }}</span>
            </div>

            <div class="notification-message">
              {{ notification.message }}
            </div>

            <div v-if="notification.source" class="notification-meta">
              <el-tag size="small" type="info">{{ notification.source }}</el-tag>
              <span v-if="notification.related_object_type" class="related-info">
                {{ notification.related_object_type }}: {{ notification.related_object_id }}
              </span>
            </div>
          </div>

          <div class="notification-actions">
            <el-button
              v-if="!notification.read"
              type="primary"
              size="small"
              link
              @click="handleMarkRead(notification.id)"
            >
              标记已读
            </el-button>
            <el-dropdown @command="(cmd) => handleCommand(cmd, notification.id)">
              <el-button circle size="small">
                <el-icon>
                  <MoreFilled />
                </el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item v-if="!notification.read" command="mark-read">
                    标记已读
                  </el-dropdown-item>
                  <el-dropdown-item divided command="delete">
                    删除通知
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>

        <el-pagination
          v-if="totalNotifications > pageSize"
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="totalNotifications"
          layout="prev, pager, next"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useNotificationsStore } from '@/stores'
import {
  ArrowDown,
  CircleCheck,
  CircleClose,
  Warning,
  InfoFilled,
  MoreFilled
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const notificationsStore = useNotificationsStore()

const currentFilter = ref('all')
const currentPage = ref(1)
const pageSize = ref(20)
const stats = ref(null)

const currentFilterText = computed(() => {
  const texts = {
    all: '全部',
    unread: '未读',
    read: '已读',
    info: '信息',
    success: '成功',
    warning: '警告',
    error: '错误'
  }
  return texts[currentFilter.value] || '全部'
})

const totalNotifications = computed(() => notificationsStore.notifications.length)

onMounted(async () => {
  await refreshData()
})

async function refreshData() {
  try {
    await Promise.all([
      fetchNotifications(),
      fetchStats()
    ])
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载数据失败')
  }
}

async function fetchNotifications() {
  try {
    const params: any = {
      page: currentPage.value,
      page_size: pageSize.value
    }

    if (currentFilter.value === 'unread') {
      params.read = 'false'
    } else if (currentFilter.value === 'read') {
      params.read = 'true'
    } else if (['info', 'success', 'warning', 'error'].includes(currentFilter.value)) {
      params.type = currentFilter.value
    }

    await notificationsStore.fetchNotifications(params)
  } catch (error) {
    console.error('获取通知失败:', error)
    throw error
  }
}

async function fetchStats() {
  try {
    const response = await notificationsStore.statistics()
    stats.value = response
  } catch (error) {
    console.error('获取统计信息失败:', error)
  }
}

async function handleMarkAllRead() {
  try {
    await notificationsStore.bulkMarkAsRead()
    ElMessage.success('已全部标记为已读')
    await refreshData()
  } catch (error) {
    console.error('标记已读失败:', error)
    ElMessage.error('操作失败')
  }
}

async function handleMarkRead(notificationId) {
  try {
    await notificationsStore.markAsRead(notificationId)
    ElMessage.success('已标记为已读')
    await refreshData()
  } catch (error) {
    console.error('标记已读失败:', error)
    ElMessage.error('操作失败')
  }
}

async function handleDelete(notificationId) {
  try {
    await notificationsStore.deleteNotification(notificationId)
    ElMessage.success('已删除')
    await refreshData()
  } catch (error) {
    console.error('删除失败:', error)
    ElMessage.error('删除失败')
  }
}

function handleCommand(command, notificationId) {
  switch (command) {
    case 'mark-read':
      handleMarkRead(notificationId)
      break
    case 'delete':
      handleDelete(notificationId)
      break
  }
}

function handleFilterCommand(filter) {
  currentFilter.value = filter
  currentPage.value = 1
  fetchNotifications()
}

function handlePageChange(page) {
  currentPage.value = page
  fetchNotifications()
}

onUnmounted(() => {
  notificationsStore.stopPolling()
})
</script>

<style scoped>
.notifications-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.stats-card {
  margin-bottom: 20px;
}

.stat-item {
  text-align: center;
  padding: 20px;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: var(--el-text-color-primary);
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.stat-item.warning .stat-value {
  color: var(--el-color-warning);
}

.stat-item.success .stat-value {
  color: var(--el-color-success);
}

.notifications-card {
  min-height: 400px;
}

.notification-item {
  display: flex;
  gap: 15px;
  padding: 20px;
  background: white;
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  margin-bottom: 12px;
  transition: all 0.3s;
}

.notification-item:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.notification-item.unread {
  border-left: 4px solid var(--el-color-primary);
  background: #ecf5ff;
}

.notification-item.unread .notification-title {
  font-weight: 600;
}

.notification-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  flex-shrink: 0;
}

.notification-icon.info {
  background: #ecf5ff;
  color: #409eff;
}

.notification-icon.success {
  background: #f0f9ff;
  color: #67c23a;
}

.notification-icon.warning {
  background: #fef9e7;
  color: #e6a23c;
}

.notification-icon.error {
  background: #fef0f0;
  color: #f56c6c;
}

.notification-body {
  flex: 1;
  min-width: 0;
}

.notification-header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.notification-title {
  margin: 0;
  font-size: 16px;
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notification-time {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  flex-shrink: 0;
}

.notification-message {
  font-size: 14px;
  color: var(--el-text-color-regular);
  line-height: 1.6;
  margin-bottom: 10px;
}

.notification-meta {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.related-info {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.notification-actions {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}

.el-pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>
