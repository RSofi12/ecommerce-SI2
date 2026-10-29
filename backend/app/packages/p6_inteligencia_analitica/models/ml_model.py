import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class MLModel(Base):
    """
    Registro y auditoría de modelos de Machine Learning (CU25, CU26, CU27).
    Guarda versiones, hiperparámetros y métricas de desempeño (R2, MAE, Silhouette).
    """
    __tablename__ = "ml_models"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    model_type = Column(String(50), nullable=False)  # DEMAND_REGRESSION, KMEANS_CLUSTERING
    version = Column(String(30), nullable=False)
    metrics = Column(JSON, nullable=False)
    model_path = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    trained_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    company = relationship("Company")
