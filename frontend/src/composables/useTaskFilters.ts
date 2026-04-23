import { ref, computed } from 'vue'
import type { Task } from '../api/tasks'

export function useTaskFilters(initialTasks: Task[] = []) {
  const searchQuery = ref('')
  const filterStatus = ref('')

  const filteredTasks = computed(() => {
    let tasks = initialTasks

    // 搜索过滤
    if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase()
      tasks = tasks.filter(task =>
        task.title.toLowerCase().includes(query) ||
        task.description?.toLowerCase().includes(query)
      )
    }

    // 状态过滤
    if (filterStatus.value) {
      tasks = tasks.filter(task => task.status === filterStatus.value)
    }

    return tasks
  })

  function resetFilters() {
    searchQuery.value = ''
    filterStatus.value = ''
  }

  function handleSearch() {
    // 可以在这里添加搜索防抖逻辑
  }

  return {
    searchQuery,
    filterStatus,
    filteredTasks,
    resetFilters,
    handleSearch,
  }
}
