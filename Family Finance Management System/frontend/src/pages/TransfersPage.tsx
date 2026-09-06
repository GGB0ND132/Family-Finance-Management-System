import { DeleteOutlined, EditOutlined, PlusOutlined, SwapOutlined } from "@ant-design/icons";
import dayjs, { type Dayjs } from "dayjs";
import {
  Button,
  Card,
  DatePicker,
  Drawer,
  Form,
  Input,
  InputNumber,
  Popconfirm,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from "antd";
import type { TableColumnsType } from "antd";
import { useState } from "react";
import { formatCurrency, type FinanceTransfer } from "../data/financeData";
import { useFinanceStore } from "../stores/financeStore";
import { useAuthStore } from "../stores/authStore";
import { accountLabel, memberLabel } from "./pageUtils";
interface TransferForm {
  fromAccountId: string;
  toAccountId: string;
  fromMemberId: string;
  toMemberId: string;
  amount: number;
  occurredAt: Dayjs;
  remark?: string;
}
export function TransfersPage() {
  const [open, setOpen] = useState(false);
  const [editingId, setEditingId] = useState<string>();
  const [form] = Form.useForm<TransferForm>();
  const [api, holder] = message.useMessage();
  const currentUserId = useAuthStore((state) => state.user?.id ?? "member-zhang");
  const isAdmin = useAuthStore((state) => state.user?.role === "ADMIN");
  const { transfers, accounts, members, addTransfer, updateTransfer, deleteTransfer, confirmTransfer } =
    useFinanceStore();
  const active = accounts.filter((a) => !a.closedAt);
  const outgoingAccounts = active.filter((account) => isAdmin || account.ownerMemberId === currentUserId);
  const fromAccountId = Form.useWatch("fromAccountId", form);
  const save = (v: TransferForm) => {
    if (v.fromAccountId === v.toAccountId) {
      api.error("转出和转入账户不能相同");
      return;
    }
    const from = accounts.find((a) => a.id === v.fromAccountId);
    const to = accounts.find((a) => a.id === v.toAccountId);
    if (!from || !to) return;
    if (!isAdmin && (v.fromMemberId !== currentUserId || from.ownerMemberId !== currentUserId)) {
      api.error("普通成员只能使用本人作为转出方");
      return;
    }
    const draft = {
      fromAccountId: from.id,
      toAccountId: to.id,
      fromMemberId: v.fromMemberId,
      toMemberId: v.toMemberId,
      recorderUserId: "member-zhang",
      amount: v.amount,
      occurredAt: v.occurredAt.format("YYYY-MM-DD"),
      remark: v.remark?.trim() || "账户转账",
    };
    if (v.fromMemberId !== from.ownerMemberId || v.toMemberId !== to.ownerMemberId) {
      api.error("转账成员必须与账户所属人一致");
      return;
    }
    if (editingId) updateTransfer(editingId, draft); else addTransfer(draft);
    api.success(editingId ? "转账已更新" : "转账已保存，未计入收支统计");
    setOpen(false);
  };
  const columns: TableColumnsType<FinanceTransfer> = [
    { title: "日期", dataIndex: "occurredAt" },
    {
      title: "转出账户",
      render: (_, t) => (
        <span>
          {accountLabel(t.fromAccountId, accounts)} ·{" "}
          {memberLabel(t.fromMemberId, members)}
        </span>
      ),
    },
    { title: "方向", render: () => <SwapOutlined /> },
    {
      title: "转入账户",
      render: (_, t) => (
        <span>
          {accountLabel(t.toAccountId, accounts)} ·{" "}
          {memberLabel(t.toMemberId, members)}
        </span>
      ),
    },
    {
      title: "金额",
      align: "right",
      render: (_, t) => formatCurrency(t.amount),
    },
    { title: "备注", dataIndex: "remark" },
    {
      title: "状态",
      render: (_, transfer) => transfer.status === "PENDING_CONFIRM" ? <Tag color="gold">{transfer.toMemberId === currentUserId ? "待我确认" : "等待对方确认"}</Tag> : <Tag color="green">已确认</Tag>,
    },
    {
      title: "操作",
      render: (_, t) => (
        <Space size={0}>
          {t.status === "PENDING_CONFIRM" && t.toMemberId === currentUserId ? <Button type="primary" size="small" onClick={() => { confirmTransfer(t.id); api.success("转账已确认"); }}>确认转账</Button> : t.status === "PENDING_CONFIRM" ? <Typography.Text type="secondary">等待对方确认</Typography.Text> : <Button type="text" icon={<EditOutlined />} aria-label="编辑转账" onClick={() => { setEditingId(t.id); form.setFieldsValue({ ...t, occurredAt: dayjs(t.occurredAt) }); setOpen(true); }} />}
          <Popconfirm
            title="删除转账？"
            description="删除后会反向恢复两个账户余额。"
            onConfirm={() => {
              deleteTransfer(t.id);
              api.success("转账已删除");
            }}
          >
            <Button type="text" danger icon={<DeleteOutlined />} aria-label="删除转账" />
          </Popconfirm>
        </Space>
      ),
    },
  ];
  return (
    <div className="page">
      {holder}
      <div className="page-heading">
        <div>
          <Typography.Title level={2}>账户转账</Typography.Title>
          <Typography.Text>
            转账只改变账户余额，不会改变收入、支出、结余或预算使用。
          </Typography.Text>
        </div>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            setEditingId(undefined);
            form.resetFields();
            form.setFieldsValue({ occurredAt: dayjs() });
            setOpen(true);
          }}
        >
          新增转账
        </Button>
      </div>
      <Card className="data-card" title={`转账记录 · ${transfers.length} 笔`}>
        <Table
          rowKey="id"
          columns={columns}
          dataSource={transfers}
          pagination={{ pageSize: 8 }}
          scroll={{ x: 900 }}
        />
      </Card>
      <Drawer
        title={editingId ? "编辑账户转账" : "新增账户转账"}
        open={open}
        onClose={() => setOpen(false)}
        width={430}
        footer={
          <Space className="drawer-actions">
            <Button onClick={() => setOpen(false)}>取消</Button>
            <Button type="primary" onClick={() => form.submit()}>
              确认
            </Button>
          </Space>
        }
      >
        <Form form={form} layout="vertical" onFinish={save}>
          <Form.Item
            label="转出账户"
            name="fromAccountId"
            rules={[{ required: true }]}
          >
            <Select
              onChange={(value) => { form.setFieldValue("fromMemberId", accounts.find((a) => a.id === value)?.ownerMemberId); if (form.getFieldValue("toAccountId") === value) { form.setFieldsValue({ toAccountId: undefined, toMemberId: undefined }); } }}
              options={outgoingAccounts.map((a) => ({
                value: a.id,
                label: `${a.name} · ${memberLabel(a.ownerMemberId, members)}`,
              }))}
            />
          </Form.Item>
          <Form.Item label="转出方成员" name="fromMemberId" rules={[{ required: true }]}>
            <Select disabled options={members.map((m) => ({ value: m.id, label: m.name }))} />
          </Form.Item>
          <Form.Item
            label="转入账户"
            name="toAccountId"
            rules={[{ required: true }]}
          >
            <Select
              onChange={(value) => form.setFieldValue("toMemberId", accounts.find((a) => a.id === value)?.ownerMemberId)}
              options={active.filter((a) => a.id !== fromAccountId).map((a) => ({
                value: a.id,
                label: `${a.name} · ${memberLabel(a.ownerMemberId, members)}`,
              }))}
            />
          </Form.Item>
          <Form.Item label="转入方成员" name="toMemberId" rules={[{ required: true }]}>
            <Select disabled options={members.map((m) => ({ value: m.id, label: m.name }))} />
          </Form.Item>
          <Form.Item
            label="金额"
            name="amount"
            rules={[
              { required: true },
              { type: "number", min: 0.01, message: "金额必须大于 0" },
            ]}
          >
            <InputNumber
              min={0.01}
              precision={2}
              addonBefore="¥"
              className="full-width"
            />
          </Form.Item>
          <Form.Item
            label="发生日期"
            name="occurredAt"
            rules={[{ required: true }]}
          >
            <DatePicker className="full-width" />
          </Form.Item>
          <Form.Item label="备注" name="remark">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Drawer>
    </div>
  );
}
