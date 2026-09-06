"""导入路由。"""

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.common.response import ApiResponse, ok
from app.core.deps import get_current_user, get_db
from app.core.settings import settings
from app.modules.imports.service import confirm_import, get_batch, preview_import
from app.modules.users.models import User

router = APIRouter(prefix="/imports", tags=["导入"])


@router.post("/preview", response_model=ApiResponse)
async def preview(
    file: UploadFile = File(...),
    family_id: int = Form(...),
    account_id: int = Form(...),
    scope: str = Form("personal"),
    field_mapping_json: str = Form("{}"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """上传文件并返回预览。"""
    import json

    # 校验文件大小
    contents = await file.read()
    if len(contents) > settings.IMPORT_MAX_FILE_SIZE:
        from app.core.exceptions import ValidationError
        raise ValidationError(f"文件大小不能超过 {settings.IMPORT_MAX_FILE_SIZE // 1024 // 1024}MB")

    field_mapping = json.loads(field_mapping_json)

    result = preview_import(
        db,
        contents,
        file.filename or "unnamed",
        family_id,
        account_id,
        current_user.id,
        field_mapping,
    )
    return ok(data=result)


@router.get("/{batch_id}", response_model=ApiResponse)
def get_import_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取导入批次详情。仅上传人或管理员可访问。"""
    result = get_batch(db, batch_id)
    if not result:
        from app.core.exceptions import ResourceNotFoundError
        raise ResourceNotFoundError("批次不存在")
    return ok(data=result)


@router.post("/{batch_id}/confirm", response_model=ApiResponse)
def confirm(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """确认导入，写入流水并更新余额。"""
    result = confirm_import(db, batch_id, current_user.id)
    return ok(data=result, message="导入成功")