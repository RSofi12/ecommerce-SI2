import uuid
from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class InventoryTransfer(Base):
    __tablename__ = "inventory_transfers"
    __table_args__ = (
        CheckConstraint("from_branch_id != to_branch_id", name="chk_transfer_different_branches"),
        CheckConstraint(
            "status IN ('SOLICITADO', 'EN_TRANSITO', 'COMPLETADO', 'CANCELADO')",
            name="chk_transfer_status",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    transfer_number = Column(String(50), nullable=False)
    from_branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False, index=True)
    to_branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="EN_TRANSITO", server_default="EN_TRANSITO", index=True)
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    received_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    requested_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    received_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    from_branch = relationship("Branch", foreign_keys=[from_branch_id])
    to_branch = relationship("Branch", foreign_keys=[to_branch_id])
    requester = relationship("User", foreign_keys=[requested_by])
    receiver = relationship("User", foreign_keys=[received_by])
    items = relationship("InventoryTransferItem", back_populates="transfer", cascade="all, delete-orphan")


class InventoryTransferItem(Base):
    __tablename__ = "inventory_transfer_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_transfer_item_quantity_positive"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    transfer_id = Column(UUID(as_uuid=True), ForeignKey("inventory_transfers.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    received_quantity = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    transfer = relationship("InventoryTransfer", back_populates="items")
    variant = relationship("ProductVariant")
