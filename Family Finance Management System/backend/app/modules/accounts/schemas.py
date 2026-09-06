"""账户 Pydantic 模型。"""

from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.common.enums import AccountType


class CreateAccountRequest(BaseModel):
    """创建账户请求。"""

    family_id: int
    owner_member_id: int
    name: str = Field(min_length=1, max_length=100)
    type: str
    initial_balance: str = "0.00"
    remark: str | None = None

    @model_validator(mode="after")
    def validate_type(self):
        valid = [t.value for t in AccountType]
        if self.type not in valid:
            raise ValueError(f"账户类型无效，允许值：{', '.join(valid)}")
        return self

    @model_validator(mode="after")
    def validate_balance(self):
        try:
            Decimal(self.initial_balance)
        except Exception:
            raise ValueError("初始余额格式无效")
        return self


class UpdateAccountRequest(BaseModel):
    """更新账户请求。"""

    name: str | None = Field(None, min_length=1, max_length=100)
    type: str | None = None
    owner_member_id: int | None = None
    remark: str | None = None

    @model_validator(mode="after")
    def validate_type(self):
        if self.type is not None:
            valid = [t.value for t in AccountType]
            if self.type not in valid:
                raise ValueError(f"账户类型无效，允许值：{', '.join(valid)}")
        return self


class AccountOut(BaseModel):
    """账户响应。"""

    id: int
    family_id: int
    owner_member_id: int
    owner_nickname: str | None = None
    name: str
    type: str
    initial_balance: str
    current_balance: str
    remark: str | None = None
    closed_at: str | None = None
    created_at: str
    updated_at: str | None = None

    model_config = {"from_attributes": True}