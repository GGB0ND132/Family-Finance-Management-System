"""流水业务逻辑：校验、锁账户、余额应用/撤销/编辑与权限。

规则来源：`docs/详细设计.md` 第 6 节。
"""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.common.money import ensure_positive, quantize_money
from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from app.modules.accounts.models import Account
from app.modules.accounts.repository import AccountRepository
from app.modules.categories.models import Category
from app.modules.families import repository as family_repo
from app.modules.families.models import FamilyMember
from app.modules.transactions.models import Transaction
from app.modules.transactions.repository import TransactionRepository
from app.modules.transactions.schemas import TransactionOut
from app.modules.users.models import User


def parse_occurred_at(value: str) -> datetime:
    """把 ISO 8601 时间字符串解析为带时区 datetime；业务精度到分钟。"""
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError) as exc:
        raise BadRequestError("发生时间格式非法，需为 ISO 8601 格式") from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _resolve_member(db: Session, family_id: int, user_id: int) -> FamilyMember:
    """校验当前用户是目标家庭成员，否则 403。"""
    member = family_repo.get_member_by_user(db, family_id, user_id)
    if member is None:
        raise ForbiddenError("你不是该家庭的成员")
    return member


def _lock_and_validate_account(db: Session, family_id: int, account_id: int) -> Account:
    """带行锁查询账户，校验家庭归属与未销户。"""
    account = AccountRepository(db).get_by_id_for_update(account_id)
    if not account:
        raise NotFoundError("账户不存在")
    if account.family_id != family_id:
        raise ForbiddenError("账户不属于当前家庭")
    if account.closed_at is not None:
        raise ConflictError("已销户账户不能产生流水")
    return account


def _validate_category(db: Session, family_id: int, category_id: int, type_: str) -> Category:
    category = db.get(Category, category_id)
    if not category:
        raise NotFoundError("分类不存在")
    if category.family_id != family_id:
        raise ForbiddenError("分类不属于当前家庭")
    if category.deleted_at is not None:
        raise BadRequestError("分类已被删除，不能用于新流水")
    if category.type != type_:
        raise BadRequestError("分类方向与流水类型不匹配")
    return category


def _validate_member(db: Session, family_id: int, member_id: int) -> FamilyMember:
    member = db.get(FamilyMember, member_id)
    if not member or member.family_id != family_id:
        raise BadRequestError("资金归属人无效或不属于当前家庭")
    return member


def _apply_balance(db: Session, account: Account, type_: str, amount: Decimal) -> None:
    """收入加余额、支出减余额；调用方需已加锁账户。"""
    if type_ == "INCOME":
        account.current_balance = quantize_money(account.current_balance + amount)
    else:
        account.current_balance = quantize_money(account.current_balance - amount)
    db.flush()


def _reverse_balance(db: Session, account: Account, type_: str, amount: Decimal) -> None:
    """反向撤销余额影响。"""
    if type_ == "INCOME":
        account.current_balance = quantize_money(account.current_balance - amount)
    else:
        account.current_balance = quantize_money(account.current_balance + amount)
    db.flush()


def _can_maintain(member: FamilyMember, tx: Transaction, account: Account) -> bool:
    """普通成员可维护账户所属人为自己、资金归属人为自己或自己录入的流水；管理员全部。"""
    if member.role == "ADMIN":
        return True
    return (
        account.owner_member_id == member.id
        or tx.beneficiary_member_id == member.id
        or tx.recorder_user_id == member.user_id
    )


def create_transaction(
    db: Session,
    user: User,
    *,
    family_id: int,
    account_id: int,
    category_id: int,
    beneficiary_member_id: int,
    type_: str,
    amount: str,
    occurred_at: str,
    remark: str | None = None,
) -> Transaction:
    """创建流水并同步更新账户余额。"""
    member = _resolve_member(db, family_id, user.id)
    account = _lock_and_validate_account(db, family_id, account_id)
    _validate_category(db, family_id, category_id, type_)
    _validate_member(db, family_id, beneficiary_member_id)

    # 普通成员只能为本人账户、本人资金归属记账；管理员不受限
    if member.role != "ADMIN":
        if account.owner_member_id != member.id or beneficiary_member_id != member.id:
            raise ForbiddenError("普通成员只能为本人账户、本人资金归属记账")

    dec_amount = ensure_positive(amount)
    occurred = parse_occurred_at(occurred_at)

    tx = Transaction(
        family_id=family_id,
        account_id=account_id,
        category_id=category_id,
        beneficiary_member_id=beneficiary_member_id,
        recorder_user_id=user.id,
        type=type_,
        amount=dec_amount,
        occurred_at=occurred,
        remark=remark,
    )
    tx = TransactionRepository(db).create(tx)
    _apply_balance(db, account, type_, dec_amount)
    db.commit()
    return tx


def get_transaction(db: Session, user: User, tx_id: int) -> Transaction:
    """获取流水详情，先校验当前用户属于该家庭。"""
    tx = TransactionRepository(db).get_by_id(tx_id)
    if not tx:
        raise NotFoundError("流水不存在")
    _resolve_member(db, tx.family_id, user.id)
    return tx


