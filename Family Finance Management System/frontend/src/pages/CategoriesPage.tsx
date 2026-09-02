import { DeleteOutlined, EditOutlined, PlusOutlined } from "@ant-design/icons";
import {
  Button,
  Card,
  Drawer,
  Form,
  Input,
  Segmented,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from "antd";
import type { TableColumnsType } from "antd";
import { useState } from "react";
import { useFinanceStore } from "../stores/financeStore";
import type { Category, CategoryType } from "../data/financeData";
import { ScopeToggle } from "../components/ScopeToggle";
type CategoryForm = {
  name: string;
  type: CategoryType;
  color: string;
  icon?: string;
};
export function CategoriesPage() {
  const [form] = Form.useForm<CategoryForm>();
  const [type, setType] = useState<CategoryType>("EXPENSE");
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<string>();
  const [api, holder] = message.useMessage();
  const { categories, addCategory, updateCategory, removeOrDeleteCategory } =
    useFinanceStore();
  const displayed = categories.filter((c) => c.type === type);
  const submit = (v: CategoryForm) => {
    if (editing) updateCategory(editing, v);
    else addCategory(v as Omit<Category, "id" | "deletedAt">);
    api.success(editing ? "分类已更新" : "分类已创建");
    setOpen(false);
  };
  const columns: TableColumnsType<Category> = [
    {
      title: "分类",
      render: (_, c) => (
        <Space>
          <span
            className="category-dot category-dot--large"
            style={{ background: c.color }}
          />
          {c.icon}
          <strong>{c.name}</strong>
        </Space>
      ),
    },
    {
      title: "类型",
      render: (_, c) => (c.type === "INCOME" ? "收入" : "支出"),
    },
    {
      title: "状态",
      render: (_, c) =>
        c.deletedAt ? (
          <Tag>保留历史</Tag>
        ) : (
          <Tag color="green">可用于新记录</Tag>
        ),
    },
    {
      title: "操作",
      render: (_, c) => (
        <Space>
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => {
              setEditing(c.id);
              form.setFieldsValue(c);
              setOpen(true);
            }}
          />
          <Button
            type="text"
            danger
            icon={<DeleteOutlined />}
            onClick={() => {
              const result = removeOrDeleteCategory(c.id);
              api.success(
                result === "HIDDEN" ? "分类已停用并保留历史名称" : "分类已删除",
              );
            }}
          />
        </Space>
      ),
    },
  ];
  return (
    <div className="page">
      {holder}
      <div className="page-heading">
        <div>
          <Typography.Title level={2}>分类管理</Typography.Title>
          <Typography.Text>
            按收入和支出分组。被历史流水引用的分类会保留名称，但不能用于新记录。
          </Typography.Text>
        </div>
        <Space><ScopeToggle /><Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            setEditing(undefined);
            form.resetFields();
            form.setFieldsValue({ type, color: "#58754d", icon: "•" });
            setOpen(true);
          }}
        >
          新增分类
        </Button></Space>
      </div>
      <Card className="filter-card" bordered={false}>
        <Segmented
          value={type}
          onChange={(v) => setType(v as CategoryType)}
          options={[
            { value: "EXPENSE", label: "支出分类" },
            { value: "INCOME", label: "收入分类" },
          ]}
        />
      </Card>
      <Card
        className="data-card"
        title={`${type === "INCOME" ? "收入" : "支出"}分类 · ${displayed.length} 项`}
      >
        <Table
          rowKey="id"
          columns={columns}
          dataSource={displayed}
          pagination={false}
        />
      </Card>
      <Drawer
        title={editing ? "编辑分类" : "新增分类"}
        open={open}
        onClose={() => setOpen(false)}
        width={420}
        footer={
          <Space className="drawer-actions">
            <Button onClick={() => setOpen(false)}>取消</Button>
            <Button type="primary" onClick={() => form.submit()}>
              保存分类
            </Button>
          </Space>
        }
      >
        <Form form={form} layout="vertical" onFinish={submit}>
          <Form.Item label="分类名称" name="name" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item label="分类类型" name="type" rules={[{ required: true }]}>
            <Segmented
              options={[
                { value: "EXPENSE", label: "支出" },
                { value: "INCOME", label: "收入" },
              ]}
            />
          </Form.Item>
          <Form.Item label="图标" name="icon">
            <Input />
          </Form.Item>
          <Form.Item label="颜色" name="color" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
        </Form>
      </Drawer>
    </div>
  );
}
