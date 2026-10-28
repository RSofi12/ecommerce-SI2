import secrets
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.packages.p4_gestion_compras_reservas.models.cart import Cart
from app.packages.p4_gestion_compras_reservas.models.cart_item import CartItem
from app.packages.p3_gestion_inventario_disponibilidad.models.inventory import Inventory
from app.packages.p3_gestion_inventario_disponibilidad.models.inventory_movement import InventoryMovement
from app.packages.p4_gestion_compras_reservas.models.order import Order
from app.packages.p4_gestion_compras_reservas.models.order_item import OrderItem
from app.packages.p4_gestion_compras_reservas.models.payment_attempt import PaymentAttempt
from app.packages.p2_gestion_productos_catalogo.models.product import Product
from app.packages.p2_gestion_productos_catalogo.models.product_variant import ProductVariant
from app.packages.p4_gestion_compras_reservas.models.promotion_code import PromotionCode
from app.packages.p4_gestion_compras_reservas.models.reservation import Reservation
from app.packages.p2_gestion_productos_catalogo.models.size import Size
from app.packages.p2_gestion_productos_catalogo.models.color import Color
from app.packages.p4_gestion_compras_reservas.models.stripe_event import StripeEvent
from app.packages.p1_gestion_usuarios_acceso.models.branch import Branch
from app.packages.p1_gestion_usuarios_acceso.models.user import User
from app.packages.p4_gestion_compras_reservas.schemas.cart_schema import CartStatusEnum
from app.packages.p3_gestion_inventario_disponibilidad.schemas.inventory_schema import InventoryMovementTypeEnum
from app.packages.p4_gestion_compras_reservas.schemas.order_schema import (
    DeliveryTypeEnum,
    FulfillmentStatusEnum,
    OrderItemRead,
    OrderRead,
    OrderStatusEnum,
    PaymentMethodEnum,
    PaymentStatusEnum,
)
from app.packages.p4_gestion_compras_reservas.schemas.reservation_schema import ReservationStatusEnum
from app.packages.p4_gestion_compras_reservas.services.pricing_service import discounted_price, discount_amount
from app.packages.p4_gestion_compras_reservas.services.cart_service import refresh_cart_totals
from app.packages.p4_gestion_compras_reservas.services.promotion_service import add_usage, validate_for_user
from app.packages.p4_gestion_compras_reservas.services.reservation_service import transition_reservation
from app.services.recommendation_service import record_completed_order_interactions
from app.services.notification_service import notify_low_stock, notify_order_event


STRIPE_RESERVATION_MINUTES = 30
CASH_RESERVATION_HOURS = 24


def _cart_rows(db: Session, cart_id: UUID):
    return db.query(
        CartItem.variant_id.label("variant_id"), CartItem.quantity.label("quantity"), CartItem.reservation_id.label("reservation_id"), ProductVariant.price.label("original_unit_price"),
        Product.discount_type.label("discount_type"), Product.discount_value.label("discount_value"),
        Product.id.label("product_id"), Product.name.label("product_name"), ProductVariant.sku.label("variant_sku"),
        ProductVariant.size_id.label("size_id"), ProductVariant.color_id.label("color_id"), ProductVariant.image_url.label("image_url"),
        ProductVariant.image_public_id.label("image_public_id"),
    ).join(ProductVariant, ProductVariant.id == CartItem.variant_id).join(Product, Product.id == ProductVariant.product_id).filter(CartItem.cart_id == cart_id).all()


def _row_unit_price(row) -> Decimal:
    return discounted_price(row.original_unit_price, row.discount_type, row.discount_value)


