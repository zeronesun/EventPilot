/**
 * Toast通知系统
 * 提供统一的轻量级通知组件和API
 */
import { ElMessage, ElNotification } from 'element-plus'

export interface ToastConfig {
  message: string
  type?: 'success' | 'warning' | 'info' | 'error'
  duration?: number
  showClose?: boolean
  center?: boolean
  dangerouslyUseHTMLString?: boolean
}

export interface NotificationConfig {
  title?: string
  message: string
  type?: 'success' | 'warning' | 'info' | 'error'
  duration?: number
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left'
  showClose?: boolean
  dangerouslyUseHTMLString?: boolean
}

/**
 * Toast通知类
 */
export class Toast {
  /**
   * 成功通知
   */
  static success(message: string, duration = 3000): void {
    ElMessage({
      message,
      type: 'success',
      duration,
      showClose: true,
    })
  }

  /**
   * 错误通知
   */
  static error(message: string, duration = 4000): void {
    ElMessage.error({
      message,
      type: 'error',
      duration,
      showClose: true,
    })
  }

  /**
   * 警告通知
   */
  static warning(message: string, duration = 3500): void {
    ElMessage.warning({
      message,
      type: 'warning',
      duration,
      showClose: true,
    })
  }

  /**
   * 信息通知
   */
  static info(message: string, duration = 3000): void {
    ElMessage.info({
      message,
      type: 'info',
      duration,
      showClose: true,
    })
  }

  /**
   * 自定义通知
   */
  static show(config: ToastConfig): void {
    ElMessage({
      message: config.message,
      type: config.type || 'info',
      duration: config.duration || 3000,
      showClose: config.showClose ?? true,
      center: config.center,
      dangerouslyUseHTMLString: config.dangerouslyUseHTMLString,
    })
  }

  /**
   * 关闭所有通知
   */
  static closeAll(): void {
    ElMessage.closeAll()
  }
}

/**
 * 通知类 - 用于更重要、需要用户注意的消息
 */
export class Notification {
  /**
   * 成功通知
   */
  static success(title: string, message: string, duration = 4500): void {
    ElNotification({
      title,
      message,
      type: 'success',
      duration,
      showClose: true,
      position: 'top-right',
    })
  }

  /**
   * 错误通知
   */
  static error(title: string, message: string, duration = 5000): void {
    ElNotification.error({
      title,
      message,
      type: 'error',
      duration,
      showClose: true,
      position: 'top-right',
    })
  }

  /**
   * 警告通知
   */
  static warning(title: string, message: string, duration = 4500): void {
    ElNotification.warning({
      title,
      message,
      type: 'warning',
      duration,
      showClose: true,
      position: 'top-right',
    })
  }

  /**
   * 信息通知
   */
  static info(title: string, message: string, duration = 4000): void {
    ElNotification.info({
      title,
      message,
      type: 'info',
      duration,
      showClose: true,
      position: 'top-right',
    })
  }

  /**
   * 自定义通知
   */
  static show(config: NotificationConfig): void {
    ElNotification({
      title: config.title || 'Notification',
      message: config.message,
      type: config.type || 'info',
      duration: config.duration || 4500,
      position: config.position || 'top-right',
      showClose: config.showClose ?? true,
      dangerouslyUseHTMLString: config.dangerouslyUseHTMLString,
    })
  }

  /**
   * 关闭所有通知
   */
  static closeAll(): void {
    ElNotification.closeAll()
  }
}

/**
 * Toast插件 - 用于Vue应用
 */
export const ToastPlugin = {
  install(app: any) {
    // 添加全局属性
    app.config.globalProperties.$toast = Toast
    app.config.globalProperties.$notification = Notification

    // 提供注入
    app.provide('toast', Toast)
    app.provide('notification', Notification)
  },
}

/**
 * 使用Composable
 */
export function useToast() {
  return {
    toast: Toast,
    notification: Notification,
  }
}

/**
 * 常用通知消息
 */
export const CommonMessages = {
  // 成功消息
  OPERATION_SUCCESS: '操作成功',
  SAVE_SUCCESS: '保存成功',
  DELETE_SUCCESS: '删除成功',
  UPDATE_SUCCESS: '更新成功',
  LOGIN_SUCCESS: '登录成功',
  LOGOUT_SUCCESS: '登出成功',
  COPY_SUCCESS: '复制成功',

  // 错误消息
  OPERATION_FAILED: '操作失败',
  SAVE_FAILED: '保存失败，请重试',
  DELETE_FAILED: '删除失败，请重试',
  UPDATE_FAILED: '更新失败，请重试',
  NETWORK_ERROR: '网络连接失败，请检查网络设置',
  SERVER_ERROR: '服务器错误，请稍后重试',

  // 验证消息
  REQUIRED_FIELD: '此字段为必填项',
  INVALID_EMAIL: '邮箱格式不正确',
  INVALID_PHONE: '手机号格式不正确',
  PASSWORD_TOO_SHORT: '密码长度至少为6位',
  PASSWORD_MISMATCH: '两次密码不一致',

  // 权限消息
  NO_PERMISSION: '您没有权限执行此操作',
  LOGIN_REQUIRED: '请先登录',
  SESSION_EXPIRED: '会话已过期，请重新登录',
}

/**
 * 快捷方法
 */
export function toastSuccess(message?: string) {
  return Toast.success(message || CommonMessages.OPERATION_SUCCESS)
}

export function toastError(message?: string) {
  return Toast.error(message || CommonMessages.OPERATION_FAILED)
}

export function toastWarning(message: string) {
  return Toast.warning(message)
}

export function toastInfo(message: string) {
  return Toast.info(message)
}

/**
 * 通知管理器 - 用于管理多个通知的队列和去重
 */
class NotificationManager {
  private queue: Map<string, number> = new Map()
  private readonly DEBOUNCE_TIME = 3000 // 防抖时间

  /**
   * 显示通知（带防抖）
   */
  show(
    key: string,
    config: ToastConfig | NotificationConfig,
    provider: 'toast' | 'notification' = 'toast'
  ): void {
    const now = Date.now()
    const lastTime = this.queue.get(key)

    // 如果在防抖时间内已显示过相同通知，则跳过
    if (lastTime && now - lastTime < this.DEBOUNCE_TIME) {
      return
    }

    if (provider === 'toast') {
      Toast.show(config as ToastConfig)
    } else {
      Notification.show(config as NotificationConfig)
    }

    this.queue.set(key, now)

    // 清理过期的key
    setTimeout(() => {
      this.queue.delete(key)
    }, this.DEBOUNCE_TIME)
  }

  /**
   * 清空队列
   */
  clear(): void {
    this.queue.clear()
  }
}

export const notificationManager = new NotificationManager()

export default Toast
