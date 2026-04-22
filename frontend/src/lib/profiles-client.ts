// 关联方档案管理接口定义
// 遵循fullstack-dev最佳实践

import { apiClient } from '@/api/client';

export type ProfileType = 'client' | 'supplier' | 'partner';

export interface ContactInfo {
  address?: {
    street?: string;
    city?: string;
    province?: string;
    postal_code?: string;
    country?: string;
  };
  phone?: string[];
  email?: string[];
  website?: string;
  social_media?: {
    wechat?: string;
    linkedin?: string;
    weibo?: string;
  };
}

export interface ContactProfile {
  id: string;
  profile_type: ProfileType;
  profile_type_display: string;
  name: string;
  company_name?: string;
  legal_person?: string;
  registration_number?: string;
  contact_info: ContactInfo;
  industry?: string;
  business_scope?: string;
  tags: string[];
  status: string;
  status_display: string;
  credit_score: number;
  quality_score: number;
  risk_level: string;
  risk_level_display: string;
  aggregate_score: number;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
  last_contact_date?: string;
}

export interface ContactPerson {
  id: string;
  profile: string;
  name: string;
  position: string;
  position_display: string;
  position_other?: string;
  contact_info: {
    phone?: string[];
    email?: string[];
    wechat?: string;
    linkedin?: string;
    qq?: string;
  };
  is_primary: boolean;
  is_active: boolean;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface InteractionHistory {
  id: string;
  profile: string;
  profile_name: string;
  interaction_type: 'event' | 'contract' | 'communication' | 'meeting' | 'payment' | 'support' | 'complaint' | 'negotiation' | 'other';
  interaction_type_display: string;
  title: string;
  description: string;
  related_event_id?: string;
  related_project_id?: string;
  metadata: Record<string, unknown>;
  satisfaction_score?: number;
  outcome_status?: string;
  interaction_date: string;
  created_at: string;
}

export interface ProfileEvaluation {
  id: string;
  profile: string;
  profile_name: string;
  evaluator: string;
  evaluator_name: string;
  evaluation_date: string;
  credit_score?: number;
  quality_score?: number;
  service_quality?: number;
  response_speed?: number;
  professional_ability?: number;
  evaluation_criteria: Record<string, unknown>;
  risk_assessment?: string;
  risk_level: string;
  recommendations: string;
  overall_conclusion?: string;
  next_evaluation_date?: string;
}

export interface ProfileAssessment {
  aggregate_score: number;
  interaction_stats: {
    total_count: number;
    event_count: number;
    contract_count: number;
    communication_count: number;
  };
  latest_evaluation: string | null;
  risk_factors: string[];
  strengths: string[];
  recommendation: string;
}

export interface RecommendationRequest {
  profile_type?: ProfileType;
  event_type?: string;
  min_credit_score?: number;
  max_risk_level?: 'low' | 'medium' | 'high';
  limit?: number;
}

export interface RecommendationResult {
  profile_id: string;
  name: string;
  company_name?: string;
  profile_type: ProfileType;
  recommendation_score: number;
  reasons: string[];
  credit_score: number;
  quality_score: number;
  risk_level: string;
  primary_contact?: string;
}

export interface RecommendationResponse {
  event_requirements: RecommendationRequest;
  recommendations: RecommendationResult[];
  count: number;
}

export interface SearchRequest {
  query: string;
  profile_type?: ProfileType;
  limit?: number;
}

export interface SearchResult {
  profile_id: string;
  name: string;
  company_name?: string;
  profile_type: ProfileType;
  status: string;
  credit_score: number;
  quality_score: number;
  relevance_score: number;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  count: number;
}

export interface AnalyticsDashboard {
  total_profiles: number;
  by_type: Record<string, number>;
  by_status: Record<string, number>;
  average_scores: {
    credit: number;
    quality: number;
  };
  risk_distribution: Record<string, number>;
  recent_interactions: number;
  high_risk_count: number;
  high_score_count: number;
}

// API Methods
export const profilesApi = {
  list: (params?: {
    profile_type?: ProfileType;
    status?: string;
    min_credit_score?: number;
    search?: string;
    page?: number;
    page_size?: number;
  }) => {
    const query = new URLSearchParams(params as any).toString();
    return apiClient.get<ContactProfile[]>(`/profiles/${query ? `?${query}` : ''}`);
  },
  
  get: (id: string) => 
    apiClient.get<ContactProfile>(`/profiles/${id}/`),
    
  create: (data: Partial<ContactProfile>) => 
    apiClient.post<ContactProfile>('/profiles/', data),
    
  update: (id: string, data: Partial<ContactProfile>) => 
    apiClient.put<ContactProfile>(`/profiles/${id}/`, data),
    
  delete: (id: string) => 
    apiClient.delete(`/profiles/${id}/`),
    
  getContacts: (id: string) => 
    apiClient.get<{ results: ContactPerson[]; count: number }>(`/profiles/${id}/contacts/`),
    
  addContact: (id: string, data: Partial<ContactPerson>) =>
    apiClient.post<ContactPerson>(`/profiles/${id}/contact/`, data),

  updateContact: (profileId: string, contactId: string, data: Partial<ContactPerson>) =>
    apiClient.put<ContactPerson>(`/profiles/${profileId}/contact/${contactId}/`, data),

  deleteContact: (profileId: string, contactId: string) =>
    apiClient.delete(`/profiles/${profileId}/contact/${contactId}/`),
    
  getInteractions: (id: string) => 
    apiClient.get<{ results: InteractionHistory[]; count: number }>(`/profiles/${id}/interactions/`),
    
  addInteraction: (id: string, data: Partial<InteractionHistory>) => 
    apiClient.post<InteractionHistory>(`/profiles/${id}/interaction/`, data),
    
  getEvaluations: (id: string) => 
    apiClient.get<{ results: ProfileEvaluation[]; count: number }>(`/profiles/${id}/evaluations/`),
    
  addEvaluation: (id: string, data: Partial<ProfileEvaluation>) => 
    apiClient.post<ProfileEvaluation>(`/profiles/${id}/evaluation/`, data),
    
  getComprehensiveAssessment: (id: string) => 
    apiClient.get<ProfileAssessment>(`/profiles/${id}/comprehensive_assessment/`),
    
  recommendSuppliers: (requirements: RecommendationRequest) => 
    apiClient.post<RecommendationResponse>('/recommendations/suppliers/', requirements),
    
  searchProfiles: (query: string, profileType?: ProfileType) => 
    apiClient.post<SearchResponse>('/search/profiles/', { query, profile_type: profileType }),
    
  getDashboardAnalytics: () => 
    apiClient.get<AnalyticsDashboard>('/analytics/dashboard/')
};