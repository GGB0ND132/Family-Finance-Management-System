export type MemberRole = 'ADMIN' | 'MEMBER'
export type AccountType = 'CASH' | 'BANK_CARD' | 'ALIPAY' | 'WECHAT' | 'CREDIT_CARD' | 'OTHER'
export type CategoryType = 'INCOME' | 'EXPENSE'
export type DataScope = 'personal' | 'family'

export interface FamilyMember { id: string; name: string; role: MemberRole; joinedAt: string; avatar: string }
export interface Account { id: string; ownerMemberId: string; name: string; type: AccountType; initialBalance: number; currentBalance: number; remark: string; closedAt?: string }
export interface Category { id: string; name: string; type: CategoryType; color: string; icon: string; deletedAt?: string }
export interface FinanceTransaction { id: string; accountId: string; categoryId: string; beneficiaryMemberId: string; recorderUserId: string; type: CategoryType; amount: number; occurredAt: string; remark: string; createdAt: string }
export type TransferStatus = 'PENDING_CONFIRM' | 'CONFIRMED'
export interface FinanceTransfer { id: string; fromAccountId: string; toAccountId: string; fromMemberId: string; toMemberId: string; recorderUserId: string; amount: number; occurredAt: string; remark: string; createdAt: string; status?: TransferStatus }
export interface BudgetItem { categoryId: string; amount: number }
export interface MonthlyBudget { month: string; scope: DataScope; memberId?: string; totalAmount: number; items: BudgetItem[] }
export interface ImportRow { rowNumber: number; date: string; amount: number; direction: CategoryType | null; remark: string; status: 'VALID' | 'INVALID' | 'DUPLICATE'; error?: string }
export interface ImportBatch { id: string; fileName: string; fileType: 'CSV' | 'XLSX'; status: 'PREVIEW' | 'CONFIRMED'; rows: ImportRow[] }

export const demoFamilyId = 'family-sunrise'
export const currentUserId = 'member-zhang'
export const demoMonth = '2026-09'
export const today = '2026-09-06'

export const familyMembers: FamilyMember[] = [
  { id: 'member-zhang', name: '张三', role: 'ADMIN', joinedAt: '2026-08-01', avatar: '张' },
  { id: 'member-li', name: '李四', role: 'MEMBER', joinedAt: '2026-08-04', avatar: '李' },
]

export const accounts: Account[] = [
  { id: 'account-cash', ownerMemberId: 'member-zhang', name: '家庭现金', type: 'CASH', initialBalance: 820, currentBalance: 820, remark: '日常零用' },
  { id: 'account-bank', ownerMemberId: 'member-zhang', name: '招商银行储蓄卡', type: 'BANK_CARD', initialBalance: 32480, currentBalance: 32480, remark: '工资卡' },
  { id: 'account-alipay', ownerMemberId: 'member-li', name: '支付宝', type: 'ALIPAY', initialBalance: 1560.5, currentBalance: 1560.5, remark: '线上消费' },
  { id: 'account-wechat', ownerMemberId: 'member-li', name: '微信钱包', type: 'WECHAT', initialBalance: 648.2, currentBalance: 648.2, remark: '' },
  { id: 'account-credit', ownerMemberId: 'member-li', name: '招商信用卡', type: 'CREDIT_CARD', initialBalance: -2380, currentBalance: -2380, remark: '每月 5 日还款' },
]

const active = (id: string, name: string, type: CategoryType, color: string, icon: string): Category => ({ id, name, type, color, icon })
// 默认分类，与后端 families/service.py 中 DEFAULT_CATEGORIES 及 `docs/详细设计.md` 第5.2节一致。
export const categories: Category[] = [
  // 收入分类
  active('borrow', '借入', 'INCOME', '#4E9F6E', '↓'),
  active('collect', '收款', 'INCOME', '#52C41A', '●'),
  active('salary', '工资', 'INCOME', '#1677FF', '¥'),
  active('bonus', '奖金', 'INCOME', '#FA8C16', '✦'),
  // 支出分类
  active('food', '餐饮', 'EXPENSE', '#E07A5F', '🍜'),
  active('stay', '住宿', 'EXPENSE', '#D8956A', '⌂'),
  active('transport', '交通', 'EXPENSE', '#5B8FF9', '🚗'),
  active('housing', '住房', 'EXPENSE', '#F6BD16', '▦'),
  active('shopping', '购物', 'EXPENSE', '#F08BB4', '◇'),
  active('entertainment', '娱乐', 'EXPENSE', '#9270CA', '♪'),
  active('medical', '医疗', 'EXPENSE', '#FF7875', '+'),
  active('lent', '借出', 'EXPENSE', '#73C0DE', '↑'),
  active('repay', '还款', 'EXPENSE', '#8C8C8C', '↻'),
]

