"""导出路由。"""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.modules.exports.service import export_transactions_csv, export_transactions_xlsx
from app.modules.users.models import User

router = APIRouter(prefix="/exports", tags=["导出"])


@router.get("/transactions")
def export_transactions(
    family_id: int,
    scope: str = Query("family", pattern="^(personal|family)$"),
    from_date: str | None = Query(None, alias="from"),
    to_date: str | None = Query(None, alias="to"),
    format: str = Query("csv", pattern="^(csv|xlsx)$"),
    type: str | None = Query(None, pattern="^(INCOME|EXPENSE)$"),
    account_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """导出流水为 CSV 或 XLSX，并按当前用户的家庭权限过滤。"""
    if format == "csv":
        output = export_transactions_csv(
            db, family_id, scope=scope, from_date=from_date, to_date=to_date, user_id=current_user.id, type_=type, account_id=account_id
        )
        filename = f"transactions-export.csv"
        return StreamingResponse(
            output,
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{filename}"
            },
        )
    else:
        output = export_transactions_xlsx(
            db, family_id, scope=scope, from_date=from_date, to_date=to_date, user_id=current_user.id, type_=type, account_id=account_id
        )
        filename = f"transactions-export.xlsx"
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{filename}"
            },
        )
