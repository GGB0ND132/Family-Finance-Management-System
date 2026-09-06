"""转账数据访问。"""

from sqlalchemy.orm import Session

from app.modules.transfers.models import Transfer


class TransferRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, transfer: Transfer) -> Transfer:
        self.db.add(transfer)
        self.db.flush()
        return transfer

    def get_by_id(self, transfer_id: int) -> Transfer | None:
        return self.db.get(Transfer, transfer_id)

    def list_with_filters(
        self,
        family_id: int,
        *,
        page: int = 1,
        page_size: int = 20,
        from_date: str | None = None,
        to_date: str | None = None,
        member_id: int | None = None,
    ) -> tuple[list[Transfer], int]:
        q = self.db.query(Transfer).filter(Transfer.family_id == family_id)

        if from_date:
            q = q.filter(Transfer.occurred_at >= from_date)
        if to_date:
            q = q.filter(Transfer.occurred_at <= to_date)
        if member_id:
            q = q.filter(
                (Transfer.from_member_id == member_id)
                | (Transfer.to_member_id == member_id)
            )

        total = q.count()
        items = (
            q.order_by(Transfer.occurred_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    def delete(self, transfer: Transfer) -> None:
        self.db.delete(transfer)
        self.db.flush()