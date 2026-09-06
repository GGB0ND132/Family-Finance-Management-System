"""流水数据访问。"""

from sqlalchemy.orm import Session

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
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> tuple[list[Transaction], int]:
        """分页筛选流水。TODO: 接入更多筛选字段。"""
        q = self.db.query(Transaction).filter(Transaction.family_id == family_id)

        if type_:
            q = q.filter(Transaction.type == type_)
        if account_id:
            q = q.filter(Transaction.account_id == account_id)
        if category_id:
            q = q.filter(Transaction.category_id == category_id)
        if beneficiary_member_id:
            q = q.filter(Transaction.beneficiary_member_id == beneficiary_member_id)
        if from_date:
            q = q.filter(Transaction.occurred_at >= from_date)
        if to_date:
            q = q.filter(Transaction.occurred_at <= to_date)

        total = q.count()
        items = (
            q.order_by(Transaction.occurred_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    def delete(self, tx: Transaction) -> None:
        self.db.delete(tx)
        self.db.flush()