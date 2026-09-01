import {
  BellOutlined,
  CalculatorOutlined,
  CreditCardOutlined,
  DashboardOutlined,
  DownOutlined,
  LogoutOutlined,
  WalletOutlined,
} from '@ant-design/icons'
import { Avatar, Badge, Button, Dropdown, Layout, Menu, Space, Typography } from 'antd'
import type { MenuProps } from 'antd'
import { useLocation, useNavigate, Outlet } from 'react-router-dom'

const { Sider, Header, Content } = Layout

const navigationItems: MenuProps['items'] = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: '首页仪表盘' },
  { key: '/transactions', icon: <CreditCardOutlined />, label: '收支流水' },
  { key: '/budgets', icon: <CalculatorOutlined />, label: '月度预算' },
]

export function AppLayout() {
  const navigate = useNavigate()
  const location = useLocation()

  const userMenu: MenuProps = {
    items: [
      { key: 'logout', icon: <LogoutOutlined />, label: '退出登录' },
    ],
    onClick: ({ key }) => {
      if (key === 'logout') {
        navigate('/login')
      }
    },
  }

  return (
    <Layout className="app-shell">
      <Sider breakpoint="lg" collapsedWidth="0" width={232} className="app-sider">
        <div className="brand-lockup" aria-label="家账本">
          <span className="brand-mark"><WalletOutlined /></span>
          <span>家账本</span>
        </div>
        <div className="family-switcher">
          <span className="family-switcher__label">当前家庭</span>
          <strong>向阳之家</strong>
          <span className="family-switcher__members">2 位成员</span>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={navigationItems}
          onClick={({ key }) => navigate(key)}
        />
        <div className="sider-footer">
          <span className="sider-footer__avatar">曾</span>
          <div>
            <strong>曾志翔</strong>
            <span>家庭管理员</span>
          </div>
        </div>
      </Sider>
      <Layout>
        <Header className="app-header">
          <Typography.Text className="app-header__title">家庭收支管理系统</Typography.Text>
          <Space size={18}>
            <Badge dot color="oklch(0.59 0.16 28)">
              <Button type="text" shape="circle" aria-label="查看通知" icon={<BellOutlined />} />
            </Badge>
            <Dropdown menu={userMenu} trigger={['click']}>
              <Button type="text" className="user-trigger">
                <Avatar size="small">曾</Avatar>
                <span>曾志翔</span>
                <DownOutlined />
              </Button>
            </Dropdown>
          </Space>
        </Header>
        <Content className="app-content">
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
