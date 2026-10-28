from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class OrderStatusEnum(str, Enum):
    pending = "pending"
    paid = "paid"
    failed = "failed"
    cancelled = "cancelled"


class PaymentMethodEnum(str, Enum):
    cash = "cash"
    stripe = "stripe"


class PaymentStatusEnum(str, Enum):
    pending = "pending"
    paid = "paid"
    failed = "failed"


class FulfillmentStatusEnum(str, Enum):
    pending_pickup = "pending_pickup"
    ready_for_pickup = "ready_for_pickup"
    ready_for_dispatch = "ready_for_dispatch"
    dispatched = "dispatched"
    collected = "collected"
    delivered = "delivered"
    expired = "expired"
    cancelled = "cancelled"


class DeliveryTypeEnum(str, Enum):
    store_pickup = "RETIRO_TIENDA"
    home_delivery = "ENVIO_DOMICILIO"


class CashCheckoutCreate(BaseModel):
    cash_reference: str | None = None
    delivery_type: str = "RETIRO_TIENDA"
    shipping_address: str | None = None


class StripeCheckoutCreate(BaseModel):
    currency: str | None = None
    delivery_type: str = "RETIRO_TIENDA"
    shipping_address: str | None = None


class OrderItemRead(BaseModel):
    id: UUID
    order_id: UUID
    tenant_id: UUID | None = None
    variant_id: UUID
    reservation_id: UUID | None = None
    quantity: int
    unit_price: Decimal
    original_unit_price: Decimal | None = None
    discount_amount: Decimal = Decimal("0.00")
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


class OrderRead(BaseModel):
    id: UUID
    tenant_id: UUID | None = None
    user_id: UUID
    status: OrderStatusEnum
    payment_method: PaymentMethodEnum
    payment_status: PaymentStatusEnum
    stripe_payment_intent_id: str | None = None
    cash_reference: str | None = None
    pickup_branch_id: UUID | None = None
    pickup_expires_at: datetime | None = None
    pickup_code: str | None = None
    fulfillment_status: FulfillmentStatusEnum | None = None
    delivery_type: str = "RETIRO_TIENDA"
    shipping_address: str | None = None
    tracking_number: str | None = None
    dispatched_at: datetime | None = None
    dispatched_by: UUID | None = None
    subtotal: Decimal
    discount_amount: Decimal
    promotion_code_id: UUID | None = None
    total_amount: Decimal
    currency: str
    created_at: datetime
    updated_at: datetime | None = None
    items: list[OrderItemRead] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class OrderDispatchRequest(BaseModel):
    shipping_notes: str | None = None


class OrderDispatchResponse(BaseModel):
    order_id: UUID
    tenant_id: UUID | None = None
    tracking_number: str
    delivery_type: str
    fulfillment_status: str
    dispatched_at: datetime
    dispatched_by: UUID | None = None
    message: str
