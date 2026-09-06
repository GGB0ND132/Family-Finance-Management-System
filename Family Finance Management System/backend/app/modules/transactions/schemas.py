"""流水 Pydantic 模型。"""

from pydantic import BaseModel, Field


class CreateTransactionRequest(BaseModel):
    family_id: int
    account_id: int
    category_id: int
    beneficiary_member_id: int
    type: str = Field(pattern="^(INCOME|EXPENSE)$")
    amount: str
    occurred_at: str
    remark: str | None = None


class UpdateTransactionRequest(BaseModel):
    account_id: int | None = None
    category_id: int | None = None
    beneficiary_member_id: int | None = None
    amount: str | None = None
    occurred_at: str | None = None
    remark: str | None = None


class TransactionOut(BaseModel):
    id: int
    family_id: int
    account_id: int
    category_id: int
    beneficiary_member_id: int
    recorder_user_id: int
    type: str
    amount: str
    occurred_at: str
    remark: str | None = None
    created_at: str

    model_config = {"from_attributes": True}