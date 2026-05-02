<template>
  <el-dropdown
    v-model="dropdownVisible"
    trigger="click"
    @visible-change="handleDropdownVisible"
  >
    <div class="notification-bell">
      <el-badge :value="notificationsStore.unreadCount" :hidden="notificationsStore.unreadCount === 0">
        <el-icon :size="20">
          <Bell />
        </el-icon>
      </el-badge>
    </div>

    <template #dropdown>
      <div class="notification-dropdown">
        <div class="notification-header">
          <span class="title">通知</span>
          <div class="header-actions">
            <el-button
              link
              type="primary"
              size="small"
              @click="handleMarkAllRead"
              :disabled="notificationsStore.unreadCount === 0"
            >
              全部已读
            </el-button>
          </div>
        </div>

        <div
          v-loading="notificationsStore.loading"
          element-loading-text="加载中..."
          element-loading-spinner="el-icon-loading"
        >
          <div
            v-if="notificationsStore.notifications.length === 0"
            class="empty-notifications"
          >
            <el-icon size="48" color="#e5e7eb">
              <Bell />
            </el-icon>
            <p>暂无通知</p>
          </div>

          <div v-else class="notification-list">
            <div
              v-for="notification in notificationsStore.notifications.slice(0, 10)"
              :key="notification.id"
              class="notification-item"
              :class="{ unread: !notification.read }"
            >
              <div class="notification-type" :class="notification.type">
                <el-icon v-if="notification.type === 'success'"><CircleCheck /></el-icon>
                <el-icon v-else-if="notification.type === 'error'"><CircleClose /></el-icon>
                <el-icon v-else-if="notification.type === 'warning'"><Warning /></el-icon>
                <el-icon v-else><InfoFilled /></el-icon>
              </div>

              <div class="notification-content">
                <div class="notification-title">{{ notification.title }}</div>
                <div class="notification-message">{{ notification.message }}</div>
                <div class="notification-meta">
                  <span class="notification-time">{{ notification.relative_time }}</span>
                  <span v-if="notification.source" class="notification-source">
                    {{ notification.source }}
                  </span>
                </div>
              </div>

              <div class="notification-actions">
                <el-dropdown
                  trigger="click"
                  @command="(cmd) => handleNotificationCommand(cmd, notification.id)"
                >
                  <el-icon class="more-icon">
                    <MoreFilled />
                  </el-icon>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item
                        v-if="!notification.read"
                        command="mark-read"
                      >
                        标记已读
                      </el-dropdown-item>
                      <el-dropdown-item command="delete" style="color: #f56c6c">
                        删除
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>
          </div>
        </div>

        <div v-if="notificationsStore.notifications.length > 0" class="notification-footer">
          <el-button link @click="handleViewAll">查看全部</el-button>
        </div>
      </div>
    </template>
  </el-dropdown>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useNotificationsStore } from '@/stores'
import {
  Bell,
  CircleCheck,
  CircleClose,
  Warning,
  InfoFilled,
  MoreFilled
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const notificationsStore = useNotificationsStore()
const dropdownVisible = ref(false)

onMounted(async () => {
  // 启动轮询，每30秒获取一次未读数量
  notificationsStore.startPolling(30000)
})

onUnmounted(() => {
  notificationsStore.stopPolling()
})

async function handleDropdownVisible(visible) {
  if (visible) {
    // 打开下拉时加载通知
    await notificationsStore.fetchNotifications()
  }
}

async function handleMarkAllRead() {
  try {
    await notificationsStore.bulkMarkAsRead()
    ElMessage.success('已全部标记为已读')
  } catch (error) {
    console.error('标记已读失败:', error)
    ElMessage.error('操作失败')
  }
}

async function handleNotificationCommand(command, notificationId) {
  switch (command) {
    case 'mark-read':
      await handleMarkRead(notificationId)
      break
    case 'delete':
      await handleDelete(notificationId)
      break
  }
}

async function handleMarkRead(notificationId) {
  try {
    await notificationsStore.markAsRead(notificationId)
    ElMessage.success('已标记为已读')
  } catch (error) {
    console.error('标记已读失败:', error)
    ElMessage.error('操作失败')
  }
}

async function handleDelete(notificationId) {
  try {
    await notificationsStore.deleteNotification(notificationId)
    ElMessage.success('已删除')
  } catch (error) {
    console.error('删除失败:', error)
    ElMessage.error('删除失败')
  }
}

function handleViewAll() {
  router.push('/notifications')
  dropdownVisible.value = false
}
</script>

<style scoped>
.notification-bell {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.3s;
}

.notification-bell:hover {
  background-color: var(--el-fill-color-light);
}

.notification-dropdown {
  width: 380px;
  max-height: 500px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid var(--el-border-color-light);
}

.notification-header .title {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.empty-notifications {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--el-text-color-secondary);
}

.empty-notifications p {
  margin: 15px 0 0 0;
  font-size: 14px;
}

.notification-list {
  max-height: 350px;
  overflow-y: auto;
}

.notification-item {
  display: flex;
  gap: 12px;
  padding: 15px 20px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  transition: background-color 0.2s;
  position: relative;
}

.notification-item:hover {
  background-color: var(--el-fill-color-light);
}

.notification-item.unread {
  background-color: #ecf5ff;
}

.notification-item.unread::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background-color: var(--el-color-primary);
}

.notification-type {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  flex-shrink: 0;
}

.notification-type.success {
  background-color: #f0f9ff;
  color: #67c23a;
}

.notification-type.error {
  background-color: #fef0f0;
  color: #f56c6c;
}

.notification-type.warning {
  background-color: #fef9e7;
  color: #e6a23c;
}

.notification-type.info {
  background-color: #ecf5ff;
  color: #409eff;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notification-message {
  font-size: 13px;
  color: var(--el-text-color-regular);
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.notification-meta {
  display: flex;
  gap: 8px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.notification-actions {
  display: flex;
  align-items: flex-start;
}

.more-icon {
  cursor: pointer;
  color: var(--el-text-color-secondary);
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s;
}

.more-icon:hover {
  background-color: var(--el-fill-color);
  color: var(--el-color-primary);
}

.notification-footer {
  padding: 10px 20px;
  border-top: 1px solid var(--el-border-color-light);
  text-align: center;
}

/* 滚动条样式 */
.notification-list::-webkit-scrollbar {
  width: 6px;
}

.notification-list::-webkit-scrollbar-track {
  background: transparent;
}

.notification-list::-webkit-scrollbar-thumb {
  background: var(--el-border-color-darker);
  border-radius: 3px;
}

.notification-list::-webkit-scrollbar-thumb:hover {
  background: var(--el-border-color-dark);
}
</style>
