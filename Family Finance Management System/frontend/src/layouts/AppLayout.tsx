import { AppstoreOutlined, BarChartOutlined, CalculatorOutlined, CreditCardOutlined, DashboardOutlined, DatabaseOutlined, DownOutlined, FileAddOutlined, FileExcelOutlined, LogoutOutlined, SettingOutlined, SwapOutlined, UserOutlined, WalletOutlined } from '@ant-design/icons'
import { Avatar, Button, Dropdown, Layout, Menu, Typography } from 'antd'
import type { MenuProps } from 'antd'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { familyApi } from '../api/familiesApi'
import type { FamilySummary } from '../api/contracts'
import { useAuthStore } from '../stores/authStore'

const { Sider, Header, Content } = Layout
const navigationItems: MenuProps['items'] = [
  { key: '/home', icon: <DashboardOutlined />, label: '首页' }, { key: '/transactions', icon: <CreditCardOutlined />, label: '收支流水' }, { key: '/transfers', icon: <SwapOutlined />, label: '账户转账' }, { key: '/budgets', icon: <CalculatorOutlined />, label: '月度预算' }, { type: 'divider' }, { key: '/accounts', icon: <AppstoreOutlined />, label: '账户管理' }, { key: '/categories', icon: <DatabaseOutlined />, label: '分类管理' }, { key: '/reports', icon: <BarChartOutlined />, label: '数据报表' }, { key: '/imports', icon: <FileAddOutlined />, label: '账单导入' }, { key: '/exports', icon: <FileExcelOutlined />, label: '数据导出' }, { key: '/family', icon: <SettingOutlined />, label: '家庭设置' },
]

export function AppLayout() {
  const navigate = useNavigate(); const location = useLocation(); const { user, familyId, logout } = useAuthStore(); const [families, setFamilies] = useState<FamilySummary[]>([])
  useEffect(() => { familyApi.list().then((response) => { const result = response.data; setFamilies(result.data ?? []) }).catch(() => setFamilies([])) }, [familyId])
  const currentFamily = families.find((family) => String(family.id) === familyId)
  const userMenu: MenuProps = { items: [{ key: 'statistics', icon: <BarChartOutlined />, label: '个人流水统计' }, { key: 'profile', icon: <UserOutlined />, label: '个人信息设置' }, { type: 'divider' }, { key: 'logout', icon: <LogoutOutlined />, label: '退出登录' }], onClick: ({ key }) => { if (key === 'statistics') navigate('/profile/statistics'); if (key === 'profile') navigate('/profile/settings'); if (key === 'logout') { logout(); navigate('/login') } } }
  const selectedPath = location.pathname === '/personal' || location.pathname === '/family-dashboard' ? '/home' : location.pathname
  return <Layout className="app-shell"><Sider breakpoint="lg" collapsedWidth="0" width={232} className="app-sider"><div className="brand-lockup"><span className="brand-mark"><WalletOutlined /></span><span>家账本</span></div><div className="family-switcher"><span className="family-switcher__label">当前家庭</span><strong>{currentFamily?.name ?? '未选择家庭'}</strong><span className="family-switcher__members">{currentFamily ? `${currentFamily.members_count} 位成员 · #${currentFamily.id}` : '请先创建或加入家庭'}</span></div><Menu theme="dark" mode="inline" selectedKeys={[selectedPath]} items={navigationItems} onClick={({ key }) => navigate(key)} /></Sider><Layout><Header className="app-header"><Typography.Text className="app-header__title">家庭收支管理系统</Typography.Text><Dropdown menu={userMenu} trigger={['click']}><Button type="text" className="user-trigger"><Avatar size="small" src={user?.avatar}>{user?.nickname?.slice(0, 1) ?? '?'}</Avatar><span>{user?.nickname ?? '未登录'}</span><DownOutlined /></Button></Dropdown></Header><Content className="app-content"><Outlet /></Content></Layout></Layout>
}
