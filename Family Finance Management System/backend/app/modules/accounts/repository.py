"""账户数据访问。"""

from sqlalchemy.orm import Session, joinedload

from app.modules.accounts.models import Account
from app.modules.families.models import FamilyMember


class AccountRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, account: Account) -> Account:
        self.db.add(account)
        self.db.flush()
        return account

    def get_by_id(self, account_id: int) -> Account | None:
        return self.db.get(Account, account_id)

    def get_by_id_with_owner(self, account_id: int) -> Account | None:
        """查询账户并预加载所属成员及用户信息。"""
        return (
            self.db.query(Account)
            .options(
                joinedload(Account.owner_member).joinedload(FamilyMember.user)
            )
            .filter(Account.id == account_id)
            .first()
        )

    def get_by_id_for_update(self, account_id: int) -> Account | None:
        """带行锁查询账户，用于余额变更等并发操作。"""
        return (
            self.db.query(Account)
            .filter(Account.id == account_id)
            .with_for_update()
            .first()
        )

    def list_by_family(
        self,
        family_id: int,
        owner_member_id: int | None = None,
        include_closed: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Account], int]:
        """分页查询家庭账户。

        Args:
            family_id: 家庭 ID。
            owner_member_id: 可选，按所属成员筛选。
            include_closed: 是否包含已销户账户（默认不包含）。
            page: 页码，从 1 开始。
            page_size: 每页条数，最大 100。

        Returns:
            (账户列表, 总数)。
        """
        q = (
            self.db.query(Account)
            .options(
                joinedload(Account.owner_member).joinedload(FamilyMember.user)
            )
            .filter(Account.family_id == family_id)
        )
        if owner_member_id is not None:
            q = q.filter(Account.owner_member_id == owner_member_id)
        if not include_closed:
            q = q.filter(Account.closed_at.is_(None))

        total = q.count()
        offset = (page - 1) * page_size
        items = q.order_by(Account.created_at.desc()).offset(offset).limit(page_size).all()
        return items, total

    def has_transactions(self, account_id: int) -> bool:
        """检查账户是否有关联的收支流水。"""
        from app.modules.transactions.models import Transaction

        return (
            self.db.query(Transaction)
            .filter(Transaction.account_id == account_id)
            .limit(1)
            .count()
            > 0
        )

    def has_transfers(self, account_id: int) -> bool:
        """检查账户是否有关联的转账记录（作为转出或转入方）。"""
        from app.modules.transfers.models import Transfer

        return (
            self.db.query(Transfer)
            .filter(
                (Transfer.from_account_id == account_id)
                | (Transfer.to_account_id == account_id)
            )
            .limit(1)
            .count()
            > 0
        )

    def has_references(self, account_id: int) -> bool:
        """检查账户是否有流水或转账引用。"""
        return self.has_transactions(account_id) or self.has_transfers(account_id)

    def delete(self, account: Account) -> None:
        """物理删除账户。"""
        self.db.delete(account)
        self.db.flush()