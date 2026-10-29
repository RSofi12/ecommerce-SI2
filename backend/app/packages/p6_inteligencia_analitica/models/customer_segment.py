import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class CustomerSegment(Base):
    """
    Segmentación K-Means de Clientes (CU27, CU28).
    Asocia a cada cliente con un cluster de comportamiento (RFM + Tasa de Devoluciones).
    """
    __tablename__ = "customer_segments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    cluster_id = Column(Integer, nullable=False)
    segment_label = Column(String(64), nullable=False)
    recency_days = Column(Integer, nullable=True)
    frequency_count = Column(Integer, nullable=True)
    monetary_total = Column(Numeric(10, 2), nullable=True)
    return_rate = Column(Numeric(5, 2), nullable=True)
    assigned_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    company = relationship("Company")
    user = relationship("User")
