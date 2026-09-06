"""流水业务逻辑：余额应用/撤销/编辑。"""

from decimal import Decimal

from sqlalchemy.orm import Session

from app.common.money import ensure_positive
from app.core.exceptions import ConflictError, ResourceNotFoundError, ValidationError
from app.modules.transactions.models import Transaction
from app.modules.transactions.repository import TransactionRepository


def _apply_balance(db: Session, account_id: int, type_: str, amount: Decimal) -> None:
    """收入加余额，支出减余额。需要调用方加锁账户。"""
    from app.modules.accounts.repository import AccountRepository

    account = AccountRepository(db).get_by_id(account_id)
    if not account:
        raise ResourceNotFoundError("账户不存在")
    if account.closed_at:
        raise ConflictError("已销户账户不能产生流水")
    if type_ == "INCOME":
        account.current_balance += amount
    else:
        account.current_balance -= amount
    db.flush()


def _reverse_balance(db: Session, account_id: int, type_: str, amount: Decimal) -> None:
    """反向恢复余额（撤销旧影响）。"""
    from app.modules.accounts.repository import AccountRepository

    account = AccountRepository(db).get_by_id(account_id)
    if not account:
        raise ResourceNotFoundError("账户不存在")
    if type_ == "INCOME":
        account.current_balance -= amount
    else:
        account.current_balance += amount
    db.flush()


def create_transaction(
    db: Session,
    *,
    family_id: int,
    account_id: int,
    category_id: int,
    beneficiary_member_id: int,
    recorder_user_id: int,
    type_: str,
    amount: str,
    occurred_at: str,
    remark: str | None = None,
) -> Transaction:
    """创建流水并应用余额变更。"""
    repo = TransactionRepository(db)

    # TODO: 校验账户/分类/成员同家庭、账户未销户、分类方向匹配
    dec_amount = ensure_positive(Decimal(amount))

    tx = Transaction(
        family_id=family_id,
        account_id=account_id,
        category_id=category_id,
        beneficiary_member_id=beneficiary_member_id,
        recorder_user_id=recorder_user_id,
        type=type_,
        amount=dec_amount,
        occurred_at=occurred_at,
        remark=remark,
    )
    tx = repo.create(tx)
    _apply_balance(db, account_id, type_, dec_amount)
    return tx


def get_transaction(db: Session, tx_id: int) -> Transaction:
    """获取流水详情。"""
    tx = TransactionRepository(db).get_by_id(tx_id)
    if not tx:
        raise ResourceNotFoundError("流水不存在")
    return tx


def update_transaction(db: Session, tx_id: int, **kwargs) -> Transaction:
    """编辑流水：先撤销旧余额影响，再应用新影响。"""
    repo = TransactionRepository(db)
    tx = get_transaction(db, tx_id)

    old_account_id = tx.account_id
    old_type = tx.type
    old_amount = tx.amount

    # 撤销旧影响
    _reverse_balance(db, old_account_id, old_type, old_amount)

    # 应用新字段
    for key, value in kwargs.items():
        if value is not None and hasattr(tx, key):
            if key == "amount":
                value = ensure_positive(Decimal(str(value)))
            setattr(tx, key, value)

    # 应用新影响
    _apply_balance(db, tx.account_id, tx.type, tx.amount)
    db.flush()
    return tx


def delete_transaction(db: Session, tx_id: int) -> None:
    """删除流水并反向恢复余额。"""
    tx = get_transaction(db, tx_id)
    _reverse_balance(db, tx.account_id, tx.type, tx.amount)
    TransactionRepository(db).delete(tx)


def list_transactions(
    db: Session, family_id: int, **filters
) -> tuple[list[Transaction], int]:
    """分页查询流水。"""
    repo = TransactionRepository(db)
    return repo.list_with_filters(family_id, **filters)