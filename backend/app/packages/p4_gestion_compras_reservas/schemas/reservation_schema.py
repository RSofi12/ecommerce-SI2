from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ReservationStatusEnum(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    attended = "attended"
    purchase_pending = "purchase_pending"
    sold = "sold"
    not_sold = "not_sold"
    cancelled = "cancelled"
    expired = "expired"


class ReservationItemCreate(BaseModel):
    variant_id: UUID
    quantity: int = Field(gt=0, description="Cantidad a apartar (debe ser mayor a 0)")


class ReservationCreate(BaseModel):
    branch_id: UUID
    visit_date: date
    items: list[ReservationItemCreate] = Field(min_length=1)
    client_reservation_id: UUID | None = Field(default=None, description="UUIDv4 generado en cliente para contingencia offline e idempotencia")

    @field_validator("visit_date")
    @classmethod
    def validate_visit_date(cls, v: date) -> date:
        today = date.today()
        if v < today:
            raise ValueError("La fecha de visita no puede ser anterior a la fecha actual.")
        if v > today + timedelta(days=7):
            raise ValueError("La fecha de reserva no puede exceder los 7 días de anticipación.")
        return v


class ReservationDecisionRequest(BaseModel):
    purchase: bool


class ReservationItemRead(BaseModel):
    id: UUID
    tenant_id: UUID | None = None
    reservation_id: UUID
    variant_id: UUID
    quantity: int
    unit_price: Decimal
    line_total: Decimal
    product_id: UUID
    product_name: str
    variant_sku: str
    size_id: UUID | None = None
    color_id: UUID | None = None
    size_name: str | None = None
    color_name: str | None = None
    image_url: str | None = None
    image_public_id: str | None = None

    model_config = {"from_attributes": True}


class ReservationRead(BaseModel):
    id: UUID
    tenant_id: UUID | None = None
    branch_id: UUID
    branch_name: str
    user_id: UUID
    user_name: str
    cart_id: UUID | None = None
    visit_date: date
    expires_at: date
    status: ReservationStatusEnum
    total_amount: Decimal
    item_count: int
    reservation_code: str = Field(default="", description="Código alfanumérico amigable de reserva, ej: RES-A1B2C3D4")
    qr_payload: str = Field(default="", description="Payload para escaneo o renderizado de código QR")
    resolved_at: datetime | None = None
    resolved_by: UUID | None = None
    resolution_note: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    items: list[ReservationItemRead] = Field(default_factory=list)

    model_config = {"from_attributes": True}
