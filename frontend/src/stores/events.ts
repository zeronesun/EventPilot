/**
 * Events Store
 * Handles event management and statistics
 */

import { defineStore } from 'pinia';
import { ref } from 'vue';
import { apiClient, ApiErrorHandler } from '@/api/client';

export interface Event {
  id: number | string;
  name: string;
  description?: string;
  type: string;
  status: string;
  start_date: string;
  end_date?: string;
  location?: string;
  budget?: number;
  actual_cost?: number | null;
  owner_name?: string;
  created_at?: string;
  updated_at?: string;
  [key: string]: any;
}

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
      events.value = (response as any).results || [];

      if ('count' in response) {
        pagination.value = {
          current: 1,
          total: (response as any).count || 0,
          lastPage: 1,
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

  async function createEvent(data: any): Promise<any> {
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

  async function updateEvent(id: string, data: any): Promise<any> {
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
    events,
    currentEvent,
    isLoading,
    error,
    pagination,
    fetchEvents,
    fetchEvent,
    createEvent,
    updateEvent,
    deleteEvent,
    fetchEventStatistics,
  };
});

function getErrorMessage(error: unknown): string {
  if (error instanceof ApiErrorHandler) {
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
