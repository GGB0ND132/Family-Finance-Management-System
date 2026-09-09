import { InboxOutlined } from '@ant-design/icons'
import { Alert, Button, Card, Select, Space, Steps, Table, Tag, Typography, Upload, message } from 'antd'
import type { UploadProps } from 'antd'
import { useEffect, useState } from 'react'
import { importApi } from '../api/importsApi'
import { accountApi } from '../api/accountsApi'
import { familyApi } from '../api/familiesApi'
import { useAuthStore } from '../stores/authStore'
import { ScopeToggle } from '../components/ScopeToggle'
import { useDataScope } from '../hooks/useDataScope'

type BatchRow = { row_number: number; validation_status: 'VALID' | 'INVALID' | 'DUPLICATE'; normalized_data?: Record<string, unknown>; errors?: string[] }
type Batch = { batch_id: number; file_name: string; status: string; total_rows: number; valid_rows: number; invalid_rows: number; duplicate_rows: number; rows: BatchRow[] }

export function ImportsPage() {
  const familyId = useAuthStore(s => s.familyId); const [scope] = useDataScope(); const [api, holder] = message.useMessage()
  const [accounts, setAccounts] = useState<Array<{ id: number; name: string; closed_at: string | null; owner_member_id?: number }>>([]); const [memberId, setMemberId] = useState<number>(); const [accountId, setAccountId] = useState<number>(); const [selectedFile, setSelectedFile] = useState<File>(); const [step, setStep] = useState(0); const [batch, setBatch] = useState<Batch>(); const [loading, setLoading] = useState(false)
  useEffect(() => { if (familyId) { Promise.all([accountApi.list({ family_id: Number(familyId), scope: 'family', include_closed: false, page_size: 100 }), familyApi.members(familyId)]).then(([a, m]) => { setAccounts((a.data.data?.items ?? []) as typeof accounts); const found = (m.data.data ?? []).find(x => String(x.user_id) === String(useAuthStore.getState().user?.id)); if (found) setMemberId(Number(found.id)) }).catch(() => api.error('账户加载失败')) } }, [familyId, api])
  const uploadProps: UploadProps = { accept: '.csv,.xlsx', showUploadList: false, beforeUpload: file => { setSelectedFile(file); setStep(1); return false } }
  const preview = async () => { if (!familyId || !accountId || !selectedFile) return; setLoading(true); try { const res = await importApi.preview({ family_id: Number(familyId), scope, account_id: accountId, file: selectedFile }); setBatch(res.data.data as Batch); setStep(2) } catch { api.error('文件解析失败，请检查格式和字段') } finally { setLoading(false) } }
  const confirm = async () => { if (!batch) return; setLoading(true); try { await importApi.confirm(batch.batch_id); api.success('导入成功'); setBatch({ ...batch, status: 'CONFIRMED' }) } catch { api.error('导入失败，请检查无效行或重复数据') } finally { setLoading(false) } }
  return <div className="page">{holder}<div className="page-heading"><div><Typography.Title level={2}>账单导入</Typography.Title><Typography.Text>上传 CSV/XLSX，预览校验后确认写入流水。</Typography.Text></div><ScopeToggle /></div><Card className="data-card"><Steps current={step} items={[{ title: '选择账户与来源' }, { title: '上传文件' }, { title: '预览并确认' }]} /></Card>
    {step === 0 && <Card className="data-card" title="1. 选择目标账户"><Select placeholder="选择目标账户" value={accountId} onChange={setAccountId} options={accounts.filter(a => scope === 'family' || a.owner_member_id === memberId).map(a => ({ value: a.id, label: a.name }))} style={{ width: 300 }} /><div style={{ marginTop: 24 }}><Upload.Dragger {...uploadProps} disabled={!accountId}><p className="ant-upload-drag-icon"><InboxOutlined /></p><p>选择 CSV 或 XLSX 文件</p><p className="ant-upload-hint">支持常见中文/英文表头，后端自动识别字段。</p></Upload.Dragger></div></Card>}
    {step === 1 && <Card className="data-card" title="2. 上传文件"><Alert message={`已选择 ${selectedFile?.name ?? '文件'}`} showIcon /><Space style={{ marginTop: 20 }}><Button onClick={() => setStep(0)}>返回</Button><Button type="primary" onClick={preview} loading={loading}>生成预览</Button></Space></Card>}
    {step === 2 && batch && <Card className="data-card" title="3. 预览并确认" extra={<Button onClick={() => { setStep(0); setBatch(undefined); setSelectedFile(undefined) }}>重新选择</Button>}><Space style={{ marginBottom: 16 }}><Tag color="green">有效 {batch.valid_rows}</Tag><Tag color="gold">重复 {batch.duplicate_rows}</Tag><Tag color="red">非法 {batch.invalid_rows}</Tag></Space><Table rowKey="row_number" dataSource={batch.rows} pagination={{ pageSize: 10 }} columns={[{ title: '行号', dataIndex: 'row_number' }, { title: '发生时间', render: (_: unknown, r: BatchRow) => String(r.normalized_data?.occurred_at ?? '-') }, { title: '金额', render: (_: unknown, r: BatchRow) => String(r.normalized_data?.amount ?? '-') }, { title: '备注', render: (_: unknown, r: BatchRow) => String(r.normalized_data?.remark ?? '') }, { title: '状态', render: (_: unknown, r: BatchRow) => <Tag color={r.validation_status === 'VALID' ? 'green' : r.validation_status === 'DUPLICATE' ? 'gold' : 'red'}>{r.validation_status === 'VALID' ? '有效' : r.validation_status === 'DUPLICATE' ? '重复' : '非法'}</Tag> }, { title: '错误信息', render: (_: unknown, r: BatchRow) => r.errors?.join('、') }]} /><Button type="primary" style={{ marginTop: 20 }} disabled={batch.invalid_rows > 0 || batch.status !== 'PREVIEWED'} loading={loading} onClick={confirm}>确认导入有效行</Button></Card>}
  </div>
}
