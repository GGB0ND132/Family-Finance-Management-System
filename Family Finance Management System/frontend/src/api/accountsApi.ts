import { apiClient } from './client'
import type { AccountType } from '../data/financeData'
import type { AccountPayload, AccountResponse, ApiResponse, PageData } from './contracts'

export const accountApi = {
  list: (params: { family_id: number; scope?: 'personal' | 'family'; owner_member_id?: number; include_closed?: boolean; page?: number; page_size?: number }) => apiClient.get<ApiResponse<PageData<AccountResponse>>>('/accounts', { params }),
  create: (payload: AccountPayload) => apiClient.post<ApiResponse<AccountResponse>>('/accounts', payload),
  update: (id: number, payload: { name?: string; type?: AccountType; owner_member_id?: number; remark?: string | null }) => apiClient.patch<ApiResponse<AccountResponse>>(`/accounts/${id}`, payload),
  remove: (id: number) => apiClient.delete<void>(`/accounts/${id}`),
}
