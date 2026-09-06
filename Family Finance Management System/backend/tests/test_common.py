from decimal import Decimal

import pytest

from app.common.enums import AccountType, CategoryType, ImportBatchStatus, MemberRole, TransactionType
from app.common.money import ensure_positive, normalize_money, to_decimal
from app.core.exceptions import BadRequestError


class TestEnums:
    def test_values(self):
        assert MemberRole.ADMIN.value == "ADMIN"
        assert AccountType.CREDIT_CARD.value == "CREDIT_CARD"
        assert TransactionType.INCOME.value == "INCOME"
        assert CategoryType.EXPENSE.value == "EXPENSE"
        assert ImportBatchStatus.PREVIEWED.value == "PREVIEWED"


class TestMoney:
    def test_normalize_rounds_to_two_places(self):
        assert normalize_money("12.345") == Decimal("12.35")
        assert normalize_money(100) == Decimal("100.00")
        assert normalize_money("0.1") == Decimal("0.10")

    def test_ensure_positive(self):
        assert ensure_positive("1.5") == Decimal("1.50")

    @pytest.mark.parametrize("value", ["0", "-1", "-0.01", 0])
    def test_ensure_positive_rejects_non_positive(self, value):
        with pytest.raises(BadRequestError):
            ensure_positive(to_decimal(value))

    def test_to_decimal_rejects_garbage(self):
        with pytest.raises(BadRequestError):
            to_decimal("abc")