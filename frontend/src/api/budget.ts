/**
 * Budget API Client
 * 预算管理API客户端
 */

import { apiClient } from './client'

export interface BudgetItem {
  id: string
  event: string
  category_name: string
  name: string
  estimated_amount: number
  actual_amount: number
  variance: number
  responsible?: string
  responsible_name?: string
  status: 'pending' | 'in_progress' | 'completed'
  created_at: string
  updated_at: string
}

export const budgetApi = {
  list: async (eventId?: string) => {
    const url = eventId ? `/events/${eventId}/budget_items/` : '/budget-items/'
    return apiClient.get<BudgetItem[]>(url)
  },

  get: async (id: string) => {
    return apiClient.get<BudgetItem>(`/budget-items/${id}/`)
  },

  create: async (data: Partial<BudgetItem>) => {
    return apiClient.post<BudgetItem>('/budget-items/', data)
  },

  update: async (id: string, data: Partial<BudgetItem>) => {
    return apiClient.put<BudgetItem>(`/budget-items/${id}/`, data)
  },

  delete: async (id: string) => {
    return apiClient.delete<void>(`/budget-items/${id}/`)
  }
}

export const createBudgetItem = budgetApi.create
export const updateBudgetItem = budgetApi.update
export const deleteBudgetItem = budgetApi.delete
