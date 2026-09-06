"""预算数据访问。"""

from sqlalchemy.orm import Session

from app.modules.budgets.models import CategoryBudget, MonthlyBudget


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