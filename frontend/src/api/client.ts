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
  constructor(
    public status: number,
    public body: unknown
  ) {
    super(
      body && typeof body === 'object' && 'message' in body
        ? String(body.message)
        : `API error ${status}`
    );
    this.name = 'ApiError';
  }
}

// API configuration
const API_BASE_URL = '/api';
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
async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
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
  setAuthToken: (token: string) => {
    currentToken = token;
    localStorage.setItem('eventpilot_token', token);
  },
  getAuthToken: () => getAuthToken(),
  clearAuthToken: () => clearAuthToken(),
};

// Domain-specific API methods
export const authApi = {
  login: (credentials: LoginRequest) =>
    apiClient.post<ApiResponse<LoginResponse>>('/users/auth/login/', credentials),
  refresh: () =>
    apiClient.post<ApiResponse<{ token: string; expires_in: number }>>('/users/auth/refresh/'),
  verify: () =>
    apiClient.post<ApiResponse<{ valid: boolean; user_id: string; username: string }>>(
      '/users/auth/verify/'
    ),
};

export const usersApi = {
  me: () => apiClient.get<User>('/users/me/'),
  list: () => apiClient.get<PaginatedResponse<User>>('/users/'),
};

export const eventsApi = {
  list: (params?: Record<string, string>) => {
    const query = new URLSearchParams(params).toString();
    return apiClient.get<PaginatedResponse<Event>>(`/events/events/${query ? `?${query}` : ''}`);
  },
  get: (id: string) => apiClient.get<Event>(`/events/events/${id}/`),
  create: (data: Partial<Event>) => apiClient.post<Event>('/events/events/', data),
  update: (id: string, data: Partial<Event>) => apiClient.put<Event>(`/events/events/${id}/`, data),
  delete: (id: string) => apiClient.delete<void>(`/events/events/${id}/`),
  statistics: (id: string) => apiClient.get<any>(`/events/events/${id}/statistics/`),
  complete: (id: string) => apiClient.post<{ message: string }>(`/events/events/${id}/complete/`),
};

export const tasksApi = {
  list: (params?: Record<string, string>) => {
    const query = new URLSearchParams(params).toString();
    return apiClient.get<PaginatedResponse<Task>>(`/tasks/${query ? `?${query}` : ''}`);
  },
  get: (id: string) => apiClient.get<Task>(`/tasks/${id}/`),
  create: (data: Partial<Task>) => apiClient.post<Task>('/tasks/', data),
  update: (id: string, data: Partial<Task>) => apiClient.put<Task>(`/tasks/${id}/`, data),
  bulkUpdateStatus: (updates: Array<{ id: string; status: string }>) =>
    apiClient.post<{ updated: number; failed: Array<{ id: string; error: string }> }>(
      '/tasks/bulk_update_status/',
      updates
    ),
  delete: (id: string) => apiClient.delete<void>(`/tasks/${id}/`),
  complete: (id: string) => apiClient.patch<{ message: string }>(`/tasks/${id}/complete/`),
  kanbanData: (eventId: string) => apiClient.get<any>(`/kanban_data?event=${eventId}`),
};

// File types and API
export interface FileMetadata {
  id: string;
  file_id: string;
  original_filename: string;
  stored_filename: string;
  file_size: number;
  file_type: string;
  mime_type: string;
  file_category: string;
  status: 'uploading' | 'processing' | 'completed' | 'failed' | 'deleted';
  uploaded_by: string;
  created_at: string;
  visibility: 'private' | 'team' | 'public' | 'shared';
  tags: string[];
  category?: string;
  description?: string;
  metadata?: Record<string, unknown>;
}

export interface FileUploadRequest {
  filename: string;
  file_size: number;
  mime_type: string;
  metadata?: Record<string, unknown>;
}

export interface FileUploadInitiateResponse {
  file_id: string;
  upload_strategy: 'direct' | 'multipart';
  presigned_url?: string;
  storage_key: string;
  upload_id?: string;
  chunk_size: number;
  max_chunks: number;
  expires_in: number;
}

export interface FileDownloadResponse {
  file_id: string;
  filename: string;
  file_size: number;
  mime_type: string;
  download_url: string;
  expires_in: number;
}

export interface FileListResponse {
  total: number;
  page: number;
  page_size: number;
  files: FileMetadata[];
}

