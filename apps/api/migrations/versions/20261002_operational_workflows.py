"""persist lockout, ownership, and tenant automation settings

Revision ID: 20261002_operational
Revises: 585f85e76efb
Create Date: 2026-10-02
"""

from alembic import op
import sqlalchemy as sa

revision = "20261002_operational"
down_revision = "585f85e76efb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("users", sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "sessions",
        sa.Column("remember_me", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column("findings", sa.Column("assigned_to_user_id", sa.String(length=36), nullable=True))
    op.add_column("findings", sa.Column("due_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(
        "fk_findings_assigned_to_user_id_users",
        "findings",
        "users",
        ["assigned_to_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_findings_assigned_to_user_id", "findings", ["assigned_to_user_id"])
    op.create_table(
        "tenant_settings",
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("daily_scans_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("daily_scan_hour_utc", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("slack_alerts_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("last_scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("tenant_id"),
    )
    op.execute("ALTER TABLE tenant_settings ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE tenant_settings FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_tenant_settings ON tenant_settings "
        "USING (tenant_id = current_setting('app.current_tenant_id', true))"
    )


def downgrade() -> None:
    op.execute("DROP POLICY tenant_isolation_tenant_settings ON tenant_settings")
    op.drop_table("tenant_settings")
    op.drop_index("ix_findings_assigned_to_user_id", table_name="findings")
    op.drop_constraint("fk_findings_assigned_to_user_id_users", "findings", type_="foreignkey")
    op.drop_column("findings", "due_at")
    op.drop_column("findings", "assigned_to_user_id")
    op.drop_column("sessions", "remember_me")
    op.drop_column("users", "locked_until")
    op.drop_column("users", "failed_login_attempts")
