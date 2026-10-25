import uuid
from sqlalchemy import Column, Integer, DateTime, JSON, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class CatalogCache(Base):
    __tablename__ = "catalog_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True)
    version = Column(Integer, default=1, nullable=False)
    payload = Column(JSON, nullable=False)
    cached_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