export const filesApi = {
  list: (params?: Record<string, string>) => {
    const query = new URLSearchParams(params).toString();
    return apiClient.get<FileListResponse>(`/files/${query ? `?${query}` : ''}`);
  },
  get: (fileId: string) => apiClient.get<FileMetadata>(`/files/${fileId}/`),
  initiateUpload: (data: FileUploadRequest) =>
    apiClient.post<FileUploadInitiateResponse>('/files/', data),
  getUploadPart: (fileId: string, partNumber: number, uploadId: string) =>
    apiClient.post<{
      presigned_url: string;
      part_number: number;
      upload_id: string;
      expires_in: number;
    }>(`/files/${fileId}/upload_part/`, { part_number: partNumber, upload_id: uploadId }),
  completeUpload: (
    fileId: string,
    uploadId: string,
    parts: Array<{ PartNumber: number; ETag: string }>
  ) =>
    apiClient.post<{ file_id: string; status: string; file_size: number; etag: string }>(
      `/files/${fileId}/complete_upload/`,
      { file_id: fileId, upload_id: uploadId, parts }
    ),
  download: (fileId: string, expiresIn: number = 3600) =>
    apiClient.post<FileDownloadResponse>(`/files/${fileId}/download/`, {
      file_id: fileId,
      expires_in: expiresIn,
    }),
  delete: (fileId: string) =>
    apiClient.delete<{ file_id: string; status: string; message: string }>(`/files/${fileId}/`),
  update: (fileId: string, data: Partial<FileMetadata>) =>
    apiClient.patch<FileMetadata>(`/files/${fileId}/`, data),
  share: (
    fileId: string,
    settings: {
      allow_download?: boolean;
      allow_preview?: boolean;
      expires_hours?: number;
      description?: string;
    }
  ) =>
    apiClient.post<{
      share_id: string;
      share_url: string;
      expires_at?: string;
      password_protected: boolean;
      settings: Record<string, unknown>;
    }>(`/files/${fileId}/share/`, settings),
  batchDelete: (fileIds: string[]) =>
    apiClient.post<{
      success: boolean;
      deleted_count: number;
      failed_count: number;
      errors: Array<Record<string, string>>;
    }>('/files/batch_delete/', { file_ids: fileIds }),
  search: (params: Record<string, string>) => {
    const query = new URLSearchParams(params).toString();
    return apiClient.get<FileListResponse>(`/files/search?${query}`);
  },
  stats: () =>
    apiClient.get<{
      total_files: number;
      total_size: number;
      by_category: Record<string, number>;
      by_status: Record<string, number>;
      by_type: Record<string, number>;
      recent_uploads: number;
      storage_used: number;
      storage_available: number;
      quota_percentage: number;
    }>('/files/stats/'),
};

export interface KnowledgeEntry {
  id: string;
  title: string;
  entry_type: 'issue' | 'experience' | 'best_practice';
  content: string;
  category?: string;
  tags: string[];
  related_events: string[];
  related_tasks: string[];
  is_public: boolean;
  is_verified: boolean;
  popularity: number;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export const knowledgeApi = {
  list: (params?: Record<string, string>) => {
    const query = new URLSearchParams(params).toString();
    return apiClient.get<PaginatedResponse<KnowledgeEntry>>(
      `/knowledge/${query ? `?${query}` : ''}`
    );
  },
  get: (id: string) => apiClient.get<KnowledgeEntry>(`/knowledge/${id}/`),
  create: (data: Partial<KnowledgeEntry>) => apiClient.post<KnowledgeEntry>('/knowledge/', data),
  update: (id: string, data: Partial<KnowledgeEntry>) =>
    apiClient.put<KnowledgeEntry>(`/knowledge/${id}/`, data),
  delete: (id: string) => apiClient.delete<void>(`/knowledge/${id}/`),
};

export interface Review {
  id: string;
  event: string;
  event_name?: string;
  title: string;
  status: 'draft' | 'in_progress' | 'completed';
  goal_achievement?: string;
  process_execution?: string;
  cost_control?: string;
  customer_feedback?: string;
  team_collaboration?: string;
  successes?: string;
  improvements?: string;
  action_items?: string;
  related_issues: string[];
  created_by?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export const reviewsApi = {
  list: (params?: Record<string, string>) => {
    const query = new URLSearchParams(params).toString();
    return apiClient.get<PaginatedResponse<Review>>(`/reviews/${query ? `?${query}` : ''}`);
  },
  get: (id: string) => apiClient.get<Review>(`/reviews/${id}/`),
  create: (data: Partial<Review>) => apiClient.post<Review>('/reviews/', data),
  update: (id: string, data: Partial<Review>) => apiClient.put<Review>(`/reviews/${id}/`, data),
  patch: (id: string, data: Partial<Review>) => apiClient.patch<Review>(`/reviews/${id}/`, data),
  delete: (id: string) => apiClient.delete<void>(`/reviews/${id}/`),
};

export interface Notification {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  title: string;
  message: string;
  data: Record<string, unknown>;
  source: string;
  related_object_type?: string;
  related_object_id?: string;
  read: boolean;
  read_at?: string;
  created_at: string;
  relative_time: string;
}

export interface NotificationListResponse {
  notifications: Notification[];
  total: number;
  page: number;
  page_size: number;
}

export interface NotificationStatsResponse {
  total: number;
  unread: number;
  read: number;
  by_type: Array<{ type: string; count: number }>;
  by_source: Array<{ source: string; count: number }>;
}

export const notificationsApi = {
  list: (params?: {
    type?: string;
    read?: string;
    page?: number;
    page_size?: number;
  }) => {
    const query = new URLSearchParams(
      params as Record<string, string>
    ).toString();
    return apiClient.get<NotificationListResponse>(`/notifications/${query ? `?${query}` : ''}`);
  },
  getUnreadCount: () => apiClient.get<{ unread_count: number }>('/notifications/unread_count/'),
  markRead: (id: string) => apiClient.post<{ message: string }>(`/notifications/${id}/mark_read/`, {}),
  bulkMarkRead: (notificationIds?: string[]) =>
    apiClient.post<{ message: string }>('/notifications/bulk_mark_read/', notificationIds ? { notification_ids: notificationIds } : {}),
  delete: (id: string) => apiClient.delete<{ message: string }>(`/notifications/${id}/delete/`),
  statistics: () => apiClient.get<NotificationStatsResponse>('/notifications/statistics/'),
};

