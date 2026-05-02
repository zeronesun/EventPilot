import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { ContactProfile, ContactPerson, InteractionHistory, ProfileEvaluation, ProfileAssessment, AnalyticsDashboard } from '@/lib/profiles-client';
import { profilesApi, type ProfileType } from '@/lib/profiles-client';

interface ProfileState {
  profiles: ContactProfile[];
  selectedProfile: ContactProfile | null;
  contacts: ContactPerson[];
  interactions: InteractionHistory[];
  evaluations: ProfileEvaluation[];
  currentAssessment: ProfileAssessment | null;
  dashboardStats: AnalyticsDashboard | null;
  filters: {
    profile_type?: ProfileType;
    status?: string;
    min_credit_score?: number;
    search?: string;
  };
  loading: boolean;
  error: string | null;
}

const initialState: ProfileState = {
  profiles: [],
  selectedProfile: null,
  contacts: [],
  interactions: [],
  evaluations: [],
  currentAssessment: null,
  dashboardStats: null,
  filters: {},
  loading: false,
  error: null
};

export const useProfilesStore = defineStore('profiles', () => {
  const state = ref<ProfileState>(JSON.parse(JSON.stringify(initialState)));
  
  // Getters
  const profiles = computed(() => state.value.profiles);
  const selectedProfile = computed(() => state.value.selectedProfile);
  const contacts = computed(() => state.value.contacts);
  const interactions = computed(() => state.value.interactions);
  const evaluations = computed(() => state.value.evaluations);
  const currentAssessment = computed(() => state.value.currentAssessment);
  const dashboardStats = computed(() => state.value.dashboardStats);
  const loading = computed(() => state.value.loading);
  const error = computed(() => state.value.error);
  
  const activeProfiles = computed(() => 
    state.value.profiles.filter(p => p.status === 'active')
  );
  
  const suppliers = computed(() =>
    state.value.profiles.filter(p => p.profile_type === 'supplier')
  );
  
  const highRatedProfiles = computed(() =>
    state.value.profiles.filter(p => p.aggregate_score >= 70)
  );
  
  const highRiskProfiles = computed(() =>
    state.value.profiles.filter(p => p.risk_level === 'high')
  );
  
  // Actions
  async function fetchProfiles(filters?: ProfileState['filters']) {
    state.value.loading = true;
    state.value.error = null;
    
    if (filters) {
      state.value.filters = { ...state.value.filters, ...filters };
    }
    
    try {
      const response = await profilesApi.list(state.value.filters);
      state.value.profiles = (response as any).results || response;
    } catch (err: any) {
      state.value.error = getErrorMessage(err);
    } finally {
      state.value.loading = false;
    }
  }
  
  async function createProfile(data: Partial<ContactProfile>) {
    state.value.loading = true;
    state.value.error = null;
    
    try {
      const profile = await profilesApi.create(data);
      state.value.profiles.unshift(profile);
      return profile;
    } catch (err: any) {
      state.value.error = getErrorMessage(err);
      return null;
    } finally {
      state.value.loading = false;
    }
  }
  
  async function updateProfile(id: string, data: Partial<ContactProfile>) {
    state.value.loading = true;
    state.value.error = null;
    
    try {
      const profile = await profilesApi.update(id, data);
      
      // Update in list
      const index = state.value.profiles.findIndex(p => p.id === id);
      if (index !== -1) {
        state.value.profiles[index] = profile;
      }
      
      // Update selected if matching
      if (state.value.selectedProfile?.id === id) {
        state.value.selectedProfile = profile;
      }
      
      return profile;
    } catch (err: any) {
      state.value.error = getErrorMessage(err);
      return null;
    } finally {
      state.value.loading = false;
    }
  }
  
  async function deleteProfile(id: string) {
    state.value.loading = true;
    state.value.error = null;
    
    try {
      await profilesApi.delete(id);
      
      // Remove from list
      state.value.profiles = state.value.profiles.filter(p => p.id !== id);
      
      // Clear selected if matching
      if (state.value.selectedProfile?.id === id) {
        state.value.selectedProfile = null;
      }
      
      return true;
    } catch (err: any) {
      state.value.error = getErrorMessage(err);
      return false;
    } finally {
      state.value.loading = false;
    }
  }
  
  async function selectProfile(id: string) {
    state.value.loading = true;
    state.value.error = null;
    
    try {
      const [profile, contacts, interactions, evaluations, assessment] = await Promise.all([
        profilesApi.get(id),
        profilesApi.getContacts(id).catch(() => ({ results: [], count: 0 })),
        profilesApi.getInteractions(id).catch(() => ({ results: [], count: 0 })),
        profilesApi.getEvaluations(id).catch(() => ({ results: [], count: 0 })),
        profilesApi.getComprehensiveAssessment(id)
      ]);
      
      state.value.selectedProfile = profile;
      state.value.contacts = contacts.results;
      state.value.interactions = interactions.results;
      state.value.evaluations = evaluations.results;
      state.value.currentAssessment = assessment;
      
      return profile;
    } catch (err: any) {
      state.value.error = getErrorMessage(err);
      return null;
    } finally {
      state.value.loading = false;
    }
  }
  
  async function fetchContacts(profileId: string) {
    try {
      const response = await profilesApi.getContacts(profileId);
      state.value.contacts = (response as any).results || [];
      return { success: true, data: state.value.contacts };
    } catch (err: any) {
      state.value.error = getErrorMessage(err);
      return { success: false, error: getErrorMessage(err) };
    }
  }

  async function createContact(profileId: string, data: Partial<ContactPerson>) {
    try {
      const contact = await profilesApi.addContact(profileId, data);
      state.value.contacts.push(contact);
      return { success: true, data: contact };
    } catch (err: any) {
      state.value.error = getErrorMessage(err);
      return { success: false, error: getErrorMessage(err) };
    }
  }

  async function updateContact(profileId: string, contactId: string, data: Partial<ContactPerson>) {
    try {
      const contact = await profilesApi.updateContact(profileId, contactId, data);
      // Update in list
      const index = state.value.contacts.findIndex(c => c.id === contactId);
      if (index !== -1) {
        state.value.contacts[index] = contact;
      }
      return { success: true, data: contact };
    } catch (err: any) {
      state.value.error = getErrorMessage(err);
      return { success: false, error: getErrorMessage(err) };
    }
  }

  async function deleteContact(profileId: string, contactId: string) {
    try {
      await profilesApi.deleteContact(profileId, contactId);
      // Remove from list
      state.value.contacts = state.value.contacts.filter(c => c.id !== contactId);
      return { success: true };
    } catch (err: any) {
      state.value.error = getErrorMessage(err);
      return { success: false, error: getErrorMessage(err) };
    }
  }
  
  async function addInteraction(profileId: string, data: Partial<InteractionHistory>) {
    try {
      const interaction = await profilesApi.addInteraction(profileId, data);
      state.value.interactions.push(interaction);
      return interaction;
    } catch (err: any) {
      state.value.error = getErrorMessage(err);
      return null;
    }
  }
  
  async function addEvaluation(profileId: string, data: Partial<ProfileEvaluation>) {
    try {
      const evaluation = await profilesApi.addEvaluation(profileId, data);
      state.value.evaluations.push(evaluation);
      return evaluation;
    } catch (err: any) {
      state.value.error = getErrorMessage(err);
      return null;
    }
  }
  
  async function searchProfiles(query: string, profileType?: ProfileType) {
    state.value.loading = true;
    state.value.error = null;
    
    try {
      const response = await profilesApi.searchProfiles(query, profileType);
      // Update profiles with search results
      state.value.profiles = (response as any).results || response;
      return response;
    } catch (err: any) {
      state.value.error = getErrorMessage(err);
      return null;
    } finally {
      state.value.loading = false;
    }
  }
  
  async function getDashboardStats() {
    state.value.loading = true;
    state.value.error = null;
    
    try {
      const stats = await profilesApi.getDashboardAnalytics();
      state.value.dashboardStats = stats;
      return stats;
    } catch (err: any) {
      state.value.error = getErrorMessage(err);
      return null;
    } finally {
      state.value.loading = false;
    }
  }
  
  function clearError() {
    state.value.error = null;
  }
  
  function resetFilters() {
    state.value.filters = {};
  }
  
  function reset() {
    state.value = JSON.parse(JSON.stringify(initialState));
  }
  
  return {
    state,
    profiles,
    selectedProfile,
    contacts,
    interactions,
    evaluations,
    currentAssessment,
    dashboardStats,
    loading,
    error,
    activeProfiles,
    suppliers,
    highRatedProfiles,
    highRiskProfiles,
    fetchProfiles,
    createProfile,
    updateProfile,
    deleteProfile,
    selectProfile,
    fetchContacts,
    createContact,
    updateContact,
    deleteContact,
    // Alias for backward compatibility
    addContact: createContact,
    addInteraction,
    addEvaluation,
    searchProfiles,
    getDashboardStats,
    clearError,
    resetFilters,
    reset
  };
}, {
  persist: {
    key: 'profiles-store',
    paths: ['filters']
  }
});

// Error message helper
function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  if (typeof error === 'string') {
    return error;
  }
  if (error && typeof error === 'object') {
    const apiError = error as any;
    if (apiError.status) {
      switch (apiError.status) {
        case 401: return '请先登录';
        case 403: return '您没有权限执行此操作';
        case 404: return '请求的资源不存在';
        case 422: return '请检查输入数据';
        default: return apiError.body?.detail || '请求失败';
      }
    }
  }
  return '发生未知错误';
}