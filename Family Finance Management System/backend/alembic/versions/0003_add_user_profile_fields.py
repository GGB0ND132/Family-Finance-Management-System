"""补充用户真实姓名和头像字段"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("real_name", sa.String(length=50), nullable=True))
    op.add_column("users", sa.Column("avatar", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "avatar")
    op.drop_column("users", "real_name")
