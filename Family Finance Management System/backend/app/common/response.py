from typing import Any


def ok(data: Any = None, message: str = "success") -> dict:
    """统一成功响应结构：{code: 0, message, data}。"""
    return {"code": 0, "message": message, "data": data}