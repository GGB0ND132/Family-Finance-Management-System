import { apiClient } from './client'

export interface TransferPayload { family_id: string; from_account_id: string; to_account_id: string; from_member_id: string; to_member_id: string; recorder_user_id: string; amount: number; occurred_at: string; remark?: string }
export const transferApi = {
  list: (familyId?: string) => apiClient.get('/transfers', { params: { family_id: familyId } }),
  create: (payload: TransferPayload) => apiClient.post('/transfers', payload),
  remove: (id: string) => apiClient.delete(`/transfers/${id}`),
}
