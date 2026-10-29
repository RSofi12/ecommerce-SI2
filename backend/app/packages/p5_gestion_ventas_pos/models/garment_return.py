import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class GarmentReturn(Base):
    """
    Modelo de Devolución de Prenda (CU20).
    Cumple la Política de Negocio 2: Se retiene entre el 20% y 50% por costos operativos
    y se reembolsa entre el 50% y 80% del valor pagado (en efectivo o nota de crédito).
    """
    __tablename__ = "garment_returns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False, index=True)
    cashier_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    sale_id = Column(UUID(as_uuid=True), ForeignKey("sales.id", ondelete="RESTRICT"), nullable=False, index=True)
    variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    original_item_amount = Column(Numeric(10, 2), nullable=False)
    retention_percentage = Column(Numeric(5, 2), nullable=False)
    retention_amount = Column(Numeric(10, 2), nullable=False)
    refund_amount = Column(Numeric(10, 2), nullable=False)
    refund_method = Column(String(30), nullable=False)
    credit_note_code = Column(String(64), nullable=True, unique=True, index=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    company = relationship("Company")
    branch = relationship("Branch")
    cashier = relationship("User", foreign_keys=[cashier_id])
    sale = relationship("Sale")
    variant = relationship("ProductVariant", foreign_keys=[variant_id])
