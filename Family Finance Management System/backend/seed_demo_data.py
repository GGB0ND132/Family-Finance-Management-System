"""生成用于开发和验收的演示数据库数据。"""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.enums import AccountType, MemberRole
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.modules.accounts.models import Account
from app.modules.categories.service import ensure_default_categories
from app.modules.families.models import Family, FamilyMember
from app.modules.users.models import User

DEMO_PASSWORD = "Demo@123456"
DEMO_FAMILY_NAME = "演示家庭"

DEMO_USERS = (
    {"username": "admin_zhang", "nickname": "张管理员", "role": MemberRole.ADMIN},
    {"username": "admin_li", "nickname": "李管理员", "role": MemberRole.ADMIN},
    {"username": "member_wang", "nickname": "王成员", "role": MemberRole.MEMBER},
)

DEMO_ACCOUNTS = (
    ("张管理员", "工资银行卡", AccountType.BANK_CARD, "12000.00"),
    ("张管理员", "张管理员现金", AccountType.CASH, "800.00"),
    ("李管理员", "李管理员支付宝", AccountType.ALIPAY, "3600.00"),
    ("李管理员", "李管理员微信", AccountType.WECHAT, "1500.00"),
    ("王成员", "王成员银行卡", AccountType.BANK_CARD, "5200.00"),
    ("王成员", "王成员现金", AccountType.CASH, "300.00"),
)


def _get_or_create_user(db: Session, username: str, nickname: str) -> User:
    user = db.scalar(select(User).where(User.username == username))
    if user is None:
        user = User(
            username=username,
            password_hash=hash_password(DEMO_PASSWORD),
            nickname=nickname,
        )
        db.add(user)
        db.flush()
    else:
        # 演示账号每次执行都恢复为文档中公布的密码，便于重复验收。
        user.password_hash = hash_password(DEMO_PASSWORD)
        user.nickname = nickname
    return user


def _get_or_create_member(
    db: Session, family_id: int, user_id: int, role: MemberRole
) -> FamilyMember:
    member = db.scalar(
        select(FamilyMember).where(
            FamilyMember.family_id == family_id,
            FamilyMember.user_id == user_id,
        )
    )
    if member is None:
        member = FamilyMember(family_id=family_id, user_id=user_id, role=role)
        db.add(member)
        db.flush()
    else:
        member.role = role
    return member


def _get_or_create_family(db: Session, owner_id: int) -> Family:
    family = db.scalar(select(Family).where(Family.name == DEMO_FAMILY_NAME))
    if family is None:
        family = Family(name=DEMO_FAMILY_NAME, owner_id=owner_id)
        db.add(family)
        db.flush()
    else:
        family.owner_id = owner_id
    return family


def _get_or_create_account(
    db: Session,
    family_id: int,
    owner_member_id: int,
    name: str,
    account_type: AccountType,
    balance: str,
) -> Account:
    account = db.scalar(
        select(Account).where(
            Account.family_id == family_id,
            Account.owner_member_id == owner_member_id,
            Account.name == name,
        )
    )
    if account is None:
        amount = Decimal(balance)
        account = Account(
            family_id=family_id,
            owner_member_id=owner_member_id,
            name=name,
            type=account_type,
            initial_balance=amount,
            current_balance=amount,
            remark="演示数据",
        )
        db.add(account)
        db.flush()
    return account


def seed_demo_data(db: Session) -> dict[str, int]:
    """创建演示数据并返回生成/复用的记录数量。"""
    users = {
        item["username"]: _get_or_create_user(db, item["username"], item["nickname"])
        for item in DEMO_USERS
    }
    family = _get_or_create_family(db, users["admin_zhang"].id)

    members = {
        item["nickname"]: _get_or_create_member(
            db,
            family.id,
            users[item["username"]].id,
            item["role"],
        )
        for item in DEMO_USERS
    }
    ensure_default_categories(db, family.id)

    for nickname, account_name, account_type, balance in DEMO_ACCOUNTS:
        _get_or_create_account(
            db,
            family.id,
            members[nickname].id,
            account_name,
            account_type,
            balance,
        )

    db.commit()
    return {"users": len(users), "members": len(members), "accounts": len(DEMO_ACCOUNTS)}


def main() -> None:
    with SessionLocal() as db:
        result = seed_demo_data(db)
    print(
        "演示数据已准备："
        f"{result['users']} 个用户、{result['members']} 个家庭成员、"
        f"{result['accounts']} 个账户。"
    )
    print("演示账号密码：Demo@123456")
    print("账号：admin_zhang、admin_li、member_wang")


if __name__ == "__main__":
    main()
