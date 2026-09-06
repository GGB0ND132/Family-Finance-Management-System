"""领域枚举（详细设计 1.1）。值以字符串形式存入 MySQL。"""

from enum import Enum


class StrEnum(str, Enum):
    """继承 str 以便 JSON 序列化时直接输出字符串值。"""


class MemberRole(StrEnum):
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"


class AccountType(StrEnum):
    CASH = "CASH"
    BANK_CARD = "BANK_CARD"
    ALIPAY = "ALIPAY"
    WECHAT = "WECHAT"
    CREDIT_CARD = "CREDIT_CARD"
    OTHER = "OTHER"


class TransactionType(StrEnum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


class CategoryType(StrEnum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


class ImportFileType(StrEnum):
    CSV = "CSV"
    XLSX = "XLSX"


class ImportBatchStatus(StrEnum):
    PREVIEWED = "PREVIEWED"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"


class ImportRowStatus(StrEnum):
    VALID = "VALID"
    INVALID = "INVALID"
    DUPLICATE = "DUPLICATE"
    PENDING_CONFIRM = "PENDING_CONFIRM"