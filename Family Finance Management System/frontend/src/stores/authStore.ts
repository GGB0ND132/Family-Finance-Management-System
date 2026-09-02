import { create } from 'zustand'
import type { AuthUser } from '../api/contracts'
import { demoFamilyId, currentUserId } from '../data/financeData'

interface AuthState { token: string | null; user: AuthUser | null; familyId: string | null; setSession: (token: string, user: AuthUser) => void; logout: () => void }
const tokenKey = 'family-finance-token'

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem(tokenKey), user: localStorage.getItem(tokenKey) ? { id: currentUserId, username: 'zhangsan', nickname: '张三', role: 'ADMIN' } : null, familyId: demoFamilyId,
  setSession: (token, user) => { localStorage.setItem(tokenKey, token); set({ token, user, familyId: demoFamilyId }) },
  logout: () => { localStorage.removeItem(tokenKey); set({ token: null, user: null, familyId: null }) },
}))
