"""家庭内部转账模块集成测试。"""

from datetime import datetime, timezone
from decimal import Decimal

from app.db.session import SessionLocal
from app.modules.accounts.models import Account
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


def _balance(account_id):
    db = SessionLocal()
    value = db.query(Account).filter(Account.id == account_id).one().current_balance
    db.close()
    return str(value)


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


def _payload(family_id, from_account_id, to_account_id, amount="200.00"):
    return {
        "family_id": family_id,
        "from_account_id": from_account_id,
        "to_account_id": to_account_id,
        "amount": amount,
        "occurred_at": "2026-09-06T13:42:00+08:00",
        "remark": "家庭内部转账",
    }


class TestTransferCreate:
    def test_create_updates_balances_and_keeps_total(self, client):
        alice, bob, fid, alice_mid, bob_mid = _setup(client)
        alice_account = _seed_account(fid, alice_mid, "alice现金", "1000.00")
        bob_account = _seed_account(fid, bob_mid, "bob现金", "500.00")

        resp = client.post(
            "/api/v1/transfers",
            json=_payload(fid, alice_account, bob_account, "200.00"),
            headers=auth_header(alice),
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["from_member_id"] == alice_mid
        assert data["to_member_id"] == bob_mid
        assert data["from_member_nickname"] == "alice"
        assert data["to_member_nickname"] == "bob"

        # 转出减少、转入增加、总资产不变
        assert _balance(alice_account) == "800.00"
        assert _balance(bob_account) == "700.00"

    def test_transfer_does_not_create_transactions(self, client):
        alice, bob, fid, alice_mid, bob_mid = _setup(client)
        alice_account = _seed_account(fid, alice_mid)
        bob_account = _seed_account(fid, bob_mid)
        client.post(
            "/api/v1/transfers",
            json=_payload(fid, alice_account, bob_account),
            headers=auth_header(alice),
        )
        resp = client.get(
            "/api/v1/transactions",
            params={"family_id": fid},
            headers=auth_header(alice),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["total"] == 0

    def test_same_account_rejected(self, client):
        alice, bob, fid, alice_mid, bob_mid = _setup(client)
        alice_account = _seed_account(fid, alice_mid)
        bob_account = _seed_account(fid, bob_mid)
        resp = client.post(
            "/api/v1/transfers",
            json=_payload(fid, alice_account, alice_account),
            headers=auth_header(alice),
        )
        assert resp.status_code == 400

    def test_non_positive_amount_rejected(self, client):
        alice, bob, fid, alice_mid, bob_mid = _setup(client)
        alice_account = _seed_account(fid, alice_mid)
        bob_account = _seed_account(fid, bob_mid)
        resp = client.post(
            "/api/v1/transfers",
            json=_payload(fid, alice_account, bob_account, amount="0"),
            headers=auth_header(alice),
        )
        assert resp.status_code == 400

    def test_cross_family_account_rejected(self, client):
        alice, bob, fid, alice_mid, bob_mid = _setup(client)
        bob_account = _seed_account(fid, bob_mid)
        # 另一个家庭里 outsider 的账户
        outsider = _register_and_login(client, "outsider")
        other_fid = client.post(
            "/api/v1/families", json={"name": "另一个家庭"}, headers=auth_header(outsider)
        ).json()["data"]["id"]
        other_members = client.get(
            f"/api/v1/families/{other_fid}/members", headers=auth_header(outsider)
        ).json()["data"]
        outsider_mid = next(m["id"] for m in other_members if m["username"] == "outsider")
        other_account = _seed_account(other_fid, outsider_mid)

        resp = client.post(
            "/api/v1/transfers",
            json=_payload(fid, other_account, bob_account),
            headers=auth_header(alice),
        )
        assert resp.status_code == 403

    def test_closed_account_rejected(self, client):
        alice, bob, fid, alice_mid, bob_mid = _setup(client)
        alice_account = _seed_account(fid, alice_mid, balance="0.00")
        bob_account = _seed_account(fid, bob_mid)
        db = SessionLocal()
        db.query(Account).filter(Account.id == alice_account).update(
            {"closed_at": datetime.now(timezone.utc)}
        )
        db.commit()
        db.close()
        resp = client.post(
            "/api/v1/transfers",
            json=_payload(fid, alice_account, bob_account),
            headers=auth_header(alice),
        )
        assert resp.status_code == 409

    def test_non_member_forbidden(self, client):
        alice, bob, fid, alice_mid, bob_mid = _setup(client)
        alice_account = _seed_account(fid, alice_mid)
        bob_account = _seed_account(fid, bob_mid)
        outsider = _register_and_login(client, "intruder")
        resp = client.post(
            "/api/v1/transfers",
            json=_payload(fid, alice_account, bob_account),
            headers=auth_header(outsider),
        )
        assert resp.status_code == 403


class TestTransferPermission:
    def test_non_admin_cannot_transfer_from_others_account(self, client):
        alice, bob, fid, alice_mid, bob_mid = _setup(client)
        alice_account = _seed_account(fid, alice_mid, "alice现金")
        bob_account = _seed_account(fid, bob_mid, "bob现金")
        resp = client.post(
            "/api/v1/transfers",
            json=_payload(fid, alice_account, bob_account),
            headers=auth_header(bob),
        )
        assert resp.status_code == 403

    def test_member_can_transfer_from_own_account(self, client):
        alice, bob, fid, alice_mid, bob_mid = _setup(client)
        bob_account = _seed_account(fid, bob_mid, "bob现金")
        alice_account = _seed_account(fid, alice_mid, "alice现金")
        resp = client.post(
            "/api/v1/transfers",
            json=_payload(fid, bob_account, alice_account, "100.00"),
            headers=auth_header(bob),
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["from_member_id"] == bob_mid

    def test_member_can_edit_and_delete_own_transfer(self, client):
        alice, bob, fid, alice_mid, bob_mid = _setup(client)
        alice_account = _seed_account(fid, alice_mid, "alice现金", "1000.00")
        bob_account = _seed_account(fid, bob_mid, "bob现金", "500.00")
        created = client.post(
            "/api/v1/transfers",
            json=_payload(fid, alice_account, bob_account, "200.00"),
            headers=auth_header(alice),
        ).json()["data"]
        transfer_id = created["id"]

        # 编辑金额 -> 余额重算
        updated = client.patch(
            f"/api/v1/transfers/{transfer_id}",
            json={"amount": "100.00"},
            headers=auth_header(alice),
        )
        assert updated.status_code == 200
        assert _balance(alice_account) == "900.00"
        assert _balance(bob_account) == "600.00"

        # 删除 -> 余额恢复
        deleted = client.delete(
            f"/api/v1/transfers/{transfer_id}", headers=auth_header(alice)
        )
        assert deleted.status_code == 204
        assert _balance(alice_account) == "1000.00"
        assert _balance(bob_account) == "500.00"

    def test_to_member_can_delete_transfer(self, client):
        alice, bob, fid, alice_mid, bob_mid = _setup(client)
        alice_account = _seed_account(fid, alice_mid, "alice现金", "1000.00")
        bob_account = _seed_account(fid, bob_mid, "bob现金", "500.00")
        created = client.post(
            "/api/v1/transfers",
            json=_payload(fid, alice_account, bob_account, "200.00"),
            headers=auth_header(alice),
        ).json()["data"]

        # 转入方 bob 作为转账双方之一，有编辑/删除权限
        resp = client.delete(
            f"/api/v1/transfers/{created['id']}", headers=auth_header(bob)
        )
        assert resp.status_code == 204
        assert _balance(alice_account) == "1000.00"
        assert _balance(bob_account) == "500.00"


class TestTransferList:
    def test_personal_scope_filters_involvement(self, client):
        alice, bob, fid, alice_mid, bob_mid = _setup(client)
        alice_account = _seed_account(fid, alice_mid, "alice现金")
        alice_account2 = _seed_account(fid, alice_mid, "alice银行卡")
        bob_account = _seed_account(fid, bob_mid, "bob现金")
        # alice -> bob（bob 参与）
        client.post(
            "/api/v1/transfers",
            json=_payload(fid, alice_account, bob_account),
            headers=auth_header(alice),
        )
        # alice -> alice（bob 不参与）
        client.post(
            "/api/v1/transfers",
            json=_payload(fid, alice_account, alice_account2),
            headers=auth_header(alice),
        )

        resp = client.get(
            "/api/v1/transfers",
            params={"family_id": fid, "scope": "personal"},
            headers=auth_header(bob),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["total"] == 1
        assert resp.json()["data"]["items"][0]["to_member_id"] == bob_mid

        family_resp = client.get(
            "/api/v1/transfers",
            params={"family_id": fid, "scope": "family"},
            headers=auth_header(alice),
        )
        assert family_resp.json()["data"]["total"] == 2

    def test_filter_by_from_member(self, client):
        alice, bob, fid, alice_mid, bob_mid = _setup(client)
        alice_account = _seed_account(fid, alice_mid, "alice现金")
        bob_account = _seed_account(fid, bob_mid, "bob现金")
        client.post(
            "/api/v1/transfers",
            json=_payload(fid, alice_account, bob_account),
            headers=auth_header(alice),
        )
        client.post(
            "/api/v1/transfers",
            json=_payload(fid, bob_account, alice_account),
            headers=auth_header(bob),
        )
        resp = client.get(
            "/api/v1/transfers",
            params={"family_id": fid, "from_member_id": alice_mid},
            headers=auth_header(alice),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["total"] == 1
        assert resp.json()["data"]["items"][0]["from_member_id"] == alice_mid