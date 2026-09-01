import {
  ArrowDownOutlined,
  ArrowUpOutlined,
  CalendarOutlined,
  CreditCardOutlined,
  PlusOutlined,
  WalletOutlined,
} from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import type { EChartsOption } from 'echarts'
import { Alert, Button, Card, Col, Dropdown, Progress, Row, Space, Statistic, Table, Typography } from 'antd'
import type { MenuProps, TableColumnsType } from 'antd'
import { useNavigate } from 'react-router-dom'
import {
  accounts,
  categories,
  demoMonth,
  findAccount,
  findCategory,
  formatCurrency,
  trendData,
  type FinanceTransaction,
} from '../data/financeData'
import { useFinanceStore } from '../stores/financeStore'

const currencyFormatter = (value: string | number | undefined) => formatCurrency(Number(value ?? 0))

export function DashboardPage() {
  const navigate = useNavigate()
  const transactions = useFinanceStore((state) => state.transactions)
  const budgets = useFinanceStore((state) => state.budgets)
  const monthTransactions = transactions.filter((transaction) => transaction.occurredAt.startsWith(demoMonth))
  const income = monthTransactions.filter((transaction) => transaction.type === 'income').reduce((sum, transaction) => sum + transaction.amount, 0)
  const expense = monthTransactions.filter((transaction) => transaction.type === 'expense').reduce((sum, transaction) => sum + transaction.amount, 0)
  const assets = accounts.filter((account) => account.balance > 0).reduce((sum, account) => sum + account.balance, 0)
  const totalBudget = budgets.reduce((sum, budget) => sum + budget.amount, 0)
  const budgetPercent = totalBudget ? Math.round((expense / totalBudget) * 100) : 0
  const expenseBreakdown = categories
    .filter((category) => category.type === 'expense')
    .map((category) => ({
      name: category.name,
      value: monthTransactions
        .filter((transaction) => transaction.type === 'expense' && transaction.categoryId === category.id)
        .reduce((sum, transaction) => sum + transaction.amount, 0),
      color: category.color,
    }))
    .filter((item) => item.value > 0)

  const trendOption: EChartsOption = {
    tooltip: { trigger: 'axis', valueFormatter: (value) => formatCurrency(Number(value)) },
    legend: { right: 8, top: 0, textStyle: { color: 'oklch(0.48 0.025 145)' } },
    grid: { left: 6, right: 10, top: 44, bottom: 8, containLabel: true },
    xAxis: { type: 'category', boundaryGap: false, data: trendData.map((item) => item.month), axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: 'oklch(0.48 0.025 145)' } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: 'oklch(0.9 0.015 140)' } }, axisLabel: { color: 'oklch(0.48 0.025 145)', formatter: (value: number) => `${value / 1000}k` } },
    series: [
      { name: '收入', type: 'line', smooth: true, data: trendData.map((item) => item.income), symbol: 'circle', symbolSize: 6, lineStyle: { width: 3, color: 'oklch(0.52 0.105 150)' }, itemStyle: { color: 'oklch(0.52 0.105 150)' }, areaStyle: { color: 'oklch(0.52 0.105 150 / 12%)' } },
      { name: '支出', type: 'line', smooth: true, data: trendData.map((item) => item.expense), symbol: 'circle', symbolSize: 6, lineStyle: { width: 3, color: 'oklch(0.59 0.16 28)' }, itemStyle: { color: 'oklch(0.59 0.16 28)' } },
    ],
  }

  const categoryOption: EChartsOption = {
    tooltip: { trigger: 'item', valueFormatter: (value) => formatCurrency(Number(value)) },
    series: [{ type: 'pie', radius: ['54%', '78%'], center: ['50%', '50%'], label: { show: false }, data: expenseBreakdown.map((item) => ({ value: item.value, name: item.name, itemStyle: { color: item.color } })) }],
  }

  const transactionColumns: TableColumnsType<FinanceTransaction> = [
    { title: '日期', dataIndex: 'occurredAt', width: 104 },
    { title: '分类', render: (_, transaction) => { const category = findCategory(transaction.categoryId); return <Space size={8}><span className="category-dot" style={{ background: category?.color }} /><span>{category?.name ?? '账户转账'}</span></Space> } },
    { title: '账户', render: (_, transaction) => findAccount(transaction.accountId)?.name },
    { title: '金额', align: 'right', render: (_, transaction) => <span className={`amount amount--${transaction.type}`}>{transaction.type === 'expense' ? '-' : '+'}{formatCurrency(transaction.amount)}</span> },
  ]

  const quickMenu: MenuProps = { items: [{ key: 'transaction', icon: <CreditCardOutlined />, label: '新增收支流水' }, { key: 'budget', icon: <CalendarOutlined />, label: '调整本月预算' }], onClick: ({ key }) => navigate(key === 'transaction' ? '/transactions' : '/budgets') }

  return (
    <div className="page dashboard-page">
      <div className="page-heading">
        <div><Typography.Title level={2}>本月概览</Typography.Title><Typography.Text>2026 年 9 月，向阳之家的收支情况</Typography.Text></div>
        <Dropdown menu={quickMenu} trigger={['click']}><Button type="primary" icon={<PlusOutlined />}>快速记一笔</Button></Dropdown>
      </div>
      <Row gutter={[16, 16]} className="summary-grid">
        <Col xs={24} sm={12} xl={6}><Card className="summary-card summary-card--income"><Statistic title="本月收入" value={income} precision={2} formatter={currencyFormatter} prefix={<span className="summary-icon"><ArrowUpOutlined /></span>} /><span className="summary-card__hint">较上月 <b>+12.4%</b></span></Card></Col>
        <Col xs={24} sm={12} xl={6}><Card className="summary-card summary-card--expense"><Statistic title="本月支出" value={expense} precision={2} formatter={currencyFormatter} prefix={<span className="summary-icon"><ArrowDownOutlined /></span>} /><span className="summary-card__hint">较上月 <b>−8.6%</b></span></Card></Col>
        <Col xs={24} sm={12} xl={6}><Card className="summary-card"><Statistic title="本月结余" value={income - expense} precision={2} formatter={currencyFormatter} prefix={<span className="summary-icon"><WalletOutlined /></span>} /><span className="summary-card__hint">收入减去支出</span></Card></Col>
        <Col xs={24} sm={12} xl={6}><Card className="summary-card"><Statistic title="家庭总资产" value={assets} precision={2} formatter={currencyFormatter} prefix={<span className="summary-icon"><CreditCardOutlined /></span>} /><span className="summary-card__hint">含现金与电子账户</span></Card></Col>
      </Row>
      <Row gutter={[16, 16]} className="dashboard-row">
        <Col xs={24} xl={16}><Card className="data-card chart-card" title="近六个月收支趋势" extra={<Button type="link" onClick={() => navigate('/transactions')}>查看流水</Button>}><ReactECharts option={trendOption} style={{ height: 286 }} /></Card></Col>
        <Col xs={24} xl={8}><Card className="data-card budget-card" title="本月预算" extra={<Button type="link" onClick={() => navigate('/budgets')}>管理预算</Button>}><div className="budget-card__main"><div><strong>{formatCurrency(expense)}</strong><span>已使用 / {formatCurrency(totalBudget)}</span></div><Progress type="circle" percent={Math.min(budgetPercent, 100)} strokeColor="oklch(0.52 0.105 150)" trailColor="oklch(0.92 0.018 140)" format={() => `${budgetPercent}%`} /></div><div className="budget-card__divider" /><div className="budget-card__detail"><span>可用余额</span><strong>{formatCurrency(totalBudget - expense)}</strong></div>{budgetPercent >= 80 && <Alert type={budgetPercent > 100 ? 'error' : 'warning'} showIcon message={budgetPercent > 100 ? '本月预算已超支' : '本月预算即将达到上限'} />}</Card></Col>
      </Row>
      <Row gutter={[16, 16]} className="dashboard-row">
        <Col xs={24} lg={14}><Card className="data-card" title="最近流水" extra={<Button type="link" onClick={() => navigate('/transactions')}>查看全部</Button>}><Table rowKey="id" columns={transactionColumns} dataSource={monthTransactions.slice(0, 5)} pagination={false} size="middle" /></Card></Col>
        <Col xs={24} lg={10}><Card className="data-card category-card" title="支出分类"><div className="category-card__body"><ReactECharts option={categoryOption} style={{ width: 180, height: 218 }} /><div className="category-legend">{expenseBreakdown.slice(0, 5).map((item) => <div key={item.name}><span className="category-dot" style={{ background: item.color }} /> <span>{item.name}</span><b>{formatCurrency(item.value)}</b></div>)}</div></div></Card></Col>
      </Row>
    </div>
  )
}
