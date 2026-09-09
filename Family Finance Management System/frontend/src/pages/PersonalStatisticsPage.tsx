import { BarChartOutlined } from '@ant-design/icons'
import { Alert, Card, Col, DatePicker, Empty, Progress, Row, Skeleton, Space, Statistic, Typography } from 'antd'
import dayjs from 'dayjs'
import { useEffect, useState } from 'react'
import { reportApi } from '../api/reportsApi'
import { useAuthStore } from '../stores/authStore'

type Summary = { income: number; expense: number; balance: number; assets: number }
type CategoryPoint = { category_id: number; category_name: string; amount: number; percentage: number }

const emptySummary: Summary = { income: 0, expense: 0, balance: 0, assets: 0 }
const formatCurrency = (value: number) => new Intl.NumberFormat('zh-CN', { style: 'currency', currency: 'CNY' }).format(value)

export function PersonalStatisticsPage() {
  const familyId = useAuthStore((state) => state.familyId)
  const [month, setMonth] = useState(() => dayjs().format('YYYY-MM'))
  const [summary, setSummary] = useState<Summary>(emptySummary)
  const [breakdown, setBreakdown] = useState<CategoryPoint[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!familyId) {
      setSummary(emptySummary)
      setBreakdown([])
      setError('请先选择家庭')
      return
    }

    const id = Number(familyId)
    const fromDate = `${month}-01`
    const toDate = `${month}-${dayjs(`${month}-01`).daysInMonth()}`
    setLoading(true)
    setError(null)
    Promise.all([
      reportApi.personalSummary({ family_id: id, from_date: fromDate, to_date: toDate }),
      reportApi.personalByCategory({ family_id: id, month }),
    ])
      .then(([summaryResponse, categoryResponse]) => {
        const value = summaryResponse.data.data
        setSummary({
          income: Number(value?.income ?? 0),
          expense: Number(value?.expense ?? 0),
          balance: Number(value?.balance ?? 0),
          assets: Number(value?.assets ?? 0),
        })
        setBreakdown((categoryResponse.data.data ?? []).map((category) => ({
          category_id: category.category_id,
          category_name: category.category_name,
          amount: Number(category.amount ?? 0),
          percentage: Number(category.percentage ?? 0),
        })))
      })
      .catch(() => setError('个人统计接口暂时不可用，请稍后重试'))
      .finally(() => setLoading(false))
  }, [familyId, month])

  return <div className="page"><div className="page-heading"><div><Typography.Title level={2}>个人流水统计</Typography.Title><Typography.Text>按月份查看当前用户已确认流水的收入、支出、结余和资产。</Typography.Text></div><Space><DatePicker picker="month" value={dayjs(`${month}-01`)} onChange={(value) => value && setMonth(value.format('YYYY-MM'))} allowClear={false} /><BarChartOutlined style={{ fontSize: 32 }} /></Space></div>{error && <Alert type="warning" showIcon message={error} style={{ marginBottom: 16 }} />}{loading ? <Skeleton active paragraph={{ rows: 4 }} /> : <><Row gutter={[16, 16]}><Col xs={24} sm={12} xl={6}><Card className="summary-card summary-card--income"><Statistic title="个人收入" value={summary.income} formatter={(value) => formatCurrency(Number(value))} /></Card></Col><Col xs={24} sm={12} xl={6}><Card className="summary-card summary-card--expense"><Statistic title="个人支出" value={summary.expense} formatter={(value) => formatCurrency(Number(value))} /></Card></Col><Col xs={24} sm={12} xl={6}><Card className="summary-card"><Statistic title="个人结余" value={summary.balance} formatter={(value) => formatCurrency(Number(value))} /></Card></Col><Col xs={24} sm={12} xl={6}><Card className="summary-card"><Statistic title="个人资产" value={summary.assets} formatter={(value) => formatCurrency(Number(value))} /></Card></Col></Row><Card className="data-card" title="支出分类统计">{breakdown.length ? <Space direction="vertical" className="full-width">{breakdown.map((category) => <div className="report-category-row" key={category.category_id}><span>{category.category_name}</span><Space><Progress percent={Math.round(category.percentage)} showInfo={false} style={{ width: 140 }} /><strong>{formatCurrency(category.amount)}</strong></Space></div>)}</Space> : <Empty description="当前月份暂无个人支出数据" />}</Card></>}</div>
}
