from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserOut(BaseModel):
    """对外输出的用户信息，不包含密码哈希。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    nickname: str
    created_at: datetime


class UpdateProfileRequest(BaseModel):
    nickname: str = Field(min_length=1, max_length=50, description="昵称")


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(min_length=1, max_length=72, description="旧密码")
    new_password: str = Field(min_length=8, max_length=72, description="新密码，至少 8 位")