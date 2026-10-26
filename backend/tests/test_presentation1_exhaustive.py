import uuid
import pytest
from fastapi.testclient import TestClient

try:
    from backend.main import app
except ModuleNotFoundError:
    from main import app

client = TestClient(app)


class TestPresentation1Exhaustive:
    """
    Suite exhaustiva de pruebas de aceptación y verificación funcional
    para la Primera Presentación (CU01 al CU10).
    """

    @pytest.fixture(scope="class")
    def superadmin_token(self):
        login_resp = client.post("/api/auth/login", json={
            "email": "superadmin@fashionstore.com",
            "password": "SuperAdmin2026!",
        })
        assert login_resp.status_code == 200, f"Superadmin login failed: {login_resp.text}"
        return login_resp.json()["data"]["access_token"]

    @pytest.fixture(scope="class")
    def elegance_admin_token(self):
        login_resp = client.post("/api/auth/login", json={
            "email": "admin@elegance.com",
            "password": "AdminElegance2026!",
        })
        assert login_resp.status_code == 200, f"Elegance Admin login failed: {login_resp.text}"
        return login_resp.json()["data"]["access_token"]

    @pytest.fixture(scope="class")
    def client_token(self):
        # CU03: Registro dinámico de cliente
        rand_email = f"cliente_{uuid.uuid4().hex[:6]}@example.com"
        reg_resp = client.post("/api/auth/register", json={
            "email": rand_email,
            "name": "Cliente Prueba",
            "password": "Password123!",
            "gender": "femenino",
        })
        assert reg_resp.status_code == 201, f"Register failed: {reg_resp.text}"
        return reg_resp.json()["data"]["access_token"]

    # -------------------------------------------------------------
    # CU01: Gestionar Empresas Contratantes (Tenants)
    # -------------------------------------------------------------
    def test_cu01_list_companies_superadmin(self, superadmin_token):
        resp = client.get(
            "/api/saas/companies",
            headers={"Authorization": f"Bearer {superadmin_token}"}
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert isinstance(data, list)
        names = [c["name"] for c in data]
        assert "Boutique Elegance" in names or len(names) > 0

    # -------------------------------------------------------------
    # CU02: Gestionar Planes de Suscripción
    # -------------------------------------------------------------
    def test_cu02_list_plans_superadmin(self, superadmin_token):
        resp = client.get(
            "/api/saas/plans",
            headers={"Authorization": f"Bearer {superadmin_token}"}
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert isinstance(data, list)
        codes = [p["code"] for p in data]
        assert "basic" in codes or "pro" in codes

    # -------------------------------------------------------------
    # CU03: Autenticación Multitenant con JWT
    # -------------------------------------------------------------
    def test_cu03_authentication_and_jwt_claims(self, elegance_admin_token):
        # Verificar token contra endpoint protegido /me
        resp = client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {elegance_admin_token}"}
        )
        assert resp.status_code == 200, resp.text
        user = resp.json()["data"]
        assert user["email"] == "admin@elegance.com"
        assert user["tenant_id"] is not None
        assert user["rol"] == "administrador"

    # -------------------------------------------------------------
    # CU04: Gestionar Sucursales Bajo Límites del Plan
    # -------------------------------------------------------------
    def test_cu04_branch_quota_inquiry(self, elegance_admin_token):
        resp = client.get(
            "/api/branches/quota",
            headers={"Authorization": f"Bearer {elegance_admin_token}"}
        )
        assert resp.status_code == 200, resp.text
        quota = resp.json()["data"]
        assert "current_active_branches" in quota
        assert "max_branches" in quota
        assert "can_create_branch" in quota

    # -------------------------------------------------------------
    # CU05: Consultar y Actualizar Perfil de Usuario
    # -------------------------------------------------------------
    def test_cu05_get_and_update_profile(self, client_token):
        # 1. Consultar
        resp = client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {client_token}"}
        )
        assert resp.status_code == 200
        original = resp.json()["data"]
        
        # 2. Actualizar
        new_name = "Cliente Nombre Modificado"
        update_resp = client.put(
            "/api/users/me",
            headers={"Authorization": f"Bearer {client_token}"},
            json={
                "name": new_name,
                "email": original["email"],
                "gender": "femenino"
            }
        )
        assert update_resp.status_code == 200
        updated = update_resp.json()["data"]
        assert updated["name"] == new_name

    # -------------------------------------------------------------
    # CU06 & CU07: Catálogo de Productos y Filtros
    # -------------------------------------------------------------
    def test_cu06_cu07_catalog_browse_and_filter(self):
        # Listado general de catálogo público
        resp = client.get("/api/catalog/products")
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert isinstance(data, list)

        # Filtro de búsqueda por query string
        filter_resp = client.get("/api/catalog/products?q=casual")
        assert filter_resp.status_code == 200
        filtered_data = filter_resp.json()["data"]
        assert isinstance(filtered_data, list)

    # -------------------------------------------------------------
    # CU08: Descargar Paquete de Catálogo Offline
    # -------------------------------------------------------------
    def test_cu08_download_offline_catalog_pack(self):
        resp = client.get("/api/catalog/offline-pack")
        assert resp.status_code == 200, resp.text
        pack = resp.json()["data"]
        assert "version" in pack
        assert "products" in pack
        assert "total_products" in pack
        assert "synced_at" in pack

    # -------------------------------------------------------------
    # CU09: Modo Offline y Sincronización Idempotente
    # -------------------------------------------------------------
    def test_cu09_offline_batch_sync_idempotency(self):
        operation_id = f"offline-op-{uuid.uuid4()}"
        batch = {
            "operations": [
                {
                    "client_operation_id": operation_id,
                    "operation_type": "OFFLINE_CART_ITEM",
                    "payload": {"sku": "SKU-TEST-001", "quantity": 2, "price": 45.0}
                }
            ]
        }
        # Intento 1: Procesado
        r1 = client.post("/api/catalog/offline-sync", json=batch)
        assert r1.status_code == 201
        res1 = r1.json()["data"]
        assert res1["processed_count"] == 1
        assert res1["skipped_count"] == 0

        # Intento 2: Detectado como duplicado (idempotencia)
        r2 = client.post("/api/catalog/offline-sync", json=batch)
        assert r2.status_code == 201
        res2 = r2.json()["data"]
        assert res2["processed_count"] == 0
        assert res2["skipped_count"] == 1
        assert res2["skipped"][0]["reason"] == "ALREADY_SYNCED"

    # -------------------------------------------------------------
    # CU10: Consultar Disponibilidad de Inventario
    # -------------------------------------------------------------
    def test_cu10_inventory_availability_check(self, elegance_admin_token):
        # Inventario consolidado
        resp = client.get(
            "/api/inventory/consolidated",
            headers={"Authorization": f"Bearer {elegance_admin_token}"}
        )
        assert resp.status_code == 200, resp.text
        stock_data = resp.json()["data"]
        assert isinstance(stock_data, list)
