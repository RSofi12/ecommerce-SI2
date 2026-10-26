import uuid
import pytest
from fastapi.testclient import TestClient

try:
    from backend.main import app
except ModuleNotFoundError:
    from main import app

from app.core.database import SessionLocal
from app.packages.p0_saas_plataforma.models.company import Company
from app.packages.p1_gestion_usuarios_acceso.models.branch import Branch
from app.packages.p2_gestion_productos_catalogo.models.category import Category
from app.packages.p2_gestion_productos_catalogo.models.product import Product
from app.packages.p2_gestion_productos_catalogo.models.product_variant import ProductVariant
from app.packages.p2_gestion_productos_catalogo.models.size import Size
from app.packages.p2_gestion_productos_catalogo.models.color import Color
from app.packages.p2_gestion_productos_catalogo.schemas.catalog_enums import ProductStatusEnum
from app.packages.p3_gestion_inventario_disponibilidad.models.inventory import Inventory
from app.packages.p3_gestion_inventario_disponibilidad.services.inventory_service import get_consolidated_stock, get_branch_stock

client = TestClient(app)


@pytest.fixture(scope="module")
def sample_tenant_and_stock():
    with SessionLocal() as db:
        tenant_a = Company(
            name=f"Tenant A {uuid.uuid4().hex[:6]}",
            business_name=f"Tenant A Corp {uuid.uuid4().hex[:6]}",
            nit_rut=f"NIT-{uuid.uuid4().hex[:8]}",
            subdomain=f"tenanta-{uuid.uuid4().hex[:6]}",
            email=f"admin-{uuid.uuid4().hex[:6]}@tenanta.com",
            status="ACTIVO",
        )
        tenant_b = Company(
            name=f"Tenant B {uuid.uuid4().hex[:6]}",
            business_name=f"Tenant B Corp {uuid.uuid4().hex[:6]}",
            nit_rut=f"NIT-{uuid.uuid4().hex[:8]}",
            subdomain=f"tenantb-{uuid.uuid4().hex[:6]}",
            email=f"admin-{uuid.uuid4().hex[:6]}@tenantb.com",
            status="ACTIVO",
        )
        db.add_all([tenant_a, tenant_b])
        db.flush()

        branch_a1 = Branch(tenant_id=tenant_a.id, name=f"Sucursal Norte A {uuid.uuid4().hex[:6]}", city="Santa Cruz", address="Av. Banzer 100", phone="7771111", is_active=True)
        branch_a2 = Branch(tenant_id=tenant_a.id, name=f"Sucursal Sur A {uuid.uuid4().hex[:6]}", city="Santa Cruz", address="Av. Santos Dumont 200", phone="7772222", is_active=True)
        branch_b = Branch(tenant_id=tenant_b.id, name=f"Sucursal B {uuid.uuid4().hex[:6]}", city="La Paz", address="Calacoto", phone="7773333", is_active=True)
        db.add_all([branch_a1, branch_a2, branch_b])
        db.flush()

        category = Category(name=f"Cat CU10 {uuid.uuid4().hex[:6]}")
        size_m = Size(name=f"M-{uuid.uuid4().hex[:4]}")
        color_blue = Color(name=f"Azul-{uuid.uuid4().hex[:4]}", hex_code="#0000FF")
        db.add_all([category, size_m, color_blue])
        db.flush()

        prod_a = Product(tenant_id=tenant_a.id, name="Vestido Gala Tenant A", description="Vestido de noche", category_id=category.id)
        prod_b = Product(tenant_id=tenant_b.id, name="Camisa Lino Tenant B", description="Camisa casual", category_id=category.id)
        db.add_all([prod_a, prod_b])
        db.flush()

        var_a = ProductVariant(
            tenant_id=tenant_a.id,
            product_id=prod_a.id,
            sku=f"SKU-A-{uuid.uuid4().hex[:6]}",
            price=120.0,
            size_id=size_m.id,
            color_id=color_blue.id,
            status=ProductStatusEnum.active,
        )
        var_b = ProductVariant(
            tenant_id=tenant_b.id,
            product_id=prod_b.id,
            sku=f"SKU-B-{uuid.uuid4().hex[:6]}",
            price=90.0,
            size_id=size_m.id,
            color_id=color_blue.id,
            status=ProductStatusEnum.active,
        )
        db.add_all([var_a, var_b])
        db.flush()

        # Inventarios:
        # branch_a1: qty=15, reserved=3 -> available=12
        inv_a1 = Inventory(variant_id=var_a.id, branch_id=branch_a1.id, tenant_id=tenant_a.id, quantity=15, reserved_quantity=3, minimum_stock=5)
        # branch_a2: qty=5, reserved=0 -> available=5
        inv_a2 = Inventory(variant_id=var_a.id, branch_id=branch_a2.id, tenant_id=tenant_a.id, quantity=5, reserved_quantity=0, minimum_stock=2)
        # branch_b: qty=20, reserved=0 -> available=20
        inv_b = Inventory(variant_id=var_b.id, branch_id=branch_b.id, tenant_id=tenant_b.id, quantity=20, reserved_quantity=0, minimum_stock=5)
        db.add_all([inv_a1, inv_a2, inv_b])
        db.commit()

        yield {
            "tenant_a_id": tenant_a.id,
            "tenant_b_id": tenant_b.id,
            "branch_a1_id": branch_a1.id,
            "branch_a2_id": branch_a2.id,
            "branch_b_id": branch_b.id,
            "product_a_id": prod_a.id,
            "variant_a_id": var_a.id,
            "product_b_id": prod_b.id,
            "variant_b_id": var_b.id,
        }


