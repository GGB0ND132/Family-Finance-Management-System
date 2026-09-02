import { apiClient } from './client'

export interface BudgetExecution { category_id: string; budget_amount: number; used_amount: number; remaining_amount: number; usage_rate: number; warning_level: 'NORMAL' | 'WARNING' | 'OVER' }
export const budgetApi = {
  get: (month: string, familyId?: string) => apiClient.get<BudgetExecution[]>(`/budgets/${month}`, { params: { family_id: familyId } }),
  save: (month: string, payload: { family_id: string; items: Array<{ category_id: string; amount: number }> }) => apiClient.put(`/budgets/${month}`, payload),
  copyFromPrevious: (month: string, familyId?: string) => apiClient.post(`/budgets/${month}/copy-from-previous`, { family_id: familyId }),
}
