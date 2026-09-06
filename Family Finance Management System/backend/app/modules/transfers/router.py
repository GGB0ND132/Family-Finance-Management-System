"""转账路由。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.response import ApiResponse, PageData, ok
from app.core.deps import get_current_user, get_db
from app.modules.transfers.schemas import (
    CreateTransferRequest,
    TransferOut,
    UpdateTransferRequest,
)
from app.modules.transfers.service import (
    create_transfer,
    delete_transfer,
    get_transfer,
    list_transfers,
    update_transfer,
)
from app.modules.users.models import User

router = APIRouter(prefix="/transfers", tags=["转账"])


@router.get("", response_model=ApiResponse[PageData[TransferOut]])
def get_transfers(
    family_id: int,
    scope: str = "family",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    from_date: str | None = Query(None, alias="from"),
    to_date: str | None = Query(None, alias="to"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查询转账列表。TODO: scope=personal 时过滤当前成员。"""
    items, total = list_transfers(
        db,
        family_id,
        page=page,
        page_size=page_size,
        from_date=from_date,
        to_date=to_date,
    )
    return ok(data=PageData(items=items, page=page, page_size=page_size, total=total))


@router.post("", response_model=ApiResponse[TransferOut], status_code=201)
def post_transfer(
    payload: CreateTransferRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transfer = create_transfer(
        db,
        family_id=payload.family_id,
        from_account_id=payload.from_account_id,
        to_account_id=payload.to_account_id,
        recorder_user_id=current_user.id,
        amount=payload.amount,
        occurred_at=payload.occurred_at,
        remark=payload.remark,
    )
    return ok(data=transfer, message="转账创建成功")


@router.patch("/{transfer_id}", response_model=ApiResponse[TransferOut])
def patch_transfer(
    transfer_id: int,
    payload: UpdateTransferRequest,
    db: Session = Depends(get_db),
):
    transfer = update_transfer(
        db, transfer_id, **payload.model_dump(exclude_none=True)
    )
    return ok(data=transfer)


@router.delete("/{transfer_id}", status_code=204)
def delete_transfer_endpoint(
    transfer_id: int,
    db: Session = Depends(get_db),
):
    delete_transfer(db, transfer_id)