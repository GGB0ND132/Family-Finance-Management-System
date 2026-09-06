"""预算路由。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.response import ApiResponse, ok
from app.core.deps import get_current_user, get_db
from app.modules.budgets.schemas import (
    BudgetOut,
    CopyBudgetRequest,
    PutBudgetRequest,
)
from app.modules.budgets.service import (
    copy_from_previous,
    get_budget,
    put_budget,
)
from app.modules.users.models import User

router = APIRouter(prefix="/budgets", tags=["预算"])


@router.get("/{month}", response_model=ApiResponse[BudgetOut])
def get_budget_endpoint(
    month: str,
    family_id: int,
    scope: str = "family",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取月度预算。TODO: 接入家庭成员权限依赖。"""
    # TODO: 个人预算获取当前成员的 member_id
    result = get_budget(db, family_id, month, scope)
    if not result:
        return ok(
            data={
                "id": 0,
                "family_id": family_id,
                "month": month,
                "scope": scope,
                "total_amount": "0.00",
                "used_amount": "0.00",
                "remaining_amount": "0.00",
                "usage_rate": "0.00",
                "warning_level": "NORMAL",
                "categories": [],
            }
        )
    return ok(data=result)


@router.put("/{month}", response_model=ApiResponse[BudgetOut])
def put_budget_endpoint(
    month: str,
    payload: PutBudgetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """保存/更新预算。TODO: 个人预算仅本人；家庭预算仅管理员。"""
    # TODO: 获取当前成员 ID
    budget = put_budget(
        db,
        family_id=payload.family_id,
        month=month,
        scope=payload.scope,
        member_id=current_user.id,  # TODO: 应使用 member_id
        total_amount=payload.total_amount,
        categories=[c.model_dump() for c in payload.categories],
    )
    usage = get_budget(db, payload.family_id, month, payload.scope)
    return ok(data=usage)


@router.post("/{month}/copy-from-previous", response_model=ApiResponse[BudgetOut], status_code=201)
def copy_budget(
    month: str,
    payload: CopyBudgetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """从上月复制预算。"""
    budget = copy_from_previous(
        db,
        family_id=payload.family_id,
        month=month,
        scope=payload.scope,
    )
    if not budget:
        return ok(
            data={
                "id": 0,
                "family_id": payload.family_id,
                "month": month,
                "scope": payload.scope,
                "total_amount": "0.00",
                "used_amount": "0.00",
                "remaining_amount": "0.00",
                "usage_rate": "0.00",
                "warning_level": "NORMAL",
                "categories": [],
            },
            message="无上月预算可复制",
        )
    usage = get_budget(db, payload.family_id, month, payload.scope)
    return ok(data=usage, message="复制成功")