import { DownloadOutlined } from "@ant-design/icons";
import {
  Button,
  Card,
  DatePicker,
  Select,
  Segmented,
  Space,
  Typography,
  message,
} from "antd";
import { useState } from "react";
import { useFinanceStore } from "../stores/financeStore";
export function ExportsPage() {
  const [format, setFormat] = useState<"CSV" | "XLSX">("CSV");
  const [api, holder] = message.useMessage();
  const { transactions } = useFinanceStore();
  const download = () => {
    if (format === "XLSX") {
      api.info(
        "演示模式：将调用后端 /api/v1/exports/transactions?format=xlsx 生成 Blob",
      );
      return;
    }
    const header = "date,type,amount,remark\n";
    const body = transactions
      .map((t) => `${t.occurredAt},${t.type},${t.amount},${t.remark}`)
      .join("\n");
    const blob = new Blob([header + body], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "family-transactions.csv";
    a.click();
    URL.revokeObjectURL(url);
    api.success("CSV 已下载");
  };
  return (
    <div className="page">
      {holder}
      <div className="page-heading">
        <div>
          <Typography.Title level={2}>数据导出</Typography.Title>
          <Typography.Text>
            按筛选条件导出收支流水，CSV 可直接下载，XLSX 由后端生成。
          </Typography.Text>
        </div>
      </div>
      <Card className="data-card" title="导出条件">
        <Space wrap>
          <DatePicker.RangePicker />
          <Select
            allowClear
            placeholder="类型"
            options={[
              { value: "INCOME", label: "收入" },
              { value: "EXPENSE", label: "支出" },
            ]}
            style={{ width: 150 }}
          />
          <Segmented
            value={format}
            onChange={(v) => setFormat(v as "CSV" | "XLSX")}
            options={[
              { value: "CSV", label: "CSV" },
              { value: "XLSX", label: "XLSX" },
            ]}
          />
          <Button type="primary" icon={<DownloadOutlined />} onClick={download}>
            导出 {format}
          </Button>
        </Space>
      </Card>
    </div>
  );
}
