import { FilterOutlined, PlusOutlined, SwapOutlined } from '@ant-design/icons'
import dayjs, { type Dayjs } from 'dayjs'
import { Button, Card, DatePicker, Drawer, Form, Input, InputNumber, Select, Space, Table, Tag, Typography, message } from 'antd'
import type { TableColumnsType } from 'antd'
import { useMemo, useState } from 'react'
import { accounts, categories, findAccount, findCategory, formatCurrency, type FinanceTransaction, type TransactionType } from '../data/financeData'
import { useFinanceStore, type TransactionDraft } from '../stores/financeStore'

interface TransactionFormValues {
  type: TransactionType
  accountId: string
  categoryId?: string
  amount: number
  occurredAt: Dayjs
  remark: string
}

const typeOptions = [
  { value: 'income', label: '收入' },
  { value: 'expense', label: '支出' },
  { value: 'transfer', label: '转账' },
]

const typeLabel: Record<TransactionType, string> = { income: '收入', expense: '支出', transfer: '转账' }

export function TransactionsPage() {
  const [form] = Form.useForm<TransactionFormValues>()
  const [messageApi, messageContext] = message.useMessage()
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [selectedType, setSelectedType] = useState<TransactionType | undefined>()
  const [selectedCategory, setSelectedCategory] = useState<string | undefined>()
  const [selectedAccount, setSelectedAccount] = useState<string | undefined>()
  const [dateRange, setDateRange] = useState<[Dayjs | null, Dayjs | null] | null>(null)
  const transactions = useFinanceStore((state) => state.transactions)
  const addTransaction = useFinanceStore((state) => state.addTransaction)

  const filteredTransactions = useMemo(() => transactions.filter((transaction) => {
    const inType = !selectedType || transaction.type === selectedType
    const inCategory = !selectedCategory || transaction.categoryId === selectedCategory
    const inAccount = !selectedAccount || transaction.accountId === selectedAccount
    const inDateRange = !dateRange || (!dateRange[0] || transaction.occurredAt >= dateRange[0].format('YYYY-MM-DD')) && (!dateRange[1] || transaction.occurredAt <= dateRange[1].format('YYYY-MM-DD'))
    return inType && inCategory && inAccount && inDateRange
  }), [dateRange, selectedAccount, selectedCategory, selectedType, transactions])

  const openDrawer = () => {
    form.setFieldsValue({ type: 'expense', accountId: 'account-alipay', occurredAt: dayjs('2026-09-06'), amount: undefined, remark: '', categoryId: undefined })
    setDrawerOpen(true)
  }

  const saveTransaction = (values: TransactionFormValues) => {
    const transaction: TransactionDraft = {
      type: values.type,
      accountId: values.accountId,
      categoryId: values.type === 'transfer' ? undefined : values.categoryId,
      amount: values.amount,
      occurredAt: values.occurredAt.format('YYYY-MM-DD'),
      remark: values.remark.trim() || '未填写备注',
    }
    addTransaction(transaction)
    messageApi.success('流水已保存，首页汇总与预算将同步更新')
    setDrawerOpen(false)
  }

  const columns: TableColumnsType<FinanceTransaction> = [
    { title: '发生日期', dataIndex: 'occurredAt', width: 116, sorter: (a, b) => a.occurredAt.localeCompare(b.occurredAt) },
    { title: '类型', dataIndex: 'type', width: 88, render: (type: TransactionType) => <Tag color={type === 'income' ? 'green' : type === 'expense' ? 'volcano' : 'blue'}>{typeLabel[type]}</Tag> },
    { title: '账户', width: 174, render: (_, transaction) => findAccount(transaction.accountId)?.name },
    { title: '分类', width: 120, render: (_, transaction) => { const category = findCategory(transaction.categoryId); return category ? <Space size={8}><span className="category-dot" style={{ background: category.color }} />{category.name}</Space> : <Typography.Text type="secondary">账户转账</Typography.Text> } },
    { title: '备注', dataIndex: 'remark', ellipsis: true },
    { title: '记录人', dataIndex: 'createdBy', width: 104 },
    { title: '金额', width: 132, align: 'right', sorter: (a, b) => a.amount - b.amount, render: (_, transaction) => <span className={`amount amount--${transaction.type}`}>{transaction.type === 'expense' ? '-' : '+'}{formatCurrency(transaction.amount)}</span> },
  ]

  const activeFormType = Form.useWatch('type', form) ?? 'expense'
  const formCategories = categories.filter((category) => category.type === activeFormType)

  return (
    <div className="page transactions-page">
      {messageContext}
      <div className="page-heading">
        <div><Typography.Title level={2}>收支流水</Typography.Title><Typography.Text>查看并维护家庭的收入、支出和账户转账记录。</Typography.Text></div>
        <Button type="primary" icon={<PlusOutlined />} onClick={openDrawer}>新增流水</Button>
      </div>
      <Card className="filter-card" bordered={false}>
        <Space wrap size={[12, 12]}>
          <Select allowClear placeholder="全部类型" prefix={<FilterOutlined />} value={selectedType} onChange={setSelectedType} options={typeOptions} className="filter-select" />
          <Select allowClear placeholder="全部分类" value={selectedCategory} onChange={setSelectedCategory} options={categories.filter((category) => category.type === 'expense' || category.type === 'income').map((category) => ({ value: category.id, label: category.name }))} className="filter-select" />
          <Select allowClear placeholder="全部账户" value={selectedAccount} onChange={setSelectedAccount} options={accounts.map((account) => ({ value: account.id, label: account.name }))} className="filter-select" />
          <DatePicker.RangePicker value={dateRange} onChange={(value) => setDateRange(value)} placeholder={['开始日期', '结束日期']} />
          <Button onClick={() => { setSelectedType(undefined); setSelectedCategory(undefined); setSelectedAccount(undefined); setDateRange(null) }}>清除筛选</Button>
        </Space>
      </Card>
      <Card className="data-card transaction-table-card" title={`流水明细 · ${filteredTransactions.length} 笔`} extra={<Typography.Text type="secondary">金额单位：元</Typography.Text>}>
        <Table rowKey="id" columns={columns} dataSource={filteredTransactions} scroll={{ x: 880 }} pagination={{ pageSize: 8, showSizeChanger: false, showTotal: (total) => `共 ${total} 笔` }} />
      </Card>
      <Drawer title="新增收支流水" width={460} open={drawerOpen} onClose={() => setDrawerOpen(false)} destroyOnHidden extra={<SwapOutlined className="drawer-title-icon" />} footer={<Space className="drawer-actions"><Button onClick={() => setDrawerOpen(false)}>取消</Button><Button type="primary" onClick={() => form.submit()}>保存流水</Button></Space>}>
        <Form<TransactionFormValues> form={form} layout="vertical" requiredMark={false} onFinish={saveTransaction}>
          <Form.Item label="流水类型" name="type" rules={[{ required: true, message: '请选择流水类型' }]}><Select options={typeOptions} onChange={(value: TransactionType) => { form.setFieldValue('categoryId', undefined); form.setFieldValue('type', value) }} /></Form.Item>
          <Form.Item label="金额" name="amount" rules={[{ required: true, message: '请输入金额' }]}><InputNumber min={0.01} precision={2} addonBefore="¥" className="full-width" placeholder="0.00" /></Form.Item>
          <Form.Item label="账户" name="accountId" rules={[{ required: true, message: '请选择账户' }]}><Select options={accounts.map((account) => ({ value: account.id, label: `${account.name} · ${formatCurrency(account.balance)}` }))} /></Form.Item>
          {activeFormType !== 'transfer' && <Form.Item label="分类" name="categoryId" rules={[{ required: true, message: '请选择分类' }]}><Select options={formCategories.map((category) => ({ value: category.id, label: category.name }))} /></Form.Item>}
          <Form.Item label="发生日期" name="occurredAt" rules={[{ required: true, message: '请选择发生日期' }]}><DatePicker className="full-width" /></Form.Item>
          <Form.Item label="备注" name="remark"><Input.TextArea rows={3} maxLength={80} showCount placeholder="例如：超市采购、午餐等" /></Form.Item>
        </Form>
      </Drawer>
    </div>
  )
}
