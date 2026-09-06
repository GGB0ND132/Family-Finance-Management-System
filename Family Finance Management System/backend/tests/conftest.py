import os

# 必须在导入 app 之前设置，保证引擎使用内存 SQLite
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-secret"
os.environ["APP_ENV"] = "test"

import pytest
from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import engine
from app.main import app


@pytest.fixture()
def client():
    Base.metadata.create_all(engine)
    try:
        with TestClient(app) as c:
            yield c
    finally:
        Base.metadata.drop_all(engine)