def _serialize_order(db: Session, order: Order) -> OrderRead:
    items = [OrderItemRead.model_validate({
        "id": row.id, "order_id": row.order_id, "tenant_id": row.tenant_id,
        "variant_id": row.variant_id, "quantity": row.quantity,
        "unit_price": row.unit_price, "line_total": row.line_total, "product_id": row.product_id,
        "product_name": row.product_name, "variant_sku": row.variant_sku, "size_id": row.size_id,
        "color_id": row.color_id, "size_name": row.size_id and db.query(Size.name).filter(Size.id == row.size_id).scalar(),
        "color_name": row.color_id and db.query(Color.name).filter(Color.id == row.color_id).scalar(),
        "image_url": row.image_url, "image_public_id": row.image_public_id,
    }).model_dump() for row in order.items]
    return OrderRead.model_validate({
        "id": order.id, "tenant_id": order.tenant_id, "user_id": order.user_id,
        "status": order.status, "payment_method": order.payment_method,
        "payment_status": order.payment_status, "stripe_payment_intent_id": order.stripe_payment_intent_id,
        "cash_reference": order.cash_reference, "pickup_branch_id": order.pickup_branch_id,
        "pickup_expires_at": order.pickup_expires_at, "pickup_code": order.pickup_code,
        "fulfillment_status": order.fulfillment_status,
        "delivery_type": order.delivery_type or DeliveryTypeEnum.store_pickup.value,
        "shipping_address": order.shipping_address,
        "tracking_number": order.tracking_number,
        "dispatched_at": order.dispatched_at,
        "dispatched_by": order.dispatched_by,
        "subtotal": order.subtotal,
        "discount_amount": order.discount_amount, "promotion_code_id": order.promotion_code_id,
        "total_amount": order.total_amount, "currency": order.currency,
        "created_at": order.created_at, "updated_at": order.updated_at, "items": items,
    })


def list_orders(db: Session, user_id: UUID, tenant_id: UUID | None = None):
    expire_due_orders(db)
    query = db.query(Order).filter(Order.user_id == user_id)
    if tenant_id:
        query = query.filter(Order.tenant_id == tenant_id)
    return [_serialize_order(db, order).model_dump() for order in query.order_by(Order.created_at.desc()).all()]


def list_orders_by_branch(db: Session, branch_id: UUID, tenant_id: UUID | None = None):
    expire_due_orders(db)
    query = db.query(Order).filter(Order.pickup_branch_id == branch_id)
    if tenant_id:
        query = query.filter(Order.tenant_id == tenant_id)
    orders = query.order_by(Order.created_at.desc()).all()
    return [_serialize_order(db, order).model_dump() for order in orders]


def get_order(db: Session, user_id: UUID, order_id: UUID, tenant_id: UUID | None = None):
    expire_due_orders(db)
    query = db.query(Order).filter(Order.id == order_id, Order.user_id == user_id)
    if tenant_id:
        query = query.filter(Order.tenant_id == tenant_id)
    order = query.first()
    return _serialize_order(db, order).model_dump() if order else None


def mark_order_ready(db: Session, order_id: UUID, branch_id: UUID, tenant_id: UUID | None = None):
    query = db.query(Order).filter(Order.id == order_id, Order.pickup_branch_id == branch_id)
    if tenant_id:
        query = query.filter(Order.tenant_id == tenant_id)
    order = query.with_for_update().first()
    if not order:
        return None
    if order.payment_status != PaymentStatusEnum.paid:
        raise ValueError("El pedido debe estar pagado antes de marcarlo como listo")
    if order.fulfillment_status not in (FulfillmentStatusEnum.pending_pickup, FulfillmentStatusEnum.ready_for_dispatch):
        raise ValueError("El pedido no está en estado válido para preparación")
    order.fulfillment_status = FulfillmentStatusEnum.ready_for_pickup
    db.commit()
    db.refresh(order)
    notify_order_event(db, order.id, order.user_id, "ready_for_pickup")
    return _serialize_order(db, order).model_dump()


def _locked_cart(db: Session, user_id: UUID) -> Cart:
    cart = db.query(Cart).filter(Cart.user_id == user_id).with_for_update().first()
    if not cart:
        raise ValueError("No tienes un carrito activo")
    return cart


def _reserve_inventory(db: Session, rows, branch_id: UUID, user_id: UUID) -> None:
    for row in rows:
        inventory = db.query(Inventory).filter(Inventory.variant_id == row.variant_id, Inventory.branch_id == branch_id).with_for_update().first()
        if not inventory:
            raise ValueError("No hay stock suficiente en la sucursal seleccionada")
        if row.reservation_id:
            reservation = db.query(Reservation).filter(Reservation.id == row.reservation_id, Reservation.user_id == user_id).with_for_update().first()
            if not reservation or reservation.status != ReservationStatusEnum.purchase_pending or reservation.branch_id != branch_id:
                raise ValueError("La reserva ya no está disponible para este checkout")
            if (inventory.reserved_quantity or 0) < row.quantity:
                raise ValueError("La reserva ya no tiene stock suficiente")
        else:
            if inventory.quantity - inventory.reserved_quantity < row.quantity:
                raise ValueError("No hay stock suficiente en la sucursal seleccionada")
            inventory.reserved_quantity += row.quantity


