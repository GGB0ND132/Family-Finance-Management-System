import { LockOutlined, UserOutlined, WalletOutlined } from "@ant-design/icons";
import { Button, Card, Form, Input, Typography, message } from "antd";
import { Link, useNavigate } from "react-router-dom";
import { useAuthStore } from "../stores/authStore";

interface RegisterForm {
  username: string;
  nickname: string;
  password: string;
  confirmPassword: string;
}

export function RegisterPage() {
  const navigate = useNavigate();
  const setSession = useAuthStore((state) => state.setSession);
  const [messageApi, messageContext] = message.useMessage();
  const submit = (values: RegisterForm) => {
    setSession(`demo-token-${values.username}`, {
      id: "member-zhang",
      username: values.username,
      nickname: values.nickname,
      role: "ADMIN",
    });
    messageApi.success("账号创建成功，已进入你的家庭账本");
    navigate("/personal");
  };
  return (
    <main className="login-page">
      <section className="login-intro" aria-labelledby="register-intro-title">
        <div className="login-intro__brand">
          <span className="brand-mark">
            <WalletOutlined />
          </span>
          <span>家账本</span>
        </div>
        <div className="login-intro__copy">
          <span className="login-intro__eyebrow">START TOGETHER</span>
          <h1 id="register-intro-title">
            从今天开始，
            <br />
            和家人一起记账。
          </h1>
          <p>创建一个家庭账本，统一记录每一笔收入和支出。</p>
        </div>
        <div className="login-intro__facts">
          <span>创建家庭</span>
          <i />
          <span>邀请成员</span>
          <i />
          <span>开始记账</span>
        </div>
      </section>
      <section className="login-form-panel" aria-labelledby="register-title">
        {messageContext}
        <Card className="login-card" bordered={false}>
          <div className="login-card__header">
            <Typography.Title id="register-title" level={2}>
              创建家庭账号
            </Typography.Title>
            <Typography.Paragraph>
              注册后你会自动成为家庭管理员。
            </Typography.Paragraph>
          </div>
          <Form<RegisterForm>
            layout="vertical"
            requiredMark={false}
            onFinish={submit}
          >
            <Form.Item
              label="用户名"
              name="username"
              rules={[
                { required: true, message: "请输入用户名" },
                { min: 3, message: "用户名至少 3 位" },
              ]}
            >
              <Input
                size="large"
                prefix={<UserOutlined />}
                placeholder="请输入用户名"
              />
            </Form.Item>
            <Form.Item
              label="昵称"
              name="nickname"
              rules={[{ required: true, message: "请输入昵称" }]}
            >
              <Input size="large" placeholder="例如：曾志翔" />
            </Form.Item>
            <Form.Item
              label="密码"
              name="password"
              rules={[
                { required: true, message: "请输入密码" },
                { min: 8, message: "密码至少为 8 位" },
              ]}
            >
              <Input.Password
                size="large"
                prefix={<LockOutlined />}
                placeholder="至少 8 位字符"
              />
            </Form.Item>
            <Form.Item
              label="确认密码"
              name="confirmPassword"
              dependencies={["password"]}
              rules={[
                { required: true, message: "请再次输入密码" },
                ({ getFieldValue }) => ({
                  validator(_, value) {
                    return !value || getFieldValue("password") === value
                      ? Promise.resolve()
                      : Promise.reject(new Error("两次输入的密码不一致"));
                  },
                }),
              ]}
            >
              <Input.Password
                size="large"
                prefix={<LockOutlined />}
                placeholder="再次输入密码"
              />
            </Form.Item>
            <Button type="primary" htmlType="submit" size="large" block>
              创建账号
            </Button>
          </Form>
          <div className="login-card__register">
            已有账号？<Link to="/login">返回登录</Link>
          </div>
        </Card>
      </section>
    </main>
  );
}
