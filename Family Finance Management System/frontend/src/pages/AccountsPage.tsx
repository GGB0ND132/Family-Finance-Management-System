import {
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  WalletOutlined,
} from "@ant-design/icons";
import {
  Button,
  Card,
  Col,
  Drawer,
  Form,
  Input,
  InputNumber,
  Popconfirm,
  Row,
  Select,
  Space,
  Tag,
  Typography,
  message,
} from "antd";
import { useState } from "react";
import { formatCurrency, type AccountType } from "../data/financeData";
import { currentUserId } from "../data/financeData";
import { ScopeToggle } from "../components/ScopeToggle";
import { useDataScope } from "../hooks/useDataScope";
import { useFinanceStore } from "../stores/financeStore";
import { memberLabel } from "./pageUtils";

const labels: Record<AccountType, string> = {
  CASH: "现金",
  BANK_CARD: "储蓄卡",
  ALIPAY: "支付宝",
  WECHAT: "微信钱包",
  CREDIT_CARD: "信用卡",
  OTHER: "其他",
};

export function AccountsPage() {
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<string>();
  const [form] = Form.useForm();
  const [api, holder] = message.useMessage();
  const [scope] = useDataScope();
  const { accounts, members, addAccount, updateAccount, removeOrCloseAccount } =
    useFinanceStore();
  const save = (v: {
    name: string;
    ownerMemberId: string;
    type: AccountType;
    initialBalance?: number;
    remark?: string;
  }) => {
    if (editing) updateAccount(editing, v);
    else
      addAccount({
        ...v,
        initialBalance: v.initialBalance ?? 0,
        remark: v.remark ?? "",
      });
    api.success(editing ? "账户已更新" : "账户已创建");
    setOpen(false);
  };
  return (
    <div className="page">
      {holder}
      <div className="page-heading">
        <div>
          <Typography.Title level={2}>账户管理</Typography.Title>
          <Typography.Text>
            按成员查看账户。销户账户不再进入当前资产和记账选择器。
          </Typography.Text>
        </div>
        <Space><ScopeToggle /><Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            setEditing(undefined);
            form.resetFields();
            setOpen(true);
          }}
        >
          新增账户
        </Button></Space>
      </div>
      <Row gutter={[16, 16]}>
        {members.map((m) => (
          <Col xs={24} lg={12} key={m.id}>
            <Card
              className="data-card"
              title={
                <Space>
                  <span className="sider-footer__avatar">{m.avatar}</span>
                  {m.name}
                  <Tag>{m.role === "ADMIN" ? "管理员" : "成员"}</Tag>
                </Space>
              }
            >
              <Space direction="vertical" className="full-width">
                {accounts
                  .filter((a) => a.ownerMemberId === m.id && (scope === 'family' || m.id === currentUserId))
                  .map((a) => (
                    <div className="report-category-row" key={a.id}>
                      <Space>
                        <span className="account-icon">
                          <WalletOutlined />
                        </span>
                        <div>
                          <strong>{a.name}</strong>
                          <div>
                            <Tag>{labels[a.type]}</Tag>
                            {a.closedAt && <Tag>已销户</Tag>}
                          </div>
                        </div>
                      </Space>
                      <Space>
                        <strong>{formatCurrency(a.currentBalance)}</strong>
                        <Button
                          type="text"
                          icon={<EditOutlined />}
                          onClick={() => {
                            setEditing(a.id);
                            form.setFieldsValue(a);
                            setOpen(true);
                          }}
                        />
                        <Popconfirm
                          title={a.closedAt ? "删除账户？" : "销户账户？"}
                          description="有历史引用的账户会保留并标记为已销户。"
                          onConfirm={() => {
                            const result = removeOrCloseAccount(a.id);
                            api[result === 'BALANCE_NOT_ZERO' ? 'error' : 'success'](result === 'BALANCE_NOT_ZERO' ? '账户余额不为 0，请先转出资金' : result === "CLOSED" ? "账户已销户" : "账户已删除");
                          }}
                        >
                          <Button
                            type="text"
                            danger
                            icon={<DeleteOutlined />}
                          />
                        </Popconfirm>
                      </Space>
                    </div>
                  ))}
              </Space>
            </Card>
          </Col>
        ))}
      </Row>
      <Drawer
        title={editing ? "编辑账户" : "新增账户"}
        open={open}
        onClose={() => setOpen(false)}
        width={430}
        footer={
          <Space className="drawer-actions">
            <Button onClick={() => setOpen(false)}>取消</Button>
            <Button type="primary" onClick={() => form.submit()}>
              保存账户
            </Button>
          </Space>
        }
      >
        <Form form={form} layout="vertical" onFinish={save}>
          <Form.Item label="账户名称" name="name" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item
            label="所属成员"
            name="ownerMemberId"
            rules={[{ required: true }]}
          >
            <Select
              options={members.map((m) => ({
                value: m.id,
                label: memberLabel(m.id, members),
              }))}
            />
          </Form.Item>
          <Form.Item label="账户类型" name="type" rules={[{ required: true }]}>
            <Select
              options={Object.entries(labels).map(([value, label]) => ({
                value,
                label,
              }))}
            />
          </Form.Item>
          {!editing && (
            <Form.Item
              label="初始余额"
              name="initialBalance"
              initialValue={0}
              rules={[{ required: true }]}
            >
              <InputNumber
                min={0}
                precision={2}
                addonBefore="¥"
                className="full-width"
              />
            </Form.Item>
          )}
          <Form.Item label="备注" name="remark">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Drawer>
    </div>
  );
}
