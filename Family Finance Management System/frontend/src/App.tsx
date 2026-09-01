import { ConfigProvider } from 'antd'
import { Navigate, Route, Routes } from 'react-router-dom'
import './App.css'
import { AppLayout } from './layouts/AppLayout'
import { BudgetsPage } from './pages/BudgetsPage'
import { DashboardPage } from './pages/DashboardPage'
import { LoginPage } from './pages/LoginPage'
import { TransactionsPage } from './pages/TransactionsPage'

function App() {
  return (
    <ConfigProvider theme={{ token: { colorPrimary: 'oklch(0.38 0.075 135)', colorInfo: 'oklch(0.43 0.09 145)', colorSuccess: 'oklch(0.52 0.105 150)', colorWarning: 'oklch(0.7 0.13 76)', colorError: 'oklch(0.59 0.16 28)', borderRadius: 6, fontFamily: 'Inter, "PingFang SC", "Microsoft YaHei", ui-sans-serif, system-ui, sans-serif' } }}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/transactions" element={<TransactionsPage />} />
          <Route path="/budgets" element={<BudgetsPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </ConfigProvider>
  )
}

export default App
