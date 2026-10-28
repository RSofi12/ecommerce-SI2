import os
import sys
import uuid
from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.packages.p0_saas_plataforma.models.company import Company
from app.packages.p1_gestion_usuarios_acceso.models.branch import Branch
from app.packages.p1_gestion_usuarios_acceso.models.user import User
from app.packages.p2_gestion_productos_catalogo.models.product import Product
from app.packages.p2_gestion_productos_catalogo.models.product_variant import ProductVariant
from app.packages.p3_gestion_inventario_disponibilidad.models.inventory import Inventory
from app.packages.p4_gestion_compras_reservas.models.cart import Cart
from app.packages.p4_gestion_compras_reservas.models.cart_item import CartItem
from app.packages.p4_gestion_compras_reservas.models.order import Order
from app.packages.p4_gestion_compras_reservas.schemas.order_schema import (
    DeliveryTypeEnum,
    FulfillmentStatusEnum,
    PaymentMethodEnum,
    PaymentStatusEnum,
)
from app.packages.p4_gestion_compras_reservas.services.order_service import (
    create_stripe_payment,
    dispatch_order,
    get_order_by_tracking,
    process_stripe_event,
)
from app.schemas.enums import RolEnum

# Contexto persistente compartido entre pasos secuenciales del CU12
_CONTEXT: dict = {}


