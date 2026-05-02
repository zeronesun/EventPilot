/**
 * Tasks Store
 * Handles task management, kanban features, and optimistic updates
 */

import { defineStore } from 'pinia';
import { ref } from 'vue';
import { apiClient, type ApiError } from '@/api/client';

export const useTasksStore = defineStore('tasks', () => {
  const tasks = ref<any[]>([]);
  const currentTask = ref<any | null>(null);
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  const isDragging = ref(false);
  const dragError = ref<string | null>(null);

  async function fetchTasks(params?: Record<string, string>): Promise<void> {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await apiClient.get(`/tasks/${params ? `?${new URLSearchParams(params)}` : ''}`)
      // 处理不同的 API 响应格式
      if (Array.isArray(response)) {
        tasks.value = response
      } else if (response && typeof response === 'object') {
        // Tasks API 返回: {data: {count, results, ...}}
        if (response.data && Array.isArray(response.data.results)) {
          tasks.value = response.data.results
        } else if (Array.isArray(response.results)) {
          // Events API 返回: {count, results, ...}
          tasks.value = response.results
        } else {
          tasks.value = []
        }
      } else {
        tasks.value = []
      }
    } catch (err) {
      error.value = getErrorMessage(err);
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  async function fetchTask(id: string): Promise<void> {
    isLoading.value = true;
    error.value = null;

    try {
      const task = await apiClient.get(`/tasks/${id}/`);
      currentTask.value = task;
    } catch (err) {
      error.value = getErrorMessage(err);
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  async function createTask(data: any): Promise<any> {
    isLoading.value = true;
    error.value = null;

    try {
      const task = await apiClient.post('/tasks/', data);
      tasks.value.unshift(task);
      return task;
    } catch (err) {
      error.value = getErrorMessage(err);
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  async function updateTask(id: string, data: any): Promise<any> {
    isLoading.value = true;
    error.value = null;

    try {
      const task = await apiClient.put(`/tasks/${id}/`, data);
      const index = tasks.value.findIndex(t => t.id === id);
      if (index !== -1) {
        tasks.value[index] = task;
      }
      if (currentTask.value?.id === id) {
        currentTask.value = task;
      }
      return task;
    } catch (err) {
      error.value = getErrorMessage(err);
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  async function completeTask(id: string): Promise<void> {
    try {
      await apiClient.post(`/tasks/${id}/complete/`)
      const task = tasks.value.find(t => t.id === id);
      if (task) {
        task.status = 'completed';
        task.progress = 100;
      }
    } catch (err) {
      error.value = getErrorMessage(err);
      throw err;
    }
  }

  async function deleteTask(id: string): Promise<void> {
    isLoading.value = true;
    error.value = null;
    try {
      await apiClient.delete(`/tasks/${id}/`);
      tasks.value = tasks.value.filter(t => t.id !== id);
      if (currentTask.value?.id === id) {
        currentTask.value = null;
      }
    } catch (err) {
      error.value = getErrorMessage(err);
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  async function fetchKanbanData(eventId: string): Promise<any> {
    try {
      return await apiClient.get(`/kanban_data?event=${eventId}`);
    } catch (err) {
      error.value = getErrorMessage(err);
      throw err;
    }
  }

  function optimisticUpdateTaskStatus(taskId: string, newStatus: string): void {
    const task = tasks.value.find(t => t.id === taskId);
    if (task) {
      task.status = newStatus;
    }
  }

  async function bulkUpdateStatus(updates: Array<{id: string; status: string}>): Promise<void> {
    dragError.value = null;
    try {
      const response = await apiClient.post('/tasks/bulk_update_status/', updates);
      if (response.data?.failed?.length > 0) {
        console.error('Some tasks failed to update:', response.data.failed);
        dragError.value = `${response.data.failed.length} 个任务更新失败`;
      }
    } catch (err) {
      dragError.value = getErrorMessage(err);
      throw err;
    }
  }

  function resetDragState(): void {
    isDragging.value = false;
    dragError.value = null;
  }

  return {
    tasks,
    currentTask,
    isLoading,
    error,
    isDragging,
    dragError,
    fetchTasks,
    fetchTask,
    createTask,
    updateTask,
    completeTask,
    deleteTask,
    fetchKanbanData,
    optimisticUpdateTaskStatus,
    bulkUpdateStatus,
    resetDragState,
  };
});

// Error message helper
function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    const body = error.body;
    if (body && typeof body === 'object') {
      if (body instanceof Array && body.length > 0) {
        const firstError = body[0];
        if (firstError && typeof firstError === 'object' && 'message' in firstError) {
          return String(firstError.message);
        }
      }
      if ('message' in body) {
        return String(body.message);
      }
      if ('detail' in body) {
        return String(body.detail);
      }
    }
    
    // Map HTTP status codes to user-friendly messages
    switch (error.status) {
      case 401:
        return '请登录以继续操作';
      case 403:
        return '您没有权限执行此操作';
      case 404:
        return '请求的资源不存在';
      case 409:
        return '此操作与其他数据冲突';
      case 422:
        return '请检查输入数据';
      case 429:
        return '请求过于频繁，请稍后再试';
      default:
        return '服务器错误，请稍后重试';
    }
  }
  
  if (error instanceof Error) {
    return error.message;
  }
  
  return '发生未知错误';
}
