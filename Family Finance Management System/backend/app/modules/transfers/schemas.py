"""转账 Pydantic 模型。"""

from pydantic import BaseModel, Field


class CreateTransferRequest(BaseModel):
    family_id: int
    from_account_id: int
    to_account_id: int
    amount: str
    occurred_at: str
    remark: str | None = None


class UpdateTransferRequest(BaseModel):
    from_account_id: int | None = None
    to_account_id: int | None = None
    amount: str | None = None
    occurred_at: str | None = None
    remark: str | None = None


class TransferOut(BaseModel):
    id: int
    family_id: int
    from_account_id: int
    to_account_id: int
    from_member_id: int
    to_member_id: int
    recorder_user_id: int
    amount: str
    occurred_at: str
    remark: str | None = None
    created_at: str

    model_config = {"from_attributes": True}