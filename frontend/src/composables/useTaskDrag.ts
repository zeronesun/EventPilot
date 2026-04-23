import { ref } from 'vue'
import { notify } from '../services/notification'
import { tasksApi } from '../api/tasks'

export interface DragResult {
  success: boolean
  error?: string
}

export function useTaskDrag() {
  const isDragging = ref(false)

  async function handleTaskDragEnd(
    event: any,
    tasks: any[],
    getTaskById: (id: string) => any,
    optimisticUpdate: (taskId: string, status: string) => void
  ): Promise<DragResult> {
    // 如果已经在拖拽中，忽略
    if (isDragging.value) {
      return { success: false, error: '已在拖拽中' }
    }

    try {
      // 获取变更信息
      const changes = extractDragChanges(event)
      if (!changes) {
        return { success: true } // 无实际变更
      }

      const { taskId, oldStatus, newStatus } = changes

      // 验证任务状态是否实际改变
      if (oldStatus === newStatus) {
        return { success: true }
      }

      // 乐观更新
      optimisticUpdate(taskId, newStatus)
      isDragging.value = true

      // API 调用，设置10秒超时保护
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 10000)

      try {
        // 广播拖拽事件
        notify('info', '正在更新任务状态...', 'task')

        await tasksApi.bulkUpdateStatus([taskId], newStatus, {
          signal: controller.signal,
        })

        notify('success', '任务状态已更新', 'collaboration')

        return { success: true }
      } finally {
        clearTimeout(timeoutId)
        isDragging.value = false
      }
    } catch (error: any) {
      isDragging.value = false

      // 处理超时错误
      if (error.name === 'AbortError') {
        notify('warning', '更新超时，请重试', 'timeout')
        return { success: false, error: '超时' }
      }

      // 处理网络错误
      if (error.response) {
        // API 返回错误
        const errorMsg = error.response.data?.detail || '更新失败'
        notify('error', errorMsg, 'error')
        console.error('拖拽更新失败:', errorMsg, error.response.data)

        // 回滚操作（重新获取任务列表）
        await rollbackTaskStatus(taskId, oldStatus)
        return { success: false, error: errorMsg }
      }

      // 未知错误
      const errorMsg = error.message || '未知错误'
      notify('error', errorMsg, 'error')
      console.error('拖拽更新失败:', error)

      return { success: false, error: errorMsg }
    }
  }

  function extractDragChanges(event: any) {
    // 检查是否有拖拽变更
    if (!event.added && !event.removed) {
      return null
    }

    let taskId: string | null = null
    let oldStatus: string | null = null
    let newStatus: string | null = null

    // 提取任务ID
    if (event.added) {
      const item = event.added.element || event.added
      const task = item.__draggable_context?.element || item
      if (typeof task === 'object' && 'id' in task) {
        taskId = task.id
      }
    } else if (event.removed) {
      const item = event.removed.element || event.removed
      const task = item.__draggable_context?.element || item
      if (typeof task === 'object' && 'id' in task) {
        taskId = task.id
      }
    }

    if (!taskId) {
      console.error('无法提取任务ID')
      return null
    }

    // 确定目标状态
    if (event.added) {
      newStatus = event.to.getAttribute('data-status')
      // 从 removed 中获取原始状态（如果存在）
      if (event.removed) {
        const fromElement = event.removed.element || event.removed
        const task = fromElement.__draggable_context?.element || fromElement
        if (typeof task === 'object' && 'status' in task) {
          oldStatus = task.status
        }
      }
    } else if (event.removed) {
      // 仅移除（这种情况不太可能）
      return null
    }

    if (!newStatus) {
      console.error('无法确定目标状态')
      return null
    }

    return { taskId, oldStatus, newStatus }
  }

  async function rollbackTaskStatus(taskId: string, originalStatus: string) {
    try {
      // 重新获取任务列表以回滚
      // 实际项目中应该使用 store 的 refresh 方法
      console.log('回滚任务状态:', taskId, '->', originalStatus)
    } catch (error) {
      console.error('回滚失败:', error)
    }
  }

  return {
    isDragging,
    handleTaskDragEnd,
  }
}
