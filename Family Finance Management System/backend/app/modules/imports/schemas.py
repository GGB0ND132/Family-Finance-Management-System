"""导入 Pydantic 模型。"""

from pydantic import BaseModel, ConfigDict


class PreviewRow(BaseModel):
    """预览行。normalized_data 存储标准化后的字段（金额以字符串表示）。"""

    row_number: int
    validation_status: str  # VALID / INVALID / DUPLICATE / SKIPPED
    normalized_data: dict | None = None
    errors: list[str] = []


class ImportBatchOut(BaseModel):
    """导入批次输出。"""

    model_config = ConfigDict(from_attributes=True)

    batch_id: int
    family_id: int
    account_id: int
    file_name: str | None = None
    file_type: str | None = None
    status: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    duplicate_rows: int
    rows: list[PreviewRow] = []


class ConfirmImportOut(BaseModel):
    """确认导入结果。"""

    batch_id: int
    status: str
    imported_rows: int


class ImportRowUpdate(BaseModel):
    row_number: int
    normalized_data: dict


class ImportRowsUpdate(BaseModel):
    rows: list[ImportRowUpdate]
