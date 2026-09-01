export type TransactionType = 'income' | 'expense' | 'transfer'

export interface Account {
  id: string
  name: string
  type: 'cash' | 'bank' | 'alipay' | 'wechat' | 'credit_card'
  balance: number
}

export interface Category {
  id: string
  name: string
  type: 'income' | 'expense'
  color: string
}

export interface FinanceTransaction {
  id: string
  type: TransactionType
  amount: number
  accountId: string
  categoryId?: string
  occurredAt: string
  remark: string
  createdBy: string
}

export interface BudgetItem {
  categoryId: string
  amount: number
}

export const demoMonth = '2026-09'

export const accounts: Account[] = [
  { id: 'account-cash', name: '家庭现金', type: 'cash', balance: 820 },
  { id: 'account-bank', name: '招商银行储蓄卡', type: 'bank', balance: 32480 },
  { id: 'account-alipay', name: '支付宝', type: 'alipay', balance: 1560.5 },
  { id: 'account-wechat', name: '微信钱包', type: 'wechat', balance: 648.2 },
  { id: 'account-credit', name: '招商信用卡', type: 'credit_card', balance: -2380 },
]

export const categories: Category[] = [
  { id: 'salary', name: '工资', type: 'income', color: 'oklch(0.52 0.105 150)' },
  { id: 'bonus', name: '奖金', type: 'income', color: 'oklch(0.61 0.105 160)' },
  { id: 'food', name: '餐饮', type: 'expense', color: 'oklch(0.64 0.13 52)' },
  { id: 'transport', name: '交通', type: 'expense', color: 'oklch(0.6 0.12 235)' },
  { id: 'housing', name: '住房', type: 'expense', color: 'oklch(0.54 0.14 28)' },
  { id: 'shopping', name: '购物', type: 'expense', color: 'oklch(0.65 0.14 335)' },
  { id: 'utilities', name: '水电', type: 'expense', color: 'oklch(0.68 0.13 85)' },
  { id: 'medical', name: '医疗', type: 'expense', color: 'oklch(0.62 0.11 15)' },
  { id: 'entertainment', name: '娱乐', type: 'expense', color: 'oklch(0.61 0.11 290)' },
]

export const initialTransactions: FinanceTransaction[] = [
  { id: 'txn-1', type: 'income', amount: 10800, accountId: 'account-bank', categoryId: 'salary', occurredAt: '2026-09-01', remark: '九月工资', createdBy: '曾志翔' },
  { id: 'txn-2', type: 'expense', amount: 2180, accountId: 'account-bank', categoryId: 'housing', occurredAt: '2026-09-02', remark: '房租', createdBy: '曾志翔' },
  { id: 'txn-3', type: 'expense', amount: 86.5, accountId: 'account-alipay', categoryId: 'food', occurredAt: '2026-09-03', remark: '晚餐', createdBy: '曾志翔' },
  { id: 'txn-4', type: 'expense', amount: 42, accountId: 'account-wechat', categoryId: 'transport', occurredAt: '2026-09-03', remark: '地铁出行', createdBy: '林悦' },
  { id: 'txn-5', type: 'expense', amount: 380, accountId: 'account-credit', categoryId: 'shopping', occurredAt: '2026-09-04', remark: '日用品采购', createdBy: '林悦' },
  { id: 'txn-6', type: 'expense', amount: 268, accountId: 'account-alipay', categoryId: 'utilities', occurredAt: '2026-09-05', remark: '水电燃气', createdBy: '曾志翔' },
  { id: 'txn-7', type: 'income', amount: 1880, accountId: 'account-bank', categoryId: 'bonus', occurredAt: '2026-09-06', remark: '项目奖金', createdBy: '林悦' },
  { id: 'txn-8', type: 'expense', amount: 512, accountId: 'account-wechat', categoryId: 'food', occurredAt: '2026-09-06', remark: '家庭聚餐', createdBy: '林悦' },
]

export const initialBudgets: BudgetItem[] = [
  { categoryId: 'food', amount: 1800 },
  { categoryId: 'transport', amount: 600 },
  { categoryId: 'housing', amount: 2200 },
  { categoryId: 'shopping', amount: 1000 },
  { categoryId: 'utilities', amount: 500 },
  { categoryId: 'medical', amount: 500 },
  { categoryId: 'entertainment', amount: 800 },
]

export const trendData = [
  { month: '4月', income: 9600, expense: 5120 },
  { month: '5月', income: 10400, expense: 6380 },
  { month: '6月', income: 9800, expense: 5740 },
  { month: '7月', income: 11600, expense: 7220 },
  { month: '8月', income: 10300, expense: 4860 },
  { month: '9月', income: 12680, expense: 3468.5 },
]

export const formatCurrency = (value: number) =>
  new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)

export const findCategory = (categoryId?: string) =>
  categories.find((category) => category.id === categoryId)

export const findAccount = (accountId: string) =>
  accounts.find((account) => account.id === accountId)
