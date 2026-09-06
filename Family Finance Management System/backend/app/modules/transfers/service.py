"""转账业务逻辑：双账户原子变更，按 ID 升序加锁防死锁。"""

from decimal import Decimal

from sqlalchemy.orm import Session

from app.common.money import ensure_positive
from app.core.exceptions import ConflictError, ResourceNotFoundError, ValidationError
from app.modules.transfers.models import Transfer
from app.modules.transfers.repository import TransferRepository


def _lock_and_get_account(db: Session, account_id: int):
    """按 ID 加排他锁获取账户。"""
    from app.modules.accounts.models import Account

    account = (
        db.query(Account)
        .filter(Account.id == account_id)
        .with_for_update()
        .first()
    )
    if not account:
        raise ResourceNotFoundError("账户不存在")
    if account.closed_at:
        raise ConflictError("已销户账户不能参与转账")
    return account


def _get_member_id(db: Session, account_id: int) -> int:
    """返回账户所属人 member_id。"""
    from app.modules.accounts.models import Account

    account = db.get(Account, account_id)
    if not account:
        raise ResourceNotFoundError("账户不存在")
    return account.owner_member_id


def create_transfer(
    db: Session,
    *,
    family_id: int,
    from_account_id: int,
    to_account_id: int,
    recorder_user_id: int,
    amount: str,
    occurred_at: str,
    remark: str | None = None,
) -> Transfer:
    """创建转账。两个账户同家庭、未销户、不同；按 ID 顺序加锁。"""
    if from_account_id == to_account_id:
        raise ValidationError("转出和转入账户不能相同")

    dec_amount = ensure_positive(Decimal(amount))

    # 按 ID 升序加锁，避免死锁
    lock_order = sorted([from_account_id, to_account_id])
    accounts = {}
    for aid in lock_order:
        accounts[aid] = _lock_and_get_account(db, aid)

    from_account = accounts[from_account_id]
    to_account = accounts[to_account_id]

    if from_account.family_id != family_id or to_account.family_id != family_id:
        raise ValidationError("两个账户必须属于同一家庭")

    from_member_id = from_account.owner_member_id
    to_member_id = to_account.owner_member_id

    from_account.current_balance -= dec_amount
    to_account.current_balance += dec_amount

    transfer = Transfer(
        family_id=family_id,
        from_account_id=from_account_id,
        to_account_id=to_account_id,
        from_member_id=from_member_id,
        to_member_id=to_member_id,
        recorder_user_id=recorder_user_id,
        amount=dec_amount,
        occurred_at=occurred_at,
        remark=remark,
    )
    return TransferRepository(db).create(transfer)


def get_transfer(db: Session, transfer_id: int) -> Transfer:
    transfer = TransferRepository(db).get_by_id(transfer_id)
    if not transfer:
        raise ResourceNotFoundError("转账不存在")
    return transfer


def _revert_transfer_balance(db: Session, transfer: Transfer) -> None:
    """反向恢复转账涉及的余额。"""
    from_account = _lock_and_get_account(db, transfer.from_account_id)
    to_account = _lock_and_get_account(db, transfer.to_account_id)
    from_account.current_balance += transfer.amount
    to_account.current_balance -= transfer.amount


def _apply_transfer_balance(db: Session, transfer: Transfer) -> None:
    """应用转账余额变更。"""
    from_account = _lock_and_get_account(db, transfer.from_account_id)
    to_account = _lock_and_get_account(db, transfer.to_account_id)
    from_account.current_balance -= transfer.amount
    to_account.current_balance += transfer.amount


def update_transfer(db: Session, transfer_id: int, **kwargs) -> Transfer:
    """编辑转账：恢复原转账 -> 更新字段 -> 应用新转账。"""
    transfer = get_transfer(db, transfer_id)
    _revert_transfer_balance(db, transfer)

    for key, value in kwargs.items():
        if value is not None and hasattr(transfer, key):
            if key == "amount":
                value = ensure_positive(Decimal(str(value)))
            setattr(transfer, key, value)

    # 校验新账户
    if transfer.from_account_id == transfer.to_account_id:
        raise ValidationError("转出和转入账户不能相同")

    # 更新成员信息
    transfer.from_member_id = _get_member_id(db, transfer.from_account_id)
    transfer.to_member_id = _get_member_id(db, transfer.to_account_id)

    _apply_transfer_balance(db, transfer)
    db.flush()
    return transfer


def delete_transfer(db: Session, transfer_id: int) -> None:
    """删除转账并反向恢复余额。"""
    transfer = get_transfer(db, transfer_id)
    _revert_transfer_balance(db, transfer)
    TransferRepository(db).delete(transfer)


def list_transfers(
    db: Session, family_id: int, **filters
) -> tuple[list[Transfer], int]:
    return TransferRepository(db).list_with_filters(family_id, **filters)