from sqlalchemy.exc import DataError
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError
from app.core.security import hash_password, verify_password
from app.modules.users.models import User


def update_profile(db: Session, user: User, nickname: str, real_name: str | None = None, avatar: str | None = None) -> User:
    user.nickname = nickname.strip()
    user.real_name = real_name.strip() if real_name else None
    user.avatar = avatar.strip() if avatar else None
    try:
        db.commit()
    except DataError as exc:
        db.rollback()
        raise BadRequestError("头像数据过大，请选择不超过 2MB 的图片") from exc
    return user


def change_password(db: Session, user: User, old_password: str, new_password: str) -> None:
    if not verify_password(old_password, user.password_hash):
        raise BadRequestError("旧密码不正确")
    if new_password == old_password:
        raise BadRequestError("新密码不能与旧密码相同")
    user.password_hash = hash_password(new_password)
    db.commit()
