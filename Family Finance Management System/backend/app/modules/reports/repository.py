"""报表数据聚合（只读查询）。

聚合逻辑集中在仓库层，确保首页和报表页使用完全一致的口径：
仅统计 CONFIRMED 流水，转账不会进入收入、支出或结余。
"""

from calendar import monthrange
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.categories.models import Category
from app.modules.accounts.models import Account
from app.modules.families.models import FamilyMember
from app.modules.transfers.models import Transfer
from app.modules.transactions.models import Transaction
from app.modules.users.models import User


class ReportRepository:
    def __init__(self, db: Session):
        self.db = db

    def personal_daily(
        self, family_id: int, beneficiary_member_id: int, date: str
    ) -> dict:
        rows = self._transactions(family_id, beneficiary_member_id, date, date)
        result = self._summary(date, rows, family_id, beneficiary_member_id)
        result.pop("month", None)
        return result

    def personal_summary(
        self, family_id: int, beneficiary_member_id: int, from_date: str, to_date: str
    ) -> dict:
        rows = self._transactions(family_id, beneficiary_member_id, from_date, to_date)
        result = self._summary(to_date, rows, family_id, beneficiary_member_id)
        result.pop("date", None)
        return result

    def personal_trend(
        self, family_id: int, beneficiary_member_id: int, from_month: str, to_month: str
    ) -> list[dict]:
        rows = self._transactions(family_id, beneficiary_member_id, f"{from_month}-01", f"{to_month}-31")
        return self._trend(rows, from_month, to_month)

    def personal_by_category(
        self, family_id: int, beneficiary_member_id: int, month: str
    ) -> list[dict]:
        rows = self._transactions(family_id, beneficiary_member_id, f"{month}-01", f"{month}-31")
        return self._categories(rows)

    def family_summary(self, family_id: int, month: str) -> dict:
        rows = self._transactions(family_id, None, f"{month}-01", f"{month}-31")
        result = self._summary(month, rows, family_id)
        result.pop("date", None)
        return result

    def family_trend(
        self, family_id: int, from_month: str, to_month: str
    ) -> list[dict]:
        rows = self._transactions(family_id, None, f"{from_month}-01", f"{to_month}-31")
        return self._trend(rows, from_month, to_month)

    def family_by_category(self, family_id: int, month: str) -> list[dict]:
        rows = self._transactions(family_id, None, f"{month}-01", f"{month}-31")
        return self._categories(rows)

    def family_by_member(self, family_id: int, month: str) -> list[dict]:
        rows = self._transactions(family_id, None, f"{month}-01", f"{month}-31")
        members = self.db.execute(
            select(FamilyMember.id, User.nickname).join(User, User.id == FamilyMember.user_id)
            .where(FamilyMember.family_id == family_id).order_by(FamilyMember.id)
        ).all()
        result = []
        for member_id, name in members:
            member_rows = [row for row in rows if row.beneficiary_member_id == member_id]
            summary = self._summary(month, member_rows)
            accounts = self.db.scalars(select(Account).where(Account.family_id == family_id, Account.owner_member_id == member_id, Account.closed_at.is_(None))).all()
            assets = sum((account.current_balance for account in accounts), Decimal("0"))
            transfers = self.db.scalars(select(Transfer).where(Transfer.family_id == family_id, Transfer.status == "CONFIRMED", Transfer.from_member_id == member_id)).all()
            transfer_out = sum((item.amount for item in transfers), Decimal("0"))
            incoming = self.db.scalars(select(Transfer).where(Transfer.family_id == family_id, Transfer.status == "CONFIRMED", Transfer.to_member_id == member_id)).all()
            transfer_in = sum((item.amount for item in incoming), Decimal("0"))
            result.append({"member_id": member_id, "member_name": name, "income": summary["income"], "expense": summary["expense"], "assets": self._money(assets), "transfer_in": self._money(transfer_in), "transfer_out": self._money(transfer_out)})
        return result

    def _transactions(self, family_id: int, member_id: int | None, from_date: str, to_date: str) -> list[Transaction]:
        start_day = date.fromisoformat(from_date[:10])
        try:
            end_day = date.fromisoformat(to_date[:10])
        except ValueError:
            year, month = (int(part) for part in to_date[:7].split("-"))
            end_day = date(year, month, monthrange(year, month)[1])
        start = datetime.combine(start_day, datetime.min.time())
        end = datetime.combine(end_day, datetime.max.time())
        stmt = select(Transaction).where(
            Transaction.family_id == family_id,
            Transaction.status == "CONFIRMED",
            Transaction.occurred_at >= start,
            Transaction.occurred_at <= end,
        )
        if member_id is not None:
            stmt = stmt.where(Transaction.beneficiary_member_id == member_id)
        return list(self.db.scalars(stmt))

    @staticmethod
    def _money(value: Decimal | int | float) -> str:
        return f"{Decimal(value):.2f}"

    def _summary(self, period: str, rows: list[Transaction], family_id: int | None = None, member_id: int | None = None) -> dict:
        income = sum((row.amount for row in rows if row.type == "INCOME"), Decimal("0"))
        expense = sum((row.amount for row in rows if row.type == "EXPENSE"), Decimal("0"))
        result = {"month": period[:7] if len(period) > 7 else period, "date": period, "income": self._money(income), "expense": self._money(expense), "balance": self._money(income - expense)}
        if family_id is not None:
            account_query = select(Account).where(Account.family_id == family_id, Account.closed_at.is_(None))
            if member_id is not None:
                account_query = account_query.where(Account.owner_member_id == member_id)
            result["assets"] = self._money(sum((account.current_balance for account in self.db.scalars(account_query)), Decimal("0")))
        return result

    def _trend(self, rows: list[Transaction], from_month: str, to_month: str) -> list[dict]:
        points: dict[str, dict[str, Decimal]] = {}
        current = date.fromisoformat(f"{from_month}-01")
        end = date.fromisoformat(f"{to_month}-01")
        while current <= end:
            key = current.strftime("%Y-%m")
            points[key] = {"income": Decimal("0"), "expense": Decimal("0")}
            current = date(current.year + 1, 1, 1) if current.month == 12 else date(current.year, current.month + 1, 1)
        for row in rows:
            key = row.occurred_at.strftime("%Y-%m")
            if key in points:
                points[key]["income" if row.type == "INCOME" else "expense"] += row.amount
        return [{"month": key, "income": self._money(value["income"]), "expense": self._money(value["expense"])} for key, value in points.items()]

    def _categories(self, rows: list[Transaction]) -> list[dict]:
        totals: dict[int, Decimal] = {}
        for row in rows:
            if row.type == "EXPENSE":
                totals[row.category_id] = totals.get(row.category_id, Decimal("0")) + row.amount
        names = dict(self.db.execute(select(Category.id, Category.name).where(Category.id.in_(list(totals) or [-1]))).all())
        total = sum(totals.values(), Decimal("0"))
        return [{"category_id": category_id, "category_name": names.get(category_id, "未分类"), "amount": self._money(amount), "percentage": self._money((amount / total * 100) if total else 0)} for category_id, amount in sorted(totals.items(), key=lambda item: item[1], reverse=True)]
