"""预算 ORM 模型。"""

from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MonthlyBudget(Base):
    __tablename__ = "monthly_budgets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    family_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("families.id"), nullable=False
    )
    member_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("family_members.id"), nullable=True
    )
    month: Mapped[str] = mapped_column(String(7), nullable=False)  # YYYY-MM
    scope: Mapped[str] = mapped_column(String(20), nullable=False)  # personal / family
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)


class CategoryBudget(Base):
    __tablename__ = "category_budgets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    budget_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("monthly_budgets.id"), nullable=False
    )
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("categories.id"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)