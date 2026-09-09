"""转账 Pydantic 模型。"""

from pydantic import BaseModel


class CreateTransferRequest(BaseModel):
    """创建转账请求。转出/转入成员由账户所属人推导，录入人由 JWT 写入。"""

    family_id: int
    from_account_id: int
    to_account_id: int
    amount: str
    occurred_at: str
    remark: str | None = None


class UpdateTransferRequest(BaseModel):
    """编辑转账请求。可改转出/转入账户、金额、发生时间和备注。"""

    from_account_id: int | None = None
    to_account_id: int | None = None
    amount: str | None = None
    occurred_at: str | None = None
    remark: str | None = None


class TransferOut(BaseModel):
    """转账响应：基础字段 + 用于展示的关联名称。"""

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
    from_account_name: str | None = None
    to_account_name: str | None = None
    from_member_nickname: str | None = None
    to_member_nickname: str | None = None
    recorder_nickname: str | None = None
    status: str = "CONFIRMED"
