from datetime import datetime
from decimal import Decimal

from app.db.session import SessionLocal
from app.modules.accounts.models import Account
from app.modules.categories.models import Category
from app.modules.families.models import FamilyMember
from app.modules.transactions.models import Transaction
from app.modules.users.models import User

from tests.test_auth_users import auth_header
from tests.test_families import create_family, generate_invite_code, register_and_login


def _family_with_members(client, names):
    """创建家庭，names[0] 为管理员创建者，其余成员加入，返回 {name: token}。"""
    tokens = {name: register_and_login(client, name) for name in names}
    admin = names[0]
    family_id = create_family(client, tokens[admin]).json()["data"]["id"]
    if len(names) > 1:
        code = generate_invite_code(client, tokens[admin], family_id).json()["data"]["invite_code"]
        for name in names[1:]:
            client.post(
                "/api/v1/families/join",
                json={"invite_code": code},
                headers=auth_header(tokens[name]),
            )
    return tokens, family_id


def _domain_ids(family_id, names):
    """返回 {name: {"user_id": int, "member_id": int}}。"""
    db = SessionLocal()
    try:
        result = {}
        for name in names:
            user = db.query(User).filter(User.username == name).one()
            member = (
                db.query(FamilyMember)
                .filter(FamilyMember.family_id == family_id, FamilyMember.user_id == user.id)
                .one()
            )
            result[name] = {"user_id": user.id, "member_id": member.id}
        return result
    finally:
        db.close()


def _seed_expense_category(family_id, name="餐饮"):
    db = SessionLocal()
    try:
        category = Category(family_id=family_id, name=name, type="EXPENSE")
        db.add(category)
        db.flush()
        category_id = category.id
        db.commit()
        return category_id
    finally:
        db.close()


def _seed_transaction(family_id, category_id, beneficiary_member_id, recorder_user_id, type_, amount, occurred_at):
    db = SessionLocal()
    try:
        account = Account(
            family_id=family_id,
            owner_member_id=beneficiary_member_id,
            name="测试账户",
            type="CASH",
            initial_balance=Decimal("0"),
            current_balance=Decimal("0"),
        )
        db.add(account)
        db.flush()
        tx = Transaction(
            family_id=family_id,
            account_id=account.id,
            category_id=category_id,
            beneficiary_member_id=beneficiary_member_id,
            recorder_user_id=recorder_user_id,
            type=type_,
            amount=Decimal(str(amount)),
            occurred_at=occurred_at,
        )
        db.add(tx)
        db.commit()
        return tx.id
    finally:
        db.close()


def _dt(month, day=1):
    year, mon = month.split("-")
    return datetime(int(year), int(mon), day, 12, 0)


