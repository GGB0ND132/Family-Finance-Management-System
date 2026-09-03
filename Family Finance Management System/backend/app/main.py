from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.common.response import ok
from app.core.exceptions import AppError
from app.core.settings import get_settings
from app.modules.auth.router import router as auth_router
from app.modules.families.router import router as families_router
from app.modules.users.router import router as users_router

settings = get_settings()

app = FastAPI(title=settings.APP_NAME, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """将领域异常转换为统一错误响应 {code, message, data: null}。"""
    return JSONResponse(status_code=exc.http_status, content={"code": exc.code, "message": exc.message, "data": None})


@app.get("/api/v1/health", tags=["健康检查"], summary="健康检查")
def health():
    return ok({"status": "ok"})


app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(families_router, prefix="/api/v1")