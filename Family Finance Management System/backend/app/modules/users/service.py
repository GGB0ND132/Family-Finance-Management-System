from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError
from app.core.security import hash_password, verify_password
from app.modules.users.models import User


def update_nickname(db: Session, user: User, nickname: str) -> User:
    user.nickname = nickname.strip()
    db.commit()
    return user


def change_password(db: Session, user: User, old_password: str, new_password: str) -> None:
    if not verify_password(old_password, user.password_hash):
        raise BadRequestError("旧密码不正确")
    if new_password == old_password:
        raise BadRequestError("新密码不能与旧密码相同")
    user.password_hash = hash_password(new_password)
    db.commit()