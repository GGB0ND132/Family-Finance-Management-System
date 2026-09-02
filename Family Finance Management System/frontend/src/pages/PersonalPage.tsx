import {
  ArrowDownOutlined,
  ArrowUpOutlined,
  PlusOutlined,
  SwapOutlined,
  WalletOutlined,
} from "@ant-design/icons";
import {
  Button,
  Card,
  Col,
  Empty,
  Row,
  Space,
  Statistic,
  Table,
  Typography,
} from "antd";
import type { TableColumnsType } from "antd";
import { useNavigate } from "react-router-dom";
import {
  demoMonth,
  formatCurrency,
  today,
  type FinanceTransaction,
} from "../data/financeData";
import { useFinanceStore } from "../stores/financeStore";
import {
  accountLabel,
  categoryLabel,
  signedAmount,
  typeTag,
} from "./pageUtils";

export function PersonalPage() {
  const navigate = useNavigate();
  const { transactions, transfers, accounts, categories } = useFinanceStore();
  const memberId = "member-zhang";
  const todayTransactions = transactions.filter(
    (t) => t.occurredAt === today && t.beneficiaryMemberId === memberId,
  );
  const income = todayTransactions
    .filter((t) => t.type === "INCOME")
    .reduce((s, t) => s + t.amount, 0);
  const expense = todayTransactions
    .filter((t) => t.type === "EXPENSE")
    .reduce((s, t) => s + t.amount, 0);
  const transferIn = transfers
    .filter((t) => t.toMemberId === memberId && t.occurredAt === today)
    .reduce((s, t) => s + t.amount, 0);
  const transferOut = transfers
    .filter((t) => t.fromMemberId === memberId && t.occurredAt === today)
    .reduce((s, t) => s + t.amount, 0);
  const assets = accounts
    .filter((a) => a.ownerMemberId === memberId && !a.closedAt)
    .reduce((s, a) => s + a.currentBalance, 0);
  const columns: TableColumnsType<FinanceTransaction> = [
    { title: "日期", dataIndex: "occurredAt", width: 110 },
    { title: "类型", render: (_, t) => typeTag(t.type) },
    {
      title: "分类",
      render: (_, t) => categoryLabel(t.categoryId, categories),
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
          <Typography.Title level={2}>个人首页</Typography.Title>
          <Typography.Text>
            只看归属于张三的收支与资产，转账单独统计。
          </Typography.Text>
        </div>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => navigate("/transactions")}
        >
          记一笔
        </Button>
      </div>
      <Row gutter={[16, 16]} className="summary-grid">
        <Col xs={24} sm={12} xl={6}>
          <Card className="summary-card summary-card--income">
            <Statistic
              title="今日收入"
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
              title="今日支出"
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
              title="今日转账"
              value={transferIn + transferOut}
              formatter={(v) => formatCurrency(Number(v))}
              prefix={
                <span className="summary-icon">
                  <SwapOutlined />
                </span>
              }
            />
            <span className="summary-card__hint">
              转入 {formatCurrency(transferIn)} · 转出{" "}
              {formatCurrency(transferOut)}
            </span>
          </Card>
        </Col>
        <Col xs={24} sm={12} xl={6}>
          <Card className="summary-card">
            <Statistic
              title="个人资产"
              value={assets}
              formatter={(v) => formatCurrency(Number(v))}
              prefix={
                <span className="summary-icon">
                  <WalletOutlined />
                </span>
              }
            />
            <span className="summary-card__hint">未销户账户余额合计</span>
          </Card>
        </Col>
      </Row>
      <Row gutter={[16, 16]} className="dashboard-row">
        <Col xs={24} lg={15}>
          <Card
            className="data-card"
            title="今日收支明细"
            extra={
              <Button type="link" onClick={() => navigate("/transactions")}>
                查看全部
              </Button>
            }
          >
            {todayTransactions.length ? (
              <Table
                rowKey="id"
                columns={columns}
                dataSource={todayTransactions}
                pagination={false}
                scroll={{ x: 620 }}
              />
            ) : (
              <Empty description="今天还没有归属于你的收支" />
            )}
          </Card>
        </Col>
        <Col xs={24} lg={9}>
          <Card className="data-card" title={`${demoMonth} 资产账户`}>
            <Space direction="vertical" className="full-width" size={12}>
              {accounts
                .filter((a) => a.ownerMemberId === memberId && !a.closedAt)
                .map((a) => (
                  <div className="report-category-row" key={a.id}>
                    <span>
                      <WalletOutlined />
                      {a.name}
                    </span>
                    <strong>{formatCurrency(a.currentBalance)}</strong>
                  </div>
                ))}
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  );
}
