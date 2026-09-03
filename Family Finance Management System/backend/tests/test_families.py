from tests.test_auth_users import auth_header, login, register_user


def register_and_login(client, username, password="password123"):
    register_user(client, username=username, password=password, nickname=username)
    token = login(client, username=username, password=password).json()["data"]["access_token"]
    return token


def create_family(client, token, name="我的家庭"):
    return client.post("/api/v1/families", json={"name": name}, headers=auth_header(token))


def generate_invite_code(client, token, family_id):
    return client.post(f"/api/v1/families/{family_id}/invite-code", headers=auth_header(token))


class TestFamilyCRUD:
    def test_create_family_and_list(self, client):
        alice = register_and_login(client, "alice")
        resp = create_family(client, alice)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["name"] == "我的家庭"
        assert data["owner_id"] > 0
        assert data["members_count"] == 1

        lst = client.get("/api/v1/families", headers=auth_header(alice)).json()["data"]
        assert len(lst) == 1
        assert lst[0]["id"] == data["id"]

    def test_join_and_rejoin(self, client):
        alice = register_and_login(client, "alice")
        bob = register_and_login(client, "bob")
        family_id = create_family(client, alice).json()["data"]["id"]
        code = generate_invite_code(client, alice, family_id).json()["data"]["invite_code"]

        joined = client.post("/api/v1/families/join", json={"invite_code": code}, headers=auth_header(bob))
        assert joined.status_code == 200
        assert joined.json()["data"]["family_id"] == family_id

        # 重复加入 -> 409
        again = client.post("/api/v1/families/join", json={"invite_code": code}, headers=auth_header(bob))
        assert again.status_code == 409

        # 无效邀请码 -> 400
        bad = client.post("/api/v1/families/join", json={"invite_code": "XXXX1234"}, headers=auth_header(bob))
        assert bad.status_code == 400

        members = client.get(f"/api/v1/families/{family_id}/members", headers=auth_header(alice))
        assert members.status_code == 200
        usernames = {m["username"] for m in members.json()["data"]}
        assert usernames == {"alice", "bob"}

    def test_revoked_invite_code_cannot_join(self, client):
        alice = register_and_login(client, "alice")
        bob = register_and_login(client, "bob")
        family_id = create_family(client, alice).json()["data"]["id"]
        code = generate_invite_code(client, alice, family_id).json()["data"]["invite_code"]
        client.delete(f"/api/v1/families/{family_id}/invite-code", headers=auth_header(alice))
        resp = client.post("/api/v1/families/join", json={"invite_code": code}, headers=auth_header(bob))
        assert resp.status_code == 400


class TestPermissions:
    def test_non_member_forbidden(self, client):
        alice = register_and_login(client, "alice")
        bob = register_and_login(client, "bob")
        family_id = create_family(client, alice).json()["data"]["id"]
        resp = client.get(f"/api/v1/families/{family_id}/members", headers=auth_header(bob))
        assert resp.status_code == 403

    def test_member_cannot_rename_or_invite(self, client):
        alice = register_and_login(client, "alice")
        bob = register_and_login(client, "bob")
        family_id = create_family(client, alice).json()["data"]["id"]
        code = generate_invite_code(client, alice, family_id).json()["data"]["invite_code"]
        client.post("/api/v1/families/join", json={"invite_code": code}, headers=auth_header(bob))

        rename = client.patch(f"/api/v1/families/{family_id}", json={"name": "改名"}, headers=auth_header(bob))
        assert rename.status_code == 403

        invite = client.post(f"/api/v1/families/{family_id}/invite-code", headers=auth_header(bob))
        assert invite.status_code == 403


class TestMemberRole:
    def _add_bob(self, client, alice, family_id):
        code = generate_invite_code(client, alice, family_id).json()["data"]["invite_code"]
        return code

    def test_demote_last_admin_conflict(self, client):
        alice = register_and_login(client, "alice")
        family_id = create_family(client, alice).json()["data"]["id"]
        members = client.get(f"/api/v1/families/{family_id}/members", headers=auth_header(alice)).json()["data"]
        alice_member_id = members[0]["id"]
        resp = client.patch(
            f"/api/v1/families/{family_id}/members/{alice_member_id}",
            json={"role": "MEMBER"},
            headers=auth_header(alice),
        )
        assert resp.status_code == 409

    def test_admin_cannot_remove_self_or_last_admin(self, client):
        alice = register_and_login(client, "alice")
        bob = register_and_login(client, "bob")
        family_id = create_family(client, alice).json()["data"]["id"]
        code = generate_invite_code(client, alice, family_id).json()["data"]["invite_code"]
        client.post("/api/v1/families/join", json={"invite_code": code}, headers=auth_header(bob))
        members = client.get(f"/api/v1/families/{family_id}/members", headers=auth_header(alice)).json()["data"]
        alice_mid, bob_mid = {m["username"]: m["id"] for m in members}["alice"], {m["username"]: m["id"] for m in members}["bob"]

        # 管理员不能移除自己
        self_rm = client.delete(f"/api/v1/families/{family_id}/members/{alice_mid}", headers=auth_header(alice))
        assert self_rm.status_code == 409

        # 把 bob 提升为管理员后，alice 不再是最后一名管理员，可移除 bob？不——移除任何管理员后仍剩 alice，允许
        # 先验证：bob 还是 MEMBER 时被移除后 alice 仍是唯一管理员，允许移除
        rm_bob = client.delete(f"/api/v1/families/{family_id}/members/{bob_mid}", headers=auth_header(alice))
        assert rm_bob.status_code == 200

    def test_member_removed_by_admin_and_role_update(self, client):
        alice = register_and_login(client, "alice")
        bob = register_and_login(client, "bob")
        family_id = create_family(client, alice).json()["data"]["id"]
        code = generate_invite_code(client, alice, family_id).json()["data"]["invite_code"]
        client.post("/api/v1/families/join", json={"invite_code": code}, headers=auth_header(bob))
        members = client.get(f"/api/v1/families/{family_id}/members", headers=auth_header(alice)).json()["data"]
        bob_mid = {m["username"]: m["id"] for m in members}["bob"]

        # 提升 bob 为管理员
        promote = client.patch(
            f"/api/v1/families/{family_id}/members/{bob_mid}",
            json={"role": "ADMIN"},
            headers=auth_header(alice),
        )
        assert promote.status_code == 200
        assert promote.json()["data"]["role"] == "ADMIN"

        # 移除后家庭只剩 alice 一名管理员，bob 可移除（bob 现在是管理员但 alice 仍是管理员）
        rm = client.delete(f"/api/v1/families/{family_id}/members/{bob_mid}", headers=auth_header(alice))
        assert rm.status_code == 200

        # 最后一名管理员不能降级
        alice_mid = {m["username"]: m["id"] for m in members}["alice"]
        demote = client.patch(
            f"/api/v1/families/{family_id}/members/{alice_mid}",
            json={"role": "MEMBER"},
            headers=auth_header(alice),
        )
        assert demote.status_code == 409