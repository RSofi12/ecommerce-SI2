import os
import sys
import uuid
from datetime import date, timedelta
from decimal import Decimal
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.packages.p0_saas_plataforma.models.company import Company
from app.packages.p1_gestion_usuarios_acceso.models.branch import Branch
from app.packages.p1_gestion_usuarios_acceso.models.user import User
from app.packages.p2_gestion_productos_catalogo.models.product import Product
from app.packages.p2_gestion_productos_catalogo.models.product_variant import ProductVariant
from app.packages.p3_gestion_inventario_disponibilidad.models.inventory import Inventory
from app.packages.p4_gestion_compras_reservas.models.reservation import Reservation
from app.packages.p4_gestion_compras_reservas.models.reservation_item import ReservationItem
from app.packages.p4_gestion_compras_reservas.schemas.reservation_schema import (
    ReservationCreate,
    ReservationItemCreate,
    ReservationStatusEnum,
)
from app.packages.p4_gestion_compras_reservas.services.reservation_service import (
    cancel_reservation,
    create_reservation,
    expire_due_reservations,
    get_reservation,
    list_reservations,
)
from app.schemas.enums import RolEnum

_CONTEXT: dict = {}


class TestCU13ReservationsWithExpiration:
    """
    Suite de pruebas para CU13:
    Crear Reserva de Prendas con Vencimiento (Online y Offline).
    Verifica Política de Negocio 6 (liberación por vencimiento) y aislamiento multitenant.
    """

    @pytest.fixture(scope="class", autouse=True)
    def setup_data(self):
        db = SessionLocal()
        try:
            # 1. Tenants Elegance y Moda Urbana
            tenant_a = db.query(Company).filter(Company.subdomain == "elegance").first()
            assert tenant_a is not None, "Tenant Boutique Elegance debe existir"

            tenant_b = db.query(Company).filter(Company.subdomain == "modaurbana").first()
            assert tenant_b is not None, "Tenant Moda Urbana debe existir"

            # 2. Sucursales
            branch_a = db.query(Branch).filter(Branch.tenant_id == tenant_a.id, Branch.is_active == True).first()
            assert branch_a is not None, "Sucursal activa de Elegance requerida"

            branch_b = db.query(Branch).filter(Branch.tenant_id == tenant_b.id, Branch.is_active == True).first()
            assert branch_b is not None, "Sucursal activa de Moda Urbana requerida"

            # 3. Clientes
            client_a = db.query(User).filter(User.email == "cliente_cu13_a@test.com").first()
            if not client_a:
                client_a = User(
                    id=uuid.uuid4(),
                    name="Cliente Elegance CU13",
                    email="cliente_cu13_a@test.com",
                    hashed_password="hashed_pw_test",
                    rol=RolEnum.cliente,
                    tenant_id=tenant_a.id,
                    branch_id=branch_a.id,
                    is_active=True,
                )
                db.add(client_a)
                db.commit()
                db.refresh(client_a)

            client_b = db.query(User).filter(User.email == "cliente_cu13_b@test.com").first()
            if not client_b:
                client_b = User(
                    id=uuid.uuid4(),
                    name="Cliente ModaUrbana CU13",
                    email="cliente_cu13_b@test.com",
                    hashed_password="hashed_pw_test",
                    rol=RolEnum.cliente,
                    tenant_id=tenant_b.id,
                    branch_id=branch_b.id,
                    is_active=True,
                )
                db.add(client_b)
                db.commit()
                db.refresh(client_b)

            # 4. Producto y Variante para Tenant A
            product_a = db.query(Product).filter(Product.tenant_id == tenant_a.id).first()
            if not product_a:
                product_a = Product(
                    id=uuid.uuid4(),
                    tenant_id=tenant_a.id,
                    name="Prenda Reserva CU13 Test",
                    description="Prenda para pruebas de reserva",
                    base_price=Decimal("80.00"),
                    is_active=True,
                )
                db.add(product_a)
                db.commit()
                db.refresh(product_a)

            variant_a = db.query(ProductVariant).filter(ProductVariant.product_id == product_a.id).first()
            if not variant_a:
                variant_a = ProductVariant(
                    id=uuid.uuid4(),
                    tenant_id=tenant_a.id,
                    product_id=product_a.id,
                    sku="CU13-RES-VAR-01",
                    price=Decimal("80.00"),
                )
                db.add(variant_a)
                db.commit()
                db.refresh(variant_a)

            # 5. Inventario en Sucursal A
            inv_a = db.query(Inventory).filter(
                Inventory.variant_id == variant_a.id,
                Inventory.branch_id == branch_a.id,
            ).first()
            if not inv_a:
                inv_a = Inventory(
                    id=uuid.uuid4(),
                    variant_id=variant_a.id,
                    branch_id=branch_a.id,
                    quantity=15,
                    reserved_quantity=0,
                )
                db.add(inv_a)
            else:
                inv_a.quantity = 15
                inv_a.reserved_quantity = 0
            db.commit()
            db.refresh(inv_a)

            _CONTEXT["tenant_a_id"] = tenant_a.id
            _CONTEXT["tenant_b_id"] = tenant_b.id
            _CONTEXT["branch_a_id"] = branch_a.id
            _CONTEXT["branch_b_id"] = branch_b.id
            _CONTEXT["client_a_id"] = client_a.id
            _CONTEXT["client_b_id"] = client_b.id
            _CONTEXT["variant_a_id"] = variant_a.id
        finally:
            db.close()

    def test_01_create_reservation_success_and_stock_locking(self):
        """
        Happy path: El cliente aparta prendas con stock disponible.
        Verifica incremento atómico de reserved_quantity y cálculo de expires_at.
        """
        db = SessionLocal()
        try:
            client_a_id = _CONTEXT["client_a_id"]
            branch_a_id = _CONTEXT["branch_a_id"]
            variant_a_id = _CONTEXT["variant_a_id"]
            tenant_a_id = _CONTEXT["tenant_a_id"]

            visit_date = date.today() + timedelta(days=2)
            payload = ReservationCreate(
                branch_id=branch_a_id,
                visit_date=visit_date,
                items=[ReservationItemCreate(variant_id=variant_a_id, quantity=3)],
            )

            res_data = create_reservation(db, client_a_id, payload, tenant_id=tenant_a_id)

            assert res_data["id"] is not None
            assert res_data["status"] == ReservationStatusEnum.pending.value
            assert res_data["expires_at"] == visit_date + timedelta(days=1)
            assert res_data["total_amount"] == Decimal(str(res_data["items"][0]["unit_price"])) * 3
            assert res_data["item_count"] == 3
            assert res_data["tenant_id"] == tenant_a_id
            assert res_data["reservation_code"].startswith("RES-")
            assert res_data["qr_payload"].startswith("FS-RES:")

            # Verificar inventario comprometido en la base de datos
            inv = db.query(Inventory).filter(
                Inventory.variant_id == variant_a_id,
                Inventory.branch_id == branch_a_id,
            ).first()
            assert inv.reserved_quantity == 3
            _CONTEXT["reservation_01_id"] = res_data["id"]
        finally:
            db.close()

    def test_02_insufficient_stock_rejection(self):
        """
        Intento de reservar más existencias que el disponible (quantity - reserved_quantity).
        Debe lanzar ValueError y no modificar el inventario.
        """
        db = SessionLocal()
        try:
            client_a_id = _CONTEXT["client_a_id"]
            branch_a_id = _CONTEXT["branch_a_id"]
            variant_a_id = _CONTEXT["variant_a_id"]
            tenant_a_id = _CONTEXT["tenant_a_id"]

            # Quedan 15 - 3 = 12 disponibles. Intentamos pedir 13.
            payload = ReservationCreate(
                branch_id=branch_a_id,
                visit_date=date.today() + timedelta(days=1),
                items=[ReservationItemCreate(variant_id=variant_a_id, quantity=13)],
            )

            with pytest.raises(ValueError, match="No hay stock disponible suficiente"):
                create_reservation(db, client_a_id, payload, tenant_id=tenant_a_id)

            # Confirmar que reserved_quantity sigue en 3
            inv = db.query(Inventory).filter(
                Inventory.variant_id == variant_a_id,
                Inventory.branch_id == branch_a_id,
            ).first()
            assert inv.reserved_quantity == 3
        finally:
            db.close()

    def test_03_invalid_dates_validation(self):
        """
        Validación de fechas de visita:
        - Fechas pasadas deben ser rechazadas.
        - Fechas con más de 7 días de anticipación deben ser rechazadas.
        """
        branch_a_id = _CONTEXT["branch_a_id"]
        variant_a_id = _CONTEXT["variant_a_id"]

        # Fecha en el pasado
        past_date = date.today() - timedelta(days=1)
        with pytest.raises(Exception):
            ReservationCreate(
                branch_id=branch_a_id,
                visit_date=past_date,
                items=[ReservationItemCreate(variant_id=variant_a_id, quantity=1)],
            )

        # Fecha muy lejana (> 7 días)
        future_date = date.today() + timedelta(days=10)
        with pytest.raises(Exception):
            ReservationCreate(
                branch_id=branch_a_id,
                visit_date=future_date,
                items=[ReservationItemCreate(variant_id=variant_a_id, quantity=1)],
            )

    def test_04_cancel_reservation_releases_stock(self):
        """
        El cliente cancela voluntariamente su reserva.
        Verifica transición a 'cancelled' y decremento atómico de reserved_quantity.
        """
        db = SessionLocal()
        try:
            client_a_id = _CONTEXT["client_a_id"]
            variant_a_id = _CONTEXT["variant_a_id"]
            branch_a_id = _CONTEXT["branch_a_id"]
            tenant_a_id = _CONTEXT["tenant_a_id"]
            reservation_id = uuid.UUID(str(_CONTEXT["reservation_01_id"]))

            cancelled_res = cancel_reservation(
                db, client_a_id, reservation_id, tenant_id=tenant_a_id
            )
            assert cancelled_res["status"] == ReservationStatusEnum.cancelled.value

            inv = db.query(Inventory).filter(
                Inventory.variant_id == variant_a_id,
                Inventory.branch_id == branch_a_id,
            ).first()
            # El inventario reservado debe haber retornado a 0
            assert inv.reserved_quantity == 0
        finally:
            db.close()

    def test_05_expiration_job_releases_stock(self):
        """
        POLÍTICA 6: Caducidad automática de reservas.
        Simula una reserva vencida en la base de datos y ejecuta expire_due_reservations().
        Verifica transición a 'expired' y restitución inmediata del stock disponible.
        """
        db = SessionLocal()
        try:
            client_a_id = _CONTEXT["client_a_id"]
            variant_a_id = _CONTEXT["variant_a_id"]
            branch_a_id = _CONTEXT["branch_a_id"]
            tenant_a_id = _CONTEXT["tenant_a_id"]

            # Crear reserva forzando expires_at <= hoy (ayer)
            expired_res_id = uuid.uuid4()
            past_visit = date.today() - timedelta(days=2)
            past_expires = date.today() - timedelta(days=1)

            res = Reservation(
                id=expired_res_id,
                tenant_id=tenant_a_id,
                branch_id=branch_a_id,
                user_id=client_a_id,
                visit_date=past_visit,
                expires_at=past_expires,
                status=ReservationStatusEnum.pending,
                total_amount=Decimal("160.00"),
            )
            db.add(res)
            db.flush()

            db.add(
                ReservationItem(
                    tenant_id=tenant_a_id,
                    reservation_id=res.id,
                    variant_id=variant_a_id,
                    quantity=2,
                    unit_price=Decimal("80.00"),
                )
            )

            # Incrementar inventario reservado
            inv = db.query(Inventory).filter(
                Inventory.variant_id == variant_a_id,
                Inventory.branch_id == branch_a_id,
            ).first()
            inv.reserved_quantity = 2
            db.commit()

            # Ejecutar el cron/job de expiración
            expired_list = expire_due_reservations(db)
            assert any(str(r.id) == str(expired_res_id) for r in expired_list)

            # Verificar estado en base de datos
            db.refresh(res)
            assert res.status == ReservationStatusEnum.expired

            # Verificar que el stock comprometido se haya liberado
            db.refresh(inv)
            assert inv.reserved_quantity == 0
        finally:
            db.close()

    def test_06_tenant_isolation(self):
        """
        Aislamiento SaaS:
        Cliente del Tenant B no puede reservar en una sucursal del Tenant A.
        Ni tampoco puede listar ni acceder a reservas del Tenant A.
        """
        db = SessionLocal()
        try:
            client_b_id = _CONTEXT["client_b_id"]
            branch_a_id = _CONTEXT["branch_a_id"]
            variant_a_id = _CONTEXT["variant_a_id"]
            tenant_b_id = _CONTEXT["tenant_b_id"]

            payload = ReservationCreate(
                branch_id=branch_a_id,
                visit_date=date.today() + timedelta(days=1),
                items=[ReservationItemCreate(variant_id=variant_a_id, quantity=1)],
            )

            # Intento de reserva cruzada: debe fallar con ValueError
            with pytest.raises(ValueError, match="no pertenece a la empresa actual"):
                create_reservation(db, client_b_id, payload, tenant_id=tenant_b_id)

            # Intento de consultar reservas de Tenant A con contexto de Tenant B
            reservations_b = list_reservations(db, client_b_id, tenant_id=tenant_b_id)
            assert all(r["tenant_id"] == tenant_b_id for r in reservations_b)
        finally:
            db.close()

    def test_07_offline_client_reservation_id_idempotency(self):
        """
        Contingencia offline: Envío de client_reservation_id (UUIDv4 generado en cliente).
        Si se reintenta el envío de la misma operación, debe responder idéntico sin duplicar apartados de stock.
        """
        db = SessionLocal()
        try:
            client_a_id = _CONTEXT["client_a_id"]
            branch_a_id = _CONTEXT["branch_a_id"]
            variant_a_id = _CONTEXT["variant_a_id"]
            tenant_a_id = _CONTEXT["tenant_a_id"]

            offline_uuid = uuid.uuid4()
            payload = ReservationCreate(
                branch_id=branch_a_id,
                visit_date=date.today() + timedelta(days=2),
                items=[ReservationItemCreate(variant_id=variant_a_id, quantity=1)],
                client_reservation_id=offline_uuid,
            )

            # Primer envío
            res_first = create_reservation(db, client_a_id, payload, tenant_id=tenant_a_id)
            assert str(res_first["id"]) == str(offline_uuid)

            # Reintento de sincronización del mismo UUID
            res_retry = create_reservation(db, client_a_id, payload, tenant_id=tenant_a_id)
            assert str(res_retry["id"]) == str(offline_uuid)

            # Validar que el stock reservado solo se incrementó en 1
            inv = db.query(Inventory).filter(
                Inventory.variant_id == variant_a_id,
                Inventory.branch_id == branch_a_id,
            ).first()
            assert inv.reserved_quantity == 1

            # Limpiar
            cancel_reservation(db, client_a_id, offline_uuid, tenant_id=tenant_a_id)
        finally:
            db.close()
