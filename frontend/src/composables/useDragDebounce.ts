import { ref } from 'vue'
import { debounce } from 'lodash-es'

/**
 * 拖拽操作防抖 composable
 * 防止快速连续拖拽导致的性能问题和状态冲突
 */

export interface PendingUpdate {
  taskId: string
  status: string
  timestamp: number
}

export function useDragDebounce() {
  const pendingUpdates = new Map<string, PendingUpdate>()
  const isBatching = ref(false)
  let processingTimeout: ReturnType<typeof setTimeout> | null = null

  // 添加待处理更新
  function addPendingUpdate(taskId: string, status: string) {
    pendingUpdates.set(taskId, {
      taskId,
      status,
      timestamp: Date.now(),
    })

    // 开始防抖处理
    startDebounceProcess()
  }

  // 获取所有待处理更新
  function getAllPendingUpdates(): PendingUpdate[] {
    return Array.from(pendingUpdates.values())
  }

  // 清空待处理更新
  function clearPendingUpdates() {
    pendingUpdates.clear()
  }

  // 开始防抖处理（延迟执行）
  function startDebounceProcess() {
    if (processingTimeout) {
      clearTimeout(processingTimeout)
    }

    processingTimeout = setTimeout(() => {
      processBatchUpdates()
    }, 300) // 300ms 防抖延迟
  }

  // 批量处理更新
  async function processBatchUpdates(
    batchUpdateCallback: (updates: PendingUpdate[]) => Promise<void>
  ): Promise<void> {
    if (pendingUpdates.size === 0) {
      return
    }

    isBatching.value = true

    try {
      const updates = getAllPendingUpdates()
      await batchUpdateCallback(updates)
      clearPendingUpdates()
    } finally {
      isBatching.value = false
    }
  }

  // 立即处理（不等待防抖）
  async function flushPendingUpdates(
    batchUpdateCallback: (updates: PendingUpdate[]) => Promise<void>
  ): Promise<void> {
    if (processingTimeout) {
      clearTimeout(processingTimeout)
      processingTimeout = null
    }

    await processBatchUpdates(batchUpdateCallback)
  }

  // 清理
  function cleanup() {
    if (processingTimeout) {
      clearTimeout(processingTimeout)
      processingTimeout = null
    }
    clearPendingUpdates()
  }

  return {
    pendingUpdates,
    isBatching,
    addPendingUpdate,
    getAllPendingUpdates,
    clearPendingUpdates,
    startDebounceProcess,
    processBatchUpdates,
    flushPendingUpdates,
    cleanup,
  }
}
