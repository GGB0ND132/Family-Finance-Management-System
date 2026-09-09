import { DownloadOutlined } from '@ant-design/icons'
import { Button, Card, DatePicker, Select, Segmented, Space, Typography, message } from 'antd'
import { useState } from 'react'
import { transactionApi, downloadBlob } from '../api/transactionsApi'
import { ScopeToggle } from '../components/ScopeToggle'
import { useDataScope } from '../hooks/useDataScope'
import { useAuthStore } from '../stores/authStore'

export function ExportsPage() {
  const familyId = useAuthStore(s => s.familyId); const [scope] = useDataScope(); const [format, setFormat] = useState<'csv' | 'xlsx'>('csv'); const [type, setType] = useState<'INCOME' | 'EXPENSE'>(); const [range, setRange] = useState<[string, string]>(); const [api, holder] = message.useMessage(); const [loading, setLoading] = useState(false)
  const download = async () => { if (!familyId) return; setLoading(true); try { const response = await transactionApi.export({ family_id: familyId, scope, type, from: range?.[0], to: range?.[1], format }); await downloadBlob(response, `transactions-export.${format}`); api.success(`${format.toUpperCase()} 已下载`) } catch { api.error('导出失败，请检查筛选条件') } finally { setLoading(false) } }
  return <div className="page">{holder}<div className="page-heading"><div><Typography.Title level={2}>数据导出</Typography.Title><Typography.Text>按范围、日期和类型导出收支流水。</Typography.Text></div></div><Card className="data-card" title="导出条件"><Space wrap><DatePicker.RangePicker onChange={dates => setRange(dates?.[0] && dates?.[1] ? [dates[0].format('YYYY-MM-DD'), dates[1].add(1, 'day').format('YYYY-MM-DDTHH:mm:ssZ')] : undefined)} /><ScopeToggle /><Select allowClear value={type} onChange={setType} placeholder="类型" options={[{ value: 'INCOME', label: '收入' }, { value: 'EXPENSE', label: '支出' }]} style={{ width: 130 }} /><Segmented value={format} onChange={v => setFormat(v as 'csv' | 'xlsx')} options={[{ value: 'csv', label: 'CSV' }, { value: 'xlsx', label: 'XLSX' }]} /><Button type="primary" icon={<DownloadOutlined />} loading={loading} onClick={download}>导出 {format.toUpperCase()}</Button></Space></Card></div>
}
