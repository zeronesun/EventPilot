// EventPilot 基础类型定义
// 这个文件定义了整个应用的核心数据类型

// ==================== 用户相关类型 ====================

export interface User {
  id: number
  username: string
  email: string
  first_name?: string
  last_name?: string
  role: string
  is_active: boolean
  created_at: string
  updated_at: string
  last_login?: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access: string
  refresh: string
  user: User
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  first_name?: string
  last_name?: string
}

// ==================== 活动相关类型 ====================

export type EventStatus = 'planning' | 'executing' | 'completed' | 'reviewed' | 'cancelled'

export interface Event {
  id: number
  name: string
  description?: string
  status: EventStatus
  start_date: string
  end_date: string
  location?: string
  estimated_budget: number
  actual_budget: number
  budget_variance: number
  owner: User
  participants: User[]
  created_at: string
  updated_at: string
  risk_level?: string
  budget_items?: BudgetItem[]
}

export interface EventCreateRequest {
  name: string
  description?: string
  start_date: string
  end_date: string
  location?: string
  estimated_budget: number
  owner?: number
  participants?: number[]
}

export interface EventUpdateRequest {
  name?: string
  description?: string
  status?: EventStatus
  start_date?: string
  end_date?: string
  location?: string
  estimated_budget?: number
  actual_budget?: number
  owner?: number
  participants?: number[]
}

// ==================== 任务相关类型 ====================

export type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'blocked'
export type TaskPriority = 'low' | 'medium' | 'high' | 'urgent'
export type TaskType = 'planning' | 'guest' | 'material' | 'venue' | 'promotion' | 'onsite' | 'review'

export interface Task {
  id: number
  title: string
  description?: string
  status: TaskStatus
  priority: TaskPriority
  type: TaskType
  event?: Event
  assigned_to?: User
  due_date?: string
  completed_at?: string
  created_at: string
  updated_at: string
  event_id?: number
  dependencies?: number[]
}

export interface TaskCreateRequest {
  title: string
  description?: string
  event?: number
  assigned_to?: number
  due_date?: string
  priority?: TaskPriority
  type?: TaskType
  status?: TaskStatus
  dependencies?: number[]
}

export interface TaskUpdateRequest {
  title?: string
  description?: string
  status?: TaskStatus
  priority?: TaskPriority
  type?: TaskType
  event?: number
  assigned_to?: number
  due_date?: string
  completed_at?: string
  dependencies?: number[]
}

// ==================== 预算相关类型 ====================

export interface BudgetItem {
  id?: number
  event: number | Event
  category_name: string
  name: string
  estimated_amount: number
  actual_amount: number
  variance: number
  responsible?: number | User
  status: string
  created_at?: string
  updated_at?: string
}

export interface BudgetItemCreate {
  event: number
  category_name: string
  name: string
  estimated_amount: number
  actual_amount?: number
  responsible?: number
  status: string
}

export interface BudgetItemUpdate {
  category_name?: string
  name?: string
  estimated_amount?: number
  actual_amount?: number
  responsible?: number
  status?: string
}

// ==================== 文件相关类型 ====================

export interface FileRecord {
  id: number
  file_name: string
  file_path: string
  file_size: number
  file_type: string
  uploaded_by: User
  event?: Event
  created_at: string
  description?: string
  tags?: string[]
}

export interface FileUploadRequest {
  file: File
  file_name?: string
  event?: number
  description?: string
  tags?: string[]
}

// ==================== 关联方档案相关类型 ====================

export interface Profile {
  id: number
  name: string
  type: 'customer' | 'supplier' | 'partner' | 'venue' | 'speaker'
  contact_info: Record<string, any>
  credit_score?: number
  quality_score?: number
  risk_level?: string
  created_at: string
  updated_at: string
  tags?: string[]
  notes?: string
}

