"""账户业务逻辑。"""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.common.money import quantize_money
from app.core.exceptions import (
    ConflictError,
    PermissionDeniedError,
    ResourceNotFoundError,
    ValidationError,
)
from app.modules.accounts.models import Account
from app.modules.accounts.repository import AccountRepository
from app.modules.families.models import FamilyMember


def _validate_owner_member(db: Session, family_id: int, owner_member_id: int):
    """校验所属成员是否存在且属于当前家庭。"""
    member = db.get(FamilyMember, owner_member_id)
    if not member or member.family_id != family_id:
        raise ValidationError("账户所属成员无效或不属于当前家庭")
    return member


def create_account(
    db: Session,
    family_id: int,
    owner_member_id: int,
    name: str,
    type_: str,
    initial_balance: str = "0.00",
    remark: str | None = None,
) -> Account:
    """创建账户。"""
    repo = AccountRepository(db)

    # 校验所属成员存在且属于当前家庭
    _validate_owner_member(db, family_id, owner_member_id)

    balance = quantize_money(Decimal(initial_balance))
    account = Account(
        family_id=family_id,
        owner_member_id=owner_member_id,
        name=name,
        type=type_,
        initial_balance=balance,
        current_balance=balance,
        remark=remark,
    )
    return repo.create(account)


def get_account(db: Session, account_id: int) -> Account:
    """获取账户，不存在时抛异常。"""
    account = AccountRepository(db).get_by_id(account_id)
    if not account:
        raise ResourceNotFoundError("账户不存在")
    return account


def get_account_with_owner(db: Session, account_id: int) -> Account:
    """获取账户并预加载所属成员及用户信息，不存在时抛异常。"""
    account = AccountRepository(db).get_by_id_with_owner(account_id)
    if not account:
        raise ResourceNotFoundError("账户不存在")
    return account


def update_account(
    db: Session,
    account_id: int,
    family_id: int,
    name: str | None = None,
    type_: str | None = None,
    owner_member_id: int | None = None,
    remark: str | None = None,
) -> Account:
    """更新账户信息。

    注意：编辑账户所属人只改变当前资产归属，不篡改历史收支的资金归属人和录入人。
    """
    repo = AccountRepository(db)
    account = get_account(db, account_id)

    # 跨家庭防护
    if account.family_id != family_id:
        raise PermissionDeniedError("无权操作该账户")

    if owner_member_id is not None:
        _validate_owner_member(db, family_id, owner_member_id)

    if name is not None:
        account.name = name
    if type_ is not None:
        account.type = type_
    if owner_member_id is not None:
        account.owner_member_id = owner_member_id
    if remark is not None:
        account.remark = remark

    db.flush()
    return account


def close_or_delete_account(
    db: Session,
    account_id: int,
    family_id: int,
) -> dict:
    """删除/销户账户。

    规则：
    - 余额非 0.00 → 拒绝（409）。
    - 余额为 0 且无历史流水和转账 → 物理删除。
    - 余额为 0 且有历史记录 → 销户（设置 closed_at）。

    Returns:
        dict: { "action": "deleted" | "closed", "account": Account }
    """
    repo = AccountRepository(db)

    # 行锁查询，避免并发余额变更
    account = repo.get_by_id_for_update(account_id)
    if not account:
        raise ResourceNotFoundError("账户不存在")
    if account.family_id != family_id:
        raise PermissionDeniedError("无权操作该账户")

    # 校验余额为零
    if account.current_balance != Decimal("0.00"):
        raise ConflictError("账户仍有资金，请先转出后再销户")

    # 检查是否有历史引用
    if repo.has_references(account_id):
        # 有历史记录 → 销户
        account.closed_at = datetime.now(timezone.utc)
        db.flush()
        return {"action": "closed", "account": account}
    else:
        # 无历史记录 → 物理删除
        repo.delete(account)
        return {"action": "deleted", "account": None}


def list_accounts(
    db: Session,
    family_id: int,
    owner_member_id: int | None = None,
    include_closed: bool = False,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Account], int]:
    """分页查询账户列表。"""
    repo = AccountRepository(db)
    return repo.list_by_family(
        family_id=family_id,
        owner_member_id=owner_member_id,
        include_closed=include_closed,
        page=page,
        page_size=page_size,
    )


def _build_account_out(account: Account) -> dict:
    """将 Account ORM 对象转换为 AccountOut 字典。"""
    return {
        "id": account.id,
        "family_id": account.family_id,
        "owner_member_id": account.owner_member_id,
        "owner_nickname": (
            account.owner_member.user.nickname
            if account.owner_member and account.owner_member.user
            else None
        ),
        "name": account.name,
        "type": account.type,
        "initial_balance": str(account.initial_balance),
        "current_balance": str(account.current_balance),
        "remark": account.remark,
        "closed_at": account.closed_at.isoformat() if account.closed_at else None,
        "created_at": account.created_at.isoformat(),
        "updated_at": account.updated_at.isoformat() if account.updated_at else None,
    }