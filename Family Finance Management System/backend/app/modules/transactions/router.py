"""收支流水路由。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.response import ApiResponse, PageData, ok
from app.core.deps import get_current_user, get_db
from app.modules.transactions.schemas import (
    CreateTransactionRequest,
    TransactionOut,
    UpdateTransactionRequest,
)
from app.modules.transactions.service import (
    create_transaction,
    delete_transaction,
    get_transaction,
    list_transactions,
    update_transaction,
)
from app.modules.users.models import User

router = APIRouter(prefix="/transactions", tags=["流水"])


@router.get("", response_model=ApiResponse[PageData[TransactionOut]])
def get_transactions(
    family_id: int,
    scope: str = "family",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type: str | None = None,
    account_id: int | None = None,
    category_id: int | None = None,
    beneficiary_member_id: int | None = None,
    from_date: str | None = Query(None, alias="from"),
    to_date: str | None = Query(None, alias="to"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """分页查询流水。TODO: scope=personal 时过滤受益人。"""
    items, total = list_transactions(
        db,
        family_id,
        page=page,
        page_size=page_size,
        type_=type,
        account_id=account_id,
        category_id=category_id,
        beneficiary_member_id=beneficiary_member_id,
        from_date=from_date,
        to_date=to_date,
    )
    return ok(data=PageData(items=items, page=page, page_size=page_size, total=total))


@router.post("", response_model=ApiResponse[TransactionOut], status_code=201)
def post_transaction(
    payload: CreateTransactionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建流水。recorder_user_id 由后端从 JWT 写入。"""
    tx = create_transaction(
        db,
        family_id=payload.family_id,
        account_id=payload.account_id,
        category_id=payload.category_id,
        beneficiary_member_id=payload.beneficiary_member_id,
        recorder_user_id=current_user.id,
        type_=payload.type,
        amount=payload.amount,
        occurred_at=payload.occurred_at,
        remark=payload.remark,
    )
    return ok(data=tx, message="流水创建成功")


@router.get("/{tx_id}", response_model=ApiResponse[TransactionOut])
def get_transaction_detail(
    tx_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tx = get_transaction(db, tx_id)
    # TODO: 校验家庭和权限
    return ok(data=tx)


@router.patch("/{tx_id}", response_model=ApiResponse[TransactionOut])
def patch_transaction(
    tx_id: int,
    payload: UpdateTransactionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tx = update_transaction(db, tx_id, **payload.model_dump(exclude_none=True))
    return ok(data=tx)


@router.delete("/{tx_id}", status_code=204)
def delete_transaction_endpoint(
    tx_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    delete_transaction(db, tx_id)