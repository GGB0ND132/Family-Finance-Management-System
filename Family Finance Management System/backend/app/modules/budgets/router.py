"""预算路由（`docs/详细设计.md` 第 9 节）。"""

from typing import Literal

from fastapi import APIRouter

from app.common.response import ok
from app.core.deps import CurrentUser, DbSession, require_family_admin, require_family_member
from app.modules.budgets.schemas import CopyBudgetRequest, PutBudgetRequest
from app.modules.budgets.service import copy_from_previous, get_budget, put_budget

router = APIRouter(prefix="/budgets", tags=["预算"])


@router.get("/{month}", summary="查询对应范围预算和执行情况")
def get_budget_endpoint(
    month: str,
    family_id: int,
    user: CurrentUser,
    db: DbSession,
    scope: Literal["personal", "family"] = "family",
):
    """个人预算返回当前成员预算，家庭预算返回家庭全部预算。"""
    member = require_family_member(db, user, family_id)
    member_id = member.id if scope == "personal" else None
    result = get_budget(db, family_id, month, scope, member_id)
    return ok(result)


@router.put("/{month}", summary="保存对应范围总预算与分类预算")
def put_budget_endpoint(
    month: str,
    payload: PutBudgetRequest,
    user: CurrentUser,
    db: DbSession,
):
    """个人预算仅本人可保存，家庭预算仅管理员可保存。"""
    if payload.scope == "personal":
        member = require_family_member(db, user, payload.family_id)
        member_id = member.id
    else:
        require_family_admin(db, user, payload.family_id)
        member_id = None

    result = put_budget(
        db,
        family_id=payload.family_id,
        month=month,
        scope=payload.scope,
        member_id=member_id,
        total_amount=payload.total_amount,
        categories=[c.model_dump() for c in payload.categories],
    )
    return ok(result, message="预算已保存")


@router.post("/{month}/copy-from-previous", summary="复制同范围上月预算")
def copy_budget_endpoint(
    month: str,
    payload: CopyBudgetRequest,
    user: CurrentUser,
    db: DbSession,
):
    """个人预算仅本人可复制，家庭预算仅管理员可复制。"""
    if payload.scope == "personal":
        member = require_family_member(db, user, payload.family_id)
        member_id = member.id
    else:
        require_family_admin(db, user, payload.family_id)
        member_id = None

    result = copy_from_previous(
        db,
        family_id=payload.family_id,
        month=month,
        scope=payload.scope,
        member_id=member_id,
    )
    if result is None:
        empty = get_budget(db, payload.family_id, month, payload.scope, member_id)
        return ok(empty, message="无上月预算可复制")
    return ok(result, message="复制成功")