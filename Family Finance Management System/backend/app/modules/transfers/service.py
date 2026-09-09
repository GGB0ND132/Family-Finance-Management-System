"""转账业务逻辑：校验、锁账户、余额应用/撤销、编辑与权限。

规则来源：`docs/详细设计.md` 第 7 节。
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
from app.modules.families import repository as family_repo
from app.modules.families.models import FamilyMember
from app.modules.transfers.models import Transfer
from app.modules.transfers.repository import TransferRepository
from app.modules.transfers.schemas import TransferOut
from app.modules.users.models import User


def parse_occurred_at(value: str) -> datetime:
    """把 ISO 8601 时间字符串解析为带时区 datetime；业务精度到分钟。"""
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError) as exc:
        raise BadRequestError("发生时间格式非法，需为 ISO 8601 格式") from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    # 转账发生时间统一按分钟保存
    return dt.replace(second=0, microsecond=0)


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
        raise ConflictError("已销户账户不能参与转账")
    return account


def _can_maintain(member: FamilyMember, transfer: Transfer) -> bool:
    """普通成员可维护自己作为转出方、转入方或录入人的转账；管理员全部。"""
    if member.role == "ADMIN":
        return True
    return (
        transfer.from_member_id == member.id
        or transfer.to_member_id == member.id
        or transfer.recorder_user_id == member.user_id
    )


def _apply_balance(from_account: Account, to_account: Account, amount: Decimal) -> None:
    """转出账户余额减少，转入账户余额增加。"""
    from_account.current_balance = quantize_money(from_account.current_balance - amount)
    to_account.current_balance = quantize_money(to_account.current_balance + amount)


def _reverse_balance(from_account: Account, to_account: Account, amount: Decimal) -> None:
    """反向恢复转账造成的余额影响。"""
    from_account.current_balance = quantize_money(from_account.current_balance + amount)
    to_account.current_balance = quantize_money(to_account.current_balance - amount)


def create_transfer(
    db: Session,
    user: User,
    *,
    family_id: int,
    from_account_id: int,
    to_account_id: int,
    amount: str,
    occurred_at: str,
    remark: str | None = None,
) -> Transfer:
    """创建转账并在同一事务内完成两个账户余额变更与记录写入。"""
    member = _resolve_member(db, family_id, user.id)

    if from_account_id == to_account_id:
        raise BadRequestError("转出和转入账户不能相同")

    dec_amount = ensure_positive(amount)
    occurred = parse_occurred_at(occurred_at)

    # 按账户 ID 升序加锁，避免死锁
    ordered_ids = sorted([from_account_id, to_account_id])
    accounts = {aid: _lock_and_validate_account(db, family_id, aid) for aid in ordered_ids}
    from_account = accounts[from_account_id]
    to_account = accounts[to_account_id]

    # 普通成员只能以本人账户作为转出账户；管理员不受限
    if member.role != "ADMIN" and from_account.owner_member_id != member.id:
        raise ForbiddenError("普通成员只能以本人账户作为转出账户")

    transfer = Transfer(
        family_id=family_id,
        from_account_id=from_account_id,
        to_account_id=to_account_id,
        from_member_id=from_account.owner_member_id,
        to_member_id=to_account.owner_member_id,
        recorder_user_id=user.id,
        amount=dec_amount,
        occurred_at=occurred,
        remark=remark,
        status="CONFIRMED" if from_account.owner_member_id == to_account.owner_member_id else "PENDING_CONFIRM",
    )
    if transfer.status == "CONFIRMED":
        _apply_balance(from_account, to_account, dec_amount)
    transfer = TransferRepository(db).create(transfer)
    db.commit()
    return transfer


def get_transfer(db: Session, user: User, transfer_id: int) -> Transfer:
    """获取转账详情，先校验当前用户属于该家庭。"""
    transfer = TransferRepository(db).get_by_id(transfer_id)
    if not transfer:
        raise NotFoundError("转账不存在")
    _resolve_member(db, transfer.family_id, user.id)
    return transfer


def update_transfer(db: Session, user: User, transfer_id: int, **fields) -> Transfer:
    """编辑转账：锁定旧/新账户，恢复原影响 -> 校验新字段 -> 应用新影响。"""
    repo = TransferRepository(db)
    transfer = repo.get_by_id(transfer_id)
    if not transfer:
        raise NotFoundError("转账不存在")
    member = _resolve_member(db, transfer.family_id, user.id)

    old_from_id = transfer.from_account_id
    old_to_id = transfer.to_account_id
    new_from_id = fields.get("from_account_id") or old_from_id
    new_to_id = fields.get("to_account_id") or old_to_id
    new_amount = ensure_positive(fields["amount"]) if fields.get("amount") else transfer.amount
    new_occurred = (
        parse_occurred_at(fields["occurred_at"])
        if fields.get("occurred_at")
        else transfer.occurred_at
    )

    if new_from_id == new_to_id:
        raise BadRequestError("转出和转入账户不能相同")

    # 按账户 ID 升序加锁旧、新账户，避免死锁
    ordered_ids = sorted({old_from_id, old_to_id, new_from_id, new_to_id})
    accounts = {aid: _lock_and_validate_account(db, transfer.family_id, aid) for aid in ordered_ids}

    if not _can_maintain(member, transfer):
        raise ForbiddenError("无权编辑该转账")

    old_from = accounts[old_from_id]
    old_to = accounts[old_to_id]
    new_from = accounts[new_from_id]
    new_to = accounts[new_to_id]

    # 普通成员编辑后仍需以本人账户作为转出账户
    if member.role != "ADMIN" and new_from.owner_member_id != member.id:
        raise ForbiddenError("普通成员只能以本人账户作为转出账户")

    if transfer.status == "CONFIRMED":
        _reverse_balance(old_from, old_to, transfer.amount)

    transfer.from_account_id = new_from_id
    transfer.to_account_id = new_to_id
    transfer.from_member_id = new_from.owner_member_id
    transfer.to_member_id = new_to.owner_member_id
    transfer.amount = new_amount
    transfer.occurred_at = new_occurred
    if "remark" in fields and fields["remark"] is not None:
        transfer.remark = fields["remark"]

    transfer.status = "CONFIRMED" if new_from.owner_member_id == new_to.owner_member_id else "PENDING_CONFIRM"
    if transfer.status == "CONFIRMED":
        _apply_balance(new_from, new_to, new_amount)
    db.flush()
    db.commit()
    return transfer


def delete_transfer(db: Session, user: User, transfer_id: int) -> None:
    """删除转账并反向恢复两个账户余额。"""
    repo = TransferRepository(db)
    transfer = repo.get_by_id(transfer_id)
    if not transfer:
        raise NotFoundError("转账不存在")
    member = _resolve_member(db, transfer.family_id, user.id)

    ordered_ids = sorted([transfer.from_account_id, transfer.to_account_id])
    accounts = {
        aid: _lock_and_validate_account(db, transfer.family_id, aid)
        for aid in ordered_ids
    }
    from_account = accounts[transfer.from_account_id]
    to_account = accounts[transfer.to_account_id]

    if not _can_maintain(member, transfer):
        raise ForbiddenError("无权删除该转账")

    if transfer.status == "CONFIRMED":
        _reverse_balance(from_account, to_account, transfer.amount)
    repo.delete(transfer)
    db.commit()


def list_transfers(
    db: Session,
    user: User,
    family_id: int,
    *,
    scope: str = "family",
    page: int = 1,
    page_size: int = 20,
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
    from_member_id: int | None = None,
    to_member_id: int | None = None,
    from_account_id: int | None = None,
    to_account_id: int | None = None,
) -> tuple[list[Transfer], int]:
    """分页查询转账。personal 范围强制按当前成员作为转出方或转入方过滤。"""
    member = _resolve_member(db, family_id, user.id)

    if scope not in ("personal", "family"):
        raise BadRequestError("scope 仅支持 personal 或 family")

    repo = TransferRepository(db)
    return repo.list_with_filters(
        family_id,
        page=page,
        page_size=page_size,
        from_dt=from_dt,
        to_dt=to_dt,
        from_member_id=from_member_id,
        to_member_id=to_member_id,
        from_account_id=from_account_id,
        to_account_id=to_account_id,
        involved_member_id=member.id if scope == "personal" else None,
    )


def _build_out(db: Session, transfer: Transfer) -> dict:
    """把 ORM 对象转换为 TransferOut 字典（含关联展示名称）。"""
    from_account = db.get(Account, transfer.from_account_id)
    to_account = db.get(Account, transfer.to_account_id)
    from_member = db.get(FamilyMember, transfer.from_member_id)
    to_member = db.get(FamilyMember, transfer.to_member_id)
    recorder_user = db.get(User, transfer.recorder_user_id)

    from_user = db.get(User, from_member.user_id) if from_member else None
    to_user = db.get(User, to_member.user_id) if to_member else None

    return TransferOut(
        id=transfer.id,
        family_id=transfer.family_id,
        from_account_id=transfer.from_account_id,
        to_account_id=transfer.to_account_id,
        from_member_id=transfer.from_member_id,
        to_member_id=transfer.to_member_id,
        recorder_user_id=transfer.recorder_user_id,
        amount=str(transfer.amount),
        occurred_at=transfer.occurred_at.isoformat(),
        remark=transfer.remark,
        created_at=transfer.created_at.isoformat() if transfer.created_at else "",
        from_account_name=from_account.name if from_account else None,
        to_account_name=to_account.name if to_account else None,
        from_member_nickname=from_user.nickname if from_user else None,
        to_member_nickname=to_user.nickname if to_user else None,
        recorder_nickname=recorder_user.nickname if recorder_user else None,
        status=transfer.status,
    ).model_dump()


def confirm_transfer(db: Session, user: User, transfer_id: int) -> Transfer:
    transfer = get_transfer(db, user, transfer_id)
    member = _resolve_member(db, transfer.family_id, user.id)
    if transfer.status != "PENDING_CONFIRM":
        raise BadRequestError("该转账无需确认")
    if member.id != transfer.to_member_id:
        raise ForbiddenError("仅转入方成员可以确认该转账")
    ordered_ids = sorted([transfer.from_account_id, transfer.to_account_id])
    accounts = {aid: _lock_and_validate_account(db, transfer.family_id, aid) for aid in ordered_ids}
    _apply_balance(accounts[transfer.from_account_id], accounts[transfer.to_account_id], transfer.amount)
    transfer.status = "CONFIRMED"
    db.commit()
    return transfer
