"""导入路由。"""

import json

from fastapi import APIRouter, File, Form, UploadFile

from app.common.response import ok
from app.core.deps import CurrentUser, DbSession
from app.core.exceptions import BadRequestError
from app.core.settings import get_settings
from app.modules.imports.service import confirm_import, get_batch, preview_import

router = APIRouter(prefix="/imports", tags=["导入"])


@router.post("/preview", summary="上传文件并返回预览批次")
async def preview(
    user: CurrentUser,
    db: DbSession,
    file: UploadFile = File(...),
    family_id: int = Form(...),
    account_id: int = Form(...),
    scope: str = Form("personal"),
    field_mapping_json: str = Form("{}"),
):
    """上传 CSV/XLSX，校验文件并返回预览批次（VALID/INVALID/DUPLICATE）。"""
    contents = await file.read()
    max_size = get_settings().IMPORT_MAX_FILE_SIZE
    if len(contents) > max_size:
        raise BadRequestError(f"文件大小不能超过 {max_size // 1024 // 1024}MB")

    try:
        field_mapping = json.loads(field_mapping_json or "{}")
    except ValueError as exc:
        raise BadRequestError("字段映射格式非法") from exc

    result = preview_import(
        db,
        contents,
        file.filename or "unnamed",
        family_id,
        account_id,
        user.id,
        field_mapping,
        scope=scope,
    )
    return ok(data=result)


@router.get("/{batch_id}", summary="获取导入批次详情")
def get_import_batch(batch_id: int, user: CurrentUser, db: DbSession):
    """获取导入批次详情。仅上传人或管理员可访问。"""
    return ok(data=get_batch(db, batch_id, user.id))


@router.post("/{batch_id}/confirm", summary="确认导入")
def confirm(batch_id: int, user: CurrentUser, db: DbSession):
    """确认导入，有效行写入流水并更新余额（整体事务，失败回滚）。"""
    result = confirm_import(db, batch_id, user.id)
    return ok(data=result, message="导入成功")
