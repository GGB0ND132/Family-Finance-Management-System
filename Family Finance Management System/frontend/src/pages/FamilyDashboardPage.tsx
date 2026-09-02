import {
  ArrowDownOutlined,
  ArrowUpOutlined,
  CreditCardOutlined,
  PlusOutlined,
  WalletOutlined,
} from "@ant-design/icons";
import ReactECharts from "echarts-for-react";
import type { EChartsOption } from "echarts";
import {
  Alert,
  Button,
  Card,
  Col,
  Progress,
  Row,
  Space,
  Statistic,
  Table,
  Typography,
} from "antd";
import type { TableColumnsType } from "antd";
import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import {
  demoMonth,
  formatCurrency,
  trendData,
  type FinanceTransaction,
} from "../data/financeData";
import { useFinanceStore } from "../stores/financeStore";
import {
  accountLabel,
  categoryLabel,
  memberLabel,
  signedAmount,
} from "./pageUtils";

export function FamilyDashboardPage() {
  const navigate = useNavigate();
  const { transactions, transfers, accounts, categories, budgets, members } =
    useFinanceStore();
  const monthTransactions = transactions.filter((t) =>
    t.occurredAt.startsWith(demoMonth),
  );
  const income = monthTransactions
    .filter((t) => t.type === "INCOME")
    .reduce((s, t) => s + t.amount, 0);
  const expense = monthTransactions
    .filter((t) => t.type === "EXPENSE")
    .reduce((s, t) => s + t.amount, 0);
  const assets = accounts
    .filter((a) => !a.closedAt)
    .reduce((s, a) => s + a.currentBalance, 0);
  const budget = budgets.find((b) => b.month === demoMonth);
  const usedPercent = budget?.totalAmount
    ? Math.round((expense / budget.totalAmount) * 100)
    : 0;
  const breakdown = useMemo(
    () =>
      categories
        .filter((c) => c.type === "EXPENSE" && !c.deletedAt)
        .map((c) => ({
          name: c.name,
          value: monthTransactions
            .filter((t) => t.type === "EXPENSE" && t.categoryId === c.id)
            .reduce((s, t) => s + t.amount, 0),
          color: c.color,
        }))
        .filter((x) => x.value > 0),
    [categories, monthTransactions],
  );
  const pieOption: EChartsOption = {
    tooltip: {
      trigger: "item",
      valueFormatter: (v) => formatCurrency(Number(v)),
    },
    series: [
      {
        type: "pie",
        radius: ["48%", "72%"],
        label: { formatter: "{b}\n{d}%" },
        data: breakdown.map((x) => ({
          name: x.name,
          value: x.value,
          itemStyle: { color: x.color },
        })),
      },
    ],
  };
  const trendOption: EChartsOption = {
    tooltip: {
      trigger: "axis",
      valueFormatter: (v) => formatCurrency(Number(v)),
    },
    legend: { data: ["收入", "支出", "结余"] },
    xAxis: { type: "category", data: trendData.map((x) => x.month) },
    yAxis: { type: "value" },
    series: [
      {
        name: "收入",
        type: "line",
        smooth: true,
        data: trendData.map((x) => x.income),
        itemStyle: { color: "#3f8f62" },
      },
      {
        name: "支出",
        type: "line",
        smooth: true,
        data: trendData.map((x) => x.expense),
        itemStyle: { color: "#c85b4b" },
      },
      {
        name: "结余",
        type: "line",
        smooth: true,
        data: trendData.map((x) => x.income - x.expense),
        itemStyle: { color: "#5579a7" },
      },
    ],
  };
  const columns: TableColumnsType<FinanceTransaction> = [
    { title: "日期", dataIndex: "occurredAt" },
    {
      title: "分类",
      render: (_, t) => categoryLabel(t.categoryId, categories),
    },
    {
      title: "资金归属人",
      render: (_, t) => memberLabel(t.beneficiaryMemberId, members),
    },
    { title: "账户", render: (_, t) => accountLabel(t.accountId, accounts) },
    {
      title: "金额",
      align: "right",
      render: (_, t) => signedAmount(t.type, t.amount),
    },
  ];
  return (
    <div className="page">
      <div className="page-heading">
        <div>
          <Typography.Title level={2}>家庭首页</Typography.Title>
          <Typography.Text>
            2026 年 9 月，家庭共同账本的收支与预算。
          </Typography.Text>
        </div>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => navigate("/transactions")}
        >
          快速记一笔
        </Button>
      </div>
      <Row gutter={[16, 16]} className="summary-grid">
        <Col xs={24} sm={12} xl={6}>
          <Card className="summary-card summary-card--income">
            <Statistic
              title="本月收入"
              value={income}
              formatter={(v) => formatCurrency(Number(v))}
              prefix={
                <span className="summary-icon">
                  <ArrowUpOutlined />
                </span>
              }
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} xl={6}>
          <Card className="summary-card summary-card--expense">
            <Statistic
              title="本月支出"
              value={expense}
              formatter={(v) => formatCurrency(Number(v))}
              prefix={
                <span className="summary-icon">
                  <ArrowDownOutlined />
                </span>
              }
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} xl={6}>
          <Card className="summary-card">
            <Statistic
              title="本月结余"
              value={income - expense}
              formatter={(v) => formatCurrency(Number(v))}
              prefix={
                <span className="summary-icon">
                  <WalletOutlined />
                </span>
              }
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} xl={6}>
          <Card className="summary-card">
            <Statistic
              title="家庭总资产"
              value={assets}
              formatter={(v) => formatCurrency(Number(v))}
              prefix={
                <span className="summary-icon">
                  <CreditCardOutlined />
                </span>
              }
            />
          </Card>
        </Col>
      </Row>
      <Row gutter={[16, 16]} className="dashboard-row">
        <Col xs={24} xl={16}>
          <Card className="data-card chart-card" title="近六个月收支趋势">
            <ReactECharts option={trendOption} style={{ height: 286 }} />
          </Card>
        </Col>
        <Col xs={24} xl={8}>
          <Card
            className="data-card budget-card"
            title="本月预算"
            extra={
              <Button type="link" onClick={() => navigate("/budgets")}>
                管理
              </Button>
            }
          >
            <div className="budget-card__main">
              <div>
                <strong>{formatCurrency(expense)}</strong>
                <span>已使用 / {formatCurrency(budget?.totalAmount ?? 0)}</span>
              </div>
              <Progress
                type="circle"
                percent={Math.min(usedPercent, 100)}
                format={() => `${usedPercent}%`}
              />
            </div>
            {usedPercent >= 80 && (
              <Alert
                type={usedPercent > 100 ? "error" : "warning"}
                showIcon
                message={
                  usedPercent > 100 ? "本月预算已超支" : "本月预算即将达到上限"
                }
              />
            )}
          </Card>
        </Col>
      </Row>
      <Row gutter={[16, 16]} className="dashboard-row">
        <Col xs={24} lg={14}>
          <Card
            className="data-card"
            title="最近流水"
            extra={
              <Button type="link" onClick={() => navigate("/transactions")}>
                查看全部
              </Button>
            }
          >
            <Table
              rowKey="id"
              columns={columns}
              dataSource={monthTransactions.slice(0, 6)}
              pagination={false}
              scroll={{ x: 640 }}
            />
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card className="data-card category-card" title="支出分类占比">
            <Space align="start">
              <ReactECharts
                option={pieOption}
                style={{ width: 190, height: 220 }}
              />
              <div className="category-legend">
                {breakdown.slice(0, 5).map((x) => (
                  <div key={x.name}>
                    <span
                      className="category-dot"
                      style={{ background: x.color }}
                    />
                    <span>{x.name}</span>
                    <b>{formatCurrency(x.value)}</b>
                  </div>
                ))}
              </div>
            </Space>
          </Card>
        </Col>
      </Row>
      <Card className="data-card" title="转账流动（不计入收支）">
        <Table
          rowKey="id"
          size="small"
          pagination={false}
          dataSource={transfers
            .filter((t) => t.occurredAt.startsWith(demoMonth))
            .slice(0, 4)}
          columns={[
            { title: "日期", dataIndex: "occurredAt" },
            {
              title: "方向",
              render: (_, t) =>
                `${memberLabel(t.fromMemberId, members)} → ${memberLabel(t.toMemberId, members)}`,
            },
            {
              title: "金额",
              align: "right",
              render: (_, t) => (
                <span className="amount amount--transfer">
                  {formatCurrency(t.amount)}
                </span>
              ),
            },
            { title: "备注", dataIndex: "remark" },
          ]}
        />
      </Card>
    </div>
  );
}
