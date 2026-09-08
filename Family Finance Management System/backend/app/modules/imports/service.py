"""导入业务逻辑：预览、批次查询、确认（去重、余额、整体回滚）。

流程（`docs/详细设计.md` 第10节 + `docs/后端开发文档.md` 第7节）：
上传/映射 -> 预览 -> 确认。金额统一 `Decimal`，去重键固定为
“账户 + 分钟级发生时间 + 两位小数金额 + 去首尾空白备注”。
"""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.common.money import quantize_money
from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from app.modules.accounts.models import Account
from app.modules.accounts.repository import AccountRepository
from app.modules.categories.models import Category
from app.modules.families.repository import get_member_by_user
from app.modules.imports.models import ImportBatch
from app.modules.imports.parsers import parse_file
from app.modules.imports.repository import ImportBatchRepository
from app.modules.transactions.models import Transaction


def preview_import(
    db: Session,
    file_bytes: bytes,
    filename: str,
    family_id: int,
    account_id: int,
    uploader_user_id: int,
    field_mapping: dict | None = None,
) -> dict:
    """上传文件并生成预览批次。

    校验扩展名、必要列、日期、金额、方向和账户后，逐行标记
    VALID / INVALID / DUPLICATE，并持久化一个 PREVIEWED 批次。
    """
    _ensure_member(db, family_id, uploader_user_id)
    account = _ensure_account(db, family_id, account_id)

    mapping = field_mapping or {}
    raw_rows = parse_file(file_bytes, filename)
    if not raw_rows:
        raise BadRequestError("文件中没有可导入的数据行")

    existing_keys = _existing_dedup_keys(db, family_id, account_id)
    seen_keys: set[str] = set()

    rows: list[dict] = []
    valid = invalid = duplicate = 0
    for idx, raw in enumerate(raw_rows):
        row_number = idx + 2  # 表头占第 1 行
        data, errors = _normalize_row(db, family_id, account, raw, mapping)
        if errors and data is None:
            status = "INVALID"
            invalid += 1
        else:
            key = _dedup_key(
                account_id,
                datetime.fromisoformat(data["occurred_at"]),
                Decimal(data["amount"]),
                data["remark"],
            )
            if key in existing_keys or key in seen_keys:
                status = "DUPLICATE"
                duplicate += 1
                errors.append("与已有流水重复" if key in existing_keys else "批次内重复")
            else:
                status = "VALID"
                valid += 1
                seen_keys.add(key)
        rows.append(
            {
                "row_number": row_number,
                "validation_status": status,
                "normalized_data": data,
                "errors": errors,
            }
        )

    batch = ImportBatchRepository(db).create(
        ImportBatch(
            family_id=family_id,
            account_id=account_id,
            uploader_user_id=uploader_user_id,
            file_name=filename,
            file_type=_file_type(filename),
            field_mapping_json=mapping,
            status="PREVIEWED",
            total_rows=len(raw_rows),
            valid_rows=valid,
            invalid_rows=invalid,
            duplicate_rows=duplicate,
            rows=rows,
        )
    )
    db.commit()
    return _batch_out(batch)


def get_batch(db: Session, batch_id: int, user_id: int) -> dict:
    """获取导入批次详情。仅上传人或管理员可访问。"""
    batch = ImportBatchRepository(db).get_by_id(batch_id)
    if batch is None:
        raise NotFoundError("批次不存在")
    _ensure_access(db, batch, user_id)
    return _batch_out(batch)


def confirm_import(db: Session, batch_id: int, user_id: int) -> dict:
    """确认导入：有效行批量写入流水并更新余额，失败整体回滚。"""
    repo = ImportBatchRepository(db)
    batch = repo.get_by_id(batch_id)
    if batch is None:
        raise NotFoundError("批次不存在")
    _ensure_access(db, batch, user_id)
    if batch.status != "PREVIEWED":
        raise BadRequestError("该批次已处理")
    if batch.invalid_rows > 0:
        raise BadRequestError("批次包含无效行，请修正后重新上传导入", code=40020)

    account = _ensure_account(db, batch.family_id, batch.account_id)

    existing_keys = _existing_dedup_keys(db, batch.family_id, batch.account_id)
    seen_keys: set[str] = set()
    to_import: list[dict] = []

    for row in batch.rows or []:
        status = row.get("validation_status")
        if status == "INVALID":
            continue
        if status == "DUPLICATE":
            continue

        data = row.get("normalized_data") or {}
        errors = _validate_confirmed_row(db, batch.family_id, data)
        if errors:
            continue

        key = _dedup_key(
            batch.account_id,
            datetime.fromisoformat(data["occurred_at"]),
            Decimal(data["amount"]),
            data["remark"],
        )
        if key in existing_keys or key in seen_keys:
            continue  # 再次去重，重复行默认跳过
        seen_keys.add(key)
        to_import.append(data)

    if not to_import:
        raise BadRequestError("没有可导入的有效行", code=40020)

    try:
        imported = _write_transactions(db, batch, account, to_import)
    except Exception:
        db.rollback()
        _mark_failed(db, batch_id)
        raise

    batch.status = "CONFIRMED"
    batch.confirmed_at = datetime.now(timezone.utc)
    db.commit()
    return {"batch_id": batch.id, "status": "CONFIRMED", "imported_rows": imported}


