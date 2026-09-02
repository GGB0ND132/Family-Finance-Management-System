import ReactECharts from "echarts-for-react";
import type { EChartsOption } from "echarts";
import dayjs, { type Dayjs } from "dayjs";
import {
  Card,
  DatePicker,
  Empty,
  Space,
  Statistic,
  Tabs,
  Tag,
  Typography,
} from "antd";
import { useMemo, useState } from "react";
import {
  categories,
  familyMembers,
  formatCurrency,
  trendData,
} from "../data/financeData";
import { useFinanceStore } from "../stores/financeStore";
import { ScopeToggle } from "../components/ScopeToggle";
import { useDataScope } from "../hooks/useDataScope";
import { currentUserId } from "../data/financeData";
export function ReportsPage() {
  const [month, setMonth] = useState("2026-09");
  const [mode] = useDataScope();
  const { transactions } = useFinanceStore();
  const scoped = transactions.filter(
    (t) =>
      t.occurredAt.startsWith(month) &&
      (mode === "family" || t.beneficiaryMemberId === currentUserId),
  );
  const income = scoped
    .filter((t) => t.type === "INCOME")
    .reduce((s, t) => s + t.amount, 0);
  const expense = scoped
    .filter((t) => t.type === "EXPENSE")
    .reduce((s, t) => s + t.amount, 0);
  const breakdown = useMemo(
    () =>
      categories
        .filter((c) => c.type === "EXPENSE")
        .map((c) => ({
          name: c.name,
          value: scoped
            .filter((t) => t.type === "EXPENSE" && t.categoryId === c.id)
            .reduce((s, t) => s + t.amount, 0),
          color: c.color,
        }))
        .filter((x) => x.value > 0),
    [scoped],
  );
  const trend: EChartsOption = {
    tooltip: {
      trigger: "axis",
      valueFormatter: (v) => formatCurrency(Number(v)),
    },
    legend: { data: ["收入", "支出", "结余"] },
    xAxis: { type: "category", data: trendData.map((x) => x.month) },
    yAxis: { type: "value" },
    series: [
      { name: "收入", type: "line", data: trendData.map((x) => x.income) },
      { name: "支出", type: "line", data: trendData.map((x) => x.expense) },
      {
        name: "结余",
        type: "line",
        data: trendData.map((x) => x.income - x.expense),
      },
    ],
  };
  const pie: EChartsOption = {
    tooltip: { trigger: "item" },
    series: [
      {
        type: "pie",
        radius: ["48%", "72%"],
        data: breakdown.map((x) => ({
          name: x.name,
          value: x.value,
          itemStyle: { color: x.color },
        })),
      },
    ],
  };
  const change = (v: Dayjs | null) => v && setMonth(v.format("YYYY-MM"));
  return (
    <div className="page">
      <div className="page-heading">
        <div>
          <Typography.Title level={2}>数据报表</Typography.Title>
          <Typography.Text>
            个人报表与家庭报表分开计算，转账不进入收支指标。
          </Typography.Text>
        </div>
        <Space>
          <ScopeToggle />
          <DatePicker
            picker="month"
            value={dayjs(month)}
            onChange={change}
            allowClear={false}
          />
        </Space>
      </div>
      <Card className="data-card">
        <Space size={40}>
          <Statistic
            title={mode === "family" ? "家庭收入" : "个人收入"}
            value={income}
            formatter={(v) => formatCurrency(Number(v))}
          />
          <Statistic
            title={mode === "family" ? "家庭支出" : "个人支出"}
            value={expense}
            formatter={(v) => formatCurrency(Number(v))}
          />
          <Statistic
            title="结余"
            value={income - expense}
            formatter={(v) => formatCurrency(Number(v))}
          />
        </Space>
      </Card>
      {scoped.length === 0 ? (
        <Card className="data-card">
          <Empty description="当前月份暂无可分析数据" />
        </Card>
      ) : (
        <Tabs
          items={[
            {
              key: "trend",
              label: "月度趋势",
              children: (
                <Card className="data-card">
                  <ReactECharts option={trend} style={{ height: 320 }} />
                </Card>
              ),
            },
            {
              key: "category",
              label: "分类占比",
              children: (
                <Card className="data-card">
                  <ReactECharts option={pie} style={{ height: 320 }} />
                </Card>
              ),
            },
            ...(mode === 'family' ? [{
              key: "members",
              label: "成员对比",
              children: (
                <Card className="data-card">
                  <Space direction="vertical" className="full-width">
                    {familyMembers.map((m) => {
                      const v = scoped
                        .filter(
                          (t) =>
                            t.type === "EXPENSE" &&
                            t.beneficiaryMemberId === m.id,
                        )
                        .reduce((s, t) => s + t.amount, 0);
                      return (
                        <div className="report-category-row" key={m.id}>
                          <span>
                            {m.name}
                            <Tag>{m.role === "ADMIN" ? "管理员" : "成员"}</Tag>
                          </span>
                          <strong>{formatCurrency(v)}</strong>
                        </div>
                      );
                    })}
                  </Space>
                </Card>
              ),
            }] : []),
          ]}
        />
      )}
    </div>
  );
}
