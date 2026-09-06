import { DeleteOutlined, PlusOutlined, ReloadOutlined, UserAddOutlined } from '@ant-design/icons'
import { Button, Card, Form, Input, Modal, Popconfirm, Segmented, Space, Table, Tag, Typography, message } from 'antd'
import { useState } from 'react'
import { demoFamilyId, familyMembers } from '../data/financeData'
import { useAuthStore } from '../stores/authStore'

export function FamilyPage() {
  const [families, setFamilies] = useState([{ id: demoFamilyId, name: '晨光家庭', owner_id: 'member-zhang', members_count: familyMembers.length, invite_code: 'SUNRISE2026' }])
  const [members, setMembers] = useState(familyMembers.map((member) => ({ ...member, user_id: member.id, family_id: demoFamilyId })))
  const [inviteOpen, setInviteOpen] = useState(false)
  const [joinOpen, setJoinOpen] = useState(false)
  const [api, holder] = message.useMessage()
  const [familyId, setFamily] = useState(useAuthStore.getState().familyId ?? '')
  const setFamilyId = useAuthStore((state) => state.setFamily)
  const [form] = Form.useForm<{ name: string }>()
  const selected = families.find((family) => family.id === familyId)
  const createFamily = ({ name }: { name: string }) => {
    const next = { id: `family-${Date.now()}`, name, owner_id: 'member-zhang', members_count: 1, invite_code: 'NEWFAMILY' }
    setFamilies((items) => [...items, next])
    setMembers([{ ...familyMembers[0], user_id: familyMembers[0].id, family_id: next.id }])
    setFamily(next.id)
    setFamilyId(next.id)
    form.resetFields()
    api.success('家庭已创建，你已成为管理员')
  }
  const joinFamily = ({ name }: { name: string }) => {
    if (name.trim().toUpperCase() !== 'SUNRISE2026') { api.error('邀请码无效或已过期'); return }
    setFamilyId(demoFamilyId)
    setFamily(demoFamilyId)
    setJoinOpen(false)
    api.success('已加入晨光家庭')
  }
  return <div className="page">{holder}<div className="page-heading"><div><Typography.Title level={2}>家庭设置</Typography.Title><Typography.Text>切换账本、管理邀请码与成员角色，家庭数据相互隔离。</Typography.Text></div><Space><Button icon={<UserAddOutlined />} onClick={() => setJoinOpen(true)}>加入家庭</Button><Button type="primary" icon={<PlusOutlined />} onClick={() => Modal.confirm({ title: '创建家庭', content: <Form form={form} layout="vertical"><Form.Item name="name" label="家庭名称" rules={[{ required: true }]}><Input placeholder="例如：我们的家" /></Form.Item></Form>, onOk: () => form.validateFields().then(createFamily) })}>创建家庭</Button></Space></div><Card className="data-card" title="我的家庭"><Segmented block value={familyId} onChange={(value) => { setFamily(String(value)); setFamilyId(String(value)) }} options={families.map((family) => ({ value: family.id, label: family.name }))} /></Card>{selected && <Card className="data-card" title={`${selected.name} · 成员管理`} extra={<Space><Button icon={<ReloadOutlined />} onClick={() => api.success('邀请码已刷新')}>生成邀请码</Button><Button onClick={() => setInviteOpen(true)}>查看邀请码</Button></Space>}><Table rowKey="id" dataSource={members.filter((member) => member.family_id === selected.id)} pagination={false} columns={[{ title: '成员', render: (_, member) => <Space><span className="sider-footer__avatar">{member.avatar}</span>{member.name}</Space> }, { title: '角色', render: (_, member) => <Tag color={member.role === 'ADMIN' ? 'blue' : 'default'}>{member.role === 'ADMIN' ? '管理员' : '成员'}</Tag> }, { title: '加入时间', dataIndex: 'joinedAt' }, { title: '操作', render: (_, member) => <Space>{member.id !== 'member-zhang' && <Segmented size="small" value={member.role} options={[{ label: '成员', value: 'MEMBER' }, { label: '管理员', value: 'ADMIN' }]} onChange={(value) => setMembers((items) => items.map((item) => item.id === member.id ? { ...item, role: value as 'ADMIN' | 'MEMBER' } : item))} />}<Popconfirm title="移除该成员？" description="请先处理该成员名下账户和历史流水。" onConfirm={() => setMembers((items) => items.filter((item) => item.id !== member.id))}><Button danger type="text" icon={<DeleteOutlined />} /></Popconfirm></Space> }]}/></Card>}<Modal title="家庭邀请码" open={inviteOpen} onCancel={() => setInviteOpen(false)} footer={<Button onClick={() => setInviteOpen(false)}>关闭</Button>}><Typography.Title level={3}>{selected?.invite_code ?? '暂无邀请码'}</Typography.Title><Typography.Text type="secondary">请将邀请码分享给需要加入家庭的成员。</Typography.Text></Modal><Modal title="加入家庭" open={joinOpen} onCancel={() => setJoinOpen(false)} onOk={() => form.validateFields().then(joinFamily)}><Form form={form} layout="vertical"><Form.Item name="name" label="邀请码" rules={[{ required: true, message: '请输入邀请码' }]}><Input placeholder="请输入邀请码" /></Form.Item></Form></Modal></div>
}