# --------------------------------------------------------------------------
# 校验与访问控制
# --------------------------------------------------------------------------


def _ensure_member(db: Session, family_id: int, user_id: int) -> None:
    if get_member_by_user(db, family_id, user_id) is None:
        raise ForbiddenError("你不是该家庭的成员")


def _ensure_account(db: Session, family_id: int, account_id: int) -> Account:
    account = db.get(Account, account_id)
    if account is None:
        raise NotFoundError("账户不存在")
    if account.family_id != family_id:
        raise ForbiddenError("账户不属于当前家庭")
    if account.closed_at:
        raise ConflictError("已销户账户不能用于导入")
    return account


def _ensure_access(db: Session, batch: ImportBatch, user_id: int) -> None:
    if batch.uploader_user_id == user_id:
        return
    member = get_member_by_user(db, batch.family_id, user_id)
    if member is not None and member.role == "ADMIN":
        return
    raise ForbiddenError("无权访问该导入批次")


# --------------------------------------------------------------------------
# 字段映射与逐行标准化
# --------------------------------------------------------------------------


def _mapped_column(mapping: dict, *aliases: str) -> str | None:
    for alias in aliases:
        col = mapping.get(alias)
        if col:
            return col
    return None


def _cell(raw: dict, col: str | None):
    return None if col is None else raw.get(col)


def _normalize_row(
    db: Session,
    family_id: int,
    account: Account,
    raw: dict,
    mapping: dict,
) -> tuple[dict | None, list[str]]:
    """把一行原始数据标准化为流水字段，返回 (标准化数据, 错误列表)。"""
    errors: list[str] = []
    date_col = _mapped_column(mapping, "occurred_at", "date", "time")
    amount_col = _mapped_column(mapping, "amount")
    direction_col = _mapped_column(mapping, "direction", "type")
    category_col = _mapped_column(mapping, "category")
    remark_col = _mapped_column(mapping, "remark", "memo", "note")

    # 发生时间
    occurred_at = None
    time_defaulted = False
    raw_date = _cell(raw, date_col)
    if raw_date is not None and str(raw_date).strip() != "":
        occurred_at, time_defaulted = _parse_datetime(str(raw_date))
    if occurred_at is None:
        errors.append("日期格式无法识别" if raw_date else "缺少日期")

    # 金额
    amount = None
    raw_amount = _cell(raw, amount_col)
    if raw_amount is None or str(raw_amount).strip() == "":
        errors.append("缺少金额")
    else:
        amount = _parse_amount(str(raw_amount))
        if amount is None:
            errors.append("金额格式非法")
        elif amount == 0:
            errors.append("金额必须大于 0")

    # 收支方向
    type_ = None
    raw_direction = _cell(raw, direction_col)
    if raw_direction is not None and str(raw_direction).strip() != "":
        type_ = _parse_direction(str(raw_direction))
        if type_ is None:
            errors.append("收支方向无法识别")
    if type_ is None and amount is not None:
        type_ = "EXPENSE" if amount < 0 else "INCOME"
    if amount is not None:
        amount = abs(amount)

    # 分类（按名称匹配当前家庭同方向现用分类）
    category_id = None
    raw_category = _cell(raw, category_col)
    if raw_category is None or str(raw_category).strip() == "":
        errors.append("缺少分类")
    else:
        category = _resolve_category(db, family_id, str(raw_category), type_)
        if category is None:
            errors.append("分类不存在或方向不匹配")
        else:
            category_id = category.id

    # 备注（去首尾空白）
    remark = ""
    raw_remark = _cell(raw, remark_col)
    if raw_remark is not None and str(raw_remark).strip() != "":
        remark = str(raw_remark).strip()

    if errors:
        return None, errors

    return (
        {
            "occurred_at": occurred_at.isoformat(),
            "type": type_,
            "amount": str(quantize_money(amount)),
            "category_id": category_id,
            "remark": remark,
            "beneficiary_member_id": account.owner_member_id,
            "time_defaulted": time_defaulted,
        },
        [],
    )


