"""转账数据访问。"""

from datetime import datetime

from sqlalchemy import or_
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

    def delete(self, transfer: Transfer) -> None:
        self.db.delete(transfer)
        self.db.flush()

    def list_with_filters(
        self,
        family_id: int,
        *,
        page: int = 1,
        page_size: int = 20,
        from_dt: datetime | None = None,
        to_dt: datetime | None = None,
        from_member_id: int | None = None,
        to_member_id: int | None = None,
        from_account_id: int | None = None,
        to_account_id: int | None = None,
        involved_member_id: int | None = None,
    ) -> tuple[list[Transfer], int]:
        """按家庭分页筛选转账。

        个人范围由调用方把 `involved_member_id` 传为当前成员 ID，
        从而过滤当前成员作为转出方或转入方的转账。
        """
        q = self.db.query(Transfer).filter(Transfer.family_id == family_id)

        if from_dt is not None:
            q = q.filter(Transfer.occurred_at >= from_dt)
        if to_dt is not None:
            q = q.filter(Transfer.occurred_at <= to_dt)
        if from_member_id is not None:
            q = q.filter(Transfer.from_member_id == from_member_id)
        if to_member_id is not None:
            q = q.filter(Transfer.to_member_id == to_member_id)
        if from_account_id is not None:
            q = q.filter(Transfer.from_account_id == from_account_id)
        if to_account_id is not None:
            q = q.filter(Transfer.to_account_id == to_account_id)
        if involved_member_id is not None:
            q = q.filter(
                or_(
                    Transfer.from_member_id == involved_member_id,
                    Transfer.to_member_id == involved_member_id,
                )
            )

        total = q.count()
        items = (
            q.order_by(Transfer.occurred_at.desc(), Transfer.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total