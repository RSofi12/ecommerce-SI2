import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class GarmentExchange(Base):
    """
    Modelo de Cambio de Prenda por Talla o Modelo (CU19).
    Cumple la Política de Negocio 1: Si la nueva prenda tiene mayor precio,
    el cambio se consolida ÚNICAMENTE si el cliente abona la diferencia.
    """
    __tablename__ = "garment_exchanges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False, index=True)
    cashier_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    sale_id = Column(UUID(as_uuid=True), ForeignKey("sales.id", ondelete="RESTRICT"), nullable=False, index=True)
    original_variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=False)
    new_variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=False)
    price_difference = Column(Numeric(10, 2), nullable=False)
    difference_paid = Column(Boolean, nullable=False, default=False)
    payment_method = Column(String(30), nullable=True)
    status = Column(String(30), nullable=False, default="COMPLETED")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    company = relationship("Company")
    branch = relationship("Branch")
    cashier = relationship("User", foreign_keys=[cashier_id])
    sale = relationship("Sale")
    original_variant = relationship("ProductVariant", foreign_keys=[original_variant_id])
    new_variant = relationship("ProductVariant", foreign_keys=[new_variant_id])