def _new_order(
    db: Session,
    cart: Cart,
    user_id: UUID,
    branch_id: UUID | None,
    method: PaymentMethodEnum,
    tenant_id: UUID | None = None,
    delivery_type: str = "RETIRO_TIENDA",
    shipping_address: str | None = None,
) -> Order:
    resolved_tenant_id = tenant_id or cart.tenant_id
    if not resolved_tenant_id:
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.tenant_id:
            resolved_tenant_id = user.tenant_id
        elif branch_id:
            branch = db.query(Branch).filter(Branch.id == branch_id).first()
            if branch and branch.tenant_id:
                resolved_tenant_id = branch.tenant_id

    resolved_branch_id = branch_id
    if not resolved_branch_id:
        query_branch = db.query(Branch).filter(Branch.is_active == True)
        if resolved_tenant_id:
            query_branch = query_branch.filter(Branch.tenant_id == resolved_tenant_id)
        default_branch = query_branch.filter(Branch.is_default == True).first() or query_branch.first()
        if default_branch:
            resolved_branch_id = default_branch.id
        else:
            raise ValueError("No hay sucursales disponibles para procesar el pedido")

    if cart.promotion_code_id:
        code = db.query(PromotionCode).filter(PromotionCode.id == cart.promotion_code_id).first()
        if not code:
            raise ValueError("El código promocional ya no existe")
        validate_for_user(db, code.code, user_id, resolved_branch_id)
    refresh_cart_totals(db, cart)
    rows = _cart_rows(db, cart.id)
    if not rows:
        raise ValueError("El carrito está vacío")
    _reserve_inventory(db, rows, resolved_branch_id, user_id)
    subtotal = sum(Decimal(str(row.original_unit_price)) * row.quantity for row in rows)
    discount = Decimal(str(cart.discount_amount or 0))
    expires = datetime.now(timezone.utc) + timedelta(minutes=STRIPE_RESERVATION_MINUTES if method == PaymentMethodEnum.stripe else CASH_RESERVATION_HOURS * 60)
    order = Order(
        tenant_id=resolved_tenant_id,
        user_id=user_id,
        status=OrderStatusEnum.pending,
        payment_method=method,
        payment_status=PaymentStatusEnum.pending,
        pickup_branch_id=resolved_branch_id,
        pickup_expires_at=expires,
        promotion_code_id=cart.promotion_code_id,
        pickup_code=secrets.token_urlsafe(9),
        fulfillment_status=FulfillmentStatusEnum.pending_pickup,
        delivery_type=delivery_type,
        shipping_address=shipping_address,
        subtotal=subtotal,
        discount_amount=discount,
        total_amount=max(subtotal - discount, Decimal("0.00")),
        currency=settings.stripe_currency.lower(),
    )
    db.add(order)
    db.flush()
    for row in rows:
        unit_price = _row_unit_price(row)
        db.add(OrderItem(
            tenant_id=resolved_tenant_id,
            order_id=order.id,
            variant_id=row.variant_id,
            quantity=row.quantity,
            unit_price=unit_price,
            reservation_id=row.reservation_id,
            line_total=unit_price * row.quantity,
            product_id=row.product_id,
            product_name=row.product_name,
            variant_sku=row.variant_sku,
            size_id=row.size_id,
            color_id=row.color_id,
            image_url=row.image_url,
            image_public_id=row.image_public_id,
        ))
    cart.tenant_id = resolved_tenant_id
    cart.status = CartStatusEnum.checkout_pending
    return order


def checkout_cash(
    db: Session,
    user_id: UUID,
    pickup_branch_id: UUID | None = None,
    tenant_id: UUID | None = None,
    delivery_type: str = "RETIRO_TIENDA",
    shipping_address: str | None = None,
):
    try:
        expire_due_orders(db)
        cart = _locked_cart(db, user_id)
        if cart.status == CartStatusEnum.checkout_pending:
            raise ValueError("El carrito tiene un checkout pendiente")
        order = _new_order(
            db, cart, user_id, pickup_branch_id, PaymentMethodEnum.cash,
            tenant_id=tenant_id, delivery_type=delivery_type, shipping_address=shipping_address,
        )
        db.commit()
        db.refresh(order)
        notify_order_event(db, order.id, order.user_id, "pending")
        return _serialize_order(db, order).model_dump()
    except Exception:
        db.rollback()
        raise


