"""Local user accounts and role-based administration."""
from alembic import op
import sqlalchemy as sa

revision = "0002_user_accounts"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "user_accounts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="viewer"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "email", name="uq_user_accounts_tenant_email"),
        sa.CheckConstraint("role IN ('admin','operator','viewer')", name="ck_user_accounts_role"),
    )
    op.create_index("ix_user_accounts_email", "user_accounts", ["email"])
    op.create_index("ix_user_accounts_tenant_id", "user_accounts", ["tenant_id"])

def downgrade():
    op.drop_index("ix_user_accounts_tenant_id", table_name="user_accounts")
    op.drop_index("ix_user_accounts_email", table_name="user_accounts")
    op.drop_table("user_accounts")