def test_cu10_missing_parameters_returns_422():
    resp = client.get("/api/catalog/availability")
    assert resp.status_code == 422


def test_cu10_single_branch_availability_compatibility(sample_tenant_and_stock):
    var_id = sample_tenant_and_stock["variant_a_id"]
    branch_1 = sample_tenant_and_stock["branch_a1_id"]

    resp = client.get(f"/api/catalog/availability?variant_id={var_id}&branch_id={branch_1}")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["variant_id"] == str(var_id)
    assert data["branch_id"] == str(branch_1)
    assert data["quantity"] == 12  # 15 - 3 = 12


def test_cu10_multi_branch_availability_for_variant(sample_tenant_and_stock):
    var_id = sample_tenant_and_stock["variant_a_id"]
    tenant_a = sample_tenant_and_stock["tenant_a_id"]

    # Consultar disponibilidad sin branch_id -> devuelve desglose por sucursales del tenant
    resp = client.get(f"/api/catalog/availability?variant_id={var_id}")
    assert resp.status_code == 200
    data = resp.json()["data"]

    assert data["variant_id"] == str(var_id)
    assert data["total_available"] == 17  # 12 (en a1) + 5 (en a2)

    branches = data["branches"]
    assert len(branches) == 2  # Sólo las 2 sucursales del Tenant A, no la del Tenant B
    branch_ids = [b["branch_id"] for b in branches]
    assert str(sample_tenant_and_stock["branch_a1_id"]) in branch_ids
    assert str(sample_tenant_and_stock["branch_a2_id"]) in branch_ids
    assert str(sample_tenant_and_stock["branch_b_id"]) not in branch_ids

    b1_info = next(b for b in branches if b["branch_id"] == str(sample_tenant_and_stock["branch_a1_id"]))
    assert b1_info["branch_name"].startswith("Sucursal Norte A")
    assert b1_info["quantity"] == 15
    assert b1_info["reserved_quantity"] == 3
    assert b1_info["available_quantity"] == 12


def test_cu10_consolidated_stock_multitenant_isolation(sample_tenant_and_stock):
    with SessionLocal() as db:
        # Filtro de tenant A
        stock_a = get_consolidated_stock(db, tenant_id=sample_tenant_and_stock["tenant_a_id"])
        # Filtro de tenant B
        stock_b = get_consolidated_stock(db, tenant_id=sample_tenant_and_stock["tenant_b_id"])

    # Tenant A sólo debe ver su producto y sus sucursales
    variant_ids_a = [item["variant_id"] for item in stock_a]
    assert sample_tenant_and_stock["variant_a_id"] in variant_ids_a
    assert sample_tenant_and_stock["variant_b_id"] not in variant_ids_a

    # Tenant B sólo debe ver su producto y sus sucursales
    variant_ids_b = [item["variant_id"] for item in stock_b]
    assert sample_tenant_and_stock["variant_b_id"] in variant_ids_b
    assert sample_tenant_and_stock["variant_a_id"] not in variant_ids_b