class TestBudgetQuery:
    def test_personal_budget_default_zero(self, client):
        tokens, family_id = _family_with_members(client, ["alice", "bob"])
        resp = client.get(
            "/api/v1/budgets/2026-09",
            params={"family_id": family_id, "scope": "personal"},
            headers=auth_header(tokens["alice"]),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["scope"] == "personal"
        assert data["total_amount"] == "0.00"
        assert data["used_amount"] == "0.00"
        assert data["usage_rate"] == "0.00"
        assert data["warning_level"] == "NORMAL"
        assert data["categories"] == []

    def test_outsider_forbidden(self, client):
        tokens, family_id = _family_with_members(client, ["alice"])
        carol = register_and_login(client, "carol")
        resp = client.get(
            "/api/v1/budgets/2026-09",
            params={"family_id": family_id, "scope": "family"},
            headers=auth_header(carol),
        )
        assert resp.status_code == 403

    def test_invalid_month(self, client):
        tokens, family_id = _family_with_members(client, ["alice"])
        resp = client.get(
            "/api/v1/budgets/2026-13",
            params={"family_id": family_id, "scope": "family"},
            headers=auth_header(tokens["alice"]),
        )
        assert resp.status_code == 400


class TestBudgetPermission:
    def test_member_cannot_save_family_budget(self, client):
        tokens, family_id = _family_with_members(client, ["alice", "bob"])
        resp = client.put(
            "/api/v1/budgets/2026-09",
            json={"family_id": family_id, "scope": "family", "total_amount": "1000", "categories": []},
            headers=auth_header(tokens["bob"]),
        )
        assert resp.status_code == 403

    def test_member_cannot_copy_family_budget(self, client):
        tokens, family_id = _family_with_members(client, ["alice", "bob"])
        resp = client.post(
            "/api/v1/budgets/2026-09/copy-from-previous",
            json={"family_id": family_id, "scope": "family"},
            headers=auth_header(tokens["bob"]),
        )
        assert resp.status_code == 403


class TestFamilyBudget:
    def test_admin_save_and_get(self, client):
        tokens, family_id = _family_with_members(client, ["alice", "bob"])
        category_id = _seed_expense_category(family_id)

        resp = client.put(
            "/api/v1/budgets/2026-09",
            json={
                "family_id": family_id,
                "scope": "family",
                "total_amount": "5000",
                "categories": [{"category_id": category_id, "amount": "1000"}],
            },
            headers=auth_header(tokens["alice"]),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["scope"] == "family"
        assert data["total_amount"] == "5000.00"
        assert len(data["categories"]) == 1
        assert data["categories"][0]["category_id"] == category_id
        assert data["categories"][0]["amount"] == "1000.00"

        got = client.get(
            "/api/v1/budgets/2026-09",
            params={"family_id": family_id, "scope": "family"},
            headers=auth_header(tokens["bob"]),
        )
        assert got.status_code == 200
        assert got.json()["data"]["total_amount"] == "5000.00"

    def test_family_budget_usage_excludes_income(self, client):
        tokens, family_id = _family_with_members(client, ["alice", "bob"])
        ids = _domain_ids(family_id, ["alice", "bob"])
        category_id = _seed_expense_category(family_id)

        _seed_transaction(family_id, category_id, ids["alice"]["member_id"], ids["alice"]["user_id"], "EXPENSE", 200, _dt("2026-09", 2))
        _seed_transaction(family_id, category_id, ids["bob"]["member_id"], ids["bob"]["user_id"], "INCOME", 300, _dt("2026-09", 3))

        client.put(
            "/api/v1/budgets/2026-09",
            json={
                "family_id": family_id,
                "scope": "family",
                "total_amount": "1000",
                "categories": [{"category_id": category_id, "amount": "1000"}],
            },
            headers=auth_header(tokens["alice"]),
        )

        resp = client.get(
            "/api/v1/budgets/2026-09",
            params={"family_id": family_id, "scope": "family"},
            headers=auth_header(tokens["alice"]),
        )
        data = resp.json()["data"]
        assert data["total_amount"] == "1000.00"
        assert data["used_amount"] == "200.00"
        assert data["remaining_amount"] == "800.00"
        assert data["usage_rate"] == "20.00"
        assert data["warning_level"] == "NORMAL"
        assert data["categories"][0]["used_amount"] == "200.00"


class TestPersonalBudget:
    def test_personal_usage_only_own_expense(self, client):
        tokens, family_id = _family_with_members(client, ["alice", "bob"])
        ids = _domain_ids(family_id, ["alice", "bob"])
        category_id = _seed_expense_category(family_id)

        _seed_transaction(family_id, category_id, ids["alice"]["member_id"], ids["alice"]["user_id"], "EXPENSE", 200, _dt("2026-09", 2))
        _seed_transaction(family_id, category_id, ids["bob"]["member_id"], ids["bob"]["user_id"], "EXPENSE", 100, _dt("2026-09", 3))

        alice_resp = client.get(
            "/api/v1/budgets/2026-09",
            params={"family_id": family_id, "scope": "personal"},
            headers=auth_header(tokens["alice"]),
        )
        bob_resp = client.get(
            "/api/v1/budgets/2026-09",
            params={"family_id": family_id, "scope": "personal"},
            headers=auth_header(tokens["bob"]),
        )
        assert alice_resp.json()["data"]["used_amount"] == "200.00"
        assert bob_resp.json()["data"]["used_amount"] == "100.00"


class TestCopyBudget:
    def test_copy_from_previous(self, client):
        tokens, family_id = _family_with_members(client, ["alice"])
        category_id = _seed_expense_category(family_id)

        client.put(
            "/api/v1/budgets/2026-08",
            json={
                "family_id": family_id,
                "scope": "family",
                "total_amount": "3000",
                "categories": [{"category_id": category_id, "amount": "800"}],
            },
            headers=auth_header(tokens["alice"]),
        )

        copied = client.post(
            "/api/v1/budgets/2026-09/copy-from-previous",
            json={"family_id": family_id, "scope": "family"},
            headers=auth_header(tokens["alice"]),
        )
        assert copied.status_code == 200
        data = copied.json()["data"]
        assert data["total_amount"] == "3000.00"
        assert data["categories"][0]["category_id"] == category_id
        assert data["categories"][0]["amount"] == "800.00"

    def test_copy_without_previous_returns_empty(self, client):
        tokens, family_id = _family_with_members(client, ["alice"])
        resp = client.post(
            "/api/v1/budgets/2026-09/copy-from-previous",
            json={"family_id": family_id, "scope": "family"},
            headers=auth_header(tokens["alice"]),
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "无上月预算可复制"
        assert resp.json()["data"]["total_amount"] == "0.00"