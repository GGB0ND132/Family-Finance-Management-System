import { apiClient } from './client'
import type { Account } from '../data/financeData'
import type { AccountPayload, AccountResponse } from './contracts'

export const accountApi = {
  list: (familyId?: string, ownerMemberId?: string) => apiClient.get<AccountResponse[]>('/accounts', { params: { family_id: familyId, owner_member_id: ownerMemberId } }),
  create: (payload: AccountPayload) => apiClient.post<AccountResponse>('/accounts', payload),
  update: (id: string, payload: Partial<Pick<Account, 'name' | 'type' | 'ownerMemberId' | 'remark'>>) => apiClient.patch<AccountResponse>(`/accounts/${id}`, payload),
  remove: (id: string) => apiClient.delete<void>(`/accounts/${id}`),
}
