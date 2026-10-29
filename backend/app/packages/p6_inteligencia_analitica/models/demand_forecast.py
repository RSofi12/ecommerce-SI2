import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class DemandForecast(Base):
    """
    Predicciones de Demanda por Variante y Periodo (CU26, CU28).
    Almacena las proyecciones calculadas con Scikit-Learn (RandomForestRegressor)
    para renderizado inmediato en dashboards ejecutivos sin sobrecargar el servidor.
    """
    __tablename__ = "demand_forecasts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id", ondelete="SET NULL"), nullable=True)
    forecast_period = Column(String(30), nullable=False)
    predicted_units = Column(Integer, nullable=False)
    confidence_lower = Column(Integer, nullable=True)
    confidence_upper = Column(Integer, nullable=True)
    algorithm_used = Column(String(50), nullable=False, default="RandomForestRegressor")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    company = relationship("Company")
    variant = relationship("ProductVariant")
    branch = relationship("Branch")
