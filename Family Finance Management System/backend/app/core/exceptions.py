"""领域异常。

统一由 app.main 中的异常处理器转换为 {code, message, data} 响应：
40000 系列 -> 400 请求不合法
40100 系列 -> 401 未登录/凭证无效
40300 系列 -> 403 无权限
40400 系列 -> 404 资源不存在
40900 系列 -> 409 冲突（用户名重复、余额非零等）
"""


class AppError(Exception):
    http_status: int = 400
    code: int = 40001

    def __init__(self, message: str, code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code


class BadRequestError(AppError):
    http_status = 400
    code = 40001


class UnauthorizedError(AppError):
    http_status = 401
    code = 40101


class ForbiddenError(AppError):
    http_status = 403
    code = 40301


class NotFoundError(AppError):
    http_status = 404
    code = 40401


class ConflictError(AppError):
    http_status = 409
    code = 40901