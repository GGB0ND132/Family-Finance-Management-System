"""预算 ORM 模型（`docs/详细设计.md` 第 9.2 节）。"""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MonthlyBudget(Base):
    """月度总预算（个人或家庭）。"""

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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class CategoryBudget(Base):
    """分类预算明细。"""

    __tablename__ = "category_budgets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    budget_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("monthly_budgets.id"), nullable=False
    )
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("categories.id"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )