from pydantic import BaseModel, Field

from app.modules.users.schemas import UserOut


class RegisterRequest(BaseModel):
    username: str = Field(min_length=2, max_length=50, description="用户名")
    password: str = Field(min_length=8, max_length=72, description="密码，至少 8 位")
    nickname: str = Field(min_length=1, max_length=50, description="昵称")


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50, description="用户名")
    password: str = Field(min_length=1, max_length=72, description="密码")


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut