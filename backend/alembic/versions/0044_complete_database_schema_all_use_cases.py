"""complete database schema for all remaining use cases (CU13-CU28)

Revision ID: 0044
Revises: 0043
Create Date: 2026-10-28 20:30:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0044"
down_revision = "0043"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -------------------------------------------------------------
    # 1. ACTUALIZAR TABLAS EXISTENTES: RESERVATIONS (CU13, CU14)
    # -------------------------------------------------------------
    op.add_column("reservations", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_reservations_tenant_id", "reservations", "companies", ["tenant_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_reservations_tenant_id", "reservations", ["tenant_id"], unique=False)

    op.add_column("reservations", sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("reservations", sa.Column("resolved_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_reservations_resolved_by", "reservations", "users", ["resolved_by"], ["id"], ondelete="SET NULL")
    op.add_column("reservations", sa.Column("resolution_note", sa.Text(), nullable=True))

    op.add_column("reservation_items", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_reservation_items_tenant_id", "reservation_items", "companies", ["tenant_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_reservation_items_tenant_id", "reservation_items", ["tenant_id"], unique=False)

    # -------------------------------------------------------------
    # 2. ACTUALIZAR TABLAS EXISTENTES: SALES (CU15, CU16, CU18)
    # -------------------------------------------------------------
    op.add_column("sales", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_sales_tenant_id", "sales", "companies", ["tenant_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_sales_tenant_id", "sales", ["tenant_id"], unique=False)

    op.add_column("sales", sa.Column("client_sale_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_sales_client_sale_id", "sales", ["client_sale_id"], unique=True)

    op.add_column("sales", sa.Column("is_offline", sa.Boolean(), server_default=sa.text("false"), nullable=False))
    op.add_column("sales", sa.Column("synced_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("sales", sa.Column("idempotency_key", sa.String(length=100), nullable=True))
    op.create_index("ix_sales_idempotency_key", "sales", ["idempotency_key"], unique=False)

    op.add_column("sale_items", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_sale_items_tenant_id", "sale_items", "companies", ["tenant_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_sale_items_tenant_id", "sale_items", ["tenant_id"], unique=False)

    # -------------------------------------------------------------
    # 3. ACTUALIZAR CONVERSACIONES (CU23: RAG Asistido por Voz)
    # -------------------------------------------------------------
    op.add_column("conversations", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_conversations_tenant_id", "conversations", "companies", ["tenant_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_conversations_tenant_id", "conversations", ["tenant_id"], unique=False)

    op.add_column("conversation_messages", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_conversation_messages_tenant_id", "conversation_messages", "companies", ["tenant_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_conversation_messages_tenant_id", "conversation_messages", ["tenant_id"], unique=False)

    # -------------------------------------------------------------
    # 4. ACTUALIZAR CODIGOS PROMOCIONALES (CU07, CU15)
    # -------------------------------------------------------------
    op.add_column("promotion_codes", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_promotion_codes_tenant_id", "promotion_codes", "companies", ["tenant_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_promotion_codes_tenant_id", "promotion_codes", ["tenant_id"], unique=False)

    op.add_column("promotion_code_usages", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_promotion_code_usages_tenant_id", "promotion_code_usages", "companies", ["tenant_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_promotion_code_usages_tenant_id", "promotion_code_usages", ["tenant_id"], unique=False)

    # -------------------------------------------------------------
    # 5. CREAR TABLA: SYNC_OPERATIONS (CU17, CU18: Sincronización Idempotente)
    # -------------------------------------------------------------
    op.create_table(
        "sync_operations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("client_operation_id", sa.String(length=100), nullable=False),
        sa.Column("operation_type", sa.String(length=50), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=30), server_default="PROCESADO", nullable=False),
        sa.Column("synced_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["companies.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_sync_operations_id", "sync_operations", ["id"], unique=False)
    op.create_index("ix_sync_operations_tenant_id", "sync_operations", ["tenant_id"], unique=False)
    op.create_index("ix_sync_operations_client_op_id", "sync_operations", ["client_operation_id"], unique=True)

    # -------------------------------------------------------------
    # 6. CREAR TABLA: GARMENT_EXCHANGES (CU19: Política de Negocio 1)
    # -------------------------------------------------------------
    op.create_table(
        "garment_exchanges",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("branch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cashier_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sale_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("original_variant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("new_variant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("price_difference", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("difference_paid", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("payment_method", sa.String(length=30), nullable=True),
        sa.Column("status", sa.String(length=30), server_default="COMPLETED", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["cashier_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["sale_id"], ["sales.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["original_variant_id"], ["product_variants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["new_variant_id"], ["product_variants.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_garment_exchanges_id", "garment_exchanges", ["id"], unique=False)
    op.create_index("ix_garment_exchanges_tenant_id", "garment_exchanges", ["tenant_id"], unique=False)
    op.create_index("ix_garment_exchanges_sale_id", "garment_exchanges", ["sale_id"], unique=False)

    # -------------------------------------------------------------
    # 7. CREAR TABLA: GARMENT_RETURNS (CU20: Política de Negocio 2)
    # -------------------------------------------------------------
    op.create_table(
        "garment_returns",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("branch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cashier_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sale_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quantity", sa.Integer(), server_default="1", nullable=False),
        sa.Column("original_item_amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("retention_percentage", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("retention_amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("refund_amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("refund_method", sa.String(length=30), nullable=False),
        sa.Column("credit_note_code", sa.String(length=64), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["cashier_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["sale_id"], ["sales.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_garment_returns_id", "garment_returns", ["id"], unique=False)
    op.create_index("ix_garment_returns_tenant_id", "garment_returns", ["tenant_id"], unique=False)
    op.create_index("ix_garment_returns_sale_id", "garment_returns", ["sale_id"], unique=False)
    op.create_index("ix_garment_returns_credit_note", "garment_returns", ["credit_note_code"], unique=True)

    # -------------------------------------------------------------
    # 8. CREAR TABLA: ML_MODELS (CU25, CU26, CU27: Registro Modelos ML)
    # -------------------------------------------------------------
    op.create_table(
        "ml_models",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("model_type", sa.String(length=50), nullable=False),
        sa.Column("version", sa.String(length=30), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("model_path", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("trained_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["companies.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_ml_models_id", "ml_models", ["id"], unique=False)
    op.create_index("ix_ml_models_tenant_id", "ml_models", ["tenant_id"], unique=False)

    # -------------------------------------------------------------
    # 9. CREAR TABLA: DEMAND_FORECASTS (CU26, CU28: Predicción Supervisada)
    # -------------------------------------------------------------
    op.create_table(
        "demand_forecasts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("branch_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("forecast_period", sa.String(length=30), nullable=False),
        sa.Column("predicted_units", sa.Integer(), nullable=False),
        sa.Column("confidence_lower", sa.Integer(), nullable=True),
        sa.Column("confidence_upper", sa.Integer(), nullable=True),
        sa.Column("algorithm_used", sa.String(length=50), server_default="RandomForestRegressor", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_demand_forecasts_id", "demand_forecasts", ["id"], unique=False)
    op.create_index("ix_demand_forecasts_tenant_id", "demand_forecasts", ["tenant_id"], unique=False)
    op.create_index("ix_demand_forecasts_variant_id", "demand_forecasts", ["variant_id"], unique=False)

    # -------------------------------------------------------------
    # 10. CREAR TABLA: CUSTOMER_SEGMENTS (CU27, CU28: K-Means Clustering)
    # -------------------------------------------------------------
    op.create_table(
        "customer_segments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cluster_id", sa.Integer(), nullable=False),
        sa.Column("segment_label", sa.String(length=64), nullable=False),
        sa.Column("recency_days", sa.Integer(), nullable=True),
        sa.Column("frequency_count", sa.Integer(), nullable=True),
        sa.Column("monetary_total", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("return_rate", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_customer_segments_id", "customer_segments", ["id"], unique=False)
    op.create_index("ix_customer_segments_tenant_id", "customer_segments", ["tenant_id"], unique=False)
    op.create_index("ix_customer_segments_user_id", "customer_segments", ["user_id"], unique=False)


def downgrade() -> None:
    # 10. Customer segments
    op.drop_table("customer_segments")

    # 9. Demand forecasts
    op.drop_table("demand_forecasts")

    # 8. ML models
    op.drop_table("ml_models")

    # 7. Garment returns
    op.drop_table("garment_returns")

    # 6. Garment exchanges
    op.drop_table("garment_exchanges")

    # 5. Sync operations
    op.drop_table("sync_operations")

    # 4. Promotion codes & usages
    op.drop_constraint("fk_promotion_code_usages_tenant_id", "promotion_code_usages", type_="foreignkey")
    op.drop_index("ix_promotion_code_usages_tenant_id", table_name="promotion_code_usages")
    op.drop_column("promotion_code_usages", "tenant_id")

    op.drop_constraint("fk_promotion_codes_tenant_id", "promotion_codes", type_="foreignkey")
    op.drop_index("ix_promotion_codes_tenant_id", table_name="promotion_codes")
    op.drop_column("promotion_codes", "tenant_id")

    # 3. Conversations
    op.drop_constraint("fk_conversation_messages_tenant_id", "conversation_messages", type_="foreignkey")
    op.drop_index("ix_conversation_messages_tenant_id", table_name="conversation_messages")
    op.drop_column("conversation_messages", "tenant_id")

    op.drop_constraint("fk_conversations_tenant_id", "conversations", type_="foreignkey")
    op.drop_index("ix_conversations_tenant_id", table_name="conversations")
    op.drop_column("conversations", "tenant_id")

    # 2. Sales
    op.drop_constraint("fk_sale_items_tenant_id", "sale_items", type_="foreignkey")
    op.drop_index("ix_sale_items_tenant_id", table_name="sale_items")
    op.drop_column("sale_items", "tenant_id")

    op.drop_index("ix_sales_idempotency_key", table_name="sales")
    op.drop_column("sales", "idempotency_key")
    op.drop_column("sales", "synced_at")
    op.drop_column("sales", "is_offline")
    op.drop_index("ix_sales_client_sale_id", table_name="sales")
    op.drop_column("sales", "client_sale_id")

    op.drop_constraint("fk_sales_tenant_id", "sales", type_="foreignkey")
    op.drop_index("ix_sales_tenant_id", table_name="sales")
    op.drop_column("sales", "tenant_id")

    # 1. Reservations
    op.drop_constraint("fk_reservation_items_tenant_id", "reservation_items", type_="foreignkey")
    op.drop_index("ix_reservation_items_tenant_id", table_name="reservation_items")
    op.drop_column("reservation_items", "tenant_id")

    op.drop_column("reservations", "resolution_note")
    op.drop_constraint("fk_reservations_resolved_by", "reservations", type_="foreignkey")
    op.drop_column("reservations", "resolved_by")
    op.drop_column("reservations", "resolved_at")

    op.drop_constraint("fk_reservations_tenant_id", "reservations", type_="foreignkey")
    op.drop_index("ix_reservations_tenant_id", table_name="reservations")
    op.drop_column("reservations", "tenant_id")
