import { create } from 'zustand'
import type { AuthUser } from '../api/contracts'

interface AuthState { token: string | null; user: AuthUser | null; familyId: string | null; setSession: (token: string, user: AuthUser, familyId?: string | null) => void; updateUser: (user: AuthUser) => void; setFamily: (familyId: string | null) => void; logout: () => void }
const tokenKey = 'family-finance-token'
const userKey = 'family-finance-user'
const familyKey = 'family-finance-family'

const storedUser = localStorage.getItem(userKey)

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem(tokenKey),
  user: storedUser ? JSON.parse(storedUser) as AuthUser : null,
  familyId: localStorage.getItem(familyKey),
  setSession: (token, user, familyId = null) => {
    localStorage.setItem(tokenKey, token)
    localStorage.setItem(userKey, JSON.stringify(user))
    if (familyId) localStorage.setItem(familyKey, familyId)
    set({ token, user, familyId })
  },
  updateUser: (user) => { localStorage.setItem(userKey, JSON.stringify(user)); set({ user }) },
  setFamily: (familyId) => {
    if (familyId) localStorage.setItem(familyKey, familyId)
    else localStorage.removeItem(familyKey)
    set({ familyId })
  },
  logout: () => { localStorage.removeItem(tokenKey); localStorage.removeItem(userKey); localStorage.removeItem(familyKey); set({ token: null, user: null, familyId: null }) },
}))
