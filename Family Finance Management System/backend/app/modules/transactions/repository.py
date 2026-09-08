"""流水数据访问。"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.modules.accounts.models import Account
from app.modules.transactions.models import Transaction


class TransactionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, tx: Transaction) -> Transaction:
        self.db.add(tx)
        self.db.flush()
        return tx

    def get_by_id(self, tx_id: int) -> Transaction | None:
        return self.db.get(Transaction, tx_id)

    def delete(self, tx: Transaction) -> None:
        self.db.delete(tx)
        self.db.flush()

    def list_with_filters(
        self,
        family_id: int,
        *,
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
        """按家庭分页筛选流水。

        个人范围由调用方把 `beneficiary_member_id` 传为当前成员 ID，
        从而强制按资金归属人过滤。
        """
        q = self.db.query(Transaction).filter(Transaction.family_id == family_id)

        if type_:
            q = q.filter(Transaction.type == type_)
        if account_id:
            q = q.filter(Transaction.account_id == account_id)
        if category_id:
            q = q.filter(Transaction.category_id == category_id)
        if beneficiary_member_id:
            q = q.filter(Transaction.beneficiary_member_id == beneficiary_member_id)
        if recorder_user_id:
            q = q.filter(Transaction.recorder_user_id == recorder_user_id)
        if owner_member_id:
            # 账户所属人筛选：通过账户表反查
            sub = (
                self.db.query(Account.id)
                .filter(Account.owner_member_id == owner_member_id)
                .subquery()
            )
            q = q.filter(Transaction.account_id.in_(sub))
        if from_dt:
            q = q.filter(Transaction.occurred_at >= from_dt)
        if to_dt:
            q = q.filter(Transaction.occurred_at <= to_dt)
        if min_amount is not None:
            q = q.filter(Transaction.amount >= min_amount)
        if max_amount is not None:
            q = q.filter(Transaction.amount <= max_amount)

        total = q.count()
        items = (
            q.order_by(Transaction.occurred_at.desc(), Transaction.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total