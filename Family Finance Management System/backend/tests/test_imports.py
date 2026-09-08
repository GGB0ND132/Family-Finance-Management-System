"""外部账单导入模块测试。

覆盖 CSV/XLSX 解析、预览行列状态、数据库重复、批次内重复、
确认写入与余额更新、非法行拦截，以及权限与越权控制。
"""

import io
import json
from datetime import datetime
from decimal import Decimal

import pytest

from app.core.exceptions import BadRequestError
from app.db.session import SessionLocal
from app.modules.accounts.models import Account
from app.modules.categories.models import Category
from app.modules.imports.parsers import parse_file
from app.modules.transactions.models import Transaction
from tests.test_auth_users import auth_header, login, register_user

MAPPING = {
    "occurred_at": "交易时间",
    "amount": "金额",
    "direction": "收/支",
    "category": "分类",
    "remark": "备注",
}

CSV_HEADER = "交易时间,金额,收/支,分类,备注\n"


def _setup(client):
    """注册用户、创建家庭，并直接写入账户与分类，返回 (token, family_id, account_id)。"""
    register_user(client, "alice")
    token = login(client).json()["data"]["access_token"]
    family_id = client.post(
        "/api/v1/families", json={"name": "我的家庭"}, headers=auth_header(token)
    ).json()["data"]["id"]
    members = client.get(
        f"/api/v1/families/{family_id}/members", headers=auth_header(token)
    ).json()["data"]
    member_id = members[0]["id"]

    with SessionLocal() as db:
        account = Account(
            family_id=family_id,
            owner_member_id=member_id,
            name="钱包",
            type="CASH",
            initial_balance=Decimal("0.00"),
            current_balance=Decimal("0.00"),
        )
        db.add(account)
        db.flush()
        account_id = account.id
        db.add(Category(family_id=family_id, name="餐饮", type="EXPENSE"))
        db.add(Category(family_id=family_id, name="工资", type="INCOME"))
        db.commit()

    return token, family_id, account_id


def _preview(client, token, family_id, account_id, content, mapping=MAPPING):
    return client.post(
        "/api/v1/imports/preview",
        headers=auth_header(token),
        files={"file": ("bill.csv", content.encode("utf-8"), "text/csv")},
        data={
            "family_id": str(family_id),
            "account_id": str(account_id),
            "scope": "personal",
            "field_mapping_json": json.dumps(mapping),
        },
    )


class TestParsers:
    def test_parse_csv_with_bom(self):
        data = "\ufeff交易时间,金额,收/支,分类,备注\n2026-09-06 13:42,128.50,支出,餐饮,晚餐\n".encode("utf-8")
        rows = parse_file(data, "bill.csv")
        assert rows == [
            {"交易时间": "2026-09-06 13:42", "金额": "128.50", "收/支": "支出", "分类": "餐饮", "备注": "晚餐"}
        ]

    def test_parse_xlsx(self):
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.append(["交易时间", "金额", "收/支", "分类", "备注"])
        ws.append(["2026-09-06 13:42", "128.50", "支出", "餐饮", "晚餐"])
        buf = io.BytesIO()
        wb.save(buf)

        rows = parse_file(buf.getvalue(), "bill.xlsx")
        assert rows[0]["金额"] == "128.50"
        assert rows[0]["分类"] == "餐饮"

    def test_parse_unsupported_extension(self):
        with pytest.raises(BadRequestError):
            parse_file(b"x", "bill.txt")