def create_stripe_payment(
    db: Session,
    user_id: UUID,
    pickup_branch_id: UUID | None = None,
    tenant_id: UUID | None = None,
    delivery_type: str = "RETIRO_TIENDA",
    shipping_address: str | None = None,
):
    if delivery_type == DeliveryTypeEnum.home_delivery.value and not shipping_address:
        raise ValueError("La dirección de entrega es obligatoria para envío a domicilio")
    try:
        expire_due_orders(db)
        cart = _locked_cart(db, user_id)
        existing = db.query(PaymentAttempt).join(Order).filter(PaymentAttempt.cart_id == cart.id, PaymentAttempt.status == "pending").with_for_update().first()
        if existing:
            order = db.query(Order).filter(Order.id == existing.order_id).one()
            attempt = existing
            db.commit()
        elif cart.status == CartStatusEnum.checkout_pending:
            raise ValueError("El carrito tiene un checkout pendiente")
        else:
            order = _new_order(
                db, cart, user_id, pickup_branch_id, PaymentMethodEnum.stripe,
                tenant_id=tenant_id, delivery_type=delivery_type, shipping_address=shipping_address,
            )
            attempt = PaymentAttempt(
                tenant_id=order.tenant_id,
                order_id=order.id,
                cart_id=cart.id,
                status="pending",
                idempotency_key=secrets.token_urlsafe(24),
            )
            db.add(attempt)
            db.commit()
    except Exception:
        db.rollback()
        raise
    try:
        import stripe
        if not settings.stripe_secret_key:
            raise ValueError("Stripe no está configurado")
        stripe.api_key = settings.stripe_secret_key
        amount = int((order.total_amount * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        metadata = {
            "order_id": str(order.id),
            "tenant_id": str(order.tenant_id or ""),
            "delivery_type": order.delivery_type or "RETIRO_TIENDA",
        }
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency=settings.stripe_currency.lower(),
            metadata=metadata,
            automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
            idempotency_key=attempt.idempotency_key,
        )
        attempt.stripe_payment_intent_id = intent.id
        order.stripe_payment_intent_id = intent.id
        db.commit()
        return _serialize_order(db, order).model_dump(), intent.client_secret, intent.id
    except Exception as exc:
        _release_order(db, order, PaymentStatusEnum.failed, FulfillmentStatusEnum.cancelled)
        attempt.status = "failed"
        db.commit()
        notify_order_event(db, order.id, order.user_id, "failed")
        raise ValueError(f"No se pudo iniciar el pago con Stripe: {exc}") from exc


def create_stripe_payment_for_order(db: Session, user_id: UUID, order_id: UUID, tenant_id: UUID | None = None):
    try:
        expire_due_orders(db)
        query = db.query(Order).filter(Order.id == order_id, Order.user_id == user_id)
        if tenant_id:
            query = query.filter(Order.tenant_id == tenant_id)
        order = query.with_for_update().first()
        if not order:
            raise ValueError("Pedido no encontrado")
        if (
            order.payment_status != PaymentStatusEnum.pending
            or order.fulfillment_status != FulfillmentStatusEnum.pending_pickup
        ):
            raise ValueError("El pedido no está pendiente de pago")

        attempt = (
            db.query(PaymentAttempt)
            .filter(PaymentAttempt.order_id == order.id, PaymentAttempt.status == "pending")
            .with_for_update()
            .first()
        )
        if not attempt and not order.stripe_payment_intent_id:
            cart = db.query(Cart).filter(Cart.user_id == order.user_id).first()
            if not cart:
                raise ValueError("El pedido no tiene un intento de pago reutilizable")
            attempt = PaymentAttempt(
                tenant_id=order.tenant_id,
                order_id=order.id,
                cart_id=cart.id,
                status="pending",
                idempotency_key=secrets.token_urlsafe(24),
            )
            db.add(attempt)
            order.payment_method = PaymentMethodEnum.stripe
            db.flush()
        db.commit()
    except Exception:
        db.rollback()
        raise

    try:
        import stripe

        if not settings.stripe_secret_key:
            raise ValueError("Stripe no está configurado")
        stripe.api_key = settings.stripe_secret_key

        existing_intent_id = order.stripe_payment_intent_id or (
            attempt.stripe_payment_intent_id if attempt else None
        )
        if existing_intent_id:
            intent = stripe.PaymentIntent.retrieve(existing_intent_id)
            if order.stripe_payment_intent_id != intent.id:
                order.stripe_payment_intent_id = intent.id
                db.commit()
        else:
            amount = int((order.total_amount * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
            metadata = {
                "order_id": str(order.id),
                "tenant_id": str(order.tenant_id or ""),
                "delivery_type": order.delivery_type or "RETIRO_TIENDA",
            }
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=order.currency.lower(),
                metadata=metadata,
                automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
                idempotency_key=attempt.idempotency_key,
            )
            attempt.stripe_payment_intent_id = intent.id
            order.stripe_payment_intent_id = intent.id
            db.commit()

        return _serialize_order(db, order).model_dump(), intent.client_secret, intent.id
    except Exception as exc:
        db.rollback()
        raise ValueError(f"No se pudo iniciar el pago con Stripe: {exc}") from exc


def _release_order(db: Session, order: Order, payment_status: PaymentStatusEnum, fulfillment_status: FulfillmentStatusEnum) -> None:
    reservation_ids = {item.reservation_id for item in order.items if item.reservation_id}
    for item in order.items:
        inventory = db.query(Inventory).filter(Inventory.variant_id == item.variant_id, Inventory.branch_id == order.pickup_branch_id).with_for_update().one()
        inventory.reserved_quantity -= item.quantity
    cart = db.query(Cart).filter(Cart.user_id == order.user_id).with_for_update().first()
    for reservation_id in reservation_ids:
        reservation = db.query(Reservation).filter(Reservation.id == reservation_id).with_for_update().first()
        if reservation and reservation.status == ReservationStatusEnum.purchase_pending:
            transition_reservation(reservation, ReservationStatusEnum.not_sold)
            reservation.cart_id = None
        if cart:
            db.query(CartItem).filter(CartItem.cart_id == cart.id, CartItem.reservation_id == reservation_id).delete(synchronize_session=False)
    order.payment_status = payment_status
    order.status = OrderStatusEnum.failed if payment_status == PaymentStatusEnum.failed else OrderStatusEnum.cancelled
    order.fulfillment_status = fulfillment_status
    if cart:
        cart.status = CartStatusEnum.active
    attempt = db.query(PaymentAttempt).filter(PaymentAttempt.order_id == order.id).first()
    if attempt:
        attempt.status = "failed"


def expire_due_orders(db: Session) -> None:
    expired = db.query(Order).filter(
        Order.payment_status == PaymentStatusEnum.pending,
        Order.fulfillment_status == FulfillmentStatusEnum.pending_pickup,
        Order.pickup_expires_at <= datetime.now(timezone.utc),
    ).with_for_update(skip_locked=True).all()
    if not expired:
        return

    intent_ids = [order.stripe_payment_intent_id for order in expired if order.stripe_payment_intent_id]
    for order in expired:
        _release_order(db, order, PaymentStatusEnum.failed, FulfillmentStatusEnum.expired)
    db.commit()
    for order in expired:
        notify_order_event(db, order.id, order.user_id, "expired")

    if not intent_ids or not settings.stripe_secret_key:
        return
    try:
        import stripe

        stripe.api_key = settings.stripe_secret_key
        for intent_id in intent_ids:
            try:
                stripe.PaymentIntent.cancel(intent_id)
            except Exception:
                pass
    except Exception:
        pass


def _consume_order(db: Session, order: Order, collected_by: UUID | None = None) -> None:
    reservation_ids = {item.reservation_id for item in order.items if item.reservation_id}
    for item in order.items:
        inventory = db.query(Inventory).filter(Inventory.variant_id == item.variant_id, Inventory.branch_id == order.pickup_branch_id).with_for_update().one()
        inventory.quantity -= item.quantity
        inventory.reserved_quantity -= item.quantity
        db.add(InventoryMovement(variant_id=item.variant_id, branch_id=order.pickup_branch_id,
               movement_type=InventoryMovementTypeEnum.outcome, quantity=item.quantity, created_by=collected_by,
               note=f"Pedido {order.id}"))
    order.payment_status = PaymentStatusEnum.paid
    order.status = OrderStatusEnum.paid
    order.fulfillment_status = FulfillmentStatusEnum.collected if collected_by else FulfillmentStatusEnum.pending_pickup
    for reservation_id in reservation_ids:
        reservation = db.query(Reservation).filter(Reservation.id == reservation_id).with_for_update().first()
        if reservation and reservation.status == ReservationStatusEnum.purchase_pending:
            transition_reservation(reservation, ReservationStatusEnum.sold)
            reservation.cart_id = None
    cart = db.query(Cart).filter(Cart.user_id == order.user_id).with_for_update().first()
    if cart:
        db.query(CartItem).filter(CartItem.cart_id == cart.id).delete(synchronize_session=False)
        cart.status = CartStatusEnum.active
        cart.promotion_code_id = None
        cart.subtotal = cart.discount_amount = cart.total_amount = Decimal("0.00")
    attempt = db.query(PaymentAttempt).filter(PaymentAttempt.order_id == order.id).first()
    if attempt:
        attempt.status = "succeeded"
    if order.promotion_code_id:
        add_usage(db, order.promotion_code_id, order.user_id)
    record_completed_order_interactions(db, order)


def cancel_order(db: Session, user_id: UUID, order_id: UUID, tenant_id: UUID | None = None):
    try:
        query = db.query(Order).filter(Order.id == order_id, Order.user_id == user_id)
        if tenant_id:
            query = query.filter(Order.tenant_id == tenant_id)
        order = query.with_for_update().first()
        if not order:
            return None
        if order.payment_status != PaymentStatusEnum.pending or order.fulfillment_status != FulfillmentStatusEnum.pending_pickup:
            raise ValueError("El pedido no se puede cancelar")
        if order.payment_method == PaymentMethodEnum.stripe and order.stripe_payment_intent_id:
            import stripe
            if not settings.stripe_secret_key:
                raise ValueError("Stripe no está configurado")
            stripe.api_key = settings.stripe_secret_key
            stripe.PaymentIntent.cancel(order.stripe_payment_intent_id)
        _release_order(db, order, PaymentStatusEnum.failed, FulfillmentStatusEnum.cancelled)
        db.commit()
        notify_order_event(db, order.id, order.user_id, "cancelled")
        return _serialize_order(db, order).model_dump()
    except Exception:
        db.rollback()
        raise


def collect_cash(db: Session, order_id: UUID, pickup_code: str, cashier_branch_id: UUID | None, cashier_id: UUID, tenant_id: UUID | None = None):
    try:
        query = db.query(Order).filter(Order.id == order_id)
        if tenant_id:
            query = query.filter(Order.tenant_id == tenant_id)
        order = query.with_for_update().first()
        if not order or cashier_branch_id != order.pickup_branch_id:
            raise ValueError("Pedido no encontrado")
        if order.payment_method != PaymentMethodEnum.cash or order.pickup_code != pickup_code:
            raise ValueError("Código de retiro inválido")
        if order.payment_status != PaymentStatusEnum.pending or order.pickup_expires_at < datetime.now(timezone.utc):
            raise ValueError("El pedido no está disponible para cobro")
        _consume_order(db, order, cashier_id)
        db.commit()
        for item in order.items:
            inventory = db.query(Inventory).filter(Inventory.variant_id == item.variant_id, Inventory.branch_id == order.pickup_branch_id).first()
            if inventory:
                notify_low_stock(db, inventory)
        notify_order_event(db, order.id, order.user_id, "collected")
        return _serialize_order(db, order).model_dump()
    except Exception:
        db.rollback()
        raise


def process_stripe_event(db: Session, event) -> None:
    event_id = event["id"]
    try:
        with db.begin_nested():
            db.add(StripeEvent(stripe_event_id=event_id))
            db.flush()
    except IntegrityError:
        return
    data = event["data"]["object"]
    order = db.query(Order).filter(Order.stripe_payment_intent_id == data.get("id")).with_for_update().first()
    if order and order.payment_method == PaymentMethodEnum.stripe and order.payment_status == PaymentStatusEnum.pending:
        if event["type"] == "payment_intent.succeeded":
            expected_amount = int((order.total_amount * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
            if data.get("amount") != expected_amount or data.get("currency", "").lower() != order.currency or data.get("metadata", {}).get("order_id") != str(order.id):
                raise ValueError("El PaymentIntent no coincide con el pedido")
            _consume_order(db, order)
            # CU12: Asignar tracking_number y estado de preparación según modalidad
            if not order.tracking_number:
                date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
                rand_code = secrets.token_hex(2).upper()
                order.tracking_number = f"DSP-{date_str}-{rand_code}"
            if order.delivery_type == DeliveryTypeEnum.home_delivery.value:
                order.fulfillment_status = FulfillmentStatusEnum.ready_for_dispatch
            else:
                order.fulfillment_status = FulfillmentStatusEnum.ready_for_pickup
        elif event["type"] in {"payment_intent.payment_failed", "payment_intent.canceled"}:
            _release_order(db, order, PaymentStatusEnum.failed, FulfillmentStatusEnum.cancelled)
    db.commit()
    if order and order.payment_status == PaymentStatusEnum.paid:
        for item in order.items:
            inventory = db.query(Inventory).filter(Inventory.variant_id == item.variant_id, Inventory.branch_id == order.pickup_branch_id).first()
            if inventory:
                notify_low_stock(db, inventory)
        notify_order_event(db, order.id, order.user_id, "paid")
    elif order and order.payment_status == PaymentStatusEnum.failed:
        notify_order_event(db, order.id, order.user_id, "failed")


def dispatch_order(
    db: Session,
    order_id: UUID,
    dispatcher_id: UUID,
    tenant_id: UUID | None = None,
    shipping_notes: str | None = None,
) -> dict:
    """
    CU12 - Despacho Condicionado:
    Política de Negocio 3: El despacho de prendas o entrega digital se efectúa
    ÚNICAMENTE cuando el pago con Stripe está confirmado (payment_status = 'paid').
    """
    query = db.query(Order).filter(Order.id == order_id)
    if tenant_id:
        query = query.filter(Order.tenant_id == tenant_id)
    order = query.with_for_update().first()

    if not order:
        raise ValueError("Pedido no encontrado o no pertenece a la empresa actual")

    # POLÍTICA DE NEGOCIO 3 INVIOLABLE: Bloqueo estricto si no está pagado
    if order.payment_status != PaymentStatusEnum.paid:
        raise ValueError(
            "Despacho bloqueado por Política de Negocio 3: El pedido debe estar pagado (payment_status = 'paid') "
            f"en Stripe para autorizar el despacho de prendas. Estado actual: '{order.payment_status.value}'"
        )

    if order.fulfillment_status == FulfillmentStatusEnum.dispatched or order.dispatched_at is not None:
        raise ValueError("El pedido ya ha sido despachado previamente")

    if order.fulfillment_status in {FulfillmentStatusEnum.cancelled, FulfillmentStatusEnum.expired}:
        raise ValueError(f"No se puede despachar un pedido cancelado o expirado (estado: '{order.fulfillment_status.value}')")

    # Generar tracking_number si aún no lo tiene
    if not order.tracking_number:
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        rand_code = secrets.token_hex(2).upper()
        order.tracking_number = f"DSP-{date_str}-{rand_code}"

    order.fulfillment_status = FulfillmentStatusEnum.dispatched
    order.dispatched_at = datetime.now(timezone.utc)
    order.dispatched_by = dispatcher_id

    db.commit()
    db.refresh(order)
    notify_order_event(db, order.id, order.user_id, "dispatched")

    return {
        "order_id": order.id,
        "tenant_id": order.tenant_id,
        "tracking_number": order.tracking_number,
        "delivery_type": order.delivery_type,
        "fulfillment_status": order.fulfillment_status.value if hasattr(order.fulfillment_status, "value") else str(order.fulfillment_status),
        "dispatched_at": order.dispatched_at,
        "dispatched_by": order.dispatched_by,
        "message": f"Pedido {order.id} despachado exitosamente con guía {order.tracking_number}",
    }


def get_order_by_tracking(db: Session, tracking_number: str, tenant_id: UUID | None = None) -> dict | None:
    query = db.query(Order).filter(Order.tracking_number == tracking_number)
    if tenant_id:
        query = query.filter(Order.tenant_id == tenant_id)
    order = query.first()
    if not order:
        return None
    return _serialize_order(db, order).model_dump()
