import { CopyOutlined, SaveOutlined } from "@ant-design/icons";
import dayjs, { type Dayjs } from "dayjs";
import {
  Alert,
  Button,
  Card,
  DatePicker,
  Empty,
  InputNumber,
  Progress,
  Space,
  Tag,
  Typography,
  message,
} from "antd";
import { useMemo, useState } from "react";
import { categories, demoMonth, formatCurrency } from "../data/financeData";
import { useFinanceStore } from "../stores/financeStore";

export function BudgetsPage() {
  const [month, setMonth] = useState(demoMonth);
  const [total, setTotal] = useState(0);
  const [items, setItems] = useState<Record<string, number>>({});
  const [api, holder] = message.useMessage();
  const { budgets, transactions, saveBudget, copyBudget } = useFinanceStore();
  const budget = budgets.find((b) => b.month === month);
  const expenseByCategory = useMemo(
    () =>
      Object.fromEntries(
        categories.map((c) => [
          c.id,
          transactions
            .filter(
              (t) =>
                t.type === "EXPENSE" &&
                t.categoryId === c.id &&
                t.occurredAt.startsWith(month),
            )
            .reduce((s, t) => s + t.amount, 0),
        ]),
      ),
    [month, transactions],
  );
  const currentTotal = budget?.totalAmount ?? total;
  const currentItems = budget
    ? Object.fromEntries(budget.items.map((i) => [i.categoryId, i.amount]))
    : items;
  const used = transactions
    .filter((t) => t.type === "EXPENSE" && t.occurredAt.startsWith(month))
    .reduce((s, t) => s + t.amount, 0);
  const percent = currentTotal ? Math.round((used / currentTotal) * 100) : 0;
  const save = () => {
    saveBudget(
      month,
      currentTotal,
      categories
        .filter((c) => c.type === "EXPENSE" && !c.deletedAt)
        .map((c) => ({ categoryId: c.id, amount: currentItems[c.id] ?? 0 }))
        .filter((i) => i.amount > 0),
    );
    api.success("预算已保存");
  };
  const changeMonth = (v: Dayjs | null) => {
    if (v) {
      setMonth(v.format("YYYY-MM"));
      const b = budgets.find((x) => x.month === v.format("YYYY-MM"));
      setTotal(b?.totalAmount ?? 0);
      setItems(
        Object.fromEntries(
          (b?.items ?? []).map((i) => [i.categoryId, i.amount]),
        ),
      );
    }
  };
  return (
    <div className="page">
      {holder}
      <div className="page-heading">
        <div>
          <Typography.Title level={2}>月度预算</Typography.Title>
          <Typography.Text>
            按月维护总预算和分类预算，支出超过 80% 进入预警。
          </Typography.Text>
        </div>
        <Space>
          <DatePicker
            picker="month"
            value={dayjs(month)}
            onChange={changeMonth}
            allowClear={false}
          />
          <Button
            icon={<CopyOutlined />}
            onClick={() => {
              copyBudget(month);
              api.success("已复制上月预算");
            }}
          >
            复制上月
          </Button>
          <Button type="primary" icon={<SaveOutlined />} onClick={save}>
            保存预算
          </Button>
        </Space>
      </div>
      <Card className="data-card" title="月度总预算">
        <Space align="center">
          <InputNumber
            min={0}
            precision={2}
            value={currentTotal}
            onChange={(v) => setTotal(v ?? 0)}
            addonBefore="¥"
          />
          <span>已支出 {formatCurrency(used)}</span>
          <Progress
            percent={Math.min(percent, 100)}
            status={
              percent > 100 ? "exception" : percent >= 80 ? "active" : "normal"
            }
          />
        </Space>
        {percent >= 80 && (
          <Alert
            className="budget-alert"
            showIcon
            type={percent > 100 ? "error" : "warning"}
            message={percent > 100 ? "总预算已超支" : "预算使用达到预警线"}
          />
        )}
      </Card>
      <Card className="data-card" title="分类预算">
        <div className="budget-list">
          {categories
            .filter((c) => c.type === "EXPENSE" && !c.deletedAt)
            .map((c) => {
              const limit = currentItems[c.id] ?? 0;
              const actual = expenseByCategory[c.id] ?? 0;
              const p = limit ? Math.round((actual / limit) * 100) : 0;
              return (
                <div className="budget-item" key={c.id}>
                  <div className="budget-item__heading">
                    <Space>
                      <span
                        className="category-dot category-dot--large"
                        style={{ background: c.color }}
                      />
                      <div>
                        <strong>{c.name}</strong>
                        <span>本月支出 {formatCurrency(actual)}</span>
                      </div>
                    </Space>
                    <InputNumber
                      min={0}
                      precision={2}
                      value={limit}
                      onChange={(v) =>
                        setItems((old) => ({ ...old, [c.id]: v ?? 0 }))
                      }
                      addonBefore="¥"
                    />
                  </div>
                  <div className="budget-item__progress">
                    <Progress
                      percent={Math.min(p, 100)}
                      status={
                        p > 100 ? "exception" : p >= 80 ? "active" : "normal"
                      }
                    />
                    <Tag color={p > 100 ? "red" : p >= 80 ? "gold" : "green"}>
                      {p > 100 ? "超支" : p >= 80 ? "预警" : "正常"}
                    </Tag>
                  </div>
                </div>
              );
            })}
        </div>
      </Card>
      {!budget && !total && <Empty description="当前月份尚未设置预算" />}
    </div>
  );
}
