from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

MAX_AVATAR_DATA_URL_LENGTH = 3 * 1024 * 1024


class UserOut(BaseModel):
    """对外输出的用户信息，不包含密码哈希。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    nickname: str
    real_name: str | None = None
    avatar: str | None = None
    created_at: datetime


class UpdateProfileRequest(BaseModel):
    nickname: str = Field(min_length=1, max_length=50, description="昵称")
    real_name: str | None = Field(default=None, max_length=50, description="真实姓名")
    avatar: str | None = Field(
        default=None,
        max_length=MAX_AVATAR_DATA_URL_LENGTH,
        description="头像地址或 Base64 图片（最大 2MB 原始图片）",
    )


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(min_length=1, max_length=72, description="旧密码")
    new_password: str = Field(min_length=8, max_length=72, description="新密码，至少 8 位")
