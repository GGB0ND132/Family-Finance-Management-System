def register_user(client, username="alice", password="password123", nickname="小红"):
    return client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": password, "nickname": nickname},
    )


def login(client, username="alice", password="password123"):
    return client.post("/api/v1/auth/login", json={"username": username, "password": password})


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


class TestHealth:
    def test_health(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json()["code"] == 0


class TestRegister:
    def test_register_success(self, client):
        resp = register_user(client)
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        data = body["data"]
        assert data["username"] == "alice"
        assert data["nickname"] == "小红"
        assert data["id"] > 0
        assert "password" not in data and "password_hash" not in data

    def test_register_duplicate_username(self, client):
        register_user(client)
        resp = register_user(client)
        assert resp.status_code == 409
        assert resp.json()["message"] == "用户名已被占用"

    def test_register_short_password(self, client):
        resp = client.post(
            "/api/v1/auth/register",
            json={"username": "bob", "password": "123", "nickname": "小bob"},
        )
        assert resp.status_code == 422


class TestLogin:
    def test_login_success(self, client):
        register_user(client)
        resp = login(client)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["access_token"]
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "alice"

    def test_login_wrong_password(self, client):
        register_user(client)
        resp = login(client, password="wrong-pass-123")
        assert resp.status_code == 401
        assert resp.json()["message"] == "用户名或密码错误"

    def test_login_unknown_user(self, client):
        resp = login(client, username="nobody")
        assert resp.status_code == 401
        assert resp.json()["message"] == "用户名或密码错误"


class TestMe:
    def test_me_requires_token(self, client):
        resp = client.get("/api/v1/users/me")
        assert resp.status_code == 401

    def test_me_invalid_token(self, client):
        resp = client.get("/api/v1/users/me", headers=auth_header("not-a-valid-token"))
        assert resp.status_code == 401

    def test_me_success(self, client):
        register_user(client)
        token = login(client).json()["data"]["access_token"]
        resp = client.get("/api/v1/users/me", headers=auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["data"]["nickname"] == "小红"


class TestUpdateProfile:
    def test_update_nickname(self, client):
        register_user(client)
        token = login(client).json()["data"]["access_token"]
        resp = client.patch(
            "/api/v1/users/me",
            json={"nickname": "新昵称"},
            headers=auth_header(token),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["nickname"] == "新昵称"
        me = client.get("/api/v1/users/me", headers=auth_header(token)).json()["data"]
        assert me["nickname"] == "新昵称"


class TestChangePassword:
    def test_change_password_success(self, client):
        register_user(client)
        token = login(client).json()["data"]["access_token"]
        resp = client.patch(
            "/api/v1/users/me/password",
            json={"old_password": "password123", "new_password": "newpass12345"},
            headers=auth_header(token),
        )
        assert resp.status_code == 200
        # 新密码可登录，旧密码不可登录
        assert login(client, password="newpass12345").status_code == 200
        assert login(client, password="password123").status_code == 401

    def test_change_password_wrong_old(self, client):
        register_user(client)
        token = login(client).json()["data"]["access_token"]
        resp = client.patch(
            "/api/v1/users/me/password",
            json={"old_password": "wrong-old", "new_password": "newpass12345"},
            headers=auth_header(token),
        )
        assert resp.status_code == 400
        assert resp.json()["message"] == "旧密码不正确"