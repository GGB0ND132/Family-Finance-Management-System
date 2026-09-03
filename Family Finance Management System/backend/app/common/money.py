"""货币工具：金额统一以 Decimal 处理，禁止 FLOAT/DOUBLE（系统设计 5.3）。"""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from app.core.exceptions import BadRequestError

TWO_PLACES = Decimal("0.01")


def to_decimal(value: str | int | float | Decimal) -> Decimal:
    """把输入转换为 Decimal；金额非法时抛 400。"""
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise BadRequestError(f"金额格式非法：{value}") from exc


def quantize_money(amount: Decimal) -> Decimal:
    """金额四舍五入到两位小数，保持 DECIMAL(12,2) 精度。"""
    return amount.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def normalize_money(value: str | int | float | Decimal) -> Decimal:
    """转换为 Decimal 并量化到两位小数。"""
    return quantize_money(to_decimal(value))


def ensure_positive(value: str | int | float | Decimal) -> Decimal:
    """业务规则 BR-04：金额必须大于 0。"""
    amount = normalize_money(value)
    if amount <= 0:
        raise BadRequestError("金额必须大于 0")
    return amount