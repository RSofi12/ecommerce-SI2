import uuid
from sqlalchemy import Column, String, Boolean, DateTime, JSON, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class OfflineOperation(Base):
    __tablename__ = "offline_operations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id", ondelete="SET NULL"), nullable=True)
    operation_type = Column(String(50), nullable=False)
    client_operation_id = Column(String(100), nullable=True, index=True)
    payload = Column(JSON, nullable=False)
    synced = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    synced_at = Column(DateTime(timezone=True), nullable=True)
