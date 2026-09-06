import type { Account, AccountType, Category, CategoryType, FamilyMember } from '../data/financeData'
<<<<<<< HEAD

export interface ApiResponse<T> {
  code: number
  message: string
  data: T | null
  request_id?: string
}

export interface PageData<T> {
  items: T[]
  page: number
  page_size: number
  total: number
}

export interface AuthUser {
  id: string
  username: string
  nickname: string
  role?: 'ADMIN' | 'MEMBER'
}

export interface AuthTokenResponse {
  access_token: string
  token_type: 'bearer'
  user: AuthUser
}

export interface RegisterPayload {
  username: string
  password: string
  nickname: string
}

export interface LoginPayload {
  username: string
  password: string
}

export interface FamilySummary {
  id: string
  name: string
  owner_id: string
  members_count: number
}

export interface AccountResponse extends Account {
  owner_member?: FamilyMember
}

/** 后端 CategoryOut 的 TypeScript 契约（后端返回 snake_case，前端映射为 camelCase）。 */
export interface CategoryResponse {
  id: number
  family_id: number
  name: string
  type: CategoryType
  icon: string | null
  color: string | null
  deleted_at: string | null
  created_at: string
  updated_at: string
}

export interface TransactionQuery {
  family_id?: string
  page?: number
  page_size?: number
  from?: string
  to?: string
  type?: CategoryType
  account_id?: string
  owner_member_id?: string
  category_id?: string
  beneficiary_member_id?: string
  recorder_user_id?: string
  min_amount?: number
  max_amount?: number
}

export interface AccountPayload {
  family_id: string
  owner_member_id: string
  name: string
  type: AccountType
  initial_balance: number
  remark?: string
}
=======
export interface ApiResponse<T> { code: number; message: string; data: T | null; request_id?: string }
export interface AuthUser { id: string; username: string; nickname: string; real_name?: string; avatar?: string; role?: 'ADMIN' | 'MEMBER' }
export interface AuthTokenResponse { access_token: string; token_type: 'bearer'; user: AuthUser }
export interface RegisterPayload { username: string; password: string; nickname: string }
export interface LoginPayload { username: string; password: string }
export interface FamilySummary { id: string; name: string; owner_id: string; members_count: number; invite_code?: string; invite_expires_at?: string }
export interface FamilyMemberResponse { id: string; user_id: string; family_id: string; name: string; username?: string; role: 'ADMIN' | 'MEMBER'; joined_at: string }
export interface AccountResponse extends Account { owner_member?: FamilyMember }
export type CategoryResponse = Category
export interface TransactionQuery { family_id?: string; page?: number; page_size?: number; from?: string; to?: string; type?: CategoryType; account_id?: string; owner_member_id?: string; category_id?: string; beneficiary_member_id?: string; recorder_user_id?: string; min_amount?: number; max_amount?: number }
export interface AccountPayload { family_id: string; owner_member_id: string; name: string; type: AccountType; initial_balance: number; remark?: string }
>>>>>>> 71adfd3 (新增个人统计，家庭，个人资料页面，优化前端样式和api调用)
