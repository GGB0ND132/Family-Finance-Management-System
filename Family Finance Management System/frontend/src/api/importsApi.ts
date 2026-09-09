import { apiClient } from './client'
export interface ImportPreviewPayload { family_id: number; scope: 'personal' | 'family'; account_id: number; file: File; mapping?: Record<string, string> }
export const importApi = {
  preview: (payload: ImportPreviewPayload) => {
    const form = new FormData()
    form.append('family_id', String(payload.family_id)); form.append('scope', payload.scope); form.append('account_id', String(payload.account_id)); form.append('file', payload.file)
    form.append('field_mapping_json', JSON.stringify(payload.mapping ?? {}))
    return apiClient.post('/imports/preview', form, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
  detail: (id: number | string) => apiClient.get(`/imports/${id}`),
  confirm: (id: number | string) => apiClient.post(`/imports/${id}/confirm`),
}
