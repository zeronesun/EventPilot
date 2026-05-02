import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { notificationsApi, type Notification, type NotificationListResponse } from '@/api/client'

interface NotificationsState {
  notifications: Notification[]
  loading: boolean
  error: string | null
  unreadCount: number
  lastFetchTime: number | null
}

export const useNotificationsStore = defineStore('notifications', () => {
  // 状态
  const notifications = ref<Notification[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const unreadCount = ref(0)
  const lastFetchTime = ref<number | null>(null)
  const polling = ref<number | null>(null)

  // 计算属性
  const unreadNotifications = computed(() =>
    notifications.value.filter(n => !n.read)
  )

  // Actions
  async function fetchNotifications(params?: {
    type?: string
    read?: string
    page?: number
    page_size?: number
  }) {
    loading.value = true
    error.value = null

    try {
      const response = await notificationsApi.list(params)
      notifications.value = response.notifications || []
      lastFetchTime.value = Date.now()
      return response
    } catch (err: any) {
      error.value = err.message || '获取通知失败'
      console.error('Fetch notifications error:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchUnreadCount() {
    try {
      const response = await notificationsApi.getUnreadCount()
      unreadCount.value = response.unread_count
      return response.unread_count
    } catch (err: any) {
      console.error('Fetch unread count error:', err)
    }
  }

  async function markAsRead(notificationId: string) {
    try {
      await notificationsApi.markRead(notificationId)

      // 更新本地状态
      const index = notifications.value.findIndex(n => n.id === notificationId)
      if (index !== -1) {
        notifications.value[index].read = true
        notifications.value[index].read_at = new Date().toISOString()
      }

      // 更新未读数
      if (unreadCount.value > 0) {
        unreadCount.value--
      }

      return true
    } catch (err: any) {
      console.error('Mark as read error:', err)
      throw err
    }
  }

  async function bulkMarkAsRead(notificationIds?: string[]) {
    try {
      await notificationsApi.bulkMarkRead(notificationIds)

      // 更新本地状态
      if (notificationIds && notificationIds.length > 0) {
        notificationIds.forEach(id => {
          const index = notifications.value.findIndex(n => n.id === id)
          if (index !== -1) {
            notifications.value[index].read = true
            notifications.value[index].read_at = new Date().toISOString()
          }
        })
      } else {
        // 全部标记已读
        notifications.value.forEach(n => {
          n.read = true
          n.read_at = new Date().toISOString()
        })
      }

      // 更新未读数
      unreadCount.value = 0

      return true
    } catch (err: any) {
      console.error('Bulk mark as read error:', err)
      throw err
    }
  }

  async function deleteNotification(notificationId: string) {
    try {
      await notificationsApi.delete(notificationId)

      // 更新本地状态
      const index = notifications.value.findIndex(n => n.id === notificationId)
      if (index !== -1) {
        if (!notifications.value[index].read && unreadCount.value > 0) {
          unreadCount.value--
        }
        notifications.value.splice(index, 1)
      }

      return true
    } catch (err: any) {
      console.error('Delete notification error:', err)
      throw err
    }
  }

  // 轮询
  function startPolling(interval = 30000) {
    if (polling.value) {
      clearInterval(polling.value)
    }

    // 立即获取一次
    fetchUnreadCount()

    polling.value = window.setInterval(() => {
      fetchUnreadCount()
    }, interval)
  }

  function stopPolling() {
    if (polling.value) {
      clearInterval(polling.value)
      polling.value = null
    }
  }

  // 添加新通知（外部调用，如WebSocket收到）
  function addNotification(notification: Notification) {
    notifications.value.unshift(notification)
    if (!notification.read) {
      unreadCount.value++
    }
  }

  // 刷新
  async function refresh() {
    await fetchNotifications()
    await fetchUnreadCount()
  }

  return {
    // 状态
    notifications,
    loading,
    error,
    unreadCount,
    lastFetchTime,

    // 计算属性
    unreadNotifications,

    // Actions
    fetchNotifications,
    fetchUnreadCount,
    markAsRead,
    bulkMarkAsRead,
    deleteNotification,
    startPolling,
    stopPolling,
    addNotification,
    refresh
  }
})
