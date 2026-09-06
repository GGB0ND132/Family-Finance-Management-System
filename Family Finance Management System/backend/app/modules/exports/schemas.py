"""导出 Pydantic 模型。"""

from pydantic import BaseModel


class ExportRequest(BaseModel):
    family_id: int
    scope: str = "family"
    from_date: str | None = None
    to_date: str | None = None
    format: str = "csv"  # csv | xlsx