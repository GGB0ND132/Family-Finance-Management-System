"""统一分页约定：page 默认 1，page_size 默认 20，最大 100。"""

from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel

T = TypeVar("T")


class Pagination(BaseModel, Generic[T]):
    page: int
    page_size: int
    total: int
    items: list[T]


def page_params(
    page: int = Query(1, ge=1, description="页码，从 1 开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数，最大 100"),
) -> tuple[int, int]:
    """FastAPI 依赖：从查询参数解析并校验分页参数。"""
    return page, page_size