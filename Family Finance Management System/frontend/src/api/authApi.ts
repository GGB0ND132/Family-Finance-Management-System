import { apiClient } from './client'
import type { LoginPayload, RegisterPayload } from './contracts'

export const authApi = {
  login: (payload: LoginPayload) => apiClient.post('/auth/login', payload),
  register: (payload: RegisterPayload) => apiClient.post('/auth/register', payload),
  me: () => apiClient.get('/users/me'),
  changePassword: (payload: { old_password: string; new_password: string }) => apiClient.patch('/users/me/password', payload),
}
