import { ConfigProvider } from 'antd'
import { Navigate, Route, Routes } from 'react-router-dom'
import './App.css'
import { AppLayout } from './layouts/AppLayout'
import { ProtectedRoute } from './router/ProtectedRoute'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { PersonalPage } from './pages/PersonalPage'
import { FamilyDashboardPage } from './pages/FamilyDashboardPage'
import { TransactionsPage } from './pages/TransactionsPage'
import { TransfersPage } from './pages/TransfersPage'
import { BudgetsPage } from './pages/BudgetsPage'
import { AccountsPage } from './pages/AccountsPage'
import { CategoriesPage } from './pages/CategoriesPage'
import { ReportsPage } from './pages/ReportsPage'
import { ImportsPage } from './pages/ImportsPage'
import { ExportsPage } from './pages/ExportsPage'

export default function App() {
  return <ConfigProvider theme={{ token: { colorPrimary: '#58754d', colorSuccess: '#3f8f62', colorWarning: '#b88426', colorError: '#c85b4b', borderRadius: 6, fontFamily: 'Inter, "PingFang SC", "Microsoft YaHei", ui-sans-serif, system-ui, sans-serif' } }}><Routes><Route path="/login" element={<LoginPage />} /><Route path="/register" element={<RegisterPage />} /><Route element={<ProtectedRoute />}><Route element={<AppLayout />}><Route path="/personal" element={<PersonalPage />} /><Route path="/family-dashboard" element={<FamilyDashboardPage />} /><Route path="/transactions" element={<TransactionsPage />} /><Route path="/transfers" element={<TransfersPage />} /><Route path="/budgets" element={<BudgetsPage />} /><Route path="/accounts" element={<AccountsPage />} /><Route path="/categories" element={<CategoriesPage />} /><Route path="/reports" element={<ReportsPage />} /><Route path="/imports" element={<ImportsPage />} /><Route path="/exports" element={<ExportsPage />} /></Route></Route><Route path="*" element={<Navigate to="/login" replace />} /></Routes></ConfigProvider>
}
