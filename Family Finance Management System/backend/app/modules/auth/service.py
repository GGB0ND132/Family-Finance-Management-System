from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.modules.users.models import User
from app.modules.users.repository import create_user, get_user_by_username


def register(db: Session, username: str, password: str, nickname: str) -> User:
    username = username.strip()
    if get_user_by_username(db, username) is not None:
        raise ConflictError("用户名已被占用")
    user = create_user(db, username, hash_password(password), nickname.strip())
    db.commit()
    return user


def login(db: Session, username: str, password: str) -> tuple[User, str]:
    """校验用户名密码，成功返回 (用户, access_token)。"""
    user = get_user_by_username(db, username.strip())
    # 统一提示，避免暴露用户名是否存在
    if user is None or not verify_password(password, user.password_hash):
        raise UnauthorizedError("用户名或密码错误")
    return user, create_access_token(user.id)