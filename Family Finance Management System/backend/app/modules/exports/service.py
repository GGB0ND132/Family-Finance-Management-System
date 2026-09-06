"""导出业务逻辑：CSV (UTF-8 BOM) / XLSX 流式输出。"""

from io import BytesIO

from sqlalchemy.orm import Session


def export_transactions_csv(
    db: Session,
    family_id: int,
    *,
    scope: str = "family",
    from_date: str | None = None,
    to_date: str | None = None,
) -> BytesIO:
    """生成 CSV 字节流（UTF-8 BOM）。

    TODO: 实现筛选查询和 CSV 写入。
    """
    output = BytesIO()
    output.write("\ufeff".encode("utf-8"))  # UTF-8 BOM
    # TODO: 写入 CSV 头和数据行
    output.seek(0)
    return output


def export_transactions_xlsx(
    db: Session,
    family_id: int,
    *,
    scope: str = "family",
    from_date: str | None = None,
    to_date: str | None = None,
) -> BytesIO:
    """生成 XLSX 字节流。

    TODO: 实现 openpyxl 写入，使用 StreamingResponse。
    """
    # TODO: import openpyxl; workbook -> BytesIO
    output = BytesIO()
    output.seek(0)
    return output