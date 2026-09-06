"""报表路由。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.response import ApiResponse, ok
from app.core.deps import get_current_user, get_db
from app.modules.reports.service import (
    get_family_by_category,
    get_family_by_member,
    get_family_summary,
    get_family_trend,
    get_personal_by_category,
    get_personal_daily,
    get_personal_summary,
    get_personal_trend,
)
from app.modules.users.models import User

router = APIRouter(prefix="/reports", tags=["报表"])


# --- 个人报表 ---

@router.get("/personal/daily", response_model=ApiResponse)
def personal_daily(
    family_id: int,
    date: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """个人日报。TODO: 获取当前成员 ID 作为 beneficiary_member_id。"""
    # TODO: 从家庭成员关系获取 beneficiary_member_id
    result = get_personal_daily(db, family_id, current_user.id, date)
    return ok(data=result)


@router.get("/personal/summary", response_model=ApiResponse)
def personal_summary(
    family_id: int,
    from_date: str,
    to_date: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = get_personal_summary(db, family_id, current_user.id, from_date, to_date)
    return ok(data=result)


@router.get("/personal/trend", response_model=ApiResponse)
def personal_trend(
    family_id: int,
    from_month: str,
    to_month: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = get_personal_trend(db, family_id, current_user.id, from_month, to_month)
    return ok(data=result)


@router.get("/personal/by-category", response_model=ApiResponse)
def personal_by_category(
    family_id: int,
    month: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = get_personal_by_category(db, family_id, current_user.id, month)
    return ok(data=result)


# --- 家庭报表 ---

@router.get("/family/summary", response_model=ApiResponse)
def family_summary(
    family_id: int,
    month: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = get_family_summary(db, family_id, month)
    return ok(data=result)


@router.get("/family/trend", response_model=ApiResponse)
def family_trend(
    family_id: int,
    from_month: str,
    to_month: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = get_family_trend(db, family_id, from_month, to_month)
    return ok(data=result)


@router.get("/family/by-category", response_model=ApiResponse)
def family_by_category(
    family_id: int,
    month: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = get_family_by_category(db, family_id, month)
    return ok(data=result)


@router.get("/family/by-member", response_model=ApiResponse)
def family_by_member(
    family_id: int,
    month: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = get_family_by_member(db, family_id, month)
    return ok(data=result)