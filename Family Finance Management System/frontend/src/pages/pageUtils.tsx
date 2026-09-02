import { Tag } from "antd";
import {
  formatCurrency,
  type Account,
  type Category,
  type CategoryType,
  type FamilyMember,
} from "../data/financeData";

export const memberLabel = (id: string, members: FamilyMember[]) =>
  members.find((m) => m.id === id)?.name ?? "未知成员";

export const accountLabel = (id: string, accounts: Account[]) =>
  accounts.find((a) => a.id === id)?.name ?? "未知账户";

export const categoryLabel = (id: string, categories: Category[]) =>
  categories.find((c) => c.id === id)?.name ?? "已删除分类";

export const typeTag = (type: CategoryType) => (
  <Tag color={type === "INCOME" ? "green" : "volcano"}>
    {type === "INCOME" ? "收入" : "支出"}
  </Tag>
);

export const signedAmount = (type: CategoryType, amount: number) => (
  <span
    className={`amount amount--${type === "INCOME" ? "income" : "expense"}`}
  >
    {type === "INCOME" ? "+" : "-"}
    {formatCurrency(amount)}
  </span>
);
