import { apiClient } from './client'

export const reportApi = {
  summary: (params: { family_id?: string; month: string; scope: 'personal' | 'family'; member_id?: string }) => apiClient.get('/reports/summary', { params }),
  trend: (params: { family_id?: string; from: string; to: string; scope: 'personal' | 'family'; member_id?: string }) => apiClient.get('/reports/trend', { params }),
  byCategory: (params: { family_id?: string; month: string; scope: 'personal' | 'family'; member_id?: string }) => apiClient.get('/reports/by-category', { params }),
  byMember: (params: { family_id?: string; month: string; scope: 'family'; member_id?: string }) => apiClient.get('/reports/by-member', { params }),
}
