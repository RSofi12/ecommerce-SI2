import uuid

from sqlalchemy import Column, ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.packages.p0_saas_plataforma.models.company import Company  # noqa: F401


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True)
    cart_id = Column(UUID(as_uuid=True), ForeignKey("carts.id"), nullable=False, index=True)
    reservation_id = Column(UUID(as_uuid=True), ForeignKey("reservations.id"), nullable=True, index=True)
    variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)

    cart = relationship("Cart", back_populates="items")
    variant = relationship("ProductVariant")
    company = relationship("Company", foreign_keys=[tenant_id])

    __table_args__ = (UniqueConstraint("cart_id", "variant_id", name="uq_cart_item_cart_variant"),)
