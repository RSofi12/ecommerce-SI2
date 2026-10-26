"""add tenant_id to products, variants, inventory and create offline sync tables

Revision ID: 0041
Revises: 0040
Create Date: 2026-10-25 18:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0041"
down_revision = "0040"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Agregar tenant_id a products
    op.add_column("products", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_products_tenant_id", "products", "companies", ["tenant_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_products_tenant_id", "products", ["tenant_id"], unique=False)

    # 2. Agregar tenant_id a product_variants
    op.add_column("product_variants", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_product_variants_tenant_id", "product_variants", "companies", ["tenant_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_product_variants_tenant_id", "product_variants", ["tenant_id"], unique=False)

    # 3. Agregar tenant_id a inventory
    op.add_column("inventory", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_inventory_tenant_id", "inventory", "companies", ["tenant_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_inventory_tenant_id", "inventory", ["tenant_id"], unique=False)

    # 4. Crear tabla 'offline_operations'
    op.create_table(
        "offline_operations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("branch_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("operation_type", sa.String(length=50), nullable=False),
        sa.Column("client_operation_id", sa.String(length=100), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("synced", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_offline_operations_id", "offline_operations", ["id"], unique=False)
    op.create_index("ix_offline_operations_tenant_id", "offline_operations", ["tenant_id"], unique=False)
    op.create_index("ix_offline_operations_client_op_id", "offline_operations", ["client_operation_id"], unique=False)

    # 5. Crear tabla 'catalog_cache'
    op.create_table(
        "catalog_cache",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("cached_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["companies.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_catalog_cache_id", "catalog_cache", ["id"], unique=False)
    op.create_index("ix_catalog_cache_tenant_id", "catalog_cache", ["tenant_id"], unique=False)


def downgrade() -> None:
    op.drop_table("catalog_cache")
    op.drop_table("offline_operations")

    op.drop_constraint("fk_inventory_tenant_id", "inventory", type_="foreignkey")
    op.drop_index("ix_inventory_tenant_id", table_name="inventory")
    op.drop_column("inventory", "tenant_id")

    op.drop_constraint("fk_product_variants_tenant_id", "product_variants", type_="foreignkey")
    op.drop_index("ix_product_variants_tenant_id", table_name="product_variants")
    op.drop_column("product_variants", "tenant_id")

    op.drop_constraint("fk_products_tenant_id", "products", type_="foreignkey")
    op.drop_index("ix_products_tenant_id", table_name="products")
    op.drop_column("products", "tenant_id")
