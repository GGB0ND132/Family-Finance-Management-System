from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.families.models import Family, FamilyMember
from app.modules.users.models import User


def get_family_by_id(db: Session, family_id: int) -> Family | None:
    return db.get(Family, family_id)


def get_family_by_invite_code(db: Session, invite_code: str) -> Family | None:
    return db.scalar(select(Family).where(Family.invite_code == invite_code))


def list_user_families(db: Session, user_id: int) -> list[Family]:
    stmt = (
        select(Family)
        .join(FamilyMember, FamilyMember.family_id == Family.id)
        .where(FamilyMember.user_id == user_id)
        .order_by(Family.id)
    )
    return list(db.scalars(stmt))


def count_family_members(db: Session, family_id: int) -> int:
    return db.scalar(
        select(func.count(FamilyMember.id)).where(FamilyMember.family_id == family_id)
    ) or 0


def count_family_admins(db: Session, family_id: int) -> int:
    return db.scalar(
        select(func.count(FamilyMember.id)).where(
            FamilyMember.family_id == family_id, FamilyMember.role == "ADMIN"
        )
    ) or 0


def get_member_by_user(db: Session, family_id: int, user_id: int) -> FamilyMember | None:
    return db.scalar(
        select(FamilyMember).where(
            FamilyMember.family_id == family_id, FamilyMember.user_id == user_id
        )
    )


def get_member_by_id(db: Session, member_id: int) -> FamilyMember | None:
    return db.get(FamilyMember, member_id)


def list_members(db: Session, family_id: int) -> list[tuple[FamilyMember, User]]:
    """返回 (成员, 用户) 列表，便于带出用户名与昵称。"""
    stmt = (
        select(FamilyMember, User)
        .join(User, User.id == FamilyMember.user_id)
        .where(FamilyMember.family_id == family_id)
        .order_by(FamilyMember.joined_at, FamilyMember.id)
    )
    return list(db.execute(stmt))


def create_family(db: Session, name: str, owner_id: int) -> Family:
    family = Family(name=name, owner_id=owner_id)
    db.add(family)
    db.flush()
    return family


def add_member(db: Session, family_id: int, user_id: int, role: str) -> FamilyMember:
    member = FamilyMember(family_id=family_id, user_id=user_id, role=role)
    db.add(member)
    db.flush()
    return member