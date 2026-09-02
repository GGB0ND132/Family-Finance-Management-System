import { InboxOutlined } from "@ant-design/icons";
import {
  Alert,
  Button,
  Card,
  Empty,
  Select,
  Space,
  Steps,
  Table,
  Tag,
  Typography,
  Upload,
  message,
} from "antd";
import type { UploadProps } from "antd";
import { useState } from "react";
import { useFinanceStore } from "../stores/financeStore";
import { ScopeToggle } from "../components/ScopeToggle";
import { useDataScope } from "../hooks/useDataScope";
import { currentUserId } from "../data/financeData";
export function ImportsPage() {
  const [step, setStep] = useState(0);
  const [api, holder] = message.useMessage();
  const [accountId, setAccountId] = useState<string>();
  const [file, setFile] = useState<{ name: string; type: "CSV" | "XLSX" }>();
  const { accounts, addImport, imports, confirmImport } = useFinanceStore();
  const [scope] = useDataScope();
  const batch = imports.at(-1);
  const uploadProps: UploadProps = {
    beforeUpload: (f) => {
      const type = f.name.toLowerCase().endsWith(".xlsx") ? "XLSX" : "CSV";
      setFile({ name: f.name, type });
      setStep(1);
      return false;
    },
    showUploadList: false,
  };
  const preview = () => {
    if (!file || !accountId) return;
    addImport({
      fileName: file.name,
      fileType: file.type,
      rows: [
        {
          rowNumber: 2,
          date: "2026-09-06",
          amount: 128.5,
          direction: "EXPENSE",
          remark: "导入示例",
          status: "VALID",
        },
        {
          rowNumber: 3,
          date: "无效日期",
          amount: 0,
          direction: null,
          remark: "待修正",
          status: "INVALID",
          error: "日期格式无法识别",
        },
        {
          rowNumber: 4,
          date: "2026-09-03",
          amount: 86.5,
          direction: "EXPENSE",
          remark: "晚餐",
          status: "DUPLICATE",
          error: "与已有流水重复",
        },
      ],
    });
    setStep(2);
  };
  return (
    <div className="page">
      {holder}
      <div className="page-heading">
        <div>
          <Typography.Title level={2}>账单导入</Typography.Title>
          <Typography.Text>
            通过三步流程导入 CSV/XLSX，先预览异常与重复行，再确认写入。
          </Typography.Text>
        </div><ScopeToggle />
      </div>
      <Card className="data-card">
        <Steps
          current={step}
          items={[
            { title: "选择账户与来源" },
            { title: "上传与字段映射" },
            { title: "预览并确认" },
          ]}
        />
      </Card>
      {step === 0 && (
        <Card className="data-card" title="1. 选择目标账户">
          <Select
            placeholder="选择目标账户"
            value={accountId}
            onChange={setAccountId}
            options={accounts
              .filter((a) => !a.closedAt && (scope === 'family' || a.ownerMemberId === currentUserId))
              .map((a) => ({ value: a.id, label: a.name }))}
            style={{ width: 300 }}
          />
          <div style={{ marginTop: 24 }}>
            <Upload.Dragger {...uploadProps} disabled={!accountId}>
              <p className="ant-upload-drag-icon">
                <InboxOutlined />
              </p>
              <p>选择 CSV 或 XLSX 文件</p>
              <p className="ant-upload-hint">
                演示模式不会解析真实文件，会生成预览样例。
              </p>
            </Upload.Dragger>
          </div>
        </Card>
      )}
      {step === 1 && (
        <Card className="data-card" title="2. 字段映射">
          <Alert
            message={`已选择 ${file?.name ?? "文件"}`}
            description="日期、金额、收支方向、备注字段将映射到流水模型。"
            showIcon
          />
          <Space style={{ marginTop: 20 }}>
            <Select
              defaultValue="date"
              options={[{ value: "date", label: "日期列：日期" }]}
            />
            <Select
              defaultValue="amount"
              options={[{ value: "amount", label: "金额列：金额" }]}
            />
            <Select
              defaultValue="remark"
              options={[{ value: "remark", label: "备注列：备注" }]}
            />
            <Button type="primary" onClick={preview}>
              生成预览
            </Button>
          </Space>
        </Card>
      )}
      {step === 2 &&
        (batch ? (
          <Card
            className="data-card"
            title="3. 预览并确认"
            extra={<Button onClick={() => setStep(0)}>重新选择</Button>}
          >
            <Space style={{ marginBottom: 16 }}>
              <Tag color="green">
                有效 {batch.rows.filter((r) => r.status === "VALID").length}
              </Tag>
              <Tag color="gold">
                重复 {batch.rows.filter((r) => r.status === "DUPLICATE").length}
              </Tag>
              <Tag color="red">
                非法 {batch.rows.filter((r) => r.status === "INVALID").length}
              </Tag>
            </Space>
            <Table
              rowKey="rowNumber"
              dataSource={batch.rows}
              pagination={false}
              columns={[
                { title: "行号", dataIndex: "rowNumber" },
                { title: "发生时间", dataIndex: "date" },
                { title: "金额", dataIndex: "amount" },
                { title: "备注", dataIndex: "remark" },
                {
                  title: "状态",
                  render: (_, r) => (
                    <Tag
                      color={
                        r.status === "VALID"
                          ? "green"
                          : r.status === "DUPLICATE"
                            ? "gold"
                            : "red"
                      }
                    >
                      {r.status === "VALID"
                        ? "有效"
                        : r.status === "DUPLICATE"
                          ? "重复"
                          : "非法"}
                    </Tag>
                  ),
                },
                { title: "错误信息", dataIndex: "error" },
              ]}
            />
            <Button
              type="primary"
              style={{ marginTop: 20 }}
              disabled={batch.rows.some((r) => r.status === "INVALID")}
              onClick={() => {
                confirmImport(batch.id);
                api.success("导入已确认，后端接入后将批量创建流水");
              }}
            >
              确认导入有效行
            </Button>
          </Card>
        ) : (
          <Empty />
        ))}
    </div>
  );
}
