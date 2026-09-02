import { apiClient } from './client'
import type { FamilySummary } from './contracts'
export const familyApi = { list: () => apiClient.get<FamilySummary[]>('/families'), detail: (id: string) => apiClient.get<FamilySummary>(`/families/${id}`), members: (id: string) => apiClient.get(`/families/${id}/members`) }
