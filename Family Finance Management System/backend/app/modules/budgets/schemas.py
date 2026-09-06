"""预算 Pydantic 模型。"""

from pydantic import BaseModel, Field


class CategoryBudgetItem(BaseModel):
    category_id: int
    amount: str


class PutBudgetRequest(BaseModel):
    family_id: int
    scope: str = Field(pattern="^(personal|family)$")
    total_amount: str
    categories: list[CategoryBudgetItem] = []


class CopyBudgetRequest(BaseModel):
    family_id: int
    scope: str = Field(pattern="^(personal|family)$")


class CategoryBudgetOut(BaseModel):
    category_id: int
    amount: str
    used_amount: str = "0.00"
    remaining_amount: str = "0.00"
    usage_rate: str = "0.00"

    model_config = {"from_attributes": True}


class BudgetOut(BaseModel):
    id: int
    family_id: int
    month: str
    scope: str
    total_amount: str
    used_amount: str = "0.00"
    remaining_amount: str = "0.00"
    usage_rate: str = "0.00"
    warning_level: str = "NORMAL"
    categories: list[CategoryBudgetOut] = []

    model_config = {"from_attributes": True}