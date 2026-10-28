from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class CheckoutMethodEnum(str, Enum):
    cash = "cash"
    stripe = "stripe"


class CashPaymentRequest(BaseModel):
    pickup_branch_id: UUID | None = None
    delivery_type: str = "RETIRO_TIENDA"
    shipping_address: str | None = None


class StripePaymentRequest(BaseModel):
    pickup_branch_id: UUID | None = None
    delivery_type: str = "RETIRO_TIENDA"
    shipping_address: str | None = None


class StripeCheckoutResponse(BaseModel):
    order_id: str
    client_secret: str
    payment_intent_id: str
    pickup_expires_at: str
    delivery_type: str = "RETIRO_TIENDA"
    shipping_address: str | None = None
    tracking_number: str | None = None


class CollectCashRequest(BaseModel):
    pickup_code: str
