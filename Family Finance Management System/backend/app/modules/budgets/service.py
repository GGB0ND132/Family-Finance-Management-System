"""预算业务逻辑。"""

from decimal import Decimal

from sqlalchemy.orm import Session

from app.common.money import quantize_money
from app.core.exceptions import PermissionDeniedError
from app.modules.budgets.models import CategoryBudget, MonthlyBudget
from app.modules.budgets.repository import BudgetRepository


def _compute_budget_usage(
    db: Session, budget: MonthlyBudget
) -> dict:
    """计算预算使用率、预警等级。"""
    # TODO: 从 transactions 表聚合当月支出
    used = Decimal("0.00")
    category_items = []
    for cb in BudgetRepository(db).list_category_budgets(budget.id):
        # TODO: 按分类聚合已用金额
        cat_used = Decimal("0.00")
        remaining = cb.amount - cat_used
        rate = (
            (cat_used / cb.amount) if cb.amount > 0 else Decimal("0.00")
        )
        category_items.append({
            "category_id": cb.category_id,
            "amount": str(cb.amount),
            "used_amount": str(cat_used),
            "remaining_amount": str(remaining),
            "usage_rate": str(quantize_money(rate * 100)),
        })
        used += cat_used

    total = budget.total_amount
    remaining = total - used
    rate = (used / total) if total > 0 else Decimal("0.00")
    pct = rate * 100

    if pct < 80:
        warning = "NORMAL"
    elif pct <= 100:
        warning = "WARNING"
    else:
        warning = "OVERSPENT"

    return {
        "used_amount": str(used),
        "remaining_amount": str(remaining),
        "usage_rate": str(quantize_money(pct)),
        "warning_level": warning,
        "categories": category_items,
    }


def get_budget(
    db: Session,
    family_id: int,
    month: str,
    scope: str,
    member_id: int | None = None,
) -> dict | None:
    """获取预算及使用情况。"""
    repo = BudgetRepository(db)
    budget = repo.get_by_month(family_id, month, scope, member_id)
    if not budget:
        return None
    usage = _compute_budget_usage(db, budget)
    return {
        "id": budget.id,
        "family_id": budget.family_id,
        "month": budget.month,
        "scope": budget.scope,
        "total_amount": str(budget.total_amount),
        **usage,
    }


def put_budget(
    db: Session,
    family_id: int,
    month: str,
    scope: str,
    member_id: int,
    total_amount: str,
    categories: list[dict],
) -> MonthlyBudget:
    """保存/更新预算，替换分类预算明细。"""
    repo = BudgetRepository(db)
    existing = repo.get_by_month(family_id, month, scope, member_id)

    if existing:
        repo.delete_category_budgets(existing.id)
        existing.total_amount = quantize_money(Decimal(total_amount))
        budget = existing
    else:
        budget = MonthlyBudget(
            family_id=family_id,
            member_id=member_id if scope == "personal" else None,
            month=month,
            scope=scope,
            total_amount=quantize_money(Decimal(total_amount)),
        )
        budget = repo.create(budget)

    for cat in categories:
        repo.add_category_budget(
            CategoryBudget(
                budget_id=budget.id,
                category_id=cat["category_id"],
                amount=quantize_money(Decimal(cat["amount"])),
            )
        )
    db.flush()
    return budget


def copy_from_previous(
    db: Session,
    family_id: int,
    month: str,
    scope: str,
    member_id: int | None = None,
) -> MonthlyBudget | None:
    """从上一个月的预算复制到当前月份。"""
    repo = BudgetRepository(db)

    # 计算上月
    year, mon = map(int, month.split("-"))
    if mon == 1:
        prev_month = f"{year - 1}-12"
    else:
        prev_month = f"{year}-{mon - 1:02d}"

    prev = repo.get_by_month(family_id, prev_month, scope, member_id)
    if not prev:
        return None

    # 删除当前月（如存在）并复制
    current = repo.get_by_month(family_id, month, scope, member_id)
    if current:
        repo.delete_category_budgets(current.id)

    new_budget = MonthlyBudget(
        family_id=family_id,
        member_id=member_id if scope == "personal" else None,
        month=month,
        scope=scope,
        total_amount=prev.total_amount,
    )
    new_budget = repo.create(new_budget)

    for cb in repo.list_category_budgets(prev.id):
        repo.add_category_budget(
            CategoryBudget(
                budget_id=new_budget.id,
                category_id=cb.category_id,
                amount=cb.amount,
            )
        )
    db.flush()
    return new_budget