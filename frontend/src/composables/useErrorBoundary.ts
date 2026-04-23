import { ref, onMounted, onUnmounted } from 'vue'
import type { ComponentInternalInstance, ErrorCapturedHook } from 'vue'

export interface ErrorBoundaryOptions {
  onError?: (error: Error, errorInfo: any) => void
}

export function useErrorBoundary(options: ErrorBoundaryOptions = {}) {
  const hasError = ref(false)
  const errorMessage = ref('')
  const errorDetails = ref('')

  const handleError: ErrorCapturedHook = (err, instance, info) => {
    hasError.value = true
    errorMessage.value = err.message || '未知错误'
    errorDetails.value = err.stack || (info ? `in ${info}` : '')

    console.error('[useErrorBoundary]', err, info)

    if (options.onError) {
      options.onError(err, { instance, info })
    }

    // 阻止错误继续向上传播
    return false
  }

  onMounted(() => {
    const instance = getCurrentInstance()
    if (instance) {
      instance.appContext.config.errorHandler = handleError
    }
  })

  onUnmounted(() => {
    const instance = getCurrentInstance()
    if (instance) {
      instance.appContext.config.errorHandler = null
    }
  })

  function reset() {
    hasError.value = false
    errorMessage.value = ''
    errorDetails.value = ''
  }

  return {
    hasError,
    errorMessage,
    errorDetails,
    handleError,
    reset,
  }
}

import { getCurrentInstance } from 'vue'
