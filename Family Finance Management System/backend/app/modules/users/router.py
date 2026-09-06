from fastapi import APIRouter

from app.common.response import ok
from app.core.deps import CurrentUser, DbSession
from app.modules.users.schemas import ChangePasswordRequest, UpdateProfileRequest, UserOut
from app.modules.users.service import change_password, update_nickname

router = APIRouter(prefix="/users", tags=["用户"])


@router.get("/me", summary="获取当前用户信息")
def get_me(user: CurrentUser):
    return ok(UserOut.model_validate(user).model_dump())


@router.patch("/me", summary="修改个人昵称")
def update_me(payload: UpdateProfileRequest, user: CurrentUser, db: DbSession):
    updated = update_nickname(db, user, payload.nickname)
    return ok(UserOut.model_validate(updated).model_dump(), message="昵称修改成功")


@router.patch("/me/password", summary="修改密码")
def update_password(payload: ChangePasswordRequest, user: CurrentUser, db: DbSession):
    change_password(db, user, payload.old_password, payload.new_password)
    return ok(message="密码修改成功")