import axios from 'axios'
import { useAuthStore } from '../stores/authStore'

export const apiClient = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api/v1', timeout: 10000, headers: { 'Content-Type': 'application/json' } })

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  const familyId = useAuthStore.getState().familyId
  if (token) config.headers.Authorization = `Bearer ${token}`
  if (familyId) config.headers['X-Family-Id'] = familyId
  return config
})

apiClient.interceptors.response.use((response) => response, (error: unknown) => {
  if (axios.isAxiosError(error) && error.response?.status === 401) useAuthStore.getState().logout()
  return Promise.reject(error)
})
