import uuid
import pytest
from decimal import Decimal
from fastapi.testclient import TestClient

try:
    from backend.main import app
except ModuleNotFoundError:
    from main import app

client = TestClient(app)


class TestCU06CU07MultitenantCatalog:
    """
    Suite de verificación estricta de aislamiento Multitenant para:
    - CU06: Gestionar Catálogo de Productos y Variantes de Precio/Talla por Tenant.
    - CU07: Consultar Catálogo Online con Búsqueda Facetada por Tenant.
    """

    @pytest.fixture(scope="class")
    def elegance_admin_auth(self):
        login_resp = client.post("/api/auth/login", json={
            "email": "admin@elegance.com",
            "password": "AdminElegance2026!",
        })
        assert login_resp.status_code == 200, f"Login Boutique Elegance failed: {login_resp.text}"
        data = login_resp.json()["data"]
        token = data["access_token"]
        user_info = data.get("user")
        tenant_id = user_info.get("tenant_id") if user_info else None
        if not tenant_id:
            me_resp = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
            tenant_id = me_resp.json()["data"]["tenant_id"]

        return {
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"},
            "tenant_id": tenant_id,
        }

    @pytest.fixture(scope="class")
    def modaurbana_admin_auth(self):
        login_resp = client.post("/api/auth/login", json={
            "email": "admin@modaurbana.com",
            "password": "AdminUrbana2026!",
        })
        assert login_resp.status_code == 200, f"Login Moda Urbana failed: {login_resp.text}"
        data = login_resp.json()["data"]
        token = data["access_token"]
        user_info = data.get("user")
        tenant_id = user_info.get("tenant_id") if user_info else None
        if not tenant_id:
            me_resp = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
            tenant_id = me_resp.json()["data"]["tenant_id"]

        return {
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"},
            "tenant_id": tenant_id,
        }

    @pytest.fixture(scope="class")
    def catalog_prerequisites(self, elegance_admin_auth):
        headers = elegance_admin_auth["headers"]

        # 1. Category
        cat_resp = client.post("/api/catalog/categories", headers=headers, json={
            "name": f"Vestidos_{uuid.uuid4().hex[:6]}"
        })
        assert cat_resp.status_code in (200, 201), cat_resp.text
        category_id = cat_resp.json()["data"]["id"]

        # 2. Sizes (Talla M y Talla L)
        size_m_resp = client.post("/api/catalog/sizes", headers=headers, json={
            "name": f"M_{uuid.uuid4().hex[:4]}"
        })
        assert size_m_resp.status_code in (200, 201), size_m_resp.text
        size_m_id = size_m_resp.json()["data"]["id"]

        size_l_resp = client.post("/api/catalog/sizes", headers=headers, json={
            "name": f"L_{uuid.uuid4().hex[:4]}"
        })
        assert size_l_resp.status_code in (200, 201), size_l_resp.text
        size_l_id = size_l_resp.json()["data"]["id"]

        # 3. Color
        col_resp = client.post("/api/catalog/colors", headers=headers, json={
            "name": f"Azul_{uuid.uuid4().hex[:4]}",
            "hex_code": "#0000FF"
        })
        assert col_resp.status_code in (200, 201), col_resp.text
        color_id = col_resp.json()["data"]["id"]

        return {
            "category_id": category_id,
            "size_m_id": size_m_id,
            "size_l_id": size_l_id,
            "color_id": color_id,
        }

    # -------------------------------------------------------------------------
    # TEST 1 (CU06): Creación de Prenda Multitenant con Precios Diferenciados por Talla
    # -------------------------------------------------------------------------
    def test_cu06_create_product_with_differential_pricing_by_size(self, elegance_admin_auth, catalog_prerequisites):
        headers = elegance_admin_auth["headers"]
        elegance_tenant_id = elegance_admin_auth["tenant_id"]
        prereqs = catalog_prerequisites

        unique_suffix = uuid.uuid4().hex[:6]
        product_payload = {
            "name": f"Vestido Seda Elegance {unique_suffix}",
            "description": "Vestido formal de alta costura con corte diferenciado",
            "category_id": prereqs["category_id"],
            "variants": [
                {
                    "sku": f"ELEG-M-{unique_suffix}",
                    "price": 50.00,  # Talla M a Bs 50
                    "size_id": prereqs["size_m_id"],
                    "color_id": prereqs["color_id"],
                },
                {
                    "sku": f"ELEG-L-{unique_suffix}",
                    "price": 70.00,  # Talla L a Bs 70 (diferencia de +20 Bs para CU19)
                    "size_id": prereqs["size_l_id"],
                    "color_id": prereqs["color_id"],
                }
            ]
        }

        resp = client.post("/api/catalog/products", headers=headers, json=product_payload)
        assert resp.status_code == 201, f"Product creation failed: {resp.text}"
        data = resp.json()["data"]

        # Verificación de Aislamiento Tenant en Entidad
        assert "id" in data
        assert data["tenant_id"] == elegance_tenant_id, "Product.tenant_id must match Boutique Elegance"

        # Verificación de variantes y diferenciación de precio por talla
        variants = data["variants"]
        assert len(variants) == 2
        for v in variants:
            assert v["tenant_id"] == elegance_tenant_id, "ProductVariant.tenant_id must match Boutique Elegance"
            if v["size_id"] == prereqs["size_m_id"]:
                assert Decimal(str(v["price"])) == Decimal("50.00")
            elif v["size_id"] == prereqs["size_l_id"]:
                assert Decimal(str(v["price"])) == Decimal("70.00")

    # -------------------------------------------------------------------------
    # TEST 2 (CU06): Aislamiento en Listado Administrativo (/api/catalog/products/admin)
    # -------------------------------------------------------------------------
    def test_cu06_admin_catalog_cross_tenant_isolation(self, elegance_admin_auth, modaurbana_admin_auth, catalog_prerequisites):
        elegance_headers = elegance_admin_auth["headers"]
        modaurbana_headers = modaurbana_admin_auth["headers"]
        prereqs = catalog_prerequisites

        # 1. Crear producto exclusivo en Boutique Elegance
        unique_e = uuid.uuid4().hex[:6]
        prod_e = client.post("/api/catalog/products", headers=elegance_headers, json={
            "name": f"Prenda Exclusiva Elegance {unique_e}",
            "category_id": prereqs["category_id"],
            "variants": [
                {
                    "sku": f"SKU-ELEG-{unique_e}",
                    "price": 120.00,
                    "size_id": prereqs["size_m_id"],
                    "color_id": prereqs["color_id"],
                }
            ]
        }).json()["data"]

        # 2. Crear producto exclusivo en Moda Urbana
        unique_u = uuid.uuid4().hex[:6]
        prod_u = client.post("/api/catalog/products", headers=modaurbana_headers, json={
            "name": f"Prenda Exclusiva Urbana {unique_u}",
            "category_id": prereqs["category_id"],
            "variants": [
                {
                    "sku": f"SKU-URB-{unique_u}",
                    "price": 85.00,
                    "size_id": prereqs["size_l_id"],
                    "color_id": prereqs["color_id"],
                }
            ]
        }).json()["data"]

        # 3. Consulta de Boutique Elegance: debe ver prod_e pero NUNCA prod_u
        resp_elegance = client.get("/api/catalog/products/admin", headers=elegance_headers)
        assert resp_elegance.status_code == 200
        items_e = resp_elegance.json()["data"]
        ids_e = [item["id"] for item in items_e]
        assert prod_e["id"] in ids_e, "Boutique Elegance must see its own product"
        assert prod_u["id"] not in ids_e, "CRITICAL: Boutique Elegance MUST NOT see Moda Urbana's product"

        # 4. Consulta de Moda Urbana: debe ver prod_u pero NUNCA prod_e
        resp_urbana = client.get("/api/catalog/products/admin", headers=modaurbana_headers)
        assert resp_urbana.status_code == 200
        items_u = resp_urbana.json()["data"]
        ids_u = [item["id"] for item in items_u]
        assert prod_u["id"] in ids_u, "Moda Urbana must see its own product"
        assert prod_e["id"] not in ids_u, "CRITICAL: Moda Urbana MUST NOT see Boutique Elegance's product"

    # -------------------------------------------------------------------------
    # TEST 3 (CU06): Protección Contra Modificación o Eliminación Cruzada
    # -------------------------------------------------------------------------
    def test_cu06_cross_tenant_update_and_delete_protection(self, elegance_admin_auth, modaurbana_admin_auth, catalog_prerequisites):
        elegance_headers = elegance_admin_auth["headers"]
        modaurbana_headers = modaurbana_admin_auth["headers"]
        prereqs = catalog_prerequisites

        # Crear producto en Elegance
        prod_e = client.post("/api/catalog/products", headers=elegance_headers, json={
            "name": f"Protegido Elegance {uuid.uuid4().hex[:6]}",
            "category_id": prereqs["category_id"],
            "variants": [
                {
                    "sku": f"PROT-{uuid.uuid4().hex[:6]}",
                    "price": 99.00,
                    "size_id": prereqs["size_m_id"],
                    "color_id": prereqs["color_id"],
                }
            ]
        }).json()["data"]

        elegance_prod_id = prod_e["id"]

        # Intento 1: Moda Urbana intenta actualizar producto de Elegance -> Debe fallar (404 / 403)
        put_resp = client.put(
            f"/api/catalog/products/{elegance_prod_id}",
            headers=modaurbana_headers,
            json={
                "name": "Nombre Hackeado",
                "category_id": prereqs["category_id"],
                "variants": [
                    {
                        "sku": f"HACK-{uuid.uuid4().hex[:6]}",
                        "price": 10.00,
                        "size_id": prereqs["size_m_id"],
                        "color_id": prereqs["color_id"],
                    }
                ]
            }
        )
        assert put_resp.status_code in (403, 404), f"Expected 404/403 on cross-tenant update, got {put_resp.status_code}"

        # Intento 2: Moda Urbana intenta eliminar producto de Elegance -> Debe fallar (404 / 403)
        del_resp = client.delete(
            f"/api/catalog/products/{elegance_prod_id}",
            headers=modaurbana_headers,
        )
        assert del_resp.status_code in (403, 404), f"Expected 404/403 on cross-tenant delete, got {del_resp.status_code}"

    # -------------------------------------------------------------------------
    # TEST 4 (CU07): Consulta y Búsqueda Facetada por Tenant en Catálogo Público
    # -------------------------------------------------------------------------
    def test_cu07_public_catalog_faceted_search_by_tenant(self, elegance_admin_auth, modaurbana_admin_auth, catalog_prerequisites):
        elegance_headers = elegance_admin_auth["headers"]
        elegance_tenant_id = elegance_admin_auth["tenant_id"]
        modaurbana_tenant_id = modaurbana_admin_auth["tenant_id"]
        prereqs = catalog_prerequisites

        unique_keyword = f"Facetado{uuid.uuid4().hex[:4]}"
        prod = client.post("/api/catalog/products", headers=elegance_headers, json={
            "name": f"Camisa {unique_keyword} Elegance",
            "category_id": prereqs["category_id"],
            "variants": [
                {
                    "sku": f"FACET-{uuid.uuid4().hex[:6]}",
                    "price": 65.00,
                    "size_id": prereqs["size_m_id"],
                    "color_id": prereqs["color_id"],
                }
            ]
        }).json()["data"]

        # 1. Búsqueda pública especificando el tenant de Elegance y la palabra clave
        resp_elegance = client.get(f"/api/catalog/products?tenant_id={elegance_tenant_id}&q={unique_keyword}")
        assert resp_elegance.status_code == 200
        items_e = resp_elegance.json()["data"]
        assert len(items_e) >= 1
        assert any(item["id"] == prod["id"] for item in items_e)

        # 2. Búsqueda pública especificando el tenant de Moda Urbana con la misma palabra clave: DEBE RETORNAR VACÍO
        resp_urbana = client.get(f"/api/catalog/products?tenant_id={modaurbana_tenant_id}&q={unique_keyword}")
        assert resp_urbana.status_code == 200
        items_u = resp_urbana.json()["data"]
        assert not any(item["id"] == prod["id"] for item in items_u), "Product from Elegance must not appear under Moda Urbana"
