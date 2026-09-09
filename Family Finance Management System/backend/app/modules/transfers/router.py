"""转账路由。"""

from fastapi import APIRouter, Query

from app.common.response import ok
from app.core.deps import CurrentUser, DbSession
from app.modules.transfers.schemas import (
    CreateTransferRequest,
    UpdateTransferRequest,
)
from app.modules.transfers.service import (
    _build_out,
    create_transfer,
    delete_transfer,
    get_transfer,
    list_transfers,
    parse_occurred_at,
    update_transfer,
    confirm_transfer,
)

router = APIRouter(prefix="/transfers", tags=["转账"])


@router.get("", summary="分页查询转账")
def api_list_transfers(
    db: DbSession,
    user: CurrentUser,
    family_id: int = Query(..., description="家庭 ID"),
    scope: str = Query("family", description="personal | family"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    from_member_id: int | None = Query(None, description="转出方成员"),
    to_member_id: int | None = Query(None, description="转入方成员"),
    from_account_id: int | None = Query(None, description="转出账户"),
    to_account_id: int | None = Query(None, description="转入账户"),
    from_: str | None = Query(None, alias="from", description="开始时间"),
    to_: str | None = Query(None, alias="to", description="结束时间"),
):
    from_dt = parse_occurred_at(from_) if from_ else None
    to_dt = parse_occurred_at(to_) if to_ else None

    items, total = list_transfers(
        db,
        user,
        family_id,
        scope=scope,
        page=page,
        page_size=page_size,
        from_dt=from_dt,
        to_dt=to_dt,
        from_member_id=from_member_id,
        to_member_id=to_member_id,
        from_account_id=from_account_id,
        to_account_id=to_account_id,
    )
    return ok(
        data={
            "items": [_build_out(db, t) for t in items],
            "page": page,
            "page_size": page_size,
            "total": total,
        }
    )


@router.post("", summary="创建转账", status_code=201)
def api_create_transfer(payload: CreateTransferRequest, db: DbSession, user: CurrentUser):
    transfer = create_transfer(
        db,
        user,
        family_id=payload.family_id,
        from_account_id=payload.from_account_id,
        to_account_id=payload.to_account_id,
        amount=payload.amount,
        occurred_at=payload.occurred_at,
        remark=payload.remark,
    )
    return ok(data=_build_out(db, transfer), message="转账创建成功")


@router.get("/{transfer_id}", summary="查询转账详情")
def api_get_transfer(transfer_id: int, db: DbSession, user: CurrentUser):
    transfer = get_transfer(db, user, transfer_id)
    return ok(data=_build_out(db, transfer))


@router.patch("/{transfer_id}", summary="编辑转账")
def api_update_transfer(
    transfer_id: int,
    payload: UpdateTransferRequest,
    db: DbSession,
    user: CurrentUser,
):
    transfer = update_transfer(db, user, transfer_id, **payload.model_dump(exclude_none=True))
    return ok(data=_build_out(db, transfer))


@router.delete("/{transfer_id}", summary="删除转账", status_code=204)
def api_delete_transfer(transfer_id: int, db: DbSession, user: CurrentUser):
    delete_transfer(db, user, transfer_id)


@router.post("/{transfer_id}/confirm", summary="转入方确认转账")
def api_confirm_transfer(transfer_id: int, db: DbSession, user: CurrentUser):
    return ok(data=_build_out(db, confirm_transfer(db, user, transfer_id)), message="转账已确认")
