from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.users.models import User


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(User.username == username))


def create_user(db: Session, username: str, password_hash: str, nickname: str) -> User:
    user = User(username=username, password_hash=password_hash, nickname=nickname)
    db.add(user)
    return user