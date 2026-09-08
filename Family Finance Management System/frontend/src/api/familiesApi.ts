import { apiClient } from './client'
import type { ApiResponse, FamilyMemberResponse, FamilySummary } from './contracts'
export const familyApi = {
	list: () => apiClient.get<ApiResponse<FamilySummary[]>>('/families'),
	create: (payload: { name: string }) => apiClient.post<ApiResponse<FamilySummary>>('/families', payload),
	join: (invite_code: string) => apiClient.post<ApiResponse<{ family_id: number }>>('/families/join', { invite_code }),
	detail: (id: string) => apiClient.get<ApiResponse<FamilySummary>>(`/families/${id}`),
	update: (id: string, payload: { name: string }) => apiClient.patch<ApiResponse<FamilySummary>>(`/families/${id}`, payload),
	members: (id: string) => apiClient.get<ApiResponse<FamilyMemberResponse[]>>(`/families/${id}/members`),
	createInvite: (id: string) => apiClient.post(`/families/${id}/invite-code`),
	revokeInvite: (id: string) => apiClient.delete(`/families/${id}/invite-code`),
	updateMember: (familyId: string, memberId: string, role: 'ADMIN' | 'MEMBER') => apiClient.patch(`/families/${familyId}/members/${memberId}`, { role }),
	removeMember: (familyId: string, memberId: string) => apiClient.delete(`/families/${familyId}/members/${memberId}`),
}
