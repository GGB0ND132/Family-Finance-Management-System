"""创建 families 与 family_members 表

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-03

"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "families",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("invite_code", sa.String(length=20), nullable=True),
        sa.Column("invite_expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "family_members",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("family_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=20), server_default="MEMBER", nullable=False),
        sa.Column("joined_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["family_id"], ["families.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("family_id", "user_id", name="uq_family_members_family_user"),
    )
    op.create_index(op.f("ix_family_members_family_id"), "family_members", ["family_id"])
    op.create_index(op.f("ix_family_members_user_id"), "family_members", ["user_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_family_members_user_id"), table_name="family_members")
    op.drop_index(op.f("ix_family_members_family_id"), table_name="family_members")
    op.drop_table("family_members")
    op.drop_table("families")