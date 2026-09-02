import { apiClient } from './client'
import type { Category, CategoryType } from '../data/financeData'
import type { CategoryResponse } from './contracts'

export const categoryApi = {
  list: (params?: { family_id?: string; type?: CategoryType; include_deleted?: boolean }) => apiClient.get<CategoryResponse[]>('/categories', { params }),
  create: (payload: { family_id: string; name: string; type: CategoryType; color: string; icon?: string }) => apiClient.post<CategoryResponse>('/categories', payload),
  update: (id: string, payload: Partial<Pick<Category, 'name' | 'color' | 'icon'>>) => apiClient.patch<CategoryResponse>(`/categories/${id}`, payload),
  remove: (id: string) => apiClient.delete<void>(`/categories/${id}`),
}