def update_transaction(db: Session, user: User, tx_id: int, **fields) -> Transaction:
    """编辑流水：锁定旧/新账户，撤销旧影响、校验新字段、应用新影响。"""
    repo = TransactionRepository(db)
    tx = repo.get_by_id(tx_id)
    if not tx:
        raise NotFoundError("流水不存在")
    member = _resolve_member(db, tx.family_id, user.id)

    old_account_id = tx.account_id
    new_account_id = fields.get("account_id") or old_account_id
    new_category_id = fields.get("category_id") or tx.category_id
    new_beneficiary_id = fields.get("beneficiary_member_id") or tx.beneficiary_member_id
    new_amount = ensure_positive(fields["amount"]) if fields.get("amount") else tx.amount
    new_occurred = parse_occurred_at(fields["occurred_at"]) if fields.get("occurred_at") else tx.occurred_at

    # 按账户 ID 升序加锁，避免死锁
    account_ids = sorted({old_account_id, new_account_id})
    accounts = {aid: _lock_and_validate_account(db, tx.family_id, aid) for aid in account_ids}

    # 权限：旧流水与本人相关（账户所属人/资金归属人/录入人）或管理员
    if not _can_maintain(member, tx, accounts[old_account_id]):
        raise ForbiddenError("无权编辑该流水")

    # 校验新字段：家庭归属、销户状态、分类方向、成员归属、金额
    _validate_category(db, tx.family_id, new_category_id, tx.type)
    _validate_member(db, tx.family_id, new_beneficiary_id)

    # 撤销旧影响 -> 应用新值 -> 应用新影响
    _reverse_balance(db, accounts[old_account_id], tx.type, tx.amount)

    tx.account_id = new_account_id
    tx.category_id = new_category_id
    tx.beneficiary_member_id = new_beneficiary_id
    tx.amount = new_amount
    tx.occurred_at = new_occurred
    if "remark" in fields and fields["remark"] is not None:
        tx.remark = fields["remark"]

    _apply_balance(db, accounts[new_account_id], tx.type, tx.amount)
    db.flush()
    db.commit()
    return tx


def delete_transaction(db: Session, user: User, tx_id: int) -> None:
    """删除流水并反向恢复余额。"""
    repo = TransactionRepository(db)
    tx = repo.get_by_id(tx_id)
    if not tx:
        raise NotFoundError("流水不存在")
    member = _resolve_member(db, tx.family_id, user.id)

    account = _lock_and_validate_account(db, tx.family_id, tx.account_id)
    if not _can_maintain(member, tx, account):
        raise ForbiddenError("无权删除该流水")

    _reverse_balance(db, account, tx.type, tx.amount)
    repo.delete(tx)
    db.commit()


def list_transactions(
    db: Session,
    user: User,
    family_id: int,
    *,
    scope: str = "family",
    page: int = 1,
    page_size: int = 20,
    type_: str | None = None,
    account_id: int | None = None,
    category_id: int | None = None,
    beneficiary_member_id: int | None = None,
    owner_member_id: int | None = None,
    recorder_user_id: int | None = None,
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
    min_amount: Decimal | None = None,
    max_amount: Decimal | None = None,
) -> tuple[list[Transaction], int]:
    """分页查询流水。personal 范围强制按当前成员作为资金归属人过滤。"""
    member = _resolve_member(db, family_id, user.id)

    if scope not in ("personal", "family"):
        raise BadRequestError("scope 仅支持 personal 或 family")

    if scope == "personal":
        beneficiary_member_id = member.id

    repo = TransactionRepository(db)
    return repo.list_with_filters(
        family_id,
        page=page,
        page_size=page_size,
        type_=type_,
        account_id=account_id,
        category_id=category_id,
        beneficiary_member_id=beneficiary_member_id,
        owner_member_id=owner_member_id,
        recorder_user_id=recorder_user_id,
        from_dt=from_dt,
        to_dt=to_dt,
        min_amount=min_amount,
        max_amount=max_amount,
    )


def _build_out(db: Session, tx: Transaction) -> dict:
    """把 ORM 对象转换为 TransactionOut 字典（含关联展示名称）。"""
    account = db.get(Account, tx.account_id)
    category = db.get(Category, tx.category_id)
    beneficiary_member = db.get(FamilyMember, tx.beneficiary_member_id)
    recorder_user = db.get(User, tx.recorder_user_id)

    owner_member = db.get(FamilyMember, account.owner_member_id) if account else None
    owner_user = db.get(User, owner_member.user_id) if owner_member else None
    beneficiary_user = db.get(User, beneficiary_member.user_id) if beneficiary_member else None

    return TransactionOut(
        id=tx.id,
        family_id=tx.family_id,
        account_id=tx.account_id,
        category_id=tx.category_id,
        beneficiary_member_id=tx.beneficiary_member_id,
        recorder_user_id=tx.recorder_user_id,
        type=tx.type,
        amount=str(tx.amount),
        occurred_at=tx.occurred_at.isoformat(),
        remark=tx.remark,
        created_at=tx.created_at.isoformat() if tx.created_at else "",
        account_name=account.name if account else None,
        account_owner_member_id=account.owner_member_id if account else None,
        account_owner_nickname=owner_user.nickname if owner_user else None,
        account_current_balance=str(account.current_balance) if account else None,
        category_name=category.name if category else None,
        category_type=category.type if category else None,
        beneficiary_nickname=beneficiary_user.nickname if beneficiary_user else None,
        recorder_nickname=recorder_user.nickname if recorder_user else None,
    ).model_dump()