"""Tenant-scoped operational workspace records."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_workspace_items"
down_revision = "0002_user_accounts"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "workspace_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("status", sa.String(40), nullable=False, server_default="open"),
        sa.Column("priority", sa.String(20), nullable=False, server_default="normal"),
        sa.Column("owner", sa.String(254)),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_by", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_workspace_items_tenant_kind", "workspace_items", ["tenant_id", "kind"])
    op.create_index("ix_workspace_items_tenant_status", "workspace_items", ["tenant_id", "status"])

def downgrade():
    op.drop_index("ix_workspace_items_tenant_status", table_name="workspace_items")
    op.drop_index("ix_workspace_items_tenant_kind", table_name="workspace_items")
    op.drop_table("workspace_items")
