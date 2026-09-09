import { apiClient } from './client'
import type { ApiResponse, BudgetResponse } from './contracts'
export const budgetApi = {
  get: (month: string, params: { family_id: number; scope: 'personal' | 'family' }) => apiClient.get<ApiResponse<BudgetResponse>>(`/budgets/${month}`, { params }),
  save: (month: string, payload: { family_id: number; scope: 'personal' | 'family'; total_amount: string; categories: Array<{ category_id: number; amount: string }> }) => apiClient.put<ApiResponse<BudgetResponse>>(`/budgets/${month}`, payload),
  copyFromPrevious: (month: string, payload: { family_id: number; scope: 'personal' | 'family' }) => apiClient.post<ApiResponse<BudgetResponse>>(`/budgets/${month}/copy-from-previous`, payload),
}
