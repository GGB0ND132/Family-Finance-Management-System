from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.modules.families import repository as family_repo
from app.modules.families.models import FamilyMember
from app.modules.users.models import User
from app.modules.users.repository import get_user_by_id

bearer_scheme = HTTPBearer(auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: DbSession,
) -> User:
    """解析 JWT 并返回当前用户；凭证缺失、无效或用户已不存在时返回 401。"""
    if credentials is None:
        raise UnauthorizedError("未登录，请先登录")
    user_id = decode_access_token(credentials.credentials)
    user = get_user_by_id(db, user_id)
    if user is None:
        raise UnauthorizedError("登录已失效，请重新登录")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_family_member(db: Session, user: User, family_id: int) -> FamilyMember:
    """校验当前用户属于目标家庭（系统设计 7，家庭数据隔离）。"""
    member = family_repo.get_member_by_user(db, family_id, user.id)
    if member is None:
        raise ForbiddenError("你不是该家庭的成员")
    return member


def require_family_admin(db: Session, user: User, family_id: int) -> FamilyMember:
    """校验当前用户是该家庭管理员。"""
    member = require_family_member(db, user, family_id)
    if member.role != "ADMIN":
        raise ForbiddenError("需要家庭管理员权限")
    return member