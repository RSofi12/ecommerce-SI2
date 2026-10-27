"""add inventory transfers and transfer items tables

Revision ID: 0042
Revises: 0041
Create Date: 2026-10-26 22:45:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0042"
down_revision = "0041"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Crear tabla 'inventory_transfers'
    op.create_table(
        "inventory_transfers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("transfer_number", sa.String(length=50), nullable=False),
        sa.Column("from_branch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("to_branch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="EN_TRANSITO", nullable=False),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("received_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["from_branch_id"], ["branches.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["to_branch_id"], ["branches.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["requested_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["received_by"], ["users.id"], ondelete="SET NULL"),
        sa.CheckConstraint("from_branch_id != to_branch_id", name="chk_transfer_different_branches"),
        sa.CheckConstraint("status IN ('SOLICITADO', 'EN_TRANSITO', 'COMPLETADO', 'CANCELADO')", name="chk_transfer_status"),
    )
    op.create_index("ix_inventory_transfers_tenant_id", "inventory_transfers", ["tenant_id"], unique=False)
    op.create_index("ix_inventory_transfers_from_branch_id", "inventory_transfers", ["from_branch_id"], unique=False)
    op.create_index("ix_inventory_transfers_to_branch_id", "inventory_transfers", ["to_branch_id"], unique=False)
    op.create_index("ix_inventory_transfers_status", "inventory_transfers", ["status"], unique=False)

    # 2. Crear tabla 'inventory_transfer_items'
    op.create_table(
        "inventory_transfer_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("transfer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("received_quantity", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["transfer_id"], ["inventory_transfers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("quantity > 0", name="chk_transfer_item_quantity_positive"),
    )
    op.create_index("ix_inventory_transfer_items_transfer_id", "inventory_transfer_items", ["transfer_id"], unique=False)
    op.create_index("ix_inventory_transfer_items_variant_id", "inventory_transfer_items", ["variant_id"], unique=False)


def downgrade() -> None:
    op.drop_table("inventory_transfer_items")
    op.drop_table("inventory_transfers")
