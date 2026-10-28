from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_roles
from app.core.database import get_db
from app.core.tenant_context import get_tenant_id_from_header
from app.schemas.enums import RolEnum
from app.packages.p4_gestion_compras_reservas.schemas.payment_schema import (
    CashPaymentRequest,
    StripeCheckoutResponse,
    StripePaymentRequest,
)
from app.packages.p4_gestion_compras_reservas.services.order_service import (
    checkout_cash,
    create_stripe_payment,
    create_stripe_payment_for_order,
    process_stripe_event,
)
from app.utils.response import response


router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/cash/checkout")
async def cash_checkout_route(
    payload: CashPaymentRequest,
    db: Session = Depends(get_db),
    tenant_id: UUID | None = Depends(get_tenant_id_from_header),
    current_user: dict = Depends(require_roles(RolEnum.cliente)),
):
    try:
        order = checkout_cash(
            db=db,
            user_id=UUID(current_user["sub"]),
            pickup_branch_id=payload.pickup_branch_id,
            tenant_id=tenant_id,
            delivery_type=payload.delivery_type,
            shipping_address=payload.shipping_address,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return response(status_code=201, message="Pago en efectivo procesado exitosamente", data=order)


@router.post("/stripe/checkout")
async def stripe_checkout_route(
    payload: StripePaymentRequest,
    db: Session = Depends(get_db),
    tenant_id: UUID | None = Depends(get_tenant_id_from_header),
    current_user: dict = Depends(require_roles(RolEnum.cliente)),
):
    try:
        order, client_secret, payment_intent_id = create_stripe_payment(
            db=db,
            user_id=UUID(current_user["sub"]),
            pickup_branch_id=payload.pickup_branch_id,
            tenant_id=tenant_id,
            delivery_type=payload.delivery_type,
            shipping_address=payload.shipping_address,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return response(
        status_code=201,
        message="Pago con Stripe iniciado exitosamente",
        data=StripeCheckoutResponse(
            order_id=str(order["id"]),
            client_secret=client_secret,
            payment_intent_id=payment_intent_id,
            pickup_expires_at=order["pickup_expires_at"].isoformat() if order.get("pickup_expires_at") else "",
            delivery_type=order.get("delivery_type", "RETIRO_TIENDA"),
            shipping_address=order.get("shipping_address"),
            tracking_number=order.get("tracking_number"),
        ).model_dump(),
    )


@router.post("/stripe/orders/{order_id}")
async def stripe_order_payment_route(
    order_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID | None = Depends(get_tenant_id_from_header),
    current_user: dict = Depends(require_roles(RolEnum.cliente)),
):
    try:
        order, client_secret, payment_intent_id = create_stripe_payment_for_order(
            db, UUID(current_user["sub"]), order_id, tenant_id=tenant_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return response(
        status_code=200,
        message="Pago con Stripe iniciado exitosamente",
        data=StripeCheckoutResponse(
            order_id=str(order["id"]),
            client_secret=client_secret,
            payment_intent_id=payment_intent_id,
            pickup_expires_at=order["pickup_expires_at"].isoformat() if order.get("pickup_expires_at") else "",
            delivery_type=order.get("delivery_type", "RETIRO_TIENDA"),
            shipping_address=order.get("shipping_address"),
            tracking_number=order.get("tracking_number"),
        ).model_dump(),
    )


@router.post("/stripe/webhook")
async def stripe_webhook_route(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
    db: Session = Depends(get_db),
):
    payload = await request.body()
    try:
        import stripe
        from app.core.config import settings

        if not settings.stripe_webhook_secret or not stripe_signature:
            raise ValueError("Falta la firma o el secreto del webhook")
        event = stripe.Webhook.construct_event(payload, stripe_signature, settings.stripe_webhook_secret)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Webhook inválido: {exc}") from exc

    try:
        process_stripe_event(db, event)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return {"received": True}
