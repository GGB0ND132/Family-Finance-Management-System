"""CSV/XLSX 文件解析器。

仅做“读取文件 -> 得到 [{列名: 值}, ...]”的机械转换，不包含业务校验；
业务校验在 `service.py` 中完成。CSV 兼容 UTF-8（含 BOM）与 GBK 编码。
"""

import csv
import io

from app.core.exceptions import BadRequestError


def parse_file(file_bytes: bytes, filename: str) -> list[dict]:
    """解析上传文件，返回行数据列表，每行形如 `{列名: 单元格文本}`。"""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == "csv":
        return _parse_csv(file_bytes)
    elif ext == "xlsx":
        return _parse_xlsx(file_bytes)
    else:
        raise BadRequestError(f"不支持的文件格式: .{ext}")


def _parse_csv(data: bytes) -> list[dict]:
    text = _decode_text(data)
    parsed_rows = list(csv.reader(io.StringIO(text)))
    header_index = next((i for i, row in enumerate(parsed_rows) if _looks_like_header(row)), None)
    if header_index is None:
        raise BadRequestError("CSV 文件缺少可识别的交易明细表头")
    headers = [str(h).strip().lstrip("\ufeff") for h in parsed_rows[header_index]]
    rows: list[dict] = []
    for values in parsed_rows[header_index + 1 :]:
        if not values or all(not str(value).strip() for value in values):
            continue
        rows.append({header: (values[idx] if idx < len(values) else "").strip() for idx, header in enumerate(headers)})
    return rows


def _parse_xlsx(data: bytes) -> list[dict]:
    try:
        from openpyxl import load_workbook
    except ImportError as exc:  # pragma: no cover - 依赖缺失保护
        raise BadRequestError("服务端未安装 openpyxl，无法解析 XLSX") from exc

    wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    try:
        ws = wb.active
        all_rows = list(ws.iter_rows(values_only=True))
        header_index = next((i for i, row in enumerate(all_rows) if _looks_like_header(row)), None)
        if header_index is None:
            raise BadRequestError("XLSX 文件缺少可识别的交易明细表头")
        headers = [str(h).strip().lstrip("\ufeff") if h is not None else "" for h in all_rows[header_index]]

        rows: list[dict] = []
        for values in all_rows[header_index + 1 :]:
            if values is None or all(v is None or str(v).strip() == "" for v in values):
                continue
            cell = {header: _cell_to_str(values[idx]) for idx, header in enumerate(headers)}
            rows.append(cell)
        return rows
    finally:
        wb.close()


def _decode_text(data: bytes) -> str:
    """优先按 UTF-8（含 BOM）解码，失败则回退 GBK。"""
    for encoding in ("utf-8-sig", "gbk"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="ignore")


def _cell_to_str(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _looks_like_header(values) -> bool:
    """识别支付宝/微信账单的明细表头，忽略导出说明行。"""
    headers = {str(value).strip().lstrip("\ufeff").lower() for value in values if value is not None}
    has_time = bool(headers & {"交易时间", "发生时间", "日期", "时间", "date", "time", "occurred_at"})
    has_direction = bool(headers & {"收/支", "收支", "方向", "direction", "type"})
    has_amount = bool(headers & {"金额", "金额(元)", "交易金额", "amount"})
    return has_time and has_direction and has_amount
