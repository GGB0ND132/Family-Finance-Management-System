import { AppstoreOutlined, BarChartOutlined, CalculatorOutlined, CreditCardOutlined, DashboardOutlined, DatabaseOutlined, DownOutlined, FileAddOutlined, FileExcelOutlined, LogoutOutlined, SwapOutlined, WalletOutlined } from '@ant-design/icons'
import { Avatar, Button, Dropdown, Layout, Menu, Typography } from 'antd'
import type { MenuProps } from 'antd'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { familyMembers, demoFamilyId } from '../data/financeData'
import { useAuthStore } from '../stores/authStore'

const { Sider, Header, Content } = Layout
const navigationItems: MenuProps['items'] = [
  { key: '/personal', icon: <WalletOutlined />, label: '个人首页' }, { key: '/family-dashboard', icon: <DashboardOutlined />, label: '家庭首页' }, { key: '/transactions', icon: <CreditCardOutlined />, label: '收支流水' }, { key: '/transfers', icon: <SwapOutlined />, label: '账户转账' }, { key: '/budgets', icon: <CalculatorOutlined />, label: '月度预算' }, { type: 'divider' }, { key: '/accounts', icon: <AppstoreOutlined />, label: '账户管理' }, { key: '/categories', icon: <DatabaseOutlined />, label: '分类管理' }, { key: '/reports', icon: <BarChartOutlined />, label: '数据报表' }, { key: '/imports', icon: <FileAddOutlined />, label: '账单导入' }, { key: '/exports', icon: <FileExcelOutlined />, label: '数据导出' },
]

export function AppLayout() {
  const navigate = useNavigate(); const location = useLocation(); const { user, logout } = useAuthStore()
  const userMenu: MenuProps = { items: [{ key: 'logout', icon: <LogoutOutlined />, label: '退出登录' }], onClick: ({ key }) => { if (key === 'logout') { logout(); navigate('/login') } } }
  return <Layout className="app-shell"><Sider breakpoint="lg" collapsedWidth="0" width={232} className="app-sider"><div className="brand-lockup"><span className="brand-mark"><WalletOutlined /></span><span>家账本</span></div><div className="family-switcher"><span className="family-switcher__label">当前家庭</span><strong>晨光家庭</strong><span className="family-switcher__members">{familyMembers.length} 位成员 · {demoFamilyId}</span></div><Menu theme="dark" mode="inline" selectedKeys={[location.pathname]} items={navigationItems} onClick={({ key }) => navigate(key)} /><div className="sider-footer"><span className="sider-footer__avatar">{user?.nickname?.slice(0, 1) ?? '张'}</span><div><strong>{user?.nickname ?? '张三'}</strong><span>{user?.role === 'ADMIN' ? '家庭管理员' : '家庭成员'}</span></div></div></Sider><Layout><Header className="app-header"><Typography.Text className="app-header__title">家庭收支管理系统</Typography.Text><Dropdown menu={userMenu} trigger={['click']}><Button type="text" className="user-trigger"><Avatar size="small">{user?.nickname?.slice(0, 1) ?? '张'}</Avatar><span>{user?.nickname ?? '张三'}</span><DownOutlined /></Button></Dropdown></Header><Content className="app-content"><Outlet /></Content></Layout></Layout>
}