class TestCU12StripeConditionedDispatch:
    """
    Suite de pruebas formal para CU12:
    Comprar Prendas con Stripe y Despacho Condicionado (Presentación 2)
    Validación de Política de Negocio 3 y Aislamiento Multitenant SaaS.
    """

    @pytest.fixture(scope="class", autouse=True)
    def setup_data(self):
        db = SessionLocal()
        try:
            # 1. Obtener tenants
            tenant_a = db.query(Company).filter(Company.subdomain == "elegance").first()
            assert tenant_a is not None, "Tenant Boutique Elegance debe existir"

            tenant_b = db.query(Company).filter(Company.subdomain == "modaurbana").first()
            assert tenant_b is not None, "Tenant Moda Urbana debe existir"

            # 2. Sucursal y usuarios
            branch_a = db.query(Branch).filter(Branch.tenant_id == tenant_a.id, Branch.is_active == True).first()
            assert branch_a is not None, "Sucursal de Boutique Elegance requerida"

            admin_a = db.query(User).filter(User.email == "admin@elegance.com").first()
            assert admin_a is not None, "Admin de Elegance requerido"

            # Cliente de prueba
            client_user = db.query(User).filter(User.email == "cliente_cu12@test.com").first()
            if not client_user:
                client_user = User(
                    id=uuid.uuid4(),
                    name="Cliente CU12 Test",
                    email="cliente_cu12@test.com",
                    hashed_password="hashed_pw_test",
                    rol=RolEnum.cliente,
                    tenant_id=tenant_a.id,
                    branch_id=branch_a.id,
                    is_active=True,
                )
                db.add(client_user)
                db.commit()
                db.refresh(client_user)

            # 3. Producto, variante e inventario
            product = db.query(Product).filter(Product.tenant_id == tenant_a.id).first()
            if not product:
                product = Product(
                    id=uuid.uuid4(),
                    tenant_id=tenant_a.id,
                    name="Vestido de Gala Elegance CU12",
                    description="Vestido para pruebas de despacho condicionado",
                    base_price=Decimal("150.00"),
                    is_active=True,
                )
                db.add(product)
                db.commit()
                db.refresh(product)

            variant = db.query(ProductVariant).filter(ProductVariant.product_id == product.id).first()
            if not variant:
                variant = ProductVariant(
                    id=uuid.uuid4(),
                    tenant_id=tenant_a.id,
                    product_id=product.id,
                    sku=f"ELEG-VEST-{uuid.uuid4().hex[:6].upper()}",
                    price=Decimal("150.00"),
                    is_active=True,
                )
                db.add(variant)
                db.commit()
                db.refresh(variant)

            inv = db.query(Inventory).filter(Inventory.variant_id == variant.id, Inventory.branch_id == branch_a.id).first()
            if not inv:
                inv = Inventory(
                    id=uuid.uuid4(),
                    tenant_id=tenant_a.id,
                    branch_id=branch_a.id,
                    variant_id=variant.id,
                    quantity=20,
                    reserved_quantity=0,
                )
                db.add(inv)
                db.commit()
                db.refresh(inv)
            else:
                inv.quantity = max(inv.quantity, 20)
                db.commit()

            _CONTEXT["tenant_a_id"] = tenant_a.id
            _CONTEXT["tenant_b_id"] = tenant_b.id
            _CONTEXT["branch_a_id"] = branch_a.id
            _CONTEXT["admin_a_id"] = admin_a.id
            _CONTEXT["client_id"] = client_user.id
            _CONTEXT["product_id"] = product.id
            _CONTEXT["variant_id"] = variant.id
        finally:
            db.close()

    def test_01_create_stripe_checkout_and_reservation(self):
        """
        Prueba 1: Creación de checkout con Stripe, reserva temporal de stock e inclusión de tenant_id.
        """
        db = SessionLocal()
        try:
            user_id = _CONTEXT["client_id"]
            variant_id = _CONTEXT["variant_id"]
            branch_id = _CONTEXT["branch_a_id"]
            tenant_id = _CONTEXT["tenant_a_id"]

            # Limpiar carrito previo si existe
            cart = db.query(Cart).filter(Cart.user_id == user_id).first()
            if not cart:
                cart = Cart(user_id=user_id, tenant_id=tenant_id)
                db.add(cart)
                db.commit()
                db.refresh(cart)
            else:
                db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
                cart.tenant_id = tenant_id
                cart.status = "active"
                db.commit()

            # Agregar prenda al carrito
            db.add(CartItem(
                cart_id=cart.id,
                tenant_id=tenant_id,
                variant_id=variant_id,
                quantity=2,
                unit_price=Decimal("150.00"),
            ))
            db.commit()

            # Mockear llamada a Stripe SDK
            mock_intent = MagicMock()
            mock_intent.id = f"pi_test_{uuid.uuid4().hex[:12]}"
            mock_intent.client_secret = f"{mock_intent.id}_secret"

            with patch("stripe.PaymentIntent.create", return_value=mock_intent):
                order_data, client_secret, payment_intent_id = create_stripe_payment(
                    db=db,
                    user_id=user_id,
                    pickup_branch_id=branch_id,
                    tenant_id=tenant_id,
                    delivery_type=DeliveryTypeEnum.home_delivery.value,
                    shipping_address="Av. San Martín #123, Santa Cruz",
                )

                assert order_data is not None
                assert order_data["payment_method"] == PaymentMethodEnum.stripe.value
                assert order_data["payment_status"] == PaymentStatusEnum.pending.value
                assert order_data["delivery_type"] == "ENVIO_DOMICILIO"
                assert order_data["shipping_address"] == "Av. San Martín #123, Santa Cruz"
                assert order_data["tenant_id"] == tenant_id
                assert client_secret == mock_intent.client_secret
                assert payment_intent_id == mock_intent.id

                # Verificar que el stock fue reservado (reserved_quantity >= 2)
                inv = db.query(Inventory).filter(Inventory.variant_id == variant_id, Inventory.branch_id == branch_id).first()
                assert inv.reserved_quantity >= 2

                # Guardar order_id y payment_intent_id para las siguientes pruebas
                _CONTEXT["order_id"] = uuid.UUID(str(order_data["id"]))
                _CONTEXT["payment_intent_id"] = payment_intent_id
                _CONTEXT["total_amount"] = Decimal(str(order_data["total_amount"]))
        finally:
            db.close()

    def test_02_policy_3_dispatch_strictly_blocked_when_unpaid(self):
        """
        Prueba 2: POLÍTICA DE NEGOCIO 3 (INVIOLABLE)
        El despacho físico o digital debe ser rechazado si payment_status != 'paid'.
        """
        db = SessionLocal()
        try:
            order_id = _CONTEXT["order_id"]
            admin_id = _CONTEXT["admin_a_id"]
            tenant_id = _CONTEXT["tenant_a_id"]

            order = db.query(Order).filter(Order.id == order_id).first()
            assert order.payment_status == PaymentStatusEnum.pending

            # Intentar despachar pedido no pagado
            with pytest.raises(ValueError) as excinfo:
                dispatch_order(
                    db=db,
                    order_id=order_id,
                    dispatcher_id=admin_id,
                    tenant_id=tenant_id,
                )

            err_msg = str(excinfo.value)
            assert "Política de Negocio 3" in err_msg
            assert "debe estar pagado" in err_msg

            # Verificar que el pedido NO cambió a despachado
            db.refresh(order)
            assert order.fulfillment_status != FulfillmentStatusEnum.dispatched
            assert order.dispatched_at is None
            assert order.dispatched_by is None
        finally:
            db.close()

    def test_03_stripe_webhook_succeeded_generates_tracking_number(self):
        """
        Prueba 3: Procesamiento exitoso del webhook de Stripe `payment_intent.succeeded`
        Generación de número de seguimiento (tracking_number) y confirmación de pago.
        """
        db = SessionLocal()
        try:
            order_id = _CONTEXT["order_id"]
            payment_intent_id = _CONTEXT["payment_intent_id"]
            total_amount = _CONTEXT["total_amount"]
            amount_cents = int(total_amount * 100)

            fake_event = {
                "id": f"evt_test_{uuid.uuid4().hex[:12]}",
                "type": "payment_intent.succeeded",
                "data": {
                    "object": {
                        "id": payment_intent_id,
                        "amount": amount_cents,
                        "currency": "usd",
                        "metadata": {
                            "order_id": str(order_id),
                        },
                    }
                },
            }

            # Procesar evento de Stripe
            process_stripe_event(db, fake_event)

            order = db.query(Order).filter(Order.id == order_id).first()
            assert order.payment_status == PaymentStatusEnum.paid
            assert order.status == "paid"
            assert order.tracking_number is not None
            assert order.tracking_number.startswith("DSP-")
            assert order.fulfillment_status == FulfillmentStatusEnum.ready_for_dispatch

            _CONTEXT["tracking_number"] = order.tracking_number
        finally:
            db.close()

    def test_04_authorized_dispatch_success_and_tracking_lookup(self):
        """
        Prueba 4: Despacho autorizado una vez que el pago está confirmado en Stripe.
        Verificación de asignación de fecha de despacho, despachador y consulta por tracking.
        """
        db = SessionLocal()
        try:
            order_id = _CONTEXT["order_id"]
            admin_id = _CONTEXT["admin_a_id"]
            tenant_id = _CONTEXT["tenant_a_id"]
            tracking_num = _CONTEXT["tracking_number"]

            result = dispatch_order(
                db=db,
                order_id=order_id,
                dispatcher_id=admin_id,
                tenant_id=tenant_id,
                shipping_notes="Prenda embalada y entregada al courier",
            )

            assert result["order_id"] == order_id
            assert result["fulfillment_status"] == FulfillmentStatusEnum.dispatched.value
            assert result["dispatched_at"] is not None
            assert result["dispatched_by"] == admin_id
            assert result["tracking_number"] == tracking_num

            # Consultar por tracking_number
            tracking_result = get_order_by_tracking(db, tracking_num, tenant_id=tenant_id)
            assert tracking_result is not None
            assert tracking_result["id"] == order_id
            assert tracking_result["fulfillment_status"] == FulfillmentStatusEnum.dispatched.value
            assert tracking_result["tracking_number"] == tracking_num
            assert tracking_result["delivery_type"] == "ENVIO_DOMICILIO"
        finally:
            db.close()

    def test_05_multitenant_dispatch_isolation(self):
        """
        Prueba 5: Aislamiento Multitenant estricto (SaaS).
        Un administrador del Tenant B (Moda Urbana) no puede ver ni despachar pedidos del Tenant A (Boutique Elegance).
        """
        db = SessionLocal()
        try:
            order_id = _CONTEXT["order_id"]
            tenant_b_id = _CONTEXT["tenant_b_id"]

            # Intentar despachar el pedido de Elegance con tenant_id de Moda Urbana
            with pytest.raises(ValueError) as excinfo:
                dispatch_order(
                    db=db,
                    order_id=order_id,
                    dispatcher_id=_CONTEXT["admin_a_id"],
                    tenant_id=tenant_b_id,
                )

            err_msg = str(excinfo.value)
            assert "no pertenece a la empresa" in err_msg or "no encontrado" in err_msg

            # Consulta de tracking con tenant_id incorrecto
            tracking_num = _CONTEXT["tracking_number"]
            foreign_lookup = get_order_by_tracking(db, tracking_num, tenant_id=tenant_b_id)
            assert foreign_lookup is None
        finally:
            db.close()
