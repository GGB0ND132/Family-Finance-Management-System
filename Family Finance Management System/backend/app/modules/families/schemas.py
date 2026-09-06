from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import MemberRole


class FamilyOut(BaseModel):
    """家庭摘要。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    owner_id: int
    members_count: int = 0
    created_at: datetime


class CreateFamilyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50, description="家庭名称")


class JoinFamilyRequest(BaseModel):
    invite_code: str = Field(min_length=1, max_length=20, description="邀请码")


class UpdateFamilyNameRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50, description="家庭名称")


class MemberOut(BaseModel):
    id: int
    family_id: int
    user_id: int
    username: str
    nickname: str
    role: MemberRole
    joined_at: datetime


class UpdateMemberRoleRequest(BaseModel):
    role: MemberRole


class InviteCodeOut(BaseModel):
    invite_code: str
    expires_at: datetime