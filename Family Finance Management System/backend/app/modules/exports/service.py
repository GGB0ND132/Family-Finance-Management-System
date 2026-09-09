"""导出业务逻辑：CSV (UTF-8 BOM) / XLSX 流式输出。"""

import csv
from datetime import datetime, timezone
from io import BytesIO, StringIO
from decimal import Decimal

from sqlalchemy.orm import Session, aliased

from app.core.exceptions import BadRequestError, ForbiddenError
from app.modules.accounts.models import Account
from app.modules.categories.models import Category
from app.modules.families.models import FamilyMember
from app.modules.families.repository import get_member_by_user
from app.modules.transactions.models import Transaction
from app.modules.users.models import User


def export_transactions_csv(
    db: Session,
    family_id: int,
    *,
    scope: str = "family",
    from_date: str | None = None,
    to_date: str | None = None,
    user_id: int | None = None,
    type_: str | None = None,
    account_id: int | None = None,
) -> BytesIO:
    """生成 CSV 字节流（UTF-8 BOM）。

    返回 UTF-8 BOM 编码的 CSV，查询始终按家庭及用户权限过滤。
    """
    rows = _query_transactions(db, family_id, scope, from_date, to_date, user_id, type_, account_id)
    text = StringIO()
    writer = csv.writer(text, lineterminator="\n")
    writer.writerow(_HEADERS)
    for row in rows:
        writer.writerow(_row_values(row))
    return BytesIO(("\ufeff" + text.getvalue()).encode("utf-8"))


def export_transactions_xlsx(
    db: Session,
    family_id: int,
    *,
    scope: str = "family",
    from_date: str | None = None,
    to_date: str | None = None,
    user_id: int | None = None,
    type_: str | None = None,
    account_id: int | None = None,
) -> BytesIO:
    """生成 XLSX 字节流。"""
    rows = _query_transactions(db, family_id, scope, from_date, to_date, user_id, type_, account_id)
    try:
        from openpyxl import Workbook
    except ImportError as exc:  # pragma: no cover
        raise BadRequestError("服务端未安装 openpyxl，无法导出 XLSX") from exc
    wb = Workbook(write_only=True)
    ws = wb.create_sheet("流水")
    ws.append(_HEADERS)
    for row in rows:
        ws.append(_row_values(row))
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output


_HEADERS = ["发生时间", "类型", "金额", "账户", "账户所属人", "分类", "资金归属人", "录入人", "备注", "创建时间"]


def _parse_bound(value: str | None, *, end: bool = False) -> datetime | None:
    if not value:
        return None
    try:
        if len(value) == 10:
            dt = datetime.fromisoformat(value)
            if end:
                dt = dt.replace(hour=23, minute=59, second=59)
        else:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise BadRequestError("日期筛选格式非法") from exc
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _query_transactions(db: Session, family_id: int, scope: str, from_date: str | None, to_date: str | None, user_id: int | None, type_: str | None = None, account_id: int | None = None):
    if scope not in {"personal", "family"}:
        raise BadRequestError("scope 仅支持 personal 或 family")
    member = get_member_by_user(db, family_id, user_id) if user_id is not None else None
    if user_id is not None and member is None:
        raise ForbiddenError("你不是该家庭的成员")
    owner_member = aliased(FamilyMember)
    beneficiary_member = aliased(FamilyMember)
    recorder_user = aliased(User)
    owner_user = aliased(User)
    beneficiary_user = aliased(User)
    q = db.query(Transaction, Account, Category, beneficiary_member, recorder_user, owner_member, owner_user, beneficiary_user).join(Account, Account.id == Transaction.account_id).join(Category, Category.id == Transaction.category_id).join(beneficiary_member, beneficiary_member.id == Transaction.beneficiary_member_id).join(recorder_user, recorder_user.id == Transaction.recorder_user_id).join(owner_member, owner_member.id == Account.owner_member_id).join(owner_user, owner_user.id == owner_member.user_id).join(beneficiary_user, beneficiary_user.id == beneficiary_member.user_id).filter(Transaction.family_id == family_id)
    if scope == "personal" and member is not None:
        q = q.filter(Transaction.beneficiary_member_id == member.id)
    if type_:
        if type_ not in {"INCOME", "EXPENSE"}:
            raise BadRequestError("type 仅支持 INCOME 或 EXPENSE")
        q = q.filter(Transaction.type == type_)
    if account_id:
        q = q.filter(Transaction.account_id == account_id)
    start, end = _parse_bound(from_date), _parse_bound(to_date, end=True)
    if start: q = q.filter(Transaction.occurred_at >= start)
    if end: q = q.filter(Transaction.occurred_at <= end)
    return q.order_by(Transaction.occurred_at.desc(), Transaction.id.desc()).all()


def _row_values(row):
    tx, account, category, beneficiary, recorder, owner_member, owner_user, beneficiary_user = row
    return [
        tx.occurred_at.isoformat(),
        "收入" if tx.type == "INCOME" else "支出",
        f"{Decimal(tx.amount):.2f}",
        account.name,
        owner_user.nickname or owner_user.username,
        category.name,
        beneficiary_user.nickname or beneficiary_user.username,
        recorder.nickname or recorder.username,
        tx.remark or "",
        tx.created_at.isoformat() if tx.created_at else "",
    ]
