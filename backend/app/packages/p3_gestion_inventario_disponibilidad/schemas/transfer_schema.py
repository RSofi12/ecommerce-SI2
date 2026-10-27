from datetime import datetime
from enum import Enum
from uuid import UUID
from pydantic import BaseModel, Field


class TransferStatusEnum(str, Enum):
    solicitado = "SOLICITADO"
    en_transito = "EN_TRANSITO"
    completado = "COMPLETADO"
    cancelado = "CANCELADO"


class TransferItemCreate(BaseModel):
    variant_id: UUID
    quantity: int = Field(gt=0, description="Cantidad a transferir (mayor a 0)")


class InventoryTransferCreate(BaseModel):
    from_branch_id: UUID
    to_branch_id: UUID
    items: list[TransferItemCreate] = Field(min_length=1, description="Lista de prendas y cantidades a transferir")
    notes: str | None = None


class InventoryTransferReceive(BaseModel):
    notes: str | None = None


class InventoryTransferCancel(BaseModel):
    reason: str | None = None


class InventoryTransferItemRead(BaseModel):
    id: UUID
    variant_id: UUID
    variant_sku: str | None = None
    product_name: str | None = None
    size_name: str | None = None
    color_name: str | None = None
    quantity: int
    received_quantity: int | None = None

    model_config = {"from_attributes": True}


class InventoryTransferRead(BaseModel):
    id: UUID
    tenant_id: UUID
    transfer_number: str
    from_branch_id: UUID
    from_branch_name: str | None = None
    to_branch_id: UUID
    to_branch_name: str | None = None
    status: str
    requested_by: UUID
    requested_by_name: str | None = None
    received_by: UUID | None = None
    received_by_name: str | None = None
    requested_at: datetime
    received_at: datetime | None = None
    notes: str | None = None
    items: list[InventoryTransferItemRead] = []

    model_config = {"from_attributes": True}
