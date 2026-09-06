"""导入 Pydantic 模型。"""

from pydantic import BaseModel


class PreviewRow(BaseModel):
    row_number: int
    validation_status: str  # VALID / INVALID / DUPLICATE
    normalized_data: dict | None = None
    errors: list[str] = []


class ImportBatchOut(BaseModel):
    batch_id: int
    status: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    duplicate_rows: int
    rows: list[PreviewRow] = []

    model_config = {"from_attributes": True}