def _validate_confirmed_row(db: Session, family_id: int, data: dict) -> list[str]:
    """确认前再次校验分类与资金归属人仍然有效。"""
    errors: list[str] = []
    category = db.get(Category, data.get("category_id"))
    if category is None or category.deleted_at is not None:
        errors.append("分类不存在或已删除")
    elif category.family_id != family_id or category.type != data.get("type"):
        errors.append("分类方向不匹配")

    from app.modules.families.models import FamilyMember

    member = db.get(FamilyMember, data.get("beneficiary_member_id"))
    if member is None or member.family_id != family_id:
        errors.append("资金归属人无效")
    return errors


# --------------------------------------------------------------------------
# 去重
# --------------------------------------------------------------------------


def _dedup_key(account_id: int, occurred_at, amount, remark: str) -> str:
    dt = occurred_at.replace(tzinfo=None) if occurred_at.tzinfo else occurred_at
    minute = dt.replace(second=0, microsecond=0)
    return f"{account_id}|{minute.isoformat()}|{quantize_money(amount)}|{remark.strip()}"


def _existing_dedup_keys(db: Session, family_id: int, account_id: int) -> set[str]:
    txs = (
        db.query(Transaction)
        .filter(Transaction.family_id == family_id, Transaction.account_id == account_id)
        .all()
    )
    return {
        _dedup_key(t.account_id, t.occurred_at, t.amount, t.remark or "") for t in txs
    }


# --------------------------------------------------------------------------
# 写入与回滚
# --------------------------------------------------------------------------


def _write_transactions(db: Session, batch: ImportBatch, account: Account, to_import: list[dict]) -> int:
    locked_account = AccountRepository(db).get_by_id_for_update(batch.account_id)
    if locked_account is None:
        raise NotFoundError("账户不存在")
    if locked_account.closed_at:
        raise ConflictError("已销户账户不能产生流水")

    imported = 0
    for data in to_import:
        amount = quantize_money(Decimal(data["amount"]))
        occurred_at = datetime.fromisoformat(data["occurred_at"])
        tx = Transaction(
            family_id=batch.family_id,
            account_id=batch.account_id,
            category_id=data["category_id"],
            beneficiary_member_id=data["beneficiary_member_id"],
            recorder_user_id=batch.uploader_user_id,
            type=data["type"],
            amount=amount,
            occurred_at=occurred_at,
            remark=data.get("remark") or None,
        )
        db.add(tx)
        if data["type"] == "INCOME":
            locked_account.current_balance += amount
        else:
            locked_account.current_balance -= amount
        imported += 1
    db.flush()
    return imported


def _mark_failed(db: Session, batch_id: int) -> None:
    batch = db.get(ImportBatch, batch_id)
    if batch is not None:
        batch.status = "FAILED"
        db.commit()


# --------------------------------------------------------------------------
# 解析与输出
# --------------------------------------------------------------------------


def _file_type(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return "XLSX" if ext in ("xls", "xlsx") else "CSV"


def _parse_datetime(value: str) -> tuple[datetime | None, bool]:
    s = value.strip()
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y%m%d",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(s, fmt)
            time_defaulted = fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d")
            if time_defaulted:
                dt = dt.replace(hour=0, minute=0, second=0)
            return dt, time_defaulted
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(s), False
    except ValueError:
        return None, False


def _parse_amount(value: str) -> Decimal | None:
    s = value.strip()
    if not s:
        return None
    negative = s.startswith("-") or s.endswith("-") or (s.startswith("(") and s.endswith(")"))
    for ch in (",", "，", "¥", "￥", "$", "元", " ", "-", "(", ")", "+"):
        s = s.replace(ch, "")
    if not s:
        return None
    try:
        amount = Decimal(s)
    except Exception:
        return None
    return -amount if negative else amount


def _parse_direction(value: str) -> str | None:
    s = value.strip().lower()
    if s in {"收入", "收", "income", "入账", "存入", "退款"}:
        return "INCOME"
    if s in {"支出", "支", "expense", "出账", "取出", "消费"}:
        return "EXPENSE"
    if "收入" in s:
        return "INCOME"
    if "支出" in s:
        return "EXPENSE"
    return None


def _resolve_category(db: Session, family_id: int, name: str, type_: str | None):
    if type_ is None:
        return None
    return (
        db.query(Category)
        .filter(
            Category.family_id == family_id,
            Category.name == name,
            Category.type == type_,
            Category.deleted_at.is_(None),
        )
        .first()
    )


def _batch_out(batch: ImportBatch) -> dict:
    return {
        "batch_id": batch.id,
        "family_id": batch.family_id,
        "account_id": batch.account_id,
        "file_name": batch.file_name,
        "file_type": batch.file_type,
        "status": batch.status,
        "total_rows": batch.total_rows,
        "valid_rows": batch.valid_rows,
        "invalid_rows": batch.invalid_rows,
        "duplicate_rows": batch.duplicate_rows,
        "rows": batch.rows or [],
    }