"""导入业务逻辑：预览、确认、去重、整体回滚。"""

from sqlalchemy.orm import Session


def preview_import(
    db: Session,
    file_bytes: bytes,
    filename: str,
    family_id: int,
    account_id: int,
    uploader_user_id: int,
    field_mapping: dict | None = None,
) -> dict:
    """上传文件并生成预览。"""
    # TODO: 校验扩展名、MIME、大小、必要列
    # TODO: 解析文件 -> 字段映射 -> 逐行校验 -> 去重检查
    # TODO: 创建 ImportBatch 写入数据库，标记 PREVIEWED
    return {
        "batch_id": 0,
        "status": "PREVIEWED",
        "total_rows": 0,
        "valid_rows": 0,
        "invalid_rows": 0,
        "duplicate_rows": 0,
        "rows": [],
    }


def get_batch(db: Session, batch_id: int) -> dict | None:
    """获取导入批次详情。"""
    # TODO: 从 import_batches 表读取
    return None


def confirm_import(db: Session, batch_id: int, user_id: int) -> dict:
    """确认导入：批量写入流水并更新余额，失败则整体回滚。"""
    # TODO: 校验家庭、账户、分类、成员和销户状态
    # TODO: 有效行批量写入 transactions 并逐行更新余额
    # TODO: 任何一行失败则整体回滚，批次标记 FAILED
    return {"status": "CONFIRMED"}