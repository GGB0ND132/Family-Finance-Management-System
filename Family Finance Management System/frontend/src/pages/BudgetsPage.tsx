import { CheckCircleFilled, EditOutlined, ExclamationCircleFilled, PlusOutlined, WarningFilled } from '@ant-design/icons'
import { Alert, Button, Card, Col, InputNumber, Progress, Row, Space, Statistic, Tag, Typography, message } from 'antd'
import { useMemo, useState } from 'react'
import { categories, demoMonth, formatCurrency } from '../data/financeData'
import { useFinanceStore } from '../stores/financeStore'

export function BudgetsPage() {
  const [editing, setEditing] = useState(false)
  const [draftBudgets, setDraftBudgets] = useState<Record<string, number>>({})
  const [messageApi, messageContext] = message.useMessage()
  const budgets = useFinanceStore((state) => state.budgets)
  const transactions = useFinanceStore((state) => state.transactions)
  const updateBudget = useFinanceStore((state) => state.updateBudget)
  const expenseCategories = categories.filter((category) => category.type === 'expense')
  const budgetedItems = expenseCategories.map((category) => ({ category, amount: budgets.find((budget) => budget.categoryId === category.id)?.amount ?? 0 }))
  const categorySpending = useMemo(() => Object.fromEntries(expenseCategories.map((category) => [category.id, transactions.filter((transaction) => transaction.type === 'expense' && transaction.categoryId === category.id && transaction.occurredAt.startsWith(demoMonth)).reduce((sum, transaction) => sum + transaction.amount, 0)])), [expenseCategories, transactions])
  const totalBudget = budgetedItems.reduce((sum, item) => sum + item.amount, 0)
  const totalSpent = Object.values(categorySpending).reduce((sum, amount) => sum + amount, 0)
  const atRisk = budgetedItems.filter((item) => item.amount > 0 && (categorySpending[item.category.id] / item.amount) >= 0.8)

  const startEditing = () => {
    setDraftBudgets(Object.fromEntries(budgetedItems.map((item) => [item.category.id, item.amount])))
    setEditing(true)
  }

  const saveBudgets = () => {
    Object.entries(draftBudgets).forEach(([categoryId, amount]) => updateBudget(categoryId, amount))
    setEditing(false)
    messageApi.success('本月预算已保存')
  }

  return (
    <div className="page budgets-page">
      {messageContext}
      <div className="page-heading">
        <div><Typography.Title level={2}>月度预算</Typography.Title><Typography.Text>管理 2026 年 9 月的分类支出上限，系统会在使用率达到 80% 时提醒。</Typography.Text></div>
        {editing ? <Space><Button onClick={() => setEditing(false)}>取消</Button><Button type="primary" icon={<CheckCircleFilled />} onClick={saveBudgets}>保存预算</Button></Space> : <Button type="primary" icon={<EditOutlined />} onClick={startEditing}>编辑预算</Button>}
      </div>
      <Row gutter={[16, 16]} className="budget-summary-grid">
        <Col xs={24} md={8}><Card className="summary-card"><Statistic title="本月总预算" value={totalBudget} precision={2} formatter={(value) => formatCurrency(Number(value ?? 0))} /><span className="summary-card__hint">覆盖 {budgetedItems.filter((item) => item.amount > 0).length} 个支出分类</span></Card></Col>
        <Col xs={24} md={8}><Card className="summary-card summary-card--expense"><Statistic title="已用预算" value={totalSpent} precision={2} formatter={(value) => formatCurrency(Number(value ?? 0))} /><span className="summary-card__hint">已使用 {totalBudget ? Math.round((totalSpent / totalBudget) * 100) : 0}%</span></Card></Col>
        <Col xs={24} md={8}><Card className="summary-card summary-card--income"><Statistic title="剩余可用" value={totalBudget - totalSpent} precision={2} formatter={(value) => formatCurrency(Number(value ?? 0))} /><span className="summary-card__hint">本月尚可安排的支出</span></Card></Col>
      </Row>
      {atRisk.length > 0 && <Alert className="budget-alert" type={atRisk.some((item) => categorySpending[item.category.id] > item.amount) ? 'error' : 'warning'} showIcon icon={<WarningFilled />} message={atRisk.some((item) => categorySpending[item.category.id] > item.amount) ? '发现超支分类，请及时调整本月支出或预算' : '部分分类预算使用已超过 80%，请留意后续支出'} description={atRisk.map((item) => `${item.category.name} ${Math.round((categorySpending[item.category.id] / item.amount) * 100)}%`).join('，')} />}
      <Card className="data-card budget-list-card" title="分类预算" extra={editing ? <Typography.Text type="secondary">编辑后请保存</Typography.Text> : <Tag color="green">预算跟踪中</Tag>}>
        <div className="budget-list">
          {budgetedItems.map(({ category, amount }) => {
            const spent = categorySpending[category.id]
            const percent = amount ? Math.round((spent / amount) * 100) : 0
            const overBudget = percent > 100
            const warning = percent >= 80 && !overBudget
            return <div className="budget-item" key={category.id}>
              <div className="budget-item__heading"><Space size={10}><span className="category-dot category-dot--large" style={{ background: category.color }} /><div><strong>{category.name}</strong><span>已用 {formatCurrency(spent)}</span></div></Space><div className="budget-item__amount">{editing ? <InputNumber min={0} precision={2} addonBefore="¥" value={draftBudgets[category.id] ?? 0} onChange={(value) => setDraftBudgets((current) => ({ ...current, [category.id]: Number(value ?? 0) }))} /> : <><strong>{formatCurrency(amount)}</strong><span>预算金额</span></>}</div></div>
              <div className="budget-item__progress"><Progress percent={Math.min(percent, 100)} showInfo={false} strokeColor={overBudget ? 'oklch(0.59 0.16 28)' : warning ? 'oklch(0.7 0.13 76)' : 'oklch(0.52 0.105 150)'} trailColor="oklch(0.93 0.014 140)" /><span className={overBudget ? 'status status--over' : warning ? 'status status--warning' : 'status status--ok'}>{overBudget ? <><ExclamationCircleFilled /> 超支 {formatCurrency(spent - amount)}</> : warning ? <><WarningFilled /> 使用 {percent}%</> : <><CheckCircleFilled /> 剩余 {formatCurrency(amount - spent)}</>}</span></div>
            </div>
          })}
          {editing && <Button type="dashed" icon={<PlusOutlined />} className="budget-add-button">添加分类预算</Button>}
        </div>
      </Card>
    </div>
  )
}
