import type { Account, AccountType, Category, CategoryType, FamilyMember } from '../data/financeData'
export interface ApiResponse<T> { code: number; message: string; data: T | null; request_id?: string }
export interface AuthUser { id: string; username: string; nickname: string; role?: 'ADMIN' | 'MEMBER' }
export interface AuthTokenResponse { access_token: string; token_type: 'bearer'; user: AuthUser }
export interface RegisterPayload { username: string; password: string; nickname: string }
export interface LoginPayload { username: string; password: string }
export interface FamilySummary { id: string; name: string; owner_id: string; members_count: number }
export interface AccountResponse extends Account { owner_member?: FamilyMember }
export type CategoryResponse = Category
export interface TransactionQuery { family_id?: string; page?: number; page_size?: number; from?: string; to?: string; type?: CategoryType; account_id?: string; owner_member_id?: string; category_id?: string; beneficiary_member_id?: string; recorder_user_id?: string; min_amount?: number; max_amount?: number }
export interface AccountPayload { family_id: string; owner_member_id: string; name: string; type: AccountType; initial_balance: number; remark?: string }
