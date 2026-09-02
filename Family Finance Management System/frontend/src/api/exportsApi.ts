import { apiClient } from './client'
export interface ExportQuery { family_id?: string; scope: 'personal' | 'family'; member_id?: string; from?: string; to?: string; type?: 'INCOME' | 'EXPENSE'; account_id?: string; owner_member_id?: string; beneficiary_member_id?: string; format: 'csv' | 'xlsx' }
export const exportApi = { transactions: (params: ExportQuery) => apiClient.get('/exports/transactions', { params, responseType: 'blob' }) }
