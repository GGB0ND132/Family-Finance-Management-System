"""扩展头像字段以保存本地图片的 Base64 数据"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "avatar",
        existing_type=sa.String(length=500),
        type_=mysql.MEDIUMTEXT(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "avatar",
        existing_type=mysql.MEDIUMTEXT(),
        type_=sa.String(length=500),
        existing_nullable=True,
    )
