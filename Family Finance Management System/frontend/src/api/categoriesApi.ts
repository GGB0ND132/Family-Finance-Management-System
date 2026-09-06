import { apiClient } from './client'
import type { CategoryType } from '../data/financeData'
import type { ApiResponse, CategoryResponse, PageData } from './contracts'

export const categoryApi = {
  /** 查询分类列表。`type` 可选 INCOME/EXPENSE；`include_deleted` 可选包含已删分类（默认 false）。 */
  list: (params: {
    family_id: number
    type?: CategoryType
    include_deleted?: boolean
  }) =>
    apiClient.get<ApiResponse<PageData<CategoryResponse>>>('/categories', {
      params,
    }),

  /** 新增自定义分类（仅管理员）。 */
  create: (payload: {
    family_id: number
    name: string
    type: CategoryType
    color: string
    icon?: string
  }) =>
    apiClient.post<ApiResponse<CategoryResponse>>('/categories', payload),

  /** 编辑分类名称、图标或颜色（仅管理员）。 */
  update: (
    id: number,
    payload: { name?: string; icon?: string; color?: string },
  ) =>
    apiClient.patch<ApiResponse<CategoryResponse>>(
      `/categories/${id}`,
      payload,
    ),

  /** 删除分类（仅管理员）。未引用时物理删除，有引用时软删除保留历史。 */
  remove: (id: number) => apiClient.delete<void>(`/categories/${id}`),
}