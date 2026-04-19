/**
 * EventPilot API Client
 * Typed fetch wrapper following fullstack-dev best practices
 */

// Types
export interface ApiError {
  status: number;
  body?: unknown;
}

export class ApiErrorHandler extends Error {
  constructor(public status: number, public body: unknown) {
    super(body && typeof body === 'object' && 'message' in body ? String(body.message) : `API error ${status}`);
    this.name = 'ApiError';
  }
}

// API configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
const API_TIMEOUT = 30000; // 30 seconds

// Type definitions for API responses
export interface ApiResponse<T> {
  data: T;
  meta?: {
    timestamp: string;
    request_id?: string;
  };
}

export interface PaginatedResponse<T> {
  data: T[];
  meta: {
    current_page: number;
    per_page: number;
    total: number;
    last_page: number;
  };
}

// User types
export interface User {
  id: string;
  username: string;
  email: string;
  phone?: string;
  department?: string;
  position?: string;
  avatar_url?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  user: User;
  token: string;
  expires_in: number;
}

// Event types
export interface Event {
  id: string;
  name: string;
  type: string;
  description?: string;
  start_date: string;
  end_date: string;
  client?: string;
  client_contact?: string;
  estimated_budget: number;
  actual_budget: number;
  budget_variance: number;
  status: 'planning' | 'executing' | 'completed' | 'reviewed' | 'cancelled';
  owner: string;
  owner_name?: string;
  tasks_count?: number;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

// Task types
export interface Task {
  id: string;
  event: string;
  title: string;
  description?: string;
  task_type: 'planning' | 'guest' | 'material' | 'venue' | 'promotion' | 'onsite' | 'review';
  assignee?: string;
  assignee_name?: string;
  status: 'pending' | 'ready' | 'in_progress' | 'completed' | 'cancelled' | 'blocked';
  progress: number;
  start_date?: string;
  due_date?: string;
  completed_at?: string;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

// Auth token management
let currentToken: string | null = null;

export function setAuthToken(token: string): void {
  currentToken = token;
  localStorage.setItem('eventpilot_token', token);
}

export function getAuthToken(): string | null {
  if (!currentToken) {
    currentToken = localStorage.getItem('eventpilot_token');
  }
  return currentToken;
}

export function clearAuthToken(): void {
  currentToken = null;
  localStorage.removeItem('eventpilot_token');
}

// Main API client function
async function api<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getAuthToken();
  const url = `${API_BASE_URL}${path}`;

  // Set up headers
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  // Set up timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);

  try {
    const response = await fetch(url, {
      ...options,
      headers,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const contentType = response.headers.get('content-type');
      let body: unknown;

      if (contentType?.includes('application/json')) {
        body = await response.json().catch(() => null);
      } else {
        body = await response.text().catch(() => null);
      }

      throw new ApiErrorHandler(response.status, body);
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return undefined as T;
    }

    const json = await response.json();
    return json as T;
  } catch (error) {
    clearTimeout(timeoutId);

    if (error instanceof ApiErrorHandler) {
      throw error;
    }

    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error('Request timeout. Please try again.');
    }

    if (error instanceof TypeError && error.message === 'Failed to fetch') {
      throw new Error('Cannot connect to server. Check your internet connection.');
    }

    throw error;
  }
}

// Exported API client methods
export const apiClient = {
  get: <T>(path: string, options?: RequestInit) => api<T>(path, { ...options, method: 'GET' }),
  post: <T>(path: string, data?: unknown, options?: RequestInit) =>
    api<T>(path, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    }),
  put: <T>(path: string, data?: unknown, options?: RequestInit) =>
    api<T>(path, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    }),
  patch: <T>(path: string, data?: unknown, options?: RequestInit) =>
    api<T>(path, {
      ...options,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    }),
  delete: <T>(path: string, options?: RequestInit) =>
    api<T>(path, { ...options, method: 'DELETE' }),
};

// Domain-specific API methods
export const authApi = {
  login: (credentials: LoginRequest) =>
    apiClient.post<ApiResponse<LoginResponse>>('/auth/login/', credentials),
  refresh: () =>
    apiClient.post<ApiResponse<{ token: string; expires_in: number }>>('/auth/refresh/'),
  verify: () =>
    apiClient.post<ApiResponse<{ valid: boolean; user_id: string; username: string }>>('/auth/verify/'),
};

export const usersApi = {
  me: () =>
    apiClient.get<User>('/users/me/'),
  list: () =>
    apiClient.get<PaginatedResponse<User>>('/users/'),
};

export const eventsApi = {
  list: (params?: Record<string, string>) => {
    const query = new URLSearchParams(params).toString();
    return apiClient.get<PaginatedResponse<Event>>(`/events/${query ? `?${query}` : ''}`);
  },
  get: (id: string) =>
    apiClient.get<Event>(`/events/${id}/`),
  create: (data: Partial<Event>) =>
    apiClient.post<Event>('/events/', data),
  update: (id: string, data: Partial<Event>) =>
    apiClient.put<Event>(`/events/${id}/`, data),
  delete: (id: string) =>
    apiClient.delete<void>(`/events/${id}/`),
  statistics: (id: string) =>
    apiClient.get<any>(`/events/${id}/statistics/`),
  complete: (id: string) =>
    apiClient.post<{ message: string }>(`/events/${id}/complete/`),
};

export const tasksApi = {
  list: (params?: Record<string, string>) => {
    const query = new URLSearchParams(params).toString();
    return apiClient.get<PaginatedResponse<Task>>(`/tasks/${query ? `?${query}` : ''}`);
  },
  get: (id: string) =>
    apiClient.get<Task>(`/tasks/${id}/`),
  create: (data: Partial<Task>) =>
    apiClient.post<Task>('/tasks/', data),
  update: (id: string, data: Partial<Task>) =>
    apiClient.put<Task>(`/tasks/${id}/`, data),
  delete: (id: string) =>
    apiClient.delete<void>(`/tasks/${id}/`),
  complete: (id: string) =>
    apiClient.patch<{ message: string }>(`/tasks/${id}/complete/`),
  kanbanData: (eventId: string) =>
    apiClient.get<any>(`/kanban_data?event=${eventId}`),
};