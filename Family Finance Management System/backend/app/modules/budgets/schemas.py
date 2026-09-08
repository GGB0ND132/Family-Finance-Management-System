"""预算 Pydantic 请求模型。"""

from typing import Literal

from pydantic import BaseModel, Field


class CategoryBudgetItem(BaseModel):
    category_id: int
    amount: str


class PutBudgetRequest(BaseModel):
    family_id: int
    scope: Literal["personal", "family"]
    total_amount: str
    categories: list[CategoryBudgetItem] = Field(default_factory=list)


class CopyBudgetRequest(BaseModel):
    family_id: int
    scope: Literal["personal", "family"]