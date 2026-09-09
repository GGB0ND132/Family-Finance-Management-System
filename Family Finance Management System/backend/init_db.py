"""快速初始化数据库表（仅用于手动验证）。"""
from app.db.base import Base
from app.db.session import engine

# 导入所有模型以注册 metadata
import app.modules.users.models  # noqa: F401
import app.modules.families.models  # noqa: F401
import app.modules.accounts.models  # noqa: F401
import app.modules.categories.models  # noqa: F401
import app.modules.budgets.models  # noqa: F401
import app.modules.transactions.models  # noqa: F401
import app.modules.transfers.models  # noqa: F401
import app.modules.imports.models  # noqa: F401

Base.metadata.create_all(engine)
print("数据库表创建成功")
