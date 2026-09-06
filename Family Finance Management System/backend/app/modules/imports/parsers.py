"""CSV/XLSX 文件解析器。"""


def parse_file(file_bytes: bytes, filename: str) -> list[dict]:
    """解析上传文件，返回行数据列表。

    TODO: 实现 CSV (UTF-8/BOM) 和 XLSX (openpyxl) 解析。
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == "csv":
        return _parse_csv(file_bytes)
    elif ext in ("xls", "xlsx"):
        return _parse_xlsx(file_bytes)
    else:
        raise ValueError(f"不支持的文件格式: {ext}")


def _parse_csv(data: bytes) -> list[dict]:
    # TODO: 实现 CSV 解析，返回 [{col: val}, ...]
    return []


def _parse_xlsx(data: bytes) -> list[dict]:
    # TODO: 实现 XLSX 解析，返回 [{col: val}, ...]
    return []