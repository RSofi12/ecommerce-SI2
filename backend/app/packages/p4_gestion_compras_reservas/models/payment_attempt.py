import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.packages.p0_saas_plataforma.models.company import Company  # noqa: F401


class PaymentAttempt(Base):
    __tablename__ = "payment_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True)
    cart_id = Column(UUID(as_uuid=True), ForeignKey("carts.id"), nullable=False, index=True)
    stripe_payment_intent_id = Column(String, nullable=True, unique=True)
    status = Column(String, nullable=False, default="pending")
    idempotency_key = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    company = relationship("Company", foreign_keys=[tenant_id])
