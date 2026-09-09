"""当前完整数据库结构。"""
from alembic import op

from app.db.base import Base

# 导入全部模型，将数据表注册到 Base.metadata。
import app.modules.accounts.models  # noqa: F401
import app.modules.budgets.models  # noqa: F401
import app.modules.categories.models  # noqa: F401
import app.modules.families.models  # noqa: F401
import app.modules.imports.models  # noqa: F401
import app.modules.transactions.models  # noqa: F401
import app.modules.transfers.models  # noqa: F401
import app.modules.users.models  # noqa: F401

revision = "latest"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
