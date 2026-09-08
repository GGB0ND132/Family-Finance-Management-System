"""创建 transfers 表

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-07

依赖表 accounts、families、family_members、users 由对应迁移或 `Base.metadata.create_all` 创建。
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "transfers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("family_id", sa.Integer(), nullable=False),
        sa.Column("from_account_id", sa.Integer(), nullable=False),
        sa.Column("to_account_id", sa.Integer(), nullable=False),
        sa.Column("from_member_id", sa.Integer(), nullable=False),
        sa.Column("to_member_id", sa.Integer(), nullable=False),
        sa.Column("recorder_user_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("remark", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["family_id"], ["families.id"]),
        sa.ForeignKeyConstraint(["from_account_id"], ["accounts.id"]),
        sa.ForeignKeyConstraint(["to_account_id"], ["accounts.id"]),
        sa.ForeignKeyConstraint(["from_member_id"], ["family_members.id"]),
        sa.ForeignKeyConstraint(["to_member_id"], ["family_members.id"]),
        sa.ForeignKeyConstraint(["recorder_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("transfers")