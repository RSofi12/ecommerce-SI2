"""add tenant_id and dispatch fields to orders, order_items, carts, cart_items, payment_attempts

Revision ID: 0043
Revises: 0042
Create Date: 2026-10-27 20:15:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0043"
down_revision = "0042"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 0. Agregar valores a fulfillmentstatusenum
    op.execute(sa.text("COMMIT"))
    op.execute(sa.text("ALTER TYPE fulfillmentstatusenum ADD VALUE IF NOT EXISTS 'ready_for_dispatch'"))
    op.execute(sa.text("ALTER TYPE fulfillmentstatusenum ADD VALUE IF NOT EXISTS 'dispatched'"))
    op.execute(sa.text("ALTER TYPE fulfillmentstatusenum ADD VALUE IF NOT EXISTS 'delivered'"))
    op.execute(sa.text("BEGIN"))

    # 1. Orders: tenant_id and dispatch fields
    op.add_column("orders", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_orders_tenant_id", "orders", "companies", ["tenant_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_orders_tenant_id", "orders", ["tenant_id"], unique=False)

    op.add_column("orders", sa.Column("delivery_type", sa.String(length=30), server_default="RETIRO_TIENDA", nullable=False))
    op.add_column("orders", sa.Column("shipping_address", sa.Text(), nullable=True))
    op.add_column("orders", sa.Column("tracking_number", sa.String(length=50), nullable=True))
    op.create_index("ix_orders_tracking_number", "orders", ["tracking_number"], unique=True)
    op.add_column("orders", sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("orders", sa.Column("dispatched_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_orders_dispatched_by", "orders", "users", ["dispatched_by"], ["id"], ondelete="SET NULL")

    # 2. Order items: tenant_id
    op.add_column("order_items", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_order_items_tenant_id", "order_items", "companies", ["tenant_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_order_items_tenant_id", "order_items", ["tenant_id"], unique=False)

    # 3. Carts: tenant_id
    op.add_column("carts", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_carts_tenant_id", "carts", "companies", ["tenant_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_carts_tenant_id", "carts", ["tenant_id"], unique=False)

    # 4. Cart items: tenant_id
    op.add_column("cart_items", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_cart_items_tenant_id", "cart_items", "companies", ["tenant_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_cart_items_tenant_id", "cart_items", ["tenant_id"], unique=False)

    # 5. Payment attempts: tenant_id
    op.add_column("payment_attempts", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_payment_attempts_tenant_id", "payment_attempts", "companies", ["tenant_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_payment_attempts_tenant_id", "payment_attempts", ["tenant_id"], unique=False)


def downgrade() -> None:
    # 5. Payment attempts
    op.drop_index("ix_payment_attempts_tenant_id", table_name="payment_attempts")
    op.drop_constraint("fk_payment_attempts_tenant_id", "payment_attempts", type_="foreignkey")
    op.drop_column("payment_attempts", "tenant_id")

    # 4. Cart items
    op.drop_index("ix_cart_items_tenant_id", table_name="cart_items")
    op.drop_constraint("fk_cart_items_tenant_id", "cart_items", type_="foreignkey")
    op.drop_column("cart_items", "tenant_id")

    # 3. Carts
    op.drop_index("ix_carts_tenant_id", table_name="carts")
    op.drop_constraint("fk_carts_tenant_id", "carts", type_="foreignkey")
    op.drop_column("carts", "tenant_id")

    # 2. Order items
    op.drop_index("ix_order_items_tenant_id", table_name="order_items")
    op.drop_constraint("fk_order_items_tenant_id", "order_items", type_="foreignkey")
    op.drop_column("order_items", "tenant_id")

    # 1. Orders
    op.drop_constraint("fk_orders_dispatched_by", "orders", type_="foreignkey")
    op.drop_column("orders", "dispatched_by")
    op.drop_column("orders", "dispatched_at")
    op.drop_index("ix_orders_tracking_number", table_name="orders")
    op.drop_column("orders", "tracking_number")
    op.drop_column("shipping_address", table_name="orders")
    op.drop_column("delivery_type", table_name="orders")
    op.drop_index("ix_orders_tenant_id", table_name="orders")
    op.drop_constraint("fk_orders_tenant_id", "orders", type_="foreignkey")
    op.drop_column("orders", "tenant_id")
