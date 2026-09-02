import { DeleteOutlined, PlusOutlined, SwapOutlined } from "@ant-design/icons";
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
  Typography,
  message,
} from "antd";
import type { TableColumnsType } from "antd";
import { useState } from "react";
import { formatCurrency, type FinanceTransfer } from "../data/financeData";
import { useFinanceStore } from "../stores/financeStore";
import { accountLabel, memberLabel } from "./pageUtils";
interface TransferForm {
  fromAccountId: string;
  toAccountId: string;
  amount: number;
  occurredAt: Dayjs;
  remark?: string;
}
export function TransfersPage() {
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm<TransferForm>();
  const [api, holder] = message.useMessage();
  const { transfers, accounts, members, addTransfer, deleteTransfer } =
    useFinanceStore();
  const active = accounts.filter((a) => !a.closedAt);
  const save = (v: TransferForm) => {
    if (v.fromAccountId === v.toAccountId) {
      api.error("转出和转入账户不能相同");
      return;
    }
    const from = accounts.find((a) => a.id === v.fromAccountId);
    const to = accounts.find((a) => a.id === v.toAccountId);
    if (!from || !to) return;
    addTransfer({
      fromAccountId: from.id,
      toAccountId: to.id,
      fromMemberId: from.ownerMemberId,
      toMemberId: to.ownerMemberId,
      recorderUserId: "member-zhang",
      amount: v.amount,
      occurredAt: v.occurredAt.format("YYYY-MM-DD"),
      remark: v.remark?.trim() || "账户转账",
    });
    api.success("转账已保存，未计入收支统计");
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
      title: "操作",
      render: (_, t) => (
        <Popconfirm
          title="删除转账？"
          description="删除后会反向恢复两个账户余额。"
          onConfirm={() => {
            deleteTransfer(t.id);
            api.success("转账已删除");
          }}
        >
          <Button type="text" danger icon={<DeleteOutlined />} />
        </Popconfirm>
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
        title="新增账户转账"
        open={open}
        onClose={() => setOpen(false)}
        width={430}
        footer={
          <Space className="drawer-actions">
            <Button onClick={() => setOpen(false)}>取消</Button>
            <Button type="primary" onClick={() => form.submit()}>
              保存转账
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
              options={active.map((a) => ({
                value: a.id,
                label: `${a.name} · ${memberLabel(a.ownerMemberId, members)}`,
              }))}
            />
          </Form.Item>
          <Form.Item
            label="转入账户"
            name="toAccountId"
            rules={[{ required: true }]}
          >
            <Select
              options={active.map((a) => ({
                value: a.id,
                label: `${a.name} · ${memberLabel(a.ownerMemberId, members)}`,
                disabled: a.id === form.getFieldValue("fromAccountId"),
              }))}
            />
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
