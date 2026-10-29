import uuid

from sqlalchemy import Column, DateTime, ForeignKey, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class SyncOperation(Base):
    """
    Registro de idempotencia y trazabilidad de operaciones sincronizadas (CU17, CU18).
    Garantiza que ventas y cobros generados offline no se dupliquen al sincronizar por lotes.
    """
    __tablename__ = "sync_operations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    client_operation_id = Column(String(100), nullable=False, unique=True, index=True)
    operation_type = Column(String(50), nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String(30), nullable=False, default="PROCESADO")
    synced_at = Column(DateTime(timezone=True), nullable=True, server_default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    company = relationship("Company")
