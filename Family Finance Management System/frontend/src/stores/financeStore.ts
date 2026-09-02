import { create } from 'zustand'
import { accounts as seedAccounts, categories as seedCategories, familyMembers, initialBudgets, initialTransactions, initialTransfers, type Account, type Category, type CategoryType, type FinanceTransaction, type FinanceTransfer, type MonthlyBudget } from '../data/financeData'

export type TransactionDraft = Omit<FinanceTransaction, 'id' | 'createdAt'>
export type TransferDraft = Omit<FinanceTransfer, 'id' | 'createdAt'>
export interface ImportDraft { fileName: string; fileType: 'CSV' | 'XLSX'; rows: Array<{ rowNumber: number; date: string; amount: number; direction: CategoryType | null; remark: string; status: 'VALID' | 'INVALID' | 'DUPLICATE'; error?: string }> }

interface FinanceState {
  members: typeof familyMembers
  accounts: Account[]
  categories: Category[]
  transactions: FinanceTransaction[]
  transfers: FinanceTransfer[]
  budgets: MonthlyBudget[]
  imports: Array<ImportDraft & { id: string; status: 'PREVIEW' | 'CONFIRMED' }>
  addTransaction: (draft: TransactionDraft) => void
  updateTransaction: (id: string, draft: TransactionDraft) => void
  deleteTransaction: (id: string) => void
  addTransfer: (draft: TransferDraft) => void
  deleteTransfer: (id: string) => void
  addAccount: (draft: Omit<Account, 'id' | 'currentBalance' | 'closedAt'>) => void
  updateAccount: (id: string, draft: Partial<Pick<Account, 'name' | 'type' | 'ownerMemberId' | 'remark'>>) => void
  removeOrCloseAccount: (id: string) => 'DELETED' | 'CLOSED'
  addCategory: (draft: Omit<Category, 'id' | 'deletedAt'>) => void
  updateCategory: (id: string, draft: Partial<Pick<Category, 'name' | 'color' | 'icon'>>) => void
  removeOrDeleteCategory: (id: string) => 'DELETED' | 'HIDDEN'
  saveBudget: (month: string, totalAmount: number, items: Array<{ categoryId: string; amount: number }>) => void
  copyBudget: (month: string) => void
  addImport: (draft: ImportDraft) => void
  confirmImport: (id: string) => void
}

const now = () => new Date().toISOString()
const accountEffect = (type: CategoryType, amount: number) => type === 'INCOME' ? amount : -amount

