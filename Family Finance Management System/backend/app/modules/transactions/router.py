"""收支流水路由。"""

from fastapi import APIRouter, Query

from app.common.money import to_decimal
from app.common.response import ok
from app.core.deps import CurrentUser, DbSession
from app.modules.transactions.schemas import (
    CreateTransactionRequest,
    UpdateTransactionRequest,
)
from app.modules.transactions.service import (
    _build_out,
    create_transaction,
    delete_transaction,
    get_transaction,
    list_transactions,
    parse_occurred_at,
    update_transaction,
)

router = APIRouter(prefix="/transactions", tags=["流水"])


@router.get("", summary="分页查询流水")
def api_list_transactions(
    db: DbSession,
    user: CurrentUser,
    family_id: int = Query(..., description="家庭 ID"),
    scope: str = Query("family", description="personal | family"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type: str | None = Query(None, description="INCOME | EXPENSE"),
    account_id: int | None = Query(None),
    category_id: int | None = Query(None),
    beneficiary_member_id: int | None = Query(None),
    owner_member_id: int | None = Query(None),
    recorder_user_id: int | None = Query(None),
    from_: str | None = Query(None, alias="from"),
    to_: str | None = Query(None, alias="to"),
    min_amount: str | None = Query(None),
    max_amount: str | None = Query(None),
):
    from_dt = parse_occurred_at(from_) if from_ else None
    to_dt = parse_occurred_at(to_) if to_ else None
    min_amt = to_decimal(min_amount) if min_amount is not None else None
    max_amt = to_decimal(max_amount) if max_amount is not None else None

    items, total = list_transactions(
        db,
        user,
        family_id,
        scope=scope,
        page=page,
        page_size=page_size,
        type_=type,
        account_id=account_id,
        category_id=category_id,
        beneficiary_member_id=beneficiary_member_id,
        owner_member_id=owner_member_id,
        recorder_user_id=recorder_user_id,
        from_dt=from_dt,
        to_dt=to_dt,
        min_amount=min_amt,
        max_amount=max_amt,
    )
    return ok(
        data={
            "items": [_build_out(db, t) for t in items],
            "page": page,
            "page_size": page_size,
            "total": total,
        }
    )


@router.post("", summary="创建收入或支出流水", status_code=201)
def api_create_transaction(
    payload: CreateTransactionRequest,
    db: DbSession,
    user: CurrentUser,
):
    tx = create_transaction(
        db,
        user,
        family_id=payload.family_id,
        account_id=payload.account_id,
        category_id=payload.category_id,
        beneficiary_member_id=payload.beneficiary_member_id,
        type_=payload.type,
        amount=payload.amount,
        occurred_at=payload.occurred_at,
        remark=payload.remark,
    )
    return ok(data=_build_out(db, tx), message="流水创建成功")


@router.get("/{tx_id}", summary="查询流水详情")
def api_get_transaction(tx_id: int, db: DbSession, user: CurrentUser):
    tx = get_transaction(db, user, tx_id)
    return ok(data=_build_out(db, tx))


@router.patch("/{tx_id}", summary="编辑流水")
def api_update_transaction(
    tx_id: int,
    payload: UpdateTransactionRequest,
    db: DbSession,
    user: CurrentUser,
):
    tx = update_transaction(db, user, tx_id, **payload.model_dump(exclude_none=True))
    return ok(data=_build_out(db, tx))


@router.delete("/{tx_id}", summary="删除流水", status_code=204)
def api_delete_transaction(tx_id: int, db: DbSession, user: CurrentUser):
    delete_transaction(db, user, tx_id)