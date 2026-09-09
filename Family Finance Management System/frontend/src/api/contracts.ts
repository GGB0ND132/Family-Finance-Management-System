import type { AccountType, CategoryType } from '../data/financeData'

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
  id: number | string
  username: string
  nickname: string
  role?: 'ADMIN' | 'MEMBER'
  real_name?: string
  avatar?: string
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
  invite_code?: string
  invite_expires_at?: string
}

export interface FamilyMemberResponse {
  id: number | string
  user_id: number | string
  family_id: number | string
  name?: string
  nickname?: string
  avatar?: string | null
  username?: string
  role: 'ADMIN' | 'MEMBER'
  joined_at: string
}

export interface AccountResponse {
  id: number
  family_id: number
  owner_member_id: number
  owner_nickname: string | null
  name: string
  type: AccountType
  initial_balance: string
  current_balance: string
  remark: string | null
  closed_at: string | null
  created_at: string
  updated_at: string | null
}

/**
 * 后端分类接口返回的数据结构。
 */
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
  scope?: 'personal' | 'family'
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
  min_amount?: string
  max_amount?: string
}

export interface TransactionResponse {
  id: number
  family_id: number
  account_id: number
  category_id: number
  beneficiary_member_id: number
  recorder_user_id: number
  type: CategoryType
  amount: string
  occurred_at: string
  remark: string | null
  created_at: string
  account_name: string | null
  account_owner_member_id: number | null
  account_owner_nickname: string | null
  account_current_balance: string | null
  category_name: string | null
  category_type: CategoryType | null
  beneficiary_nickname: string | null
  recorder_nickname: string | null
  status?: 'PENDING_CONFIRM' | 'CONFIRMED'
  pending_update?: { account_id?: number; category_id?: number; beneficiary_member_id?: number; amount?: string; occurred_at?: string; remark?: string }
}

export interface TransferResponse {
  id: number
  family_id: number
  from_account_id: number
  to_account_id: number
  from_member_id: number
  to_member_id: number
  recorder_user_id: number
  amount: string
  occurred_at: string
  remark: string | null
  created_at: string
  from_account_name: string | null
  to_account_name: string | null
  from_member_nickname: string | null
  to_member_nickname: string | null
  recorder_nickname: string | null
  status: 'PENDING_CONFIRM' | 'CONFIRMED'
}

export interface AccountPayload {
  family_id: number
  owner_member_id: number
  name: string
  type: AccountType
  initial_balance: string
  remark?: string
}

export interface BudgetCategoryExecution {
  category_id: number
  amount: string
  used_amount: string
  remaining_amount: string
  usage_rate: string
}

export interface BudgetResponse {
  id: number
  family_id: number
  month: string
  scope: 'personal' | 'family'
  total_amount: string
  used_amount: string
  remaining_amount: string
  usage_rate: string
  warning_level: 'NORMAL' | 'WARNING' | 'OVERSPENT'
  categories: BudgetCategoryExecution[]
}

export interface ReportSummaryResponse {
  month?: string
  date?: string
  income: string
  expense: string
  balance: string
  assets?: string
  transfer_in?: string
  transfer_out?: string
}

export interface ReportTrendPoint { month: string; income: string; expense: string }
export interface ReportCategoryPoint { category_id: number; category_name: string; amount: string; percentage: string }
export interface ReportMemberPoint { member_id: number; member_name: string; income: string; expense: string; assets?: string; transfer_in?: string; transfer_out?: string }
