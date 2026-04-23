/**
 * 统一错误处理 composable
 * 集成日志、通知、回滚、上报等功能
 */

import { ElNotification } from 'element-plus'

export interface ErrorContext {
  component?: string
  action?: string
  data?: Record<string, any>
}

export interface ErrorHandlerOptions {
  enableNotification?: boolean
  enableLogging?: boolean
  enableReporting?: boolean
  enableRollback?: boolean
  onRollback?: () => Promise<void>
  onErrorReport?: (error: Error, context?: ErrorContext) => Promise<void>
}

export interface HandledError {
  original: Error
  message: string
  context?: ErrorContext
  handled: boolean
  logged: boolean
  reported: boolean
}

export function useErrorHandler(options: ErrorHandlerOptions = {}) {
  const defaultOptions: ErrorHandlerOptions = {
    enableNotification: true,
    enableLogging: true,
    enableReporting: false, // 需要配置后再启用
    enableRollback: false,
    ...options,
  }

  const errorHistory: HandledError[] = []
  const MAX_HISTORY = 50

  /**
   * 处理错误的核心方法
   */
  async function handleError(
    error: Error | unknown,
    context?: ErrorContext
  ): Promise<HandledError> {
    // 标准化错误对象
    const standardError = error instanceof Error ? error : new Error(String(error))
    
    const handledError: HandledError = {
      original: standardError,
      message: standardError.message || '未知错误',
      context,
      handled: false,
      logged: false,
      reported: false,
    }

    try {
      // 1. 日志记录
      if (defaultOptions.enableLogging) {
        logError(standardError, context)
        handledError.logged = true
      }

      // 2. 用户通知
      if (defaultOptions.enableNotification) {
        showUserNotification(standardError, context)
      }

      // 3. 错误回滚
      if (defaultOptions.enableRollback && defaultOptions.onRollback) {
        await defaultOptions.onRollback()
        console.log('[ErrorHandler] Rollback executed')
      }

      // 4. 错误上报
      if (defaultOptions.enableReporting && defaultOptions.onErrorReport) {
        await defaultOptions.onErrorReport(standardError, context)
        handledError.reported = true
      }

      handledError.handled = true

      // 5. 记录历史
      addToHistory(handledError)

      return handledError

    } catch (handlingError) {
      console.error('[ErrorHandler] Failed to handle error:', handlingError)
      handledError.handled = false
      return handledError
    }
  }

  /**
   * 分类处理不同类型的错误
   */
  function categorizeError(error: Error): 'network' | 'validation' | 'auth' | 'permission' | 'server' | 'unknown' {
    const message = error.message.toLowerCase()

    if (message.includes('network') || message.includes('fetch') || message.includes('timeout')) {
      return 'network'
    }

    if (message.includes('validation') || message.includes('invalid') || message.includes('格式')) {
      return 'validation'
    }

    if (message.includes('unauthorized') || message.includes('认证') || message.includes('token')) {
      return 'auth'
    }

    if (message.includes('permission') || message.includes('权限') || message.includes('forbidden')) {
      return 'permission'
    }

    if (message.includes('server') || message.includes('500') || message.includes('internal')) {
      return 'server'
    }

    return 'unknown'
  }

  /**
   * 获取 user-friendly 错误消息
   */
  function getFriendlyMessage(error: Error, context?: ErrorContext): string {
    const category = categorizeError(error)

    const messages: Record<string, string> = {
      network: '网络连接失败，请检查您的网络设置',
      validation: '数据格式不正确，请检查输入',
      auth: '登录已过期，请重新登录',
      permission: '您没有权限执行此操作',
      server: '服务器错误，请稍后重试',
      unknown: '操作失败，请重试或联系管理员',
    }

    return messages[category]
  }

  /**
   * 记录错误日志
   */
  function logError(error: Error, context?: ErrorContext): void {
    // 确保 contexts are defined in browsers. In non-browser environments (server-side rendering),
    // these will be undefined but the error will still be logged to console.
    const isBrowser = typeof window !== 'undefined' && typeof navigator !== 'undefined'

    const logData = {
      message: error.message,
      stack: error.stack,
      context,
      timestamp: new Date().toISOString(),
      url: isBrowser ? window.location.href : 'SSR',
      userAgent: isBrowser ? navigator.userAgent : 'SSR',
    }

    console.error('[ErrorHandler]', logData)
  }

  /**
   * 显示用户通知
   */
  function showUserNotification(error: Error, context?: ErrorContext): void {
    const category = categorizeError(error)
    const friendlyMessage = getFriendlyMessage(error, context)

    // 根据类别选择通知类型
    const types: Record<string, 'error' | 'warning' | 'info'> = {
      network: 'error',
      validation: 'warning',
      auth: 'warning',
      permission: 'warning',
      server: 'error',
      unknown: 'error',
    }

    ElNotification({
      title: '操作失败',
      message: friendlyMessage,
      type: types[category],
      duration: 5000,
    })
  }

  /**
   * 添加到历史记录
   */
  function addToHistory(handledError: HandledError): void {
    errorHistory.push(handledError)

    // 限制历史记录数量
    if (errorHistory.length > MAX_HISTORY) {
      errorHistory.shift()
    }
  }

  /**
   * 获取错误历史
   */
  function getErrorHistory(): HandledError[] {
    return [...errorHistory]
  }

  /**
   * 清空错误历史
   */
  function clearHistory(): void {
    errorHistory.length = 0
  }

  /**
   * 包装异步函数，自动捕获和处理错误
   */
  function wrapAsync<T>(
    fn: (...args: any[]) => Promise<T>,
    context?: ErrorContext
  ): (...args: any[]) => Promise<T> {
    return async (...args: any[]): Promise<T> => {
      try {
        return await fn(...args)
      } catch (error) {
        await handleError(error, context)
        throw error // 重新抛出，让调用者决定是否需要处理
      }
    }
  }

  return {
    handleError,
    categorizeError,
    getFriendlyMessage,
    getErrorHistory,
    clearHistory,
    wrapAsync,
  }
}
