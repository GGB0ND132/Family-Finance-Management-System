from fastapi import APIRouter

from app.common.response import ok
from app.core.deps import DbSession
from app.modules.auth.schemas import LoginRequest, LoginResponse, RegisterRequest
from app.modules.auth.service import login, register
from app.modules.users.schemas import UserOut

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", summary="注册")
def register_user(payload: RegisterRequest, db: DbSession):
    user = register(db, payload.username, payload.password, payload.nickname)
    return ok(UserOut.model_validate(user).model_dump(), message="注册成功")


@router.post("/login", summary="登录")
def login_user(payload: LoginRequest, db: DbSession):
    user, token = login(db, payload.username, payload.password)
    data = LoginResponse(access_token=token, user=UserOut.model_validate(user)).model_dump()
    return ok(data, message="登录成功")