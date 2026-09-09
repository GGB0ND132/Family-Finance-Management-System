import { apiClient } from './client'
import type { ApiResponse, PageData, TransferResponse } from './contracts'
export interface TransferQuery { family_id: number; scope: 'personal' | 'family'; page?: number; page_size?: number; from?: string; to?: string; from_member_id?: number; to_member_id?: number; from_account_id?: number; to_account_id?: number }
export interface TransferPayload { family_id: number; from_account_id: number; to_account_id: number; amount: string; occurred_at: string; remark?: string }
export interface UpdateTransferPayload { from_account_id?: number; to_account_id?: number; amount?: string; occurred_at?: string; remark?: string }
export const transferApi = {
  list: (params: TransferQuery) => apiClient.get<ApiResponse<PageData<TransferResponse>>>('/transfers', { params }),
  get: (id: number) => apiClient.get<ApiResponse<TransferResponse>>(`/transfers/${id}`),
  create: (payload: TransferPayload) => apiClient.post<ApiResponse<TransferResponse>>('/transfers', payload),
  update: (id: number, payload: UpdateTransferPayload) => apiClient.patch<ApiResponse<TransferResponse>>(`/transfers/${id}`, payload),
  confirm: (id: number) => apiClient.post<ApiResponse<TransferResponse>>(`/transfers/${id}/confirm`),
  remove: (id: number) => apiClient.delete<void>(`/transfers/${id}`),
}
