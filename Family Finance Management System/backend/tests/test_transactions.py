"""收入/支出流水模块集成测试。"""

from datetime import datetime, timezone
from decimal import Decimal

from app.db.session import SessionLocal
from app.modules.accounts.models import Account
from app.modules.categories.models import Category
from tests.test_auth_users import auth_header, login, register_user


def _register_and_login(client, username, password="password123"):
    register_user(client, username=username, password=password, nickname=username)
    return login(client, username=username, password=password).json()["data"]["access_token"]


def _seed_account(family_id, owner_member_id, name="现金", balance="1000.00"):
    db = SessionLocal()
    account = Account(
        family_id=family_id,
        owner_member_id=owner_member_id,
        name=name,
        type="CASH",
        initial_balance=Decimal(balance),
        current_balance=Decimal(balance),
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    account_id = account.id
    db.close()
    return account_id


def _seed_category(family_id, name, type_):
    db = SessionLocal()
    category = Category(family_id=family_id, name=name, type=type_)
    db.add(category)
    db.commit()
    db.refresh(category)
    category_id = category.id
    db.close()
    return category_id


def _setup(client):
    """创建家庭 alice(管理员)+bob(成员)，返回相关 ID。"""
    alice_token = _register_and_login(client, "alice")
    bob_token = _register_and_login(client, "bob")
    family_id = client.post(
        "/api/v1/families", json={"name": "我的家庭"}, headers=auth_header(alice_token)
    ).json()["data"]["id"]
    code = client.post(
        f"/api/v1/families/{family_id}/invite-code", headers=auth_header(alice_token)
    ).json()["data"]["invite_code"]
    client.post("/api/v1/families/join", json={"invite_code": code}, headers=auth_header(bob_token))
    members = client.get(
        f"/api/v1/families/{family_id}/members", headers=auth_header(alice_token)
    ).json()["data"]
    alice_member_id = next(m["id"] for m in members if m["username"] == "alice")
    bob_member_id = next(m["id"] for m in members if m["username"] == "bob")
    return alice_token, bob_token, family_id, alice_member_id, bob_member_id


def _payload(family_id, account_id, category_id, beneficiary_member_id, type_="EXPENSE", amount="35.60"):
    return {
        "family_id": family_id,
        "account_id": account_id,
        "category_id": category_id,
        "beneficiary_member_id": beneficiary_member_id,
        "type": type_,
        "amount": amount,
        "occurred_at": "2026-09-06T13:42:00+08:00",
        "remark": "午餐",
    }


class TestTransactionCreate:
    def test_expense_reduces_balance(self, client):
        alice, bob, fid, alice_mid, bob_mid = _setup(client)
        account_id = _seed_account(fid, alice_mid)
        cat_id = _seed_category(fid, "餐饮", "EXPENSE")
        resp = client.post(
            "/api/v1/transactions",
            json=_payload(fid, account_id, cat_id, alice_mid),
            headers=auth_header(alice),
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["amount"] == "35.60"
        assert data["account_current_balance"] == "964.40"
        assert data["beneficiary_nickname"] == "alice"
        assert data["recorder_nickname"] == "alice"

    def test_income_increases_balance(self, client):
        alice, bob, fid, alice_mid, bob_mid = _setup(client)
        account_id = _seed_account(fid, alice_mid)
        cat_id = _seed_category(fid, "工资", "INCOME")
        resp = client.post(
            "/api/v1/transactions",
            json=_payload(fid, account_id, cat_id, alice_mid, type_="INCOME", amount="500.00"),
            headers=auth_header(alice),
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["account_current_balance"] == "1500.00"

    def test_non_positive_amount_rejected(self, client):
        alice, bob, fid, alice_mid, bob_mid = _setup(client)
        account_id = _seed_account(fid, alice_mid)
        cat_id = _seed_category(fid, "餐饮", "EXPENSE")
        resp = client.post(
            "/api/v1/transactions",
            json=_payload(fid, account_id, cat_id, alice_mid, amount="0"),
            headers=auth_header(alice),
        )
        assert resp.status_code == 400

    def test_category_direction_mismatch_rejected(self, client):
        alice, bob, fid, alice_mid, bob_mid = _setup(client)
        account_id = _seed_account(fid, alice_mid)
        income_cat = _seed_category(fid, "工资", "INCOME")
        resp = client.post(
            "/api/v1/transactions",
            json=_payload(fid, account_id, income_cat, alice_mid, type_="EXPENSE"),
            headers=auth_header(alice),
        )
        assert resp.status_code == 400

    def test_closed_account_rejected(self, client):
        alice, bob, fid, alice_mid, bob_mid = _setup(client)
        account_id = _seed_account(fid, alice_mid, balance="0.00")
        cat_id = _seed_category(fid, "餐饮", "EXPENSE")
        # 直接销户
        db = SessionLocal()
        db.query(Account).filter(Account.id == account_id).update(
            {"closed_at": datetime.now(timezone.utc)}
        )
        db.commit()
        db.close()
        resp = client.post(
            "/api/v1/transactions",
            json=_payload(fid, account_id, cat_id, alice_mid),
            headers=auth_header(alice),
        )
        assert resp.status_code == 409

    def test_non_member_forbidden(self, client):
        alice, bob, fid, alice_mid, bob_mid = _setup(client)
        account_id = _seed_account(fid, alice_mid)
        cat_id = _seed_category(fid, "餐饮", "EXPENSE")
        outsider = _register_and_login(client, "outsider")
        resp = client.post(
            "/api/v1/transactions",
            json=_payload(fid, account_id, cat_id, alice_mid),
            headers=auth_header(outsider),
        )
        assert resp.status_code == 403


class TestTransactionPermission:
    def test_non_admin_cannot_create_for_others_account(self, client):
        alice, bob, fid, alice_mid, bob_mid = _setup(client)
        alice_account = _seed_account(fid, alice_mid, name="alice现金")
        cat_id = _seed_category(fid, "餐饮", "EXPENSE")
        # bob 尝试在 alice 账户下记账
        resp = client.post(
            "/api/v1/transactions",
            json=_payload(fid, alice_account, cat_id, bob_mid),
            headers=auth_header(bob),
        )
        assert resp.status_code == 403

    def test_non_admin_can_create_for_own_account(self, client):
        alice, bob, fid, alice_mid, bob_mid = _setup(client)
        bob_account = _seed_account(fid, bob_mid, name="bob现金")
        cat_id = _seed_category(fid, "餐饮", "EXPENSE")
        resp = client.post(
            "/api/v1/transactions",
            json=_payload(fid, bob_account, cat_id, bob_mid),
            headers=auth_header(bob),
        )
        assert resp.status_code == 201

    def test_member_can_edit_and_delete_own_transaction(self, client):
        alice, bob, fid, alice_mid, bob_mid = _setup(client)
        account_id = _seed_account(fid, alice_mid)
        cat_id = _seed_category(fid, "餐饮", "EXPENSE")
        created = client.post(
            "/api/v1/transactions",
            json=_payload(fid, account_id, cat_id, alice_mid),
            headers=auth_header(alice),
        ).json()["data"]
        tx_id = created["id"]

        # 编辑金额 -> 余额重算
        updated = client.patch(
            f"/api/v1/transactions/{tx_id}",
            json={"amount": "20.00"},
            headers=auth_header(alice),
        )
        assert updated.status_code == 200
        assert updated.json()["data"]["account_current_balance"] == "980.00"

        # 删除 -> 余额恢复
        deleted = client.delete(f"/api/v1/transactions/{tx_id}", headers=auth_header(alice))
        assert deleted.status_code == 204
        db = SessionLocal()
        balance = db.query(Account).filter(Account.id == account_id).one().current_balance
        db.close()
        assert str(balance) == "1000.00"


class TestTransactionList:
    def test_personal_scope_filters_by_beneficiary(self, client):
        alice, bob, fid, alice_mid, bob_mid = _setup(client)
        alice_account = _seed_account(fid, alice_mid, name="alice现金")
        bob_account = _seed_account(fid, bob_mid, name="bob现金")
        cat_id = _seed_category(fid, "餐饮", "EXPENSE")
        client.post(
            "/api/v1/transactions",
            json=_payload(fid, alice_account, cat_id, alice_mid),
            headers=auth_header(alice),
        )
        client.post(
            "/api/v1/transactions",
            json=_payload(fid, bob_account, cat_id, bob_mid),
            headers=auth_header(bob),
        )

        # 个人范围：bob 只能看到自己的流水
        resp = client.get(
            "/api/v1/transactions",
            params={"family_id": fid, "scope": "personal"},
            headers=auth_header(bob),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 1
        assert data["items"][0]["beneficiary_member_id"] == bob_mid

        # 家庭范围：管理员可看到全部
        family_resp = client.get(
            "/api/v1/transactions",
            params={"family_id": fid, "scope": "family"},
            headers=auth_header(alice),
        )
        assert family_resp.json()["data"]["total"] == 2

    def test_filters(self, client):
        alice, bob, fid, alice_mid, bob_mid = _setup(client)
        account_id = _seed_account(fid, alice_mid)
        cat_id = _seed_category(fid, "餐饮", "EXPENSE")
        client.post(
            "/api/v1/transactions",
            json=_payload(fid, account_id, cat_id, alice_mid, amount="10.00"),
            headers=auth_header(alice),
        )
        client.post(
            "/api/v1/transactions",
            json=_payload(fid, account_id, cat_id, alice_mid, amount="100.00"),
            headers=auth_header(alice),
        )
        resp = client.get(
            "/api/v1/transactions",
            params={"family_id": fid, "type": "EXPENSE", "min_amount": "50.00"},
            headers=auth_header(alice),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["total"] == 1