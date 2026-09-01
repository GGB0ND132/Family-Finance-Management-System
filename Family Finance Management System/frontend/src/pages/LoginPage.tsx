import { LockOutlined, MailOutlined, WalletOutlined } from '@ant-design/icons'
import { Button, Card, Checkbox, Form, Input, Typography } from 'antd'
import { useNavigate } from 'react-router-dom'

interface LoginForm {
  account: string
  password: string
  remember: boolean
}

export function LoginPage() {
  const navigate = useNavigate()

  const handleFinish = () => {
    navigate('/dashboard')
  }

  return (
    <main className="login-page">
      <section className="login-intro" aria-labelledby="login-intro-title">
        <div className="login-intro__brand">
          <span className="brand-mark"><WalletOutlined /></span>
          <span>家账本</span>
        </div>
        <div className="login-intro__copy">
          <span className="login-intro__eyebrow">FAMILY FINANCE</span>
          <h1 id="login-intro-title">让每一笔家庭收支<br />都有清晰去向。</h1>
          <p>统一管理账户、流水与月度预算，和家人共同掌握每月的财务进度。</p>
        </div>
        <div className="login-intro__facts" aria-label="产品能力">
          <span>收支记录</span><i />
          <span>预算提醒</span><i />
          <span>家庭共享</span>
        </div>
      </section>
      <section className="login-form-panel" aria-labelledby="login-title">
        <Card className="login-card" bordered={false}>
          <div className="login-card__header">
            <Typography.Title id="login-title" level={2}>欢迎回来</Typography.Title>
            <Typography.Paragraph>登录后继续管理XXX之家的家庭账本。</Typography.Paragraph>
          </div>
          <Form<LoginForm>
            layout="vertical"
            requiredMark={false}
            initialValues={{ account: 'zengzhixiang', password: '12345678', remember: true }}
            onFinish={handleFinish}
          >
            <Form.Item label="用户名或邮箱" name="account" rules={[{ required: true, message: '请输入用户名或邮箱' }]}>
              <Input size="large" prefix={<MailOutlined />} placeholder="请输入用户名或邮箱" autoComplete="username" />
            </Form.Item>
            <Form.Item label="密码" name="password" rules={[{ required: true, message: '请输入密码' }, { min: 8, message: '密码至少为 8 位' }]}>
              <Input.Password size="large" prefix={<LockOutlined />} placeholder="请输入密码" autoComplete="current-password" />
            </Form.Item>
            <div className="login-card__options">
              <Form.Item name="remember" valuePropName="checked" noStyle><Checkbox>记住登录状态</Checkbox></Form.Item>
              <Button type="link">忘记密码？</Button>
            </div>
            <Button type="primary" htmlType="submit" size="large" block>登录</Button>
          </Form>
          <div className="login-card__register">还没有账号？<Button type="link">创建家庭账号</Button></div>
        </Card>
      </section>
    </main>
  )
}
