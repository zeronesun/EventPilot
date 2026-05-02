/**
 * Authentication Store
 * Handles user authentication, token management, and user state
 */

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { User, LoginRequest, LoginResponse } from '@/api/client';
import { authApi, usersApi, apiClient, ApiErrorHandler } from '@/api/client';

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

      // Store user (directly from login response)
      currentUser.value = response.data.user;
      localStorage.setItem('eventpilot_user', JSON.stringify(response.data.user));
      error.value = null;

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
      const user = await usersApi.me();
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

// Error message helper
function getErrorMessage(error: unknown): string {
  if (error instanceof ApiErrorHandler) {
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
