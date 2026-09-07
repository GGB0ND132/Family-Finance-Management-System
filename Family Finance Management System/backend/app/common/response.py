from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PageData(BaseModel, Generic[T]):
    """统一分页响应结构。"""

    items: list[T]
    page: int = 1
    page_size: int = 20
    total: int = 0


class ApiResponse(BaseModel, Generic[T]):
    """统一 API 响应结构。"""

    code: int = 0
    message: str = "success"
    data: T | None = None


def ok(data: Any = None, message: str = "success") -> dict:
    """统一成功响应结构：{code: 0, message, data}。"""
    return {"code": 0, "message": message, "data": data}