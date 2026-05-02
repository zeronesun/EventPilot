/**
 * Profiles Client API
 * 关联方档案管理API客户端
 */

import { apiClient } from '@/api/client'

// Type definitions
export type ProfileType = 'client' | 'supplier' | 'partner'
export type RiskLevel = 'low' | 'medium' | 'high'
export type Status = 'prospective' | 'active' | 'inactive' | 'blacklisted'

export interface ContactProfile {
  id: string
  profile_type: ProfileType
  name: string
  company_name?: string
  industry?: string
  address?: string
  phone?: string
  email?: string
  credit_score: number
  quality_score: number
  aggregate_score: number
  risk_level: RiskLevel
  status: Status
  notes?: string
  created_at: string
  updated_at: string
  // Computed fields
  profile_type_display?: string
  risk_level_display?: string
  status_display?: string
  is_deleted?: boolean
}

export interface ContactPerson {
  id: string
  profile: string
  name: string
  position?: string
  phone?: string
  email?: string
  is_primary: boolean
  created_at: string
}

export interface InteractionHistory {
  id: string
  profile: string
  interaction_type: string
  description?: string
  outcome?: string
  interaction_date: string
  created_at: string
}

export interface ProfileEvaluation {
  id: string
  profile: string
  evaluation_type: string
  score: number
  notes?: string
  evaluated_by?: string
  created_at: string
}

export interface ProfileAssessment {
  profile_id: string
  aggregate_score: number
  credit_score: number
  quality_score: number
  risk_level: RiskLevel
  risk_factors: string[]
  recommendations: string[]
  last_updated: string
}

export interface AnalyticsDashboard {
  total_profiles: number
  high_score_count: number
  high_risk_count: number
  recent_interactions: number
  by_type: {
    profile_type: string
    count: number
  }[]
  by_status: {
    status: string
    count: number
  }[]
}

/**
 * Profiles API
 */
export const profilesApi = {
  list: async (params?: {
    profile_type?: ProfileType
    status?: Status
    search?: string
    min_credit_score?: number
  }) => {
    const query = new URLSearchParams(params as any).toString()
    return apiClient.get<ContactProfile[]>(
      `/profiles/${query ? `?${query}` : ''}`
    )
  },

  get: async (id: string) => {
    return apiClient.get<ContactProfile>(`/profiles/${id}/`)
  },

  create: async (data: Partial<ContactProfile>) => {
    return apiClient.post<ContactProfile>('/profiles/', data)
  },

  update: async (id: string, data: Partial<ContactProfile>) => {
    return apiClient.put<ContactProfile>(`/profiles/${id}/`, data)
  },

  delete: async (id: string) => {
    return apiClient.delete<void>(`/profiles/${id}/`)
  },

  // Contacts
  getContacts: async (profileId: string) => {
    return apiClient.get<{ results: ContactPerson[]; count: number }>(
      `/profiles/${profileId}/contacts/`
    )
  },

  addContact: async (profileId: string, data: Partial<ContactPerson>) => {
    return apiClient.post<ContactPerson>(`/profiles/${profileId}/contacts/`, data)
  },

  updateContact: async (
    profileId: string,
    contactId: string,
    data: Partial<ContactPerson>
  ) => {
    return apiClient.put<ContactPerson>(
      `/profiles/${profileId}/contacts/${contactId}/`,
      data
    )
  },

  deleteContact: async (profileId: string, contactId: string) => {
    return apiClient.delete<void>(
      `/profiles/${profileId}/contacts/${contactId}/`
    )
  },

  // Interactions
  getInteractions: async (profileId: string) => {
    return apiClient.get<{ results: InteractionHistory[]; count: number }>(
      `/profiles/${profileId}/interactions/`
    )
  },

  addInteraction: async (
    profileId: string,
    data: Partial<InteractionHistory>
  ) => {
    return apiClient.post<InteractionHistory>(
      `/profiles/${profileId}/interactions/`,
      data
    )
  },

  // Evaluations
  getEvaluations: async (profileId: string) => {
    return apiClient.get<{ results: ProfileEvaluation[]; count: number }>(
      `/profiles/${profileId}/evaluations/`
    )
  },

  addEvaluation: async (
    profileId: string,
    data: Partial<ProfileEvaluation>
  ) => {
    return apiClient.post<ProfileEvaluation>(
      `/profiles/${profileId}/evaluations/`,
      data
    )
  },

  // Comprehensive
  getComprehensiveAssessment: async (profileId: string) => {
    return apiClient.get<ProfileAssessment>(
      `/profiles/${profileId}/assessment/`
    )
  },

  // Search
  searchProfiles: async (query: string, profileType?: ProfileType) => {
    const params: any = { search: query }
    if (profileType) params.profile_type = profileType
    const queryString = new URLSearchParams(params).toString()
    return apiClient.get<ContactProfile[]>(`/profiles/search/?${queryString}`)
  },

  // Dashboard Analytics
  getDashboardAnalytics: async () => {
    return apiClient.get<AnalyticsDashboard>('/profiles/analytics/')
  }
}
