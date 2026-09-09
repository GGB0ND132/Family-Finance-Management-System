import { apiClient } from './client'
import type { ApiResponse, ReportCategoryPoint, ReportMemberPoint, ReportSummaryResponse, ReportTrendPoint } from './contracts'

export const reportApi = {
  personalSummary: (params: { family_id: number; from_date: string; to_date: string }) => apiClient.get<ApiResponse<ReportSummaryResponse>>('/reports/personal/summary', { params }),
  personalDaily: (params: { family_id: number; date: string }) => apiClient.get<ApiResponse<ReportSummaryResponse>>('/reports/personal/daily', { params }),
  personalTrend: (params: { family_id: number; from_month: string; to_month: string }) => apiClient.get<ApiResponse<ReportTrendPoint[]>>('/reports/personal/trend', { params }),
  personalByCategory: (params: { family_id: number; month: string }) => apiClient.get<ApiResponse<ReportCategoryPoint[]>>('/reports/personal/by-category', { params }),
  familySummary: (params: { family_id: number; month: string }) => apiClient.get<ApiResponse<ReportSummaryResponse>>('/reports/family/summary', { params }),
  familyTrend: (params: { family_id: number; from_month: string; to_month: string }) => apiClient.get<ApiResponse<ReportTrendPoint[]>>('/reports/family/trend', { params }),
  familyByCategory: (params: { family_id: number; month: string }) => apiClient.get<ApiResponse<ReportCategoryPoint[]>>('/reports/family/by-category', { params }),
  familyByMember: (params: { family_id: number; month: string }) => apiClient.get<ApiResponse<ReportMemberPoint[]>>('/reports/family/by-member', { params }),
}
