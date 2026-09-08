from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


<<<<<<< HEAD
class ApiResponse(BaseModel, Generic[T]):
    """统一成功响应结构（`docs/后端开发文档.md` 3.3）。"""
=======
class PageData(BaseModel, Generic[T]):
    """统一分页结构。"""

    items: list[T]
    page: int
    page_size: int
    total: int


class ApiResponse(BaseModel, Generic[T]):
    """统一响应结构。"""
>>>>>>> ce9db4e (feat: 外部账单导入模块)

    code: int = 0
    message: str = "success"
    data: T | None = None
<<<<<<< HEAD
    request_id: str | None = None


class PageData(BaseModel, Generic[T]):
    """统一分页结构：items/page/page_size/total。"""

    items: list[T]
    page: int = 1
    page_size: int = 20
    total: int = 0
=======
>>>>>>> ce9db4e (feat: 外部账单导入模块)


def ok(data: Any = None, message: str = "success") -> dict:
    """统一成功响应结构：{code: 0, message, data}。"""
    return {"code": 0, "message": message, "data": data}