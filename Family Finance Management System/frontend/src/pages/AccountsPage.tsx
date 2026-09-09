import {
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  WalletOutlined,
} from "@ant-design/icons";
import {
  Button,
  Card,
  Drawer,
  Form,
  Input,
  InputNumber,
  Popconfirm,
  Select,
  Space,
  Tag,
  Typography,
  message,
} from "antd";
import { useEffect, useState } from "react";
import { accountApi } from "../api/accountsApi";
import { familyApi } from "../api/familiesApi";
import type { AccountResponse, FamilyMemberResponse } from "../api/contracts";
import type { AccountType } from "../data/financeData";
import { ScopeToggle } from "../components/ScopeToggle";
import { useDataScope } from "../hooks/useDataScope";
import { useAuthStore } from "../stores/authStore";

const labels: Record<AccountType, string> = {
  CASH: "现金",
  BANK_CARD: "储蓄卡",
  ALIPAY: "支付宝",
  WECHAT: "微信钱包",
  CREDIT_CARD: "信用卡",
  OTHER: "其他",
};
type FormValues = {
  name: string;
  owner_member_id: number | string;
  type: AccountType;
  initial_balance?: number;
  remark?: string;
};

export function AccountsPage() {
  const familyId = useAuthStore((s) => s.familyId);
  const user = useAuthStore((s) => s.user);
  const [scope] = useDataScope();
  const [accounts, setAccounts] = useState<AccountResponse[]>([]);
  const [members, setMembers] = useState<FamilyMemberResponse[]>([]);
  const [editing, setEditing] = useState<AccountResponse | null>(null);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm<FormValues>();
  const [api, holder] = message.useMessage();
  const load = async () => {
    if (!familyId) return;
    setLoading(true);
    try {
      const [a, m] = await Promise.all([
        accountApi.list({
          family_id: Number(familyId),
          scope,
          include_closed: true,
          page_size: 100,
        }),
        familyApi.members(familyId),
      ]);
      setAccounts(a.data.data?.items ?? []);
      setMembers(m.data.data ?? []);
    } catch {
      api.error("账户加载失败");
    } finally {
      setLoading(false);
    }
  };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    void load();
  }, [familyId, scope]);
  const allowedMembers =
    scope === "personal"
      ? members.filter((m) => String(m.user_id) === String(user?.id))
      : members;
  const submit = async (v: FormValues) => {
    if (!familyId) return;
    try {
      if (editing)
        await accountApi.update(editing.id, {
          name: v.name,
          type: v.type,
          owner_member_id: Number(v.owner_member_id),
          remark: v.remark,
        });
      else
        await accountApi.create({
          family_id: Number(familyId),
          owner_member_id: Number(v.owner_member_id),
          name: v.name,
          type: v.type,
          initial_balance: Number(v.initial_balance ?? 0).toFixed(2),
          remark: v.remark,
        });
      api.success(editing ? "账户已更新" : "账户已创建");
      setOpen(false);
      await load();
    } catch {
      api.error("保存失败，请检查权限或输入");
    }
  };
  const remove = async (id: number) => {
    try {
      await accountApi.remove(id);
      api.success("账户已删除或销户");
      await load();
    } catch {
      api.error("账户余额不为 0，无法销户");
    }
  };
  return (
    <div className="page">
      {holder}
      <div className="page-heading">
        <div>
          <Typography.Title level={2}>账户管理</Typography.Title>
          <Typography.Text>
            账户余额由后端流水实时维护，销户账户保留历史记录。
          </Typography.Text>
        </div>
        <Space>
          <ScopeToggle />
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              setEditing(null);
              form.resetFields();
              form.setFieldsValue({
                owner_member_id: allowedMembers[0]?.id,
                type: "CASH",
                initial_balance: 0,
              });
              setOpen(true);
            }}
          >
            新增账户
          </Button>
        </Space>
      </div>
      <Card loading={loading} className="data-card">
        <Space direction="vertical" className="full-width">
          {accounts
            .filter(
              (a) =>
                scope === "family" ||
                allowedMembers.some((m) => m.id === a.owner_member_id),
            )
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
                      {a.closed_at && <Tag>已销户</Tag>}
                      <Typography.Text type="secondary">
                        {a.owner_nickname ?? "未知成员"}
                      </Typography.Text>
                    </div>
                  </div>
                </Space>
                <Space>
                  <strong>
                    {Number(a.current_balance).toLocaleString("zh-CN", {
                      style: "currency",
                      currency: "CNY",
                    })}
                  </strong>
                  <Button
                    type="text"
                    icon={<EditOutlined />}
                    onClick={() => {
                      setEditing(a);
                      form.setFieldsValue({
                        name: a.name,
                        owner_member_id: a.owner_member_id,
                        type: a.type,
                        remark: a.remark ?? "",
                      });
                      setOpen(true);
                    }}
                  />
                  <Popconfirm
                    title="销户账户？"
                    onConfirm={() => void remove(a.id)}
                  >
                    <Button type="text" danger icon={<DeleteOutlined />} />
                  </Popconfirm>
                </Space>
              </div>
            ))}
        </Space>
      </Card>
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
        <Form form={form} layout="vertical" onFinish={submit}>
          <Form.Item label="账户名称" name="name" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item
            label="所属成员"
            name="owner_member_id"
            rules={[{ required: true }]}
          >
            <Select
              options={allowedMembers.map((m) => ({
                value: m.id,
                label: m.nickname ?? m.username,
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
              name="initial_balance"
              rules={[{ required: true }]}
            >
              <InputNumber
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