class TestPreview:
    def test_preview_valid_and_invalid_rows(self, client):
        token, family_id, account_id = _setup(client)
        content = (
            CSV_HEADER
            + "2026-09-06 13:42,128.50,支出,餐饮,晚餐\n"
            + "坏日期,10.00,支出,餐饮,早餐\n"
        )
        resp = _preview(client, token, family_id, account_id, content)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total_rows"] == 2
        assert data["valid_rows"] == 1
        assert data["invalid_rows"] == 1
        statuses = {r["row_number"]: r["validation_status"] for r in data["rows"]}
        assert statuses[2] == "VALID"
        assert statuses[3] == "INVALID"

    def test_preview_duplicate_with_existing_transaction(self, client):
        token, family_id, account_id = _setup(client)
        with SessionLocal() as db:
            db.add(
                Transaction(
                    family_id=family_id,
                    account_id=account_id,
                    category_id=1,
                    beneficiary_member_id=1,
                    recorder_user_id=1,
                    type="EXPENSE",
                    amount=Decimal("128.50"),
                    occurred_at=datetime(2026, 9, 6, 13, 42),
                    remark="晚餐",
                )
            )
            db.commit()

        content = CSV_HEADER + "2026-09-06 13:42,128.50,支出,餐饮,晚餐\n"
        resp = _preview(client, token, family_id, account_id, content)
        data = resp.json()["data"]
        assert data["duplicate_rows"] == 1
        assert data["rows"][0]["validation_status"] == "DUPLICATE"
        assert "重复" in data["rows"][0]["errors"][0]

    def test_preview_batch_internal_duplicate(self, client):
        token, family_id, account_id = _setup(client)
        content = (
            CSV_HEADER
            + "2026-09-06 13:42,128.50,支出,餐饮,晚餐\n"
            + "2026-09-06 13:42,128.50,支出,餐饮,晚餐\n"
        )
        resp = _preview(client, token, family_id, account_id, content)
        data = resp.json()["data"]
        assert data["valid_rows"] == 1
        assert data["duplicate_rows"] == 1
        assert data["rows"][1]["errors"][0] == "批次内重复"

    def test_preview_infer_direction_from_negative_amount(self, client):
        token, family_id, account_id = _setup(client)
        mapping = {"occurred_at": "交易时间", "amount": "金额", "category": "分类"}
        content = CSV_HEADER.replace("交易时间,金额,收/支,分类,备注\n", "交易时间,金额,分类\n") + \
            "2026-09-06 08:00,-30.00,餐饮\n"
        resp = _preview(client, token, family_id, account_id, content, mapping=mapping)
        data = resp.json()["data"]
        assert data["valid_rows"] == 1
        row = data["rows"][0]["normalized_data"]
        assert row["type"] == "EXPENSE"
        assert row["amount"] == "30.00"

    def test_preview_non_member_forbidden(self, client):
        token, family_id, account_id = _setup(client)
        register_user(client, "bob")
        bob_token = login(client, username="bob").json()["data"]["access_token"]
        resp = _preview(client, bob_token, family_id, account_id, CSV_HEADER + "2026-09-06 13:42,10,支出,餐饮,早餐\n")
        assert resp.status_code == 403


class TestConfirm:
    def test_confirm_writes_transactions_and_balance(self, client):
        token, family_id, account_id = _setup(client)
        content = (
            CSV_HEADER
            + "2026-09-06 13:42,128.50,支出,餐饮,晚餐\n"
            + "2026-09-06 14:00,3000.00,收入,工资,工资\n"
        )
        preview = _preview(client, token, family_id, account_id, content).json()["data"]
        batch_id = preview["batch_id"]
        assert preview["valid_rows"] == 2

        resp = client.post(f"/api/v1/imports/{batch_id}/confirm", headers=auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["data"]["imported_rows"] == 2

        with SessionLocal() as db:
            txs = db.query(Transaction).filter(Transaction.family_id == family_id).all()
            assert len(txs) == 2
            account = db.get(Account, account_id)
            # 3000.00 收入 - 128.50 支出
            assert account.current_balance == Decimal("2871.50")

    def test_confirm_with_invalid_rows_rejected(self, client):
        token, family_id, account_id = _setup(client)
        content = CSV_HEADER + "2026-09-06 13:42,128.50,支出,餐饮,晚餐\n坏日期,10,支出,餐饮,早餐\n"
        preview = _preview(client, token, family_id, account_id, content).json()["data"]
        resp = client.post(f"/api/v1/imports/{preview['batch_id']}/confirm", headers=auth_header(token))
        assert resp.status_code == 400
        assert resp.json()["code"] == 40020

    def test_get_batch_permission(self, client):
        token, family_id, account_id = _setup(client)
        preview = _preview(client, token, family_id, account_id, CSV_HEADER + "2026-09-06 13:42,10,支出,餐饮,早餐\n").json()["data"]

        register_user(client, "bob")
        bob_token = login(client, username="bob").json()["data"]["access_token"]
        resp = client.get(f"/api/v1/imports/{preview['batch_id']}", headers=auth_header(bob_token))
        assert resp.status_code == 403