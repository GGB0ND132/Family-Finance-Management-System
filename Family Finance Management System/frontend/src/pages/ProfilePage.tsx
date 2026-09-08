import { BarChartOutlined, SaveOutlined, UserOutlined } from '@ant-design/icons'
import { Avatar, Button, Card, Col, Divider, Form, Input, Progress, Row, Space, Statistic, Tag, Typography, message } from 'antd'
import { useEffect, useMemo } from 'react'
import { formatCurrency } from '../data/financeData'
import { authApi } from '../api/authApi'
import type { ApiResponse, AuthUser } from '../api/contracts'
import { useAuthStore } from '../stores/authStore'
import { useFinanceStore } from '../stores/financeStore'

interface ProfileForm { nickname: string; real_name?: string; avatar?: string }

export function ProfilePage() {
  const [form] = Form.useForm<ProfileForm>()
  const [api, holder] = message.useMessage()
  const { user, updateUser } = useAuthStore()
  const { transactions, accounts, categories } = useFinanceStore()
  const memberId = user?.id ? String(user.id) : ''
  const personalTransactions = transactions.filter((item) => item.beneficiaryMemberId === memberId)
  const income = personalTransactions.filter((item) => item.type === 'INCOME').reduce((sum, item) => sum + item.amount, 0)
  const expense = personalTransactions.filter((item) => item.type === 'EXPENSE').reduce((sum, item) => sum + item.amount, 0)
  const assets = accounts.filter((account) => account.ownerMemberId === memberId && !account.closedAt).reduce((sum, account) => sum + account.currentBalance, 0)
  const breakdown = useMemo(() => categories.filter((category) => category.type === 'EXPENSE').map((category) => ({ ...category, amount: personalTransactions.filter((item) => item.type === 'EXPENSE' && item.categoryId === category.id).reduce((sum, item) => sum + item.amount, 0) })).filter((category) => category.amount > 0).sort((left, right) => right.amount - left.amount), [categories, personalTransactions])
  useEffect(() => { form.setFieldsValue({ nickname: user?.nickname, real_name: user?.real_name, avatar: user?.avatar }) }, [form, user])
  const saveProfile = async (values: ProfileForm) => {
    let nextUser = { ...user, ...values } as AuthUser
    const response = await authApi.updateProfile({ nickname: values.nickname, real_name: values.real_name, avatar: values.avatar }); const result = response.data as ApiResponse<AuthUser>; nextUser = result.data ?? nextUser
    updateUser(nextUser)
    api.success('个人信息已保存')
  }
  return <div className="page">{holder}<div className="page-heading"><div><Typography.Title level={2}>个人中心</Typography.Title><Typography.Text>查看个人流水统计，并维护你的头像与基本资料。</Typography.Text></div><Avatar size={52} src={user?.avatar}>{user?.nickname?.slice(0, 1) ?? <UserOutlined />}</Avatar></div><Row gutter={[16, 16]} id="statistics"><Col xs={24} sm={12} xl={6}><Card className="summary-card summary-card--income"><Statistic title="个人收入" value={income} formatter={(value) => formatCurrency(Number(value))} /></Card></Col><Col xs={24} sm={12} xl={6}><Card className="summary-card summary-card--expense"><Statistic title="个人支出" value={expense} formatter={(value) => formatCurrency(Number(value))} /></Card></Col><Col xs={24} sm={12} xl={6}><Card className="summary-card"><Statistic title="个人结余" value={income - expense} formatter={(value) => formatCurrency(Number(value))} /></Card></Col><Col xs={24} sm={12} xl={6}><Card className="summary-card"><Statistic title="个人资产" value={assets} formatter={(value) => formatCurrency(Number(value))} /></Card></Col></Row><Row gutter={[16, 16]}><Col xs={24} lg={13}><Card className="data-card" title={<Space><BarChartOutlined />支出分类统计</Space>}><Space direction="vertical" className="full-width">{breakdown.length ? breakdown.map((category) => <div className="report-category-row" key={category.id}><span>{category.icon} {category.name}</span><Space><Progress percent={expense ? Math.round(category.amount / expense * 100) : 0} showInfo={false} style={{ width: 120 }} /><strong>{formatCurrency(category.amount)}</strong></Space></div>) : <Typography.Text type="secondary">暂无个人支出数据</Typography.Text>}</Space></Card></Col><Col xs={24} lg={11}><Card className="data-card" title="个人资料设置" id="settings"><Form form={form} layout="vertical" onFinish={saveProfile}><Form.Item label="头像地址" name="avatar" extra="填写图片地址后将作为个人头像显示"><Input placeholder="https://..." /></Form.Item><Form.Item label="昵称" name="nickname" rules={[{ required: true, message: '请输入昵称' }]}><Input /></Form.Item><Form.Item label="真实姓名" name="real_name"><Input placeholder="请输入真实姓名" /></Form.Item><Divider /><Typography.Text type="secondary">登录用户名：{user?.username ?? '未设置'} <Tag>{user?.role === 'ADMIN' ? '管理员' : '成员'}</Tag></Typography.Text><Button type="primary" htmlType="submit" icon={<SaveOutlined />} block style={{ marginTop: 20 }}>保存个人信息</Button></Form></Card></Col></Row><Card className="data-card" title="数据口径"><Typography.Text>个人收入、支出按资金归属人统计；个人资产按本人未销户账户余额统计，内部转账不计入收支。</Typography.Text></Card></div>
}
