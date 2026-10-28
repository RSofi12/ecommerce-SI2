import uuid

from sqlalchemy import Column, DateTime, Enum as SQLAlchemyEnum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.packages.p4_gestion_compras_reservas.schemas.order_schema import (
    DeliveryTypeEnum,
    FulfillmentStatusEnum,
    OrderStatusEnum,
    PaymentMethodEnum,
    PaymentStatusEnum,
)
from app.packages.p0_saas_plataforma.models.company import Company  # noqa: F401
from app.packages.p1_gestion_usuarios_acceso.models.user import User  # noqa: F401
from app.packages.p1_gestion_usuarios_acceso.models.branch import Branch  # noqa: F401


class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    promotion_code_id = Column(UUID(as_uuid=True), ForeignKey("promotion_codes.id"), nullable=True, index=True)
    status = Column(SQLAlchemyEnum(OrderStatusEnum, name="orderstatusenum"), nullable=False, default=OrderStatusEnum.pending)
    payment_method = Column(SQLAlchemyEnum(PaymentMethodEnum, name="paymentmethodenum"), nullable=False)
    payment_status = Column(SQLAlchemyEnum(PaymentStatusEnum, name="paymentstatusenum"), nullable=False, default=PaymentStatusEnum.pending)
    stripe_payment_intent_id = Column(String, nullable=True, index=True)
    cash_reference = Column(String, nullable=True)
    pickup_branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=True, index=True)
    pickup_expires_at = Column(DateTime(timezone=True), nullable=True)
    pickup_code = Column(String, nullable=True, unique=True)
    fulfillment_status = Column(SQLAlchemyEnum(FulfillmentStatusEnum, name="fulfillmentstatusenum"), nullable=True)
    delivery_type = Column(String(30), nullable=False, default=DeliveryTypeEnum.store_pickup.value)
    shipping_address = Column(Text, nullable=True)
    tracking_number = Column(String(50), nullable=True, unique=True, index=True)
    dispatched_at = Column(DateTime(timezone=True), nullable=True)
    dispatched_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    subtotal = Column(Numeric(10, 2), nullable=False, default=0)
    discount_amount = Column(Numeric(10, 2), nullable=False, default=0)
    total_amount = Column(Numeric(10, 2), nullable=False, default=0)
    currency = Column(String, nullable=False, default="usd")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    company = relationship("Company", foreign_keys=[tenant_id])
    dispatcher = relationship("User", foreign_keys=[dispatched_by])
