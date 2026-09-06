"""报表 Pydantic 模型。"""

from pydantic import BaseModel


class DailySummary(BaseModel):
    date: str
    income: str = "0.00"
    expense: str = "0.00"
    balance: str = "0.00"


class MonthlySummary(BaseModel):
    month: str
    income: str = "0.00"
    expense: str = "0.00"
    balance: str = "0.00"


class TrendPoint(BaseModel):
    month: str
    income: str = "0.00"
    expense: str = "0.00"


class CategoryStat(BaseModel):
    category_id: int
    category_name: str
    amount: str
    percentage: str = "0.00"


class MemberStat(BaseModel):
    member_id: int
    member_name: str
    income: str = "0.00"
    expense: str = "0.00"