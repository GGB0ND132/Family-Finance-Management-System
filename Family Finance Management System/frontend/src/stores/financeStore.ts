import { create } from 'zustand'
import {
  type BudgetItem,
  type FinanceTransaction,
  initialBudgets,
  initialTransactions,
} from '../data/financeData'

export type TransactionDraft = Omit<FinanceTransaction, 'id' | 'createdBy'>

interface FinanceState {
  transactions: FinanceTransaction[]
  budgets: BudgetItem[]
  addTransaction: (transaction: TransactionDraft) => void
  updateBudget: (categoryId: string, amount: number) => void
}

export const useFinanceStore = create<FinanceState>((set) => ({
  transactions: initialTransactions,
  budgets: initialBudgets,
  addTransaction: (transaction) => {
    set((state) => ({
      transactions: [
        {
          ...transaction,
          id: `txn-${crypto.randomUUID()}`,
          createdBy: '曾志翔',
        },
        ...state.transactions,
      ],
    }))
  },
  updateBudget: (categoryId, amount) => {
    set((state) => {
      const existing = state.budgets.find((budget) => budget.categoryId === categoryId)
      if (existing) {
        return {
          budgets: state.budgets.map((budget) =>
            budget.categoryId === categoryId ? { ...budget, amount } : budget,
          ),
        }
      }

      return { budgets: [...state.budgets, { categoryId, amount }] }
    })
  },
}))
