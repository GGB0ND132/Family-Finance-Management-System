"""预算业务逻辑（`docs/详细设计.md` 第 9 节）。"""

import re
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.common.money import normalize_money, quantize_money
from app.core.exceptions import BadRequestError
from app.modules.budgets.models import CategoryBudget, MonthlyBudget
from app.modules.budgets.repository import BudgetRepository
from app.modules.categories.repository import CategoryRepository

_MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def _parse_month(month: str) -> tuple[int, int]:
    if not _MONTH_RE.match(month):
        raise BadRequestError("月份格式应为 YYYY-MM")
    year, mon = month.split("-")
    return int(year), int(mon)


def _month_range(month: str) -> tuple[datetime, datetime]:
    year, mon = _parse_month(month)
    start = datetime(year, mon, 1)
    end = datetime(year + 1, 1, 1) if mon == 12 else datetime(year, mon + 1, 1)
    return start, end


def _previous_month(month: str) -> str:
    year, mon = _parse_month(month)
    return f"{year - 1}-12" if mon == 1 else f"{year}-{mon - 1:02d}"


def _money(value: Decimal) -> str:
    return format(quantize_money(value), ".2f")


def _non_negative(value: str, label: str) -> Decimal:
    amount = normalize_money(value)
    if amount < 0:
        raise BadRequestError(f"{label}不能为负")
    return amount


def _warning_level(pct: Decimal) -> str:
    if pct < 80:
        return "NORMAL"
    if pct <= 100:
        return "WARNING"
    return "OVERSPENT"


def _build_output(
    db: Session,
    budget: MonthlyBudget | None,
    family_id: int,
    month: str,
    scope: str,
    member_id: int | None,
) -> dict:
    repo = BudgetRepository(db)
    start, end = _month_range(month)
    beneficiary = member_id if scope == "personal" else None

    total_used = repo.sum_expense(family_id, start, end, beneficiary)
    used_by_category = repo.sum_expense_by_category(
        family_id, start, end, beneficiary
    )

    total = budget.total_amount if budget else Decimal("0.00")

    categories = []
    if budget:
        for cb in repo.list_category_budgets(budget.id):
            cat_used = used_by_category.get(cb.category_id, Decimal("0.00"))
            cat_remaining = cb.amount - cat_used
            cat_rate = (cat_used / cb.amount * 100) if cb.amount > 0 else Decimal("0.00")
            categories.append(
                {
                    "category_id": cb.category_id,
                    "amount": _money(cb.amount),
                    "used_amount": _money(cat_used),
                    "remaining_amount": _money(cat_remaining),
                    "usage_rate": _money(cat_rate),
                }
            )

    remaining = total - total_used
    rate = (total_used / total * 100) if total > 0 else Decimal("0.00")

    return {
        "id": budget.id if budget else 0,
        "family_id": family_id,
        "month": month,
        "scope": scope,
        "total_amount": _money(total),
        "used_amount": _money(total_used),
        "remaining_amount": _money(remaining),
        "usage_rate": _money(rate),
        "warning_level": _warning_level(rate),
        "categories": categories,
    }


def get_budget(
    db: Session,
    family_id: int,
    month: str,
    scope: str,
    member_id: int | None = None,
) -> dict:
    """返回预算及执行情况；无预算时总预算与分类预算按 0 处理。"""
    budget = BudgetRepository(db).get_by_month(family_id, month, scope, member_id)
    return _build_output(db, budget, family_id, month, scope, member_id)


def put_budget(
    db: Session,
    family_id: int,
    month: str,
    scope: str,
    member_id: int | None,
    total_amount: str,
    categories: list[dict],
) -> dict:
    """保存/更新预算并整体替换分类预算（设计 9.3）。"""
    _parse_month(month)
    repo = BudgetRepository(db)
    total = _non_negative(total_amount, "预算金额")

    normalized = []
    for item in categories:
        category = CategoryRepository(db).get_by_id(item["category_id"])
        if category is None or category.family_id != family_id:
            raise BadRequestError("分类不存在或不属于当前家庭")
        if category.type != "EXPENSE":
            raise BadRequestError("预算仅支持支出分类")
        if category.deleted_at is not None:
            raise BadRequestError("分类已被删除")
        amount = _non_negative(item["amount"], "分类预算金额")
        normalized.append({"category_id": category.id, "amount": amount})

    existing = repo.get_by_month(family_id, month, scope, member_id)
    if existing:
        repo.delete_category_budgets(existing.id)
        existing.total_amount = total
        budget = existing
    else:
        budget = repo.create(
            MonthlyBudget(
                family_id=family_id,
                member_id=member_id if scope == "personal" else None,
                month=month,
                scope=scope,
                total_amount=total,
            )
        )

    for item in normalized:
        repo.add_category_budget(
            CategoryBudget(
                budget_id=budget.id,
                category_id=item["category_id"],
                amount=item["amount"],
            )
        )

    db.commit()
    return get_budget(db, family_id, month, scope, member_id)


def copy_from_previous(
    db: Session,
    family_id: int,
    month: str,
    scope: str,
    member_id: int | None = None,
) -> dict | None:
    """复制同范围上月预算到当前月；无上月预算返回 None。"""
    _parse_month(month)
    repo = BudgetRepository(db)
    prev = repo.get_by_month(family_id, _previous_month(month), scope, member_id)
    if prev is None:
        return None

    current = repo.get_by_month(family_id, month, scope, member_id)
    if current is None:
        budget = repo.create(
            MonthlyBudget(
                family_id=family_id,
                member_id=member_id if scope == "personal" else None,
                month=month,
                scope=scope,
                total_amount=prev.total_amount,
            )
        )
    else:
        repo.delete_category_budgets(current.id)
        current.total_amount = prev.total_amount
        budget = current

    for cb in repo.list_category_budgets(prev.id):
        repo.add_category_budget(
            CategoryBudget(
                budget_id=budget.id,
                category_id=cb.category_id,
                amount=cb.amount,
            )
        )

    db.commit()
    return get_budget(db, family_id, month, scope, member_id)