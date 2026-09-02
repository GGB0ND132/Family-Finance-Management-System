import { apiClient } from './client'
export interface ImportPreviewPayload { family_id: string; account_id: string; file_name: string; file_type: 'CSV' | 'XLSX'; mapping: Record<string, string> }
export const importApi = { preview: (payload: ImportPreviewPayload) => apiClient.post('/imports/preview', payload), detail: (id: string) => apiClient.get(`/imports/${id}`), confirm: (id: string) => apiClient.post(`/imports/${id}/confirm`) }
