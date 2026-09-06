import { apiClient } from './client'
import type { FamilySummary } from './contracts'
export const familyApi = {
	list: () => apiClient.get<FamilySummary[]>('/families'),
	create: (payload: { name: string }) => apiClient.post<FamilySummary>('/families', payload),
	join: (invite_code: string) => apiClient.post<FamilySummary>('/families/join', { invite_code }),
	detail: (id: string) => apiClient.get<FamilySummary>(`/families/${id}`),
	update: (id: string, payload: { name: string }) => apiClient.patch<FamilySummary>(`/families/${id}`, payload),
	members: (id: string) => apiClient.get(`/families/${id}/members`),
	createInvite: (id: string) => apiClient.post(`/families/${id}/invite-code`),
	revokeInvite: (id: string) => apiClient.delete(`/families/${id}/invite-code`),
	updateMember: (familyId: string, memberId: string, role: 'ADMIN' | 'MEMBER') => apiClient.patch(`/families/${familyId}/members/${memberId}`, { role }),
	removeMember: (familyId: string, memberId: string) => apiClient.delete(`/families/${familyId}/members/${memberId}`),
}
