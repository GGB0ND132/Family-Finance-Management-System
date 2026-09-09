import { apiClient } from './client'
import type { ApiResponse, PageData, TransactionQuery, TransactionResponse } from './contracts'

export interface CreateTransactionPayload {
  family_id: number
  account_id: number
  category_id: number
  beneficiary_member_id: number | string
  type: 'INCOME' | 'EXPENSE'
  amount: string
  occurred_at: string
  remark?: string
}

export const transactionApi = {
  list: (params: TransactionQuery) => apiClient.get<ApiResponse<PageData<TransactionResponse>>>('/transactions', { params }),
  create: (payload: CreateTransactionPayload) => apiClient.post<ApiResponse<TransactionResponse>>('/transactions', payload),
  update: (id: number, payload: Partial<Omit<CreateTransactionPayload, 'family_id' | 'type'>>) => apiClient.patch<ApiResponse<TransactionResponse>>(`/transactions/${id}`, payload),
  confirm: (id: number) => apiClient.post<ApiResponse<TransactionResponse>>(`/transactions/${id}/confirm`),
  remove: (id: number) => apiClient.delete<void>(`/transactions/${id}`),
  export: (params: TransactionQuery & { format: 'csv' | 'xlsx' }) => apiClient.get('/exports/transactions', { params, responseType: 'blob' }),
}

export async function downloadBlob(response: { data: Blob }, filename: string) {
  const url = URL.createObjectURL(response.data)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
}