export const useFinanceStore = create<FinanceState>((set, get) => ({
  members: familyMembers,
  accounts: seedAccounts.map((account) => ({ ...account })), categories: seedCategories.map((category) => ({ ...category })), transactions: initialTransactions.map((transaction) => ({ ...transaction })), transfers: initialTransfers.map((transfer) => ({ ...transfer })), budgets: initialBudgets.map((budget) => ({ ...budget, items: budget.items.map((item) => ({ ...item })) })), imports: [],
  addTransaction: (draft) => set((state) => ({ transactions: [{ ...draft, id: `txn-${crypto.randomUUID()}`, createdAt: now() }, ...state.transactions], accounts: state.accounts.map((account) => account.id === draft.accountId ? { ...account, currentBalance: account.currentBalance + accountEffect(draft.type, draft.amount) } : account) })),
  updateTransaction: (id, draft) => set((state) => { const old = state.transactions.find((item) => item.id === id); if (!old) return state; return { transactions: state.transactions.map((item) => item.id === id ? { ...draft, id, createdAt: item.createdAt } : item), accounts: state.accounts.map((account) => account.id === old.accountId ? { ...account, currentBalance: account.currentBalance - accountEffect(old.type, old.amount) } : account).map((account) => account.id === draft.accountId ? { ...account, currentBalance: account.currentBalance + accountEffect(draft.type, draft.amount) } : account) } }),
  deleteTransaction: (id) => set((state) => { const target = state.transactions.find((item) => item.id === id); if (!target) return state; return { transactions: state.transactions.filter((item) => item.id !== id), accounts: state.accounts.map((account) => account.id === target.accountId ? { ...account, currentBalance: account.currentBalance - accountEffect(target.type, target.amount) } : account) } }),
  addTransfer: (draft) => set((state) => ({ transfers: [{ ...draft, id: `transfer-${crypto.randomUUID()}`, createdAt: now() }, ...state.transfers], accounts: state.accounts.map((account) => account.id === draft.fromAccountId ? { ...account, currentBalance: account.currentBalance - draft.amount } : account.id === draft.toAccountId ? { ...account, currentBalance: account.currentBalance + draft.amount } : account) })),
  deleteTransfer: (id) => set((state) => { const target = state.transfers.find((item) => item.id === id); if (!target) return state; return { transfers: state.transfers.filter((item) => item.id !== id), accounts: state.accounts.map((account) => account.id === target.fromAccountId ? { ...account, currentBalance: account.currentBalance + target.amount } : account.id === target.toAccountId ? { ...account, currentBalance: account.currentBalance - target.amount } : account) } }),
  addAccount: ({ name, ownerMemberId, type, initialBalance, remark }) => set((state) => ({ accounts: [...state.accounts, { id: `account-${crypto.randomUUID()}`, name, ownerMemberId, type, initialBalance, currentBalance: initialBalance, remark }] })),
  updateAccount: (id, draft) => set((state) => ({ accounts: state.accounts.map((account) => account.id === id ? { ...account, ...draft } : account) })),
  removeOrCloseAccount: (id) => { const hasReferences = get().transactions.some((item) => item.accountId === id) || get().transfers.some((item) => item.fromAccountId === id || item.toAccountId === id); if (hasReferences) { set((state) => ({ accounts: state.accounts.map((account) => account.id === id ? { ...account, closedAt: now() } : account) })); return 'CLOSED' } set((state) => ({ accounts: state.accounts.filter((account) => account.id !== id) })); return 'DELETED' },
  addCategory: (draft) => set((state) => ({ categories: [...state.categories, { ...draft, id: `category-${crypto.randomUUID()}` }] })),
  updateCategory: (id, draft) => set((state) => ({ categories: state.categories.map((category) => category.id === id ? { ...category, ...draft } : category) })),
  removeOrDeleteCategory: (id) => { const hasReferences = get().transactions.some((item) => item.categoryId === id) || get().budgets.some((budget) => budget.items.some((item) => item.categoryId === id)); if (hasReferences) { set((state) => ({ categories: state.categories.map((category) => category.id === id ? { ...category, deletedAt: now() } : category) })); return 'HIDDEN' } set((state) => ({ categories: state.categories.filter((category) => category.id !== id) })); return 'DELETED' },
  saveBudget: (month, totalAmount, items) => set((state) => { const next = { month, totalAmount, items }; const exists = state.budgets.some((budget) => budget.month === month); return { budgets: exists ? state.budgets.map((budget) => budget.month === month ? next : budget) : [...state.budgets, next] } }),
  copyBudget: (month) => set((state) => { const current = new Date(`${month}-01T00:00:00`); current.setMonth(current.getMonth() - 1); const previousMonth = current.toISOString().slice(0, 7); const source = state.budgets.find((budget) => budget.month === previousMonth); if (!source) return state; const next = { month, totalAmount: source.totalAmount, items: source.items.map((item) => ({ ...item })) }; return { budgets: [...state.budgets.filter((budget) => budget.month !== month), next] } }),
  addImport: (draft) => set((state) => ({ imports: [...state.imports, { ...draft, id: `import-${crypto.randomUUID()}`, status: 'PREVIEW' }] })),
  confirmImport: (id) => set((state) => ({ imports: state.imports.map((item) => item.id === id ? { ...item, status: 'CONFIRMED' } : item) })),
}))

export const memberName = (id: string) => familyMembers.find((member) => member.id === id)?.name ?? '未知成员'