export interface ProfileContact {
  id: number
  profile: number | Profile
  name: string
  role?: string
  email?: string
  phone?: string
  is_primary: boolean
}

export interface ProfileInteraction {
  id: number
  profile: number | Profile
  interaction_type: string
  notes?: string
  date: string
  user: number | User
}

// ==================== 知识库相关类型 ====================

export interface KnowledgeEntry {
  id: number
  title: string
  content: string
  category?: string
  tags?: string[]
  created_by: User
  created_at: string
  updated_at: string
  is_public: boolean
  related_events?: number[]
}

// ==================== 复盘相关类型 ====================

export interface Review {
  id: number
  event: number | Event
  overall_score: number
  highlights: string[]
  improvements: string[]
  lessons_learned: string[]
  best_practices: string[]
  next_steps: string[]
  created_by: User
  created_at: string
  reviewed_by?: User
  reviewed_at?: string
}

// ==================== 检查清单相关类型 ====================

export interface ChecklistTemplate {
  id: number
  name: string
  category?: string
  items: ChecklistItem[]
  created_by: User
  created_at: string
  updated_at: string
}

export interface ChecklistInstance {
  id: number
  template: number | ChecklistTemplate
  event: number | Event
  items: ChecklistInstanceItem[]
  status: string
  completed_at?: string
  created_at: string
  updated_at: string
}

export interface ChecklistItem {
  id?: number
  name: string
  description?: string
  category?: string
  required: boolean
  weight?: number
}

export interface ChecklistInstanceItem {
  id: number
  item: number | ChecklistItem
  checked: boolean
  checked_by?: User
  checked_at?: string
  notes?: string
  attachment_url?: string
}

// ==================== 分析和统计相关类型 ====================

export interface AnalyticsOverview {
  total_events: number
  total_tasks: number
  task_completion_rate: number
  budget_variance_rate: number
  total_estimated_budget: number
  total_actual_budget: number
  budget_variance: number
}

export interface StatusDistribution {
  [key: string]: {
    count: number
    percentage: number
  }
}

export interface TypeDistribution {
  [key: string]: {
    name: string
    count: number
    percentage: number
  }
}

export interface DashboardAnalytics {
  overview: AnalyticsOverview
  status_distribution: StatusDistribution
  type_distribution: TypeDistribution
  task_type_distribution: TypeDistribution
  monthly_trend: MonthlyTrend[]
  high_risk_events: HighRiskEvent[]
  upcoming_deadlines: UpcomingDeadline[]
  top_owners: TopOwner[]
  generated_at: string
}

export interface MonthlyTrend {
  month: string
  count: number
  total_budget: number
}

export interface HighRiskEvent {
  id: number
  name: string
  risk_level: string
  factors_count: number
}

export interface UpcomingDeadline {
  id: number
  name: string
  days_remaining: number
  end_date: string
}

export interface TopOwner {
  username: string
  event_count: number
  total_budget: number
}

// ==================== API响应通用类型 ====================

export interface PaginatedResponse<T> {
  count: number
  next?: string
  previous?: string
  results: T[]
}

export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: string
  errors?: Record<string, string[]>
}

export interface ApiError {
  detail?: string
  non_field_errors?: string[]
  [key: string]: any
}

// ==================== 搜索和过滤相关类型 ====================

export interface SearchParams {
  search?: string
  page?: number
  page_size?: number
  ordering?: string
  [key: string]: any
}

export interface FilterParams {
  status?: string
  event?: number
  assigned_to?: number
  start_date_from?: string
  start_date_to?: string
  end_date_from?: string
  end_date_to?: string
  [key: string]: any
}

// ==================== WebSocket 相关类型 ====================

export interface WebSocketMessage {
  type: string
  payload: any
  sender?: string
  timestamp?: string
}

export interface NotificationData {
  id?: string
  type: 'info' | 'success' | 'warning' | 'error'
  title: string
  message: string
  data?: any
  read: boolean
  created_at?: string
}
