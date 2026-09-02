import {
  DeleteOutlined,
  EditOutlined,
  ExportOutlined,
  FilterOutlined,
  PlusOutlined,
} from "@ant-design/icons";
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
import { useMemo, useState } from "react";
import {
  demoFamilyId,
  formatCurrency,
  type CategoryType,
  type FinanceTransaction,
} from "../data/financeData";
import { useFinanceStore } from "../stores/financeStore";
import {
  accountLabel,
  categoryLabel,
  memberLabel,
  signedAmount,
  typeTag,
} from "./pageUtils";

interface FormValues {
  type: CategoryType;
  accountId: string;
  categoryId: string;
  beneficiaryMemberId: string;
  amount: number;
  occurredAt: Dayjs;
  remark?: string;
}
export function TransactionsPage() {
  const [form] = Form.useForm<FormValues>();
  const [open, setOpen] = useState(false);
  const [editingId, setEditingId] = useState<string>();
  const [messageApi, holder] = message.useMessage();
  const [filters, setFilters] = useState<{
    type?: CategoryType;
    accountId?: string;
    ownerMemberId?: string;
    categoryId?: string;
    beneficiaryMemberId?: string;
    recorderUserId?: string;
    dates?: [Dayjs | null, Dayjs | null];
    min?: number;
    max?: number;
  }>({});
  const {
    transactions,
    accounts,
    categories,
    members,
    addTransaction,
    updateTransaction,
    deleteTransaction,
  } = useFinanceStore();
  const activeAccounts = accounts.filter((a) => !a.closedAt);
  const activeCategories = categories.filter((c) => !c.deletedAt);
  const activeType = Form.useWatch("type", form) ?? "EXPENSE";
  const filtered = useMemo(
    () =>
      transactions.filter((t) => {
        const a = accounts.find((x) => x.id === t.accountId);
        const f = filters;
        return (
          (!f.type || t.type === f.type) &&
          (!f.accountId || t.accountId === f.accountId) &&
          (!f.ownerMemberId || a?.ownerMemberId === f.ownerMemberId) &&
          (!f.categoryId || t.categoryId === f.categoryId) &&
          (!f.beneficiaryMemberId ||
            t.beneficiaryMemberId === f.beneficiaryMemberId) &&
          (!f.recorderUserId || t.recorderUserId === f.recorderUserId) &&
          (!f.dates ||
            ((!f.dates[0] || t.occurredAt >= f.dates[0].format("YYYY-MM-DD")) &&
              (!f.dates[1] ||
                t.occurredAt <= f.dates[1].format("YYYY-MM-DD")))) &&
          (f.min == null || t.amount >= f.min) &&
          (f.max == null || t.amount <= f.max)
        );
      }),
    [accounts, filters, transactions],
  );
  const clear = () => setFilters({});
  const openCreate = () => {
    setEditingId(undefined);
    form.resetFields();
    form.setFieldsValue({
      type: "EXPENSE",
      occurredAt: dayjs(),
      beneficiaryMemberId: "member-zhang",
    });
    setOpen(true);
  };
  const openEdit = (t: FinanceTransaction) => {
    setEditingId(t.id);
    form.setFieldsValue({ ...t, occurredAt: dayjs(t.occurredAt) });
    setOpen(true);
  };
  const save = (v: FormValues) => {
    const draft = {
      ...v,
      occurredAt: v.occurredAt.format("YYYY-MM-DD"),
      remark: v.remark?.trim() || "未填写备注",
      recorderUserId: "member-zhang",
    };
    if (editingId) updateTransaction(editingId, draft);
    else addTransaction(draft);
    messageApi.success(editingId ? "流水已更新" : "流水已保存");
    setOpen(false);
  };
  const columns: TableColumnsType<FinanceTransaction> = [
    { title: "日期", dataIndex: "occurredAt", width: 112 },
    { title: "类型", render: (_, t) => typeTag(t.type) },
    { title: "账户", render: (_, t) => accountLabel(t.accountId, accounts) },
    {
      title: "账户所属人",
      render: (_, t) =>
        memberLabel(
          accounts.find((a) => a.id === t.accountId)?.ownerMemberId ?? "",
          members,
        ),
    },
    {
      title: "分类",
      render: (_, t) => categoryLabel(t.categoryId, categories),
    },
    {
      title: "资金归属人",
      render: (_, t) => memberLabel(t.beneficiaryMemberId, members),
    },
    {
      title: "录入人",
      render: (_, t) => memberLabel(t.recorderUserId, members),
    },
    {
      title: "金额",
      align: "right",
      render: (_, t) => signedAmount(t.type, t.amount),
    },
    { title: "备注", dataIndex: "remark", ellipsis: true },
    {
      title: "操作",
      fixed: "right",
      width: 110,
      render: (_, t) => (
        <Space size={0}>
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => openEdit(t)}
            aria-label="编辑流水"
          />
          <Popconfirm
            title="删除这笔流水？"
            description="删除后会恢复账户余额。"
            onConfirm={() => {
              deleteTransaction(t.id);
              messageApi.success("流水已删除");
            }}
          >
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              aria-label="删除流水"
            />
          </Popconfirm>
        </Space>
      ),
    },
  ];
  const setFilter = (key: string, value: unknown) =>
    setFilters((f) => ({ ...f, [key]: value || undefined }));
  return (
    <div className="page">
      {holder}
      <div className="page-heading">
        <div>
          <Typography.Title level={2}>收支流水</Typography.Title>
          <Typography.Text>
            记录收入与支出。转账已独立到“账户转账”，不会进入收支统计。
          </Typography.Text>
        </div>
        <Space>
          <Button
            icon={<ExportOutlined />}
            onClick={() =>
              messageApi.info("演示模式：请前往数据导出选择 CSV 或 XLSX")
            }
          >
            导出
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
            新增流水
          </Button>
        </Space>
      </div>
      <Card className="filter-card" bordered={false}>
        <Space wrap size={[10, 10]}>
          <Select
            allowClear
            placeholder="全部类型"
            prefix={<FilterOutlined />}
            value={filters.type}
            onChange={(v) => setFilter("type", v)}
            options={[
              { value: "INCOME", label: "收入" },
              { value: "EXPENSE", label: "支出" },
            ]}
            className="filter-select"
          />
          <Select
            allowClear
            placeholder="账户"
            value={filters.accountId}
            onChange={(v) => setFilter("accountId", v)}
            options={activeAccounts.map((a) => ({
              value: a.id,
              label: a.name,
            }))}
            className="filter-select"
          />
          <Select
            allowClear
            placeholder="账户所属人"
            value={filters.ownerMemberId}
            onChange={(v) => setFilter("ownerMemberId", v)}
            options={members.map((m) => ({ value: m.id, label: m.name }))}
            className="filter-select"
          />
          <Select
            allowClear
            placeholder="分类"
            value={filters.categoryId}
            onChange={(v) => setFilter("categoryId", v)}
            options={activeCategories.map((c) => ({
              value: c.id,
              label: c.name,
            }))}
            className="filter-select"
          />
          <Select
            allowClear
            placeholder="资金归属人"
            value={filters.beneficiaryMemberId}
            onChange={(v) => setFilter("beneficiaryMemberId", v)}
            options={members.map((m) => ({ value: m.id, label: m.name }))}
            className="filter-select"
          />
          <Select
            allowClear
            placeholder="录入人"
            value={filters.recorderUserId}
            onChange={(v) => setFilter("recorderUserId", v)}
            options={members.map((m) => ({ value: m.id, label: m.name }))}
            className="filter-select"
          />
          <DatePicker.RangePicker
            value={filters.dates ?? null}
            onChange={(v) =>
              setFilters((f) => ({ ...f, dates: v ? [v[0], v[1]] : undefined }))
            }
          />
          <InputNumber
            min={0}
            placeholder="最低金额"
            value={filters.min}
            onChange={(v) => setFilter("min", v)}
          />
          <InputNumber
            min={0}
            placeholder="最高金额"
            value={filters.max}
            onChange={(v) => setFilter("max", v)}
          />
          <Button onClick={clear}>清除筛选</Button>
        </Space>
      </Card>
      <Card
        className="data-card transaction-table-card"
        title={`流水明细 · ${filtered.length} 笔`}
        extra={<Tag>{demoFamilyId}</Tag>}
      >
        <Table
          rowKey="id"
          columns={columns}
          dataSource={filtered}
          scroll={{ x: 1220 }}
          pagination={{ pageSize: 8, showSizeChanger: false }}
        />
      </Card>
      <Drawer
        title={editingId ? "编辑收支流水" : "新增收支流水"}
        width={460}
        open={open}
        onClose={() => setOpen(false)}
        destroyOnHidden
        footer={
          <Space className="drawer-actions">
            <Button onClick={() => setOpen(false)}>取消</Button>
            <Button type="primary" onClick={() => form.submit()}>
              保存流水
            </Button>
          </Space>
        }
      >
        <Form
          form={form}
          layout="vertical"
          requiredMark={false}
          onFinish={save}
        >
          <Form.Item label="流水类型" name="type" rules={[{ required: true }]}>
            <Select
              options={[
                { value: "INCOME", label: "收入" },
                { value: "EXPENSE", label: "支出" },
              ]}
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
            label="账户"
            name="accountId"
            rules={[{ required: true, message: "请选择未销户账户" }]}
          >
            <Select
              options={activeAccounts.map((a) => ({
                value: a.id,
                label: `${a.name} · ${formatCurrency(a.currentBalance)}`,
              }))}
            />
          </Form.Item>
          <Form.Item
            label="分类"
            name="categoryId"
            rules={[{ required: true }]}
          >
            <Select
              options={activeCategories.map((c) => ({
                value: c.id,
                label: `${c.icon} ${c.name}`,
                disabled: activeType !== c.type,
              }))}
            />
          </Form.Item>
          <Form.Item
            label="资金归属人"
            name="beneficiaryMemberId"
            rules={[{ required: true }]}
          >
            <Select
              options={members.map((m) => ({ value: m.id, label: m.name }))}
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
            <Input.TextArea rows={3} maxLength={80} showCount />
          </Form.Item>
        </Form>
      </Drawer>
    </div>
  );
}
