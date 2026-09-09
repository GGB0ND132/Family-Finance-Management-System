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
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import dayjs from "dayjs";
import { reportApi } from "../api/reportsApi";
import { transactionApi } from "../api/transactionsApi";
import { transferApi } from "../api/transfersApi";
import { accountApi } from "../api/accountsApi";
import { budgetApi } from "../api/budgetsApi";
import type { TransactionResponse, TransferResponse, AccountResponse, BudgetResponse } from "../api/contracts";
import { useAuthStore } from "../stores/authStore";
import { Skeleton } from "antd";
import { HomeScopeToggle } from "../components/HomeScopeToggle";
const formatCurrency = (value: number) => new Intl.NumberFormat("zh-CN", { style: "currency", currency: "CNY" }).format(value);

export function FamilyDashboardPage() {
  const navigate = useNavigate();
  const month = dayjs().format("YYYY-MM");
  const endOfMonth = dayjs(`${month}-01`).endOf("month").format("YYYY-MM-DD");
  const familyId = useAuthStore((state) => state.familyId);
  const [report, setReport] = useState<{ income: number; expense: number; balance: number; assets?: number } | null>(null);
  const [remoteTrend, setRemoteTrend] = useState<Array<{ month: string; income: number; expense: number }>>([]);
  const [remoteBreakdown, setRemoteBreakdown] = useState<Array<{ name: string; value: number; color: string }>>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const [remoteLoaded, setRemoteLoaded] = useState(false);
  const [remoteTransactions, setRemoteTransactions] = useState<TransactionResponse[]>([]);
  const [remoteTransfers, setRemoteTransfers] = useState<TransferResponse[]>([]);
  const [remoteAccounts, setRemoteAccounts] = useState<AccountResponse[]>([]);
  const [remoteBudget, setRemoteBudget] = useState<BudgetResponse | null>(null);
  useEffect(() => {
    if (!familyId) return;
    setLoading(true); setError(false); setRemoteLoaded(false);
    const id = Number(familyId);
    Promise.all([reportApi.familySummary({ family_id: id, month }), reportApi.familyTrend({ family_id: id, from_month: dayjs(`${month}-01`).subtract(5, "month").format("YYYY-MM"), to_month: month }), reportApi.familyByCategory({ family_id: id, month }), transactionApi.list({ family_id: familyId, scope: "family", from: `${month}-01T00:00`, to: `${endOfMonth}T23:59`, page: 1, page_size: 100 }), transferApi.list({ family_id: id, scope: "family", from: `${month}-01T00:00`, to: `${endOfMonth}T23:59`, page: 1, page_size: 100 }), accountApi.list({ family_id: id, scope: "family", include_closed: false, page: 1, page_size: 100 }), budgetApi.get(month, { family_id: id, scope: "family" })])
      .then(([summary, trend, category, tx, tr, ac, budget]) => {
        const s = (summary.data as { data?: { income?: string; expense?: string; balance?: string; assets?: string } }).data;
        const t = (trend.data as { data?: Array<{ month: string; income: string; expense: string }> }).data ?? [];
        const c = (category.data as { data?: Array<{ category_name: string; amount: string; percentage?: string }> }).data ?? [];
        if (s) setReport({ income: Number(s.income ?? 0), expense: Number(s.expense ?? 0), balance: Number(s.balance ?? 0), assets: Number(s.assets ?? 0) });
        setRemoteTrend(t.map((x) => ({ month: x.month.slice(5) + "月", income: Number(x.income), expense: Number(x.expense) })));
        setRemoteBreakdown(c.map((x) => ({ name: x.category_name, value: Number(x.amount), color: "#58754d" })));
        setRemoteTransactions(tx.data.data?.items ?? []); setRemoteTransfers(tr.data.data?.items ?? []); setRemoteAccounts(ac.data.data?.items ?? []); setRemoteBudget(budget.data.data ?? null);
        setRemoteLoaded(true);
      })
      .catch(() => setError(true)).finally(() => setLoading(false));
  }, [familyId, month, endOfMonth]);
  const monthTransactions = remoteLoaded ? remoteTransactions : [];
  const localIncome = monthTransactions
    .filter((t) => t.type === "INCOME")
    .reduce((s, t) => s + Number(t.amount), 0);
  const localExpense = monthTransactions
    .filter((t) => t.type === "EXPENSE")
    .reduce((s, t) => s + Number(t.amount), 0);
  const income = report?.income ?? localIncome;
  const expense = report?.expense ?? localExpense;
  const localAssets = remoteAccounts.reduce((s, a) => s + Number(a.current_balance), 0);
  const assets = report?.assets ?? localAssets;
  const usedPercent = remoteBudget?.total_amount
    ? Math.round((Number(remoteBudget.used_amount) / Number(remoteBudget.total_amount)) * 100)
    : 0;
  const breakdown = useMemo(
    () =>
      remoteBreakdown,
    [remoteBreakdown],
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
    xAxis: { type: "category", data: remoteTrend.map((x) => x.month) },
    yAxis: { type: "value" },
    series: [
      {
        name: "收入",
        type: "line",
        smooth: true,
        data: remoteTrend.map((x) => x.income),
        itemStyle: { color: "#3f8f62" },
      },
      {
        name: "支出",
        type: "line",
        smooth: true,
        data: remoteTrend.map((x) => x.expense),
        itemStyle: { color: "#c85b4b" },
      },
      {
        name: "结余",
        type: "line",
        smooth: true,
        data: remoteTrend.map((x) => x.income - x.expense),
        itemStyle: { color: "#5579a7" },
      },
    ],
  };
  const columns: TableColumnsType<TransactionResponse> = [
    { title: "日期", dataIndex: "occurred_at" },
    {
      title: "分类",
      render: (_, t) => t.category_name ?? "未分类",
    },
    {
      title: "资金归属人",
      render: (_, t) => t.beneficiary_nickname ?? "未知成员",
    },
    { title: "账户", render: (_, t) => t.account_name ?? "未知账户" },
    {
      title: "金额",
      align: "right",
      render: (_, t) => <span className={`amount amount--${t.type === "INCOME" ? "income" : "expense"}`}>{t.type === "INCOME" ? "+" : "-"}{formatCurrency(Number(t.amount))}</span>,
    },
  ];
  return (
    <div className="page">
      <div className="page-heading">
        <div>
          <Typography.Title level={2}>家庭首页</Typography.Title>
          <Typography.Text>
            {month.replace('-', ' 年 ')} 月，家庭共同账本的收支与预算。
          </Typography.Text>
        </div>
        <Space direction="vertical" align="end" size={10}><HomeScopeToggle /><Button type="primary" icon={<PlusOutlined />} onClick={() => navigate("/transactions")}>快速记一笔</Button></Space>
      </div>
      {error && <Alert type="warning" showIcon message="报表接口暂时不可用，当前显示本地缓存数据" style={{ marginBottom: 16 }} />}
      {loading && <Skeleton active paragraph={{ rows: 1 }} style={{ marginBottom: 16 }} />}
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
                <span>已使用 / {formatCurrency(Number(remoteBudget?.total_amount ?? 0))}</span>
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
          dataSource={remoteTransfers.slice(0, 4)}
          columns={[
            { title: "日期", dataIndex: "occurredAt" },
            {
              title: "方向",
              render: (_, t) => `${t.from_member_nickname ?? '未知成员'} → ${t.to_member_nickname ?? '未知成员'}`,
            },
            {
              title: "金额",
              align: "right",
              render: (_, t) => (
                <span className="amount amount--transfer">
                  {formatCurrency(Number(t.amount))}
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
