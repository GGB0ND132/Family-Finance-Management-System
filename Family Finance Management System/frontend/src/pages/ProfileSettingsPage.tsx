import { SaveOutlined, UserOutlined } from '@ant-design/icons'
import { Avatar, Button, Card, Divider, Form, Input, Space, Tag, Typography, Upload, message } from 'antd'
import type { UploadProps } from 'antd'
import { useEffect, useState } from 'react'
import { authApi } from '../api/authApi'
import type { ApiResponse, AuthUser } from '../api/contracts'
import { useAuthStore } from '../stores/authStore'

interface ProfileForm { nickname: string; real_name?: string; avatar?: string }

export function ProfileSettingsPage() {
  const [form] = Form.useForm<ProfileForm>()
  const [api, holder] = message.useMessage()
  const [selectedAvatar, setSelectedAvatar] = useState<string>()
  const [readingAvatar, setReadingAvatar] = useState(false)
  const { user, updateUser } = useAuthStore()
  useEffect(() => { form.setFieldsValue({ nickname: user?.nickname, real_name: user?.real_name, avatar: user?.avatar }); setSelectedAvatar(user?.avatar) }, [form, user])
  const saveProfile = async (values: ProfileForm) => {
    const avatar = selectedAvatar?.trim() || values.avatar?.trim() || undefined
    let nextUser = { ...user, ...values, avatar } as AuthUser
    if (import.meta.env.VITE_API_BASE_URL) { const response = await authApi.updateProfile({ nickname: values.nickname, real_name: values.real_name, avatar }); const result = response.data as ApiResponse<AuthUser> | AuthUser; nextUser = ('data' in result ? result.data : result) ?? nextUser }
    updateUser(nextUser); form.setFieldValue('avatar', avatar ?? ''); api.success('个人信息已保存，头像已更新')
  }
  const uploadProps: UploadProps = { accept: 'image/png,image/jpeg,image/webp,image/gif', showUploadList: false, beforeUpload: (file) => { if (file.size > 2 * 1024 * 1024) { api.error('头像图片不能超过 2MB'); return Upload.LIST_IGNORE } setReadingAvatar(true); const reader = new FileReader(); reader.onload = () => { const result = typeof reader.result === 'string' ? reader.result : undefined; setSelectedAvatar(result); form.setFieldValue('avatar', result); setReadingAvatar(false) }; reader.onerror = () => { setReadingAvatar(false); api.error('头像读取失败，请重新选择图片') }; reader.readAsDataURL(file); return false } }
  return <div className="page">{holder}<div className="page-heading"><div><Typography.Title level={2}>个人信息设置</Typography.Title><Typography.Text>设置头像、昵称和真实姓名，资料会同步显示在系统顶部。</Typography.Text></div></div><Card className="data-card" style={{ maxWidth: 640 }}><Form form={form} layout="vertical" onFinish={saveProfile}><Form.Item label="个人头像" name="avatar" extra="支持 JPG、PNG、WEBP、GIF，图片大小不超过 2MB"><Space align="center"><Avatar size={64} src={selectedAvatar}>{user?.nickname?.slice(0, 1) ?? <UserOutlined />}</Avatar><Upload {...uploadProps}><Button icon={<UserOutlined />} loading={readingAvatar}>更换头像</Button></Upload></Space></Form.Item><Form.Item label="昵称" name="nickname" rules={[{ required: true, message: '请输入昵称' }]}><Input /></Form.Item><Form.Item label="真实姓名" name="real_name"><Input placeholder="请输入真实姓名" /></Form.Item><Divider /><Space><Typography.Text type="secondary">登录用户名：{user?.username ?? '未设置'}</Typography.Text><Tag>{user?.role === 'ADMIN' ? '管理员' : '成员'}</Tag></Space><Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={readingAvatar} disabled={readingAvatar} block style={{ marginTop: 20 }}>保存个人信息</Button></Form></Card></div>
}