from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.common.enums import MemberRole
from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.modules.families import repository as family_repo
from app.modules.families.models import Family, FamilyMember
from app.modules.users.models import User

INVITE_CODE_VALID_HOURS = 24 * 7  # 邀请码默认 7 天有效


def create_family(db: Session, user: User, name: str) -> Family:
    """创建家庭，并在同一事务中写入创建者的管理员成员记录（详细设计 3.3）。"""
    family = family_repo.create_family(db, name.strip(), user.id)
    family_repo.add_member(db, family.id, user.id, MemberRole.ADMIN)
    db.commit()
    db.refresh(family)
    return family


def join_family(db: Session, user: User, invite_code: str) -> FamilyMember:
    """使用邀请码加入家庭：校验邀请码存在、未过期、未失效且未重复加入。"""
    invite_code = invite_code.strip()
    family = family_repo.get_family_by_invite_code(db, invite_code)
    if family is None or family.invite_expires_at is None or family.invite_expires_at < datetime.utcnow():
        raise BadRequestError("邀请码无效或已过期")
    existing = family_repo.get_member_by_user(db, family.id, user.id)
    if existing is not None:
        raise ConflictError("你已在该家庭中")
    member = family_repo.add_member(db, family.id, user.id, MemberRole.MEMBER)
    db.commit()
    db.refresh(member)
    return member


def update_family_name(db: Session, family: Family, name: str) -> Family:
    family.name = name.strip()
    db.commit()
    db.refresh(family)
    return family


def generate_invite_code(db: Session, family: Family) -> tuple[str, datetime]:
    """生成新的邀请码并设置有效期；旧邀请码立即失效。"""
    code = _random_invite_code()
    family.invite_code = code
    family.invite_expires_at = datetime.utcnow() + timedelta(hours=INVITE_CODE_VALID_HOURS)
    db.commit()
    db.refresh(family)
    return family.invite_code, family.invite_expires_at


def revoke_invite_code(db: Session, family: Family) -> None:
    family.invite_code = None
    family.invite_expires_at = None
    db.commit()


def update_member_role(db: Session, admin: FamilyMember, member: FamilyMember, role: MemberRole) -> FamilyMember:
    """调整成员角色；不能把最后一名管理员降级（BR-14）。"""
    if member.family_id != admin.family_id:
        raise ForbiddenError("该成员不属于当前家庭")
    if member.role == MemberRole.ADMIN and role == MemberRole.MEMBER:
        admins = family_repo.count_family_admins(db, admin.family_id)
        if admins <= 1:
            raise ConflictError("家庭必须至少保留一名管理员")
    member.role = role
    db.commit()
    db.refresh(member)
    return member


def remove_member(db: Session, admin: FamilyMember, member: FamilyMember) -> None:
    """移除成员；管理员不能移除自己，也不能移除最后一名管理员（BR-14）。"""
    if member.family_id != admin.family_id:
        raise ForbiddenError("该成员不属于当前家庭")
    if member.user_id == admin.user_id:
        raise ConflictError("管理员不能移除自己")
    if member.role == MemberRole.ADMIN:
        admins = family_repo.count_family_admins(db, admin.family_id)
        if admins <= 1:
            raise ConflictError("家庭必须至少保留一名管理员")
    db.delete(member)
    db.commit()


def _random_invite_code() -> str:
    import secrets

    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # 去掉易混淆字符
    return "".join(secrets.choice(alphabet) for _ in range(8))