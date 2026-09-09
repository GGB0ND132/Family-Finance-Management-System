"""生成用于开发和验收的演示数据库数据。"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.enums import AccountType, MemberRole
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.modules.accounts.models import Account
from app.modules.budgets.models import CategoryBudget, MonthlyBudget
from app.modules.categories.models import Category
from app.modules.categories.service import ensure_default_categories
from app.modules.families.models import Family, FamilyMember
from app.modules.transactions.models import Transaction
from app.modules.transfers.models import Transfer
from app.modules.users.models import User

DEMO_PASSWORD = "Demo@123456"
DEMO_FAMILY_NAME = "演示家庭"
DEMO_MARKER = "[seed-demo-2026]"
DEMO_MONTHS = ("2026-07", "2026-08", "2026-09")

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

# 每月每人 8 条流水：工资/其他收入，以及餐饮、交通、住房、购物、娱乐等日常支出。
MONTHLY_TRANSACTIONS = (
    ("张管理员", "工资银行卡", "工资", "INCOME", "8500.00", "01", "工资到账"),
    ("张管理员", "工资银行卡", "奖金", "INCOME", "1200.00", "05", "项目奖金"),
    ("张管理员", "工资银行卡", "住房", "EXPENSE", "2600.00", "03", "房租和物业"),
    ("张管理员", "张管理员现金", "餐饮", "EXPENSE", "320.00", "08", "工作日餐饮"),
    ("张管理员", "工资银行卡", "交通", "EXPENSE", "180.00", "12", "通勤交通"),
    ("张管理员", "工资银行卡", "购物", "EXPENSE", "460.00", "17", "日用品采购"),
    ("张管理员", "张管理员现金", "娱乐", "EXPENSE", "260.00", "22", "周末休闲"),
    ("张管理员", "工资银行卡", "医疗", "EXPENSE", "180.00", "26", "常备药品"),
    ("李管理员", "李管理员支付宝", "工资", "INCOME", "7200.00", "01", "工资到账"),
    ("李管理员", "李管理员支付宝", "奖金", "INCOME", "800.00", "06", "兼职收入"),
    ("李管理员", "李管理员支付宝", "住房", "EXPENSE", "2200.00", "03", "房租和物业"),
    ("李管理员", "李管理员微信", "餐饮", "EXPENSE", "380.00", "09", "日常餐饮"),
    ("李管理员", "李管理员支付宝", "交通", "EXPENSE", "160.00", "13", "通勤交通"),
    ("李管理员", "李管理员支付宝", "购物", "EXPENSE", "520.00", "16", "生活用品"),
    ("李管理员", "李管理员微信", "娱乐", "EXPENSE", "300.00", "23", "电影和聚餐"),
    ("李管理员", "李管理员支付宝", "医疗", "EXPENSE", "120.00", "27", "药品"),
    ("王成员", "王成员银行卡", "工资", "INCOME", "5600.00", "01", "工资到账"),
    ("王成员", "王成员银行卡", "奖金", "INCOME", "500.00", "07", "绩效奖金"),
    ("王成员", "王成员银行卡", "住房", "EXPENSE", "1800.00", "03", "房租分摊"),
    ("王成员", "王成员现金", "餐饮", "EXPENSE", "300.00", "10", "日常餐饮"),
    ("王成员", "王成员银行卡", "交通", "EXPENSE", "220.00", "14", "通勤交通"),
    ("王成员", "王成员银行卡", "购物", "EXPENSE", "380.00", "18", "衣物和日用品"),
    ("王成员", "王成员现金", "娱乐", "EXPENSE", "220.00", "24", "周末活动"),
    ("王成员", "王成员银行卡", "医疗", "EXPENSE", "100.00", "28", "药品"),
)

MONTHLY_BUDGETS = {
    "family": ("9000.00", (("餐饮", "1200.00"), ("交通", "700.00"), ("购物", "1500.00"), ("娱乐", "900.00"), ("医疗", "600.00"))),
    "张管理员": ("4200.00", (("餐饮", "600.00"), ("交通", "350.00"), ("购物", "600.00"), ("娱乐", "400.00"), ("医疗", "300.00"))),
    "李管理员": ("3800.00", (("餐饮", "650.00"), ("交通", "300.00"), ("购物", "650.00"), ("娱乐", "450.00"), ("医疗", "250.00"))),
    "王成员": ("3200.00", (("餐饮", "550.00"), ("交通", "400.00"), ("购物", "500.00"), ("娱乐", "350.00"), ("医疗", "200.00"))),
}

DEMO_TRANSFERS = (
    ("张管理员", "工资银行卡", "张管理员", "张管理员现金", "300.00", "11", "日常备用金"),
    ("李管理员", "李管理员支付宝", "李管理员", "李管理员微信", "450.00", "15", "微信日常消费充值"),
    ("张管理员", "工资银行卡", "王成员", "王成员银行卡", "600.00", "20", "家庭生活费，等待转入方确认"),
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


def _category_map(db: Session, family_id: int) -> dict[tuple[str, str], Category]:
    categories = db.scalars(
        select(Category).where(Category.family_id == family_id, Category.deleted_at.is_(None))
    ).all()
    return {(category.name, category.type): category for category in categories}


def _seed_budgets(
    db: Session,
    family_id: int,
    members: dict[str, FamilyMember],
    categories: dict[tuple[str, str], Category],
) -> int:
    created = 0
    for month in DEMO_MONTHS:
        for scope_name, (total, items) in MONTHLY_BUDGETS.items():
            scope = "family" if scope_name == "family" else "personal"
            member_id = None if scope == "family" else members[scope_name].id
            budget = db.scalar(
                select(MonthlyBudget).where(
                    MonthlyBudget.family_id == family_id,
                    MonthlyBudget.month == month,
                    MonthlyBudget.scope == scope,
                    MonthlyBudget.member_id == member_id,
                )
            )
            if budget is None:
                budget = MonthlyBudget(
                    family_id=family_id,
                    member_id=member_id,
                    month=month,
                    scope=scope,
                    total_amount=Decimal(total),
                )
                db.add(budget)
                db.flush()
                created += 1
            else:
                budget.total_amount = Decimal(total)
                db.query(CategoryBudget).filter(CategoryBudget.budget_id == budget.id).delete(
                    synchronize_session=False
                )

            for category_name, amount in items:
                db.add(
                    CategoryBudget(
                        budget_id=budget.id,
                        category_id=categories[(category_name, "EXPENSE")].id,
                        amount=Decimal(amount),
                    )
                )
    return created


def _parse_demo_datetime(month: str, day: str) -> datetime:
    return datetime.fromisoformat(f"{month}-{day}T12:00:00+00:00")


def _seed_transactions(
    db: Session,
    family_id: int,
    members: dict[str, FamilyMember],
    users: dict[str, User],
    accounts: dict[tuple[str, str], Account],
    categories: dict[tuple[str, str], Category],
) -> int:
    created = 0
    for month in DEMO_MONTHS[:2]:
        for owner, account_name, category_name, type_, amount, day, remark in MONTHLY_TRANSACTIONS:
            marker = f"{DEMO_MARKER} {month}-{day} {owner} {remark}"
            exists = db.scalar(select(Transaction).where(Transaction.remark == marker))
            if exists is not None:
                continue
            account = accounts[(owner, account_name)]
            member = members[owner]
            category = categories[(category_name, type_)]
            value = Decimal(amount)
            db.add(
                Transaction(
                    family_id=family_id,
                    account_id=account.id,
                    category_id=category.id,
                    beneficiary_member_id=member.id,
                    recorder_user_id=users[next(item["username"] for item in DEMO_USERS if item["nickname"] == owner)].id,
                    type=type_,
                    amount=value,
                    occurred_at=_parse_demo_datetime(month, day),
                    remark=marker,
                    status="CONFIRMED",
                )
            )
            if type_ == "INCOME":
                account.current_balance += value
            else:
                account.current_balance -= value
            created += 1
    return created


def _seed_transfers(
    db: Session,
    family_id: int,
    members: dict[str, FamilyMember],
    users: dict[str, User],
    accounts: dict[tuple[str, str], Account],
) -> int:
    created = 0
    recorder_id = users["admin_zhang"].id
    for month in DEMO_MONTHS[:2]:
        for from_owner, from_name, to_owner, to_name, amount, day, remark in DEMO_TRANSFERS:
            marker = f"{DEMO_MARKER} {month}-{day} {remark}"
            if db.scalar(select(Transfer).where(Transfer.remark == marker)) is not None:
                continue
            from_account = accounts[(from_owner, from_name)]
            to_account = accounts[(to_owner, to_name)]
            value = Decimal(amount)
            same_member = from_account.owner_member_id == to_account.owner_member_id
            db.add(
                Transfer(
                    family_id=family_id,
                    from_account_id=from_account.id,
                    to_account_id=to_account.id,
                    from_member_id=members[from_owner].id,
                    to_member_id=members[to_owner].id,
                    recorder_user_id=recorder_id,
                    amount=value,
                    occurred_at=_parse_demo_datetime(month, day),
                    remark=marker,
                    status="CONFIRMED" if same_member else "PENDING_CONFIRM",
                )
            )
            if same_member:
                from_account.current_balance -= value
                to_account.current_balance += value
            created += 1
    return created


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

    account_records = {}
    for nickname, account_name, account_type, balance in DEMO_ACCOUNTS:
        account_records[(nickname, account_name)] = _get_or_create_account(
            db,
            family.id,
            members[nickname].id,
            account_name,
            account_type,
            balance,
        )

    categories = _category_map(db, family.id)
    budget_count = _seed_budgets(db, family.id, members, categories)
    transaction_count = _seed_transactions(
        db, family.id, members, users, account_records, categories
    )
    transfer_count = _seed_transfers(db, family.id, members, users, account_records)
    db.commit()
    return {
        "users": len(users),
        "members": len(members),
        "accounts": len(DEMO_ACCOUNTS),
        "budgets": len(DEMO_MONTHS) * len(MONTHLY_BUDGETS),
        "transactions": len(DEMO_MONTHS[:2]) * len(MONTHLY_TRANSACTIONS),
        "transfers": len(DEMO_MONTHS[:2]) * len(DEMO_TRANSFERS),
        "created_budgets": budget_count,
        "created_transactions": transaction_count,
        "created_transfers": transfer_count,
    }


def main() -> None:
    with SessionLocal() as db:
        result = seed_demo_data(db)
    print(
        "演示数据已准备："
        f"{result['users']} 个用户、{result['members']} 个家庭成员、"
        f"{result['accounts']} 个账户、{result['budgets']} 条预算、"
        f"{result['transactions']} 条流水、{result['transfers']} 条转账。"
    )
    print("演示账号密码：Demo@123456")
    print("账号：admin_zhang、admin_li、member_wang")


if __name__ == "__main__":
    main()
