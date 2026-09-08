"""预算数据访问。"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.budgets.models import CategoryBudget, MonthlyBudget
from app.modules.transactions.models import Transaction


class BudgetRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_month(
        self, family_id: int, month: str, scope: str, member_id: int | None = None
    ) -> MonthlyBudget | None:
        q = self.db.query(MonthlyBudget).filter(
            MonthlyBudget.family_id == family_id,
            MonthlyBudget.month == month,
            MonthlyBudget.scope == scope,
        )
        if scope == "personal":
            q = q.filter(MonthlyBudget.member_id == member_id)
        return q.first()

    def create(self, budget: MonthlyBudget) -> MonthlyBudget:
        self.db.add(budget)
        self.db.flush()
        return budget

    def list_category_budgets(self, budget_id: int) -> list[CategoryBudget]:
        return (
            self.db.query(CategoryBudget)
            .filter(CategoryBudget.budget_id == budget_id)
            .all()
        )

    def delete_category_budgets(self, budget_id: int) -> None:
        self.db.query(CategoryBudget).filter(
            CategoryBudget.budget_id == budget_id
        ).delete()

    def add_category_budget(self, cb: CategoryBudget) -> CategoryBudget:
        self.db.add(cb)
        self.db.flush()
        return cb

    def sum_expense(
        self,
        family_id: int,
        start: datetime,
        end: datetime,
        beneficiary_member_id: int | None = None,
    ) -> Decimal:
        """汇总范围内支出总额（不含收入与转账，详见设计 9.3）。"""
        q = self.db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
            Transaction.family_id == family_id,
            Transaction.type == "EXPENSE",
            Transaction.occurred_at >= start,
            Transaction.occurred_at < end,
        )
        if beneficiary_member_id is not None:
            q = q.filter(Transaction.beneficiary_member_id == beneficiary_member_id)
        return Decimal(q.scalar() or 0)

    def sum_expense_by_category(
        self,
        family_id: int,
        start: datetime,
        end: datetime,
        beneficiary_member_id: int | None = None,
    ) -> dict[int, Decimal]:
        """按分类汇总范围内支出，返回 {category_id: 支出总额}。"""
        q = self.db.query(
            Transaction.category_id,
            func.coalesce(func.sum(Transaction.amount), 0),
        ).filter(
            Transaction.family_id == family_id,
            Transaction.type == "EXPENSE",
            Transaction.occurred_at >= start,
            Transaction.occurred_at < end,
        )
        if beneficiary_member_id is not None:
            q = q.filter(Transaction.beneficiary_member_id == beneficiary_member_id)
        rows = q.group_by(Transaction.category_id).all()
        return {category_id: Decimal(amount) for category_id, amount in rows}