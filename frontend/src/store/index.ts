/**
 * EventPilot Pinia Stores
 * State management following fullstack-dev best practices
 */

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { User, LoginRequest, LoginResponse } from '@/api/client';
import { authApi, apiClient, type ApiError } from '@/api/client';

// Auth Store
export const useAuthStore = defineStore('auth', () => {
  // State
  const currentUser = ref<User | null>(null);
  const token = ref<string | null>(null);
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  // Computed
  const isAuthenticated = computed(() => !!currentUser.value && !!token.value);
  const userId = computed(() => currentUser.value?.id ?? null);
  const username = computed(() => currentUser.value?.username ?? '');
  const userRole = computed(() => currentUser.value?.role ?? 'executor');

  // Initialize from localStorage
  function initialize() {
    const savedToken = localStorage.getItem('eventpilot_token');
    const savedUser = localStorage.getItem('eventpilot_user');
    
    if (savedToken) {
      token.value = savedToken;
      if (savedUser) {
        try {
          currentUser.value = JSON.parse(savedUser) as User;
        } catch {
          console.error('Failed to parse saved user');
        }
      }
    }
  }

  // Actions
  async function login(credentials: LoginRequest): Promise<void> {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await authApi.login(credentials);
      
      // Store token
      token.value = response.data.token;
      localStorage.setItem('eventpilot_token', response.data.token);
      
      // Store user
      currentUser.value = response.data.user;
      localStorage.setItem('eventpilot_user', JSON.stringify(response.data.user));
      
    } catch (err) {
      error.value = getErrorMessage(err);
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  async function logout(): Promise<void> {
    try {
      // Optionally call logout endpoint if exists
      // await authApi.logout();
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      // Clear all auth state
      token.value = null;
      currentUser.value = null;
      error.value = null;
      
      // Clear localStorage
      localStorage.removeItem('eventpilot_token');
      localStorage.removeItem('eventpilot_user');
      
      // Clear API client token
      apiClient.setAuthToken('');
    }
  }

  async function fetchCurrentUser(): Promise<void> {
    if (!token.value) return;

    isLoading.value = true;
    try {
      const user = await authApi.me();
      currentUser.value = user;
      localStorage.setItem('eventpilot_user', JSON.stringify(user));
    } catch (err) {
      console.error('Failed to fetch current user:', err);
      // Token might be invalid, clear auth state
      await logout();
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  async function verifyToken(): Promise<boolean> {
    if (!token.value) return false;

    try {
      const response = await authApi.verify();
      return response.data.valid;
    } catch (err) {
      console.error('Token verification failed:', err);
      return false;
    }
  }

  async function refreshToken(): Promise<void> {
    if (!token.value) {
      throw new Error('No token to refresh');
    }

    try {
      const response = await authApi.refresh();
      token.value = response.data.token;
      localStorage.setItem('eventpilot_token', response.data.token);
      apiClient.setAuthToken(response.data.token);
    } catch (err) {
      console.error('Token refresh failed:', err);
      await logout();
      throw err;
    }
  }

  return {
    // State
    currentUser,
    token,
    isLoading,
    error,
    
    // Computed
    isAuthenticated,
    userId,
    username,
    userRole,
    
    // Actions
    initialize,
    login,
    logout,
    fetchCurrentUser,
    verifyToken,
    refreshToken,
  };
});

// Events Store
export const useEventsStore = defineStore('events', () => {
  const events = ref<any[]>([]);
  const currentEvent = ref<any | null>(null);
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  const pagination = ref({
    current: 1,
    total: 0,
    lastPage: 0,
  });

  async function fetchEvents(params?: Record<string, string>): Promise<void> {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await apiClient.get(`/events/${params ? `?${new URLSearchParams(params)}` : ''}`);
      events.value = response.data || [];
      
      if (response.meta) {
        pagination.value = {
          current: response.meta.current_page || 1,
          total: response.meta.total || 0,
          lastPage: response.meta.last_page || 1,
        };
      }
    } catch (err) {
      error.value = getErrorMessage(err);
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  async function fetchEvent(id: string): Promise<void> {
    isLoading.value = true;
    error.value = null;

    try {
      const event = await apiClient.get(`/events/${id}/`);
      currentEvent.value = event;
    } catch (err) {
      error.value = getErrorMessage(err);
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  async function createEvent(data: any): Promise<void> {
    isLoading.value = true;
    error.value = null;

    try {
      const event = await apiClient.post('/events/', data);
      events.value.unshift(event);
      return event;
    } catch (err) {
      error.value = getErrorMessage(err);
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  async function updateEvent(id: string, data: any): Promise<void> {
    isLoading.value = true;
    error.value = null;

    try {
      const event = await apiClient.put(`/events/${id}/`, data);
      const index = events.value.findIndex(e => e.id === id);
      if (index !== -1) {
        events.value[index] = event;
      }
      if (currentEvent.value?.id === id) {
        currentEvent.value = event;
      }
      return event;
    } catch (err) {
      error.value = getErrorMessage(err);
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  async function deleteEvent(id: string): Promise<void> {
    isLoading.value = true;
    error.value = null;

    try {
      await apiClient.delete(`/events/${id}/`);
      events.value = events.value.filter(e => e.id !== id);
      if (currentEvent.value?.id === id) {
        currentEvent.value = null;
      }
    } catch (err) {
      error.value = getErrorMessage(err);
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  async function fetchEventStatistics(id: string): Promise<any> {
    try {
      return await apiClient.get(`/events/${id}/statistics/`);
    } catch (err) {
      error.value = getErrorMessage(err);
      throw err;
    }
  }

  return {
    // State
    events,
    currentEvent,
    isLoading,
    error,
    pagination,
    
    // Actions
    fetchEvents,
    fetchEvent,
    createEvent,
    updateEvent,
    deleteEvent,
    fetchEventStatistics,
  };
});

// Tasks Store
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
      const response = await apiClient.get(`/tasks/${params ? `?${new URLSearchParams(params)}` : ''}`);
      tasks.value = response.data || [];
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
      await apiClient.patch(`/tasks/${id}/complete/`);
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