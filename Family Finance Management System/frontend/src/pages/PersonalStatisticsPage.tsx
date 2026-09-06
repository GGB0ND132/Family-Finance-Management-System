import { BarChartOutlined } from '@ant-design/icons'
import { Card, Col, Progress, Row, Space, Statistic, Typography } from 'antd'
import { useMemo } from 'react'
import { formatCurrency } from '../data/financeData'
import { useAuthStore } from '../stores/authStore'
import { useFinanceStore } from '../stores/financeStore'

export function PersonalStatisticsPage() {
  const user = useAuthStore((state) => state.user)
  const { transactions, accounts, categories } = useFinanceStore()
  const memberId = user?.id ?? 'member-zhang'
  const personalTransactions = transactions.filter((item) => item.beneficiaryMemberId === memberId)
  const income = personalTransactions.filter((item) => item.type === 'INCOME').reduce((sum, item) => sum + item.amount, 0)
  const expense = personalTransactions.filter((item) => item.type === 'EXPENSE').reduce((sum, item) => sum + item.amount, 0)
  const assets = accounts.filter((account) => account.ownerMemberId === memberId && !account.closedAt).reduce((sum, account) => sum + account.currentBalance, 0)
  const breakdown = useMemo(() => categories.filter((category) => category.type === 'EXPENSE' && !category.deletedAt).map((category) => ({ ...category, amount: personalTransactions.filter((item) => item.type === 'EXPENSE' && item.categoryId === category.id).reduce((sum, item) => sum + item.amount, 0) })).filter((category) => category.amount > 0).sort((left, right) => right.amount - left.amount), [categories, personalTransactions])
  return <div className="page"><div className="page-heading"><div><Typography.Title level={2}>个人流水统计</Typography.Title><Typography.Text>按当前用户的资金归属人查看个人收入、支出、结余和资产。</Typography.Text></div><BarChartOutlined style={{ fontSize: 32 }} /></div><Row gutter={[16, 16]}><Col xs={24} sm={12} xl={6}><Card className="summary-card summary-card--income"><Statistic title="个人收入" value={income} formatter={(value) => formatCurrency(Number(value))} /></Card></Col><Col xs={24} sm={12} xl={6}><Card className="summary-card summary-card--expense"><Statistic title="个人支出" value={expense} formatter={(value) => formatCurrency(Number(value))} /></Card></Col><Col xs={24} sm={12} xl={6}><Card className="summary-card"><Statistic title="个人结余" value={income - expense} formatter={(value) => formatCurrency(Number(value))} /></Card></Col><Col xs={24} sm={12} xl={6}><Card className="summary-card"><Statistic title="个人资产" value={assets} formatter={(value) => formatCurrency(Number(value))} /></Card></Col></Row><Card className="data-card" title="支出分类统计"><Space direction="vertical" className="full-width">{breakdown.length ? breakdown.map((category) => <div className="report-category-row" key={category.id}><span>{category.icon} {category.name}</span><Space><Progress percent={expense ? Math.round(category.amount / expense * 100) : 0} showInfo={false} style={{ width: 140 }} /><strong>{formatCurrency(category.amount)}</strong></Space></div>) : <Typography.Text type="secondary">暂无个人支出数据</Typography.Text>}</Space></Card></div>
}