export const initialTransactions: FinanceTransaction[] = [
  { id: 'txn-1', accountId: 'account-bank', categoryId: 'salary', beneficiaryMemberId: 'member-zhang', recorderUserId: 'member-zhang', type: 'INCOME', amount: 10800, occurredAt: '2026-09-01T09:00:00+08:00', remark: '九月工资', createdAt: '2026-09-01T09:00:00+08:00' },
  { id: 'txn-2', accountId: 'account-bank', categoryId: 'housing', beneficiaryMemberId: 'member-zhang', recorderUserId: 'member-zhang', type: 'EXPENSE', amount: 2180, occurredAt: '2026-09-02T10:00:00+08:00', remark: '房租', createdAt: '2026-09-02T10:00:00+08:00' },
  { id: 'txn-3', accountId: 'account-alipay', categoryId: 'food', beneficiaryMemberId: 'member-li', recorderUserId: 'member-zhang', type: 'EXPENSE', amount: 86.5, occurredAt: '2026-09-03T19:00:00+08:00', remark: '晚餐', createdAt: '2026-09-03T19:00:00+08:00' },
  { id: 'txn-4', accountId: 'account-wechat', categoryId: 'transport', beneficiaryMemberId: 'member-li', recorderUserId: 'member-li', type: 'EXPENSE', amount: 42, occurredAt: '2026-09-03T08:00:00+08:00', remark: '地铁出行', createdAt: '2026-09-03T08:00:00+08:00' },
  { id: 'txn-5', accountId: 'account-credit', categoryId: 'shopping', beneficiaryMemberId: 'member-li', recorderUserId: 'member-li', type: 'EXPENSE', amount: 380, occurredAt: '2026-09-04T15:00:00+08:00', remark: '日用品采购', createdAt: '2026-09-04T15:00:00+08:00' },
  { id: 'txn-6', accountId: 'account-alipay', categoryId: 'utilities', beneficiaryMemberId: 'member-li', recorderUserId: 'member-zhang', type: 'EXPENSE', amount: 268, occurredAt: '2026-09-05T11:00:00+08:00', remark: '水电燃气', createdAt: '2026-09-05T11:00:00+08:00' },
  { id: 'txn-7', accountId: 'account-bank', categoryId: 'bonus', beneficiaryMemberId: 'member-zhang', recorderUserId: 'member-li', type: 'INCOME', amount: 1880, occurredAt: '2026-09-06T09:00:00+08:00', remark: '项目奖金', createdAt: '2026-09-06T09:00:00+08:00' },
  { id: 'txn-8', accountId: 'account-wechat', categoryId: 'food', beneficiaryMemberId: 'member-li', recorderUserId: 'member-li', type: 'EXPENSE', amount: 512, occurredAt: '2026-09-06T13:00:00+08:00', remark: '家庭聚餐', createdAt: '2026-09-06T13:00:00+08:00' },
]

export const initialTransfers: FinanceTransfer[] = [{ id: 'transfer-1', fromAccountId: 'account-bank', toAccountId: 'account-alipay', fromMemberId: 'member-zhang', toMemberId: 'member-li', recorderUserId: 'member-zhang', amount: 500, occurredAt: '2026-09-02T12:00:00+08:00', remark: '给李四本月生活费', createdAt: '2026-09-02T12:00:00+08:00' }]
export const initialBudgets: MonthlyBudget[] = [{ scope: 'family', month: '2026-08', totalAmount: 7800, items: [{ categoryId: 'food', amount: 1600 }, { categoryId: 'transport', amount: 600 }, { categoryId: 'housing', amount: 2200 }, { categoryId: 'shopping', amount: 900 }, { categoryId: 'utilities', amount: 500 }, { categoryId: 'entertainment', amount: 800 }] }, { scope: 'family', month: '2026-09', totalAmount: 7400, items: [{ categoryId: 'food', amount: 1800 }, { categoryId: 'transport', amount: 600 }, { categoryId: 'housing', amount: 2200 }, { categoryId: 'shopping', amount: 1000 }, { categoryId: 'utilities', amount: 500 }, { categoryId: 'entertainment', amount: 800 }] }]
export const trendData = [{ month: '4月', income: 9600, expense: 5120 }, { month: '5月', income: 10400, expense: 6380 }, { month: '6月', income: 9800, expense: 5740 }, { month: '7月', income: 11600, expense: 7220 }, { month: '8月', income: 10300, expense: 4860 }, { month: '9月', income: 12680, expense: 3468.5 }]
export const formatCurrency = (value: number) => new Intl.NumberFormat('zh-CN', { style: 'currency', currency: 'CNY', minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(value)
export const formatDateTime = (value: string) => value ? new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false, timeZone: 'Asia/Shanghai' }).format(new Date(value)).replace(/\//g, '-') : '-'
export const getCategory = (id?: string, source: Category[] = categories) => source.find((item) => item.id === id)
export const getAccount = (id?: string, source: Account[] = accounts) => source.find((item) => item.id === id)
export const getMember = (id?: string, source: FamilyMember[] = familyMembers) => source.find((item) => item.id === id)
