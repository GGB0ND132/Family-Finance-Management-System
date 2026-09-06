"""分类 Pydantic 模型。"""

from datetime import datetime

from pydantic import BaseModel, Field


class CreateCategoryRequest(BaseModel):
    family_id: int
    name: str = Field(min_length=1, max_length=50)
    type: str = Field(pattern="^(INCOME|EXPENSE)$")
    icon: str | None = None
    color: str | None = None


class UpdateCategoryRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=50)
    icon: str | None = None
    color: str | None = None


class CategoryOut(BaseModel):
    id: int
    family_id: int
    name: str
    type: str
    icon: str | None = None
    color: str | None = None
    deleted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}