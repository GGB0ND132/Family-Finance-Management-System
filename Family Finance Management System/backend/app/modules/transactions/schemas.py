"""流水 Pydantic 模型。"""

from decimal import Decimal
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, BeforeValidator


def _str_converter(v):
    if isinstance(v, Decimal):
        return str(v)
    if isinstance(v, datetime):
        return v.isoformat()
    return v


StrField = Annotated[str, BeforeValidator(_str_converter)]


class CreateTransactionRequest(BaseModel):
    """创建流水请求。recorder_user_id 由后端从 JWT 写入，前端不得伪造。"""

    family_id: int
    account_id: int
    category_id: int
    beneficiary_member_id: int
    type: str = Field(pattern="^(INCOME|EXPENSE)$")
    amount: str
    occurred_at: str
    remark: str | None = None


class UpdateTransactionRequest(BaseModel):
    """编辑流水请求。类型不可修改，只能改金额、账户、分类、资金归属人、发生时间和备注。"""

    account_id: int | None = None
    category_id: int | None = None
    beneficiary_member_id: int | None = None
    amount: str | None = None
    occurred_at: str | None = None
    remark: str | None = None


class TransactionOut(BaseModel):
    """流水响应：基础字段 + 用于展示的各关联名称。"""

    id: int
    family_id: int
    account_id: int
    category_id: int
    beneficiary_member_id: int
    recorder_user_id: int
    type: str
    amount: StrField
    occurred_at: StrField
    remark: str | None = None
    created_at: str
    account_name: str | None = None
    account_owner_member_id: int | None = None
    account_owner_nickname: str | None = None
    account_current_balance: str | None = None
    category_name: str | None = None
    category_type: str | None = None
    beneficiary_nickname: str | None = None
    recorder_nickname: str | None = None
    status: str = "CONFIRMED"
    pending_update: dict | None = None
