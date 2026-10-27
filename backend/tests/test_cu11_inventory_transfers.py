import uuid
import pytest
from fastapi.testclient import TestClient

try:
    from backend.main import app
except ModuleNotFoundError:
    from main import app

client = TestClient(app)


class TestCU11InventoryTransfers:
    """
    Suite de verificación formal para el CU11:
    Registrar y Autorizar Traslados de Mercadería entre Sucursales (Presentación 2)
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
    def elegance_branches_and_variant(self, elegance_admin_auth):
        headers = elegance_admin_auth["headers"]
        branches_resp = client.get("/api/branches/", headers=headers)
        assert branches_resp.status_code == 200
        branches = branches_resp.json()["data"]
        assert len(branches) >= 2, "Boutique Elegance debe tener al menos 2 sucursales para traslados"

        branch_a = branches[0]["id"]
        branch_b = branches[1]["id"]

        # Obtener un producto y variante de Elegance
        products_resp = client.get("/api/catalog/products/admin", headers=headers)
        assert products_resp.status_code == 200
        products = products_resp.json()["data"]
        assert len(products) > 0, "Debe existir al menos un producto para Elegance"

        variant_id = products[0]["variants"][0]["id"]

        # Asegurar stock inicial en sucursal A mediante ingreso
        income_resp = client.post("/api/inventory/movements/income", headers=headers, json={
            "variant_id": variant_id,
            "branch_id": branch_a,
            "quantity": 50,
            "note": "Carga inicial de prueba para traslados CU11",
        })
        assert income_resp.status_code == 201

        return {
            "branch_a": branch_a,
            "branch_b": branch_b,
            "variant_id": variant_id,
        }

    def test_01_create_transfer_in_transit_decrements_origin_stock(self, elegance_admin_auth, elegance_branches_and_variant):
        headers = elegance_admin_auth["headers"]
        branch_a = elegance_branches_and_variant["branch_a"]
        branch_b = elegance_branches_and_variant["branch_b"]
        variant_id = elegance_branches_and_variant["variant_id"]

        # Consultar stock previo en A y B
        stock_a_prev = client.get(f"/api/inventory/branches/{branch_a}", headers=headers).json()["data"]
        item_a_prev = next((item for item in stock_a_prev if item["variant_id"] == variant_id), None)
        qty_a_prev = item_a_prev["quantity"] if item_a_prev else 0

        stock_b_prev = client.get(f"/api/inventory/branches/{branch_b}", headers=headers).json()["data"]
        item_b_prev = next((item for item in stock_b_prev if item["variant_id"] == variant_id), None)
        qty_b_prev = item_b_prev["quantity"] if item_b_prev else 0

        # Crear orden de traslado para 7 unidades
        transfer_payload = {
            "from_branch_id": branch_a,
            "to_branch_id": branch_b,
            "items": [
                {"variant_id": variant_id, "quantity": 7}
            ],
            "notes": "Prueba de traslado de mercadería CU11",
        }
        create_resp = client.post("/api/inventory/transfers", headers=headers, json=transfer_payload)
        assert create_resp.status_code == 201, f"Fallo al crear traslado: {create_resp.text}"

        transfer_data = create_resp.json()["data"]
        assert transfer_data["status"] == "EN_TRANSITO"
        assert transfer_data["transfer_number"].startswith("TRF-")
        assert len(transfer_data["items"]) == 1
        assert transfer_data["items"][0]["quantity"] == 7

        transfer_id = transfer_data["id"]

        # Verificar que el stock en origen se decrementó
        stock_a_post = client.get(f"/api/inventory/branches/{branch_a}", headers=headers).json()["data"]
        item_a_post = next((item for item in stock_a_post if item["variant_id"] == variant_id), None)
        assert item_a_post["quantity"] == qty_a_prev - 7

        # Verificar que el stock en destino aún NO se incrementó (sigue en tránsito)
        stock_b_post = client.get(f"/api/inventory/branches/{branch_b}", headers=headers).json()["data"]
        item_b_post = next((item for item in stock_b_post if item["variant_id"] == variant_id), None)
        qty_b_post = item_b_post["quantity"] if item_b_post else 0
        assert qty_b_post == qty_b_prev

        # Guardar en contexto para el siguiente test
        elegance_branches_and_variant["last_transfer_id"] = transfer_id
        elegance_branches_and_variant["qty_b_before_receipt"] = qty_b_post

    def test_02_receive_transfer_increments_destination_stock(self, elegance_admin_auth, elegance_branches_and_variant):
        headers = elegance_admin_auth["headers"]
        branch_b = elegance_branches_and_variant["branch_b"]
        variant_id = elegance_branches_and_variant["variant_id"]
        transfer_id = elegance_branches_and_variant["last_transfer_id"]
        qty_b_prev = elegance_branches_and_variant["qty_b_before_receipt"]

        # Confirmar recepción física en destino
        receive_resp = client.post(
            f"/api/inventory/transfers/{transfer_id}/receive",
            headers=headers,
            json={"notes": "Mercadería recibida en perfecto estado en sucursal destino"},
        )
        assert receive_resp.status_code == 200, f"Fallo al recibir traslado: {receive_resp.text}"

        transfer_data = receive_resp.json()["data"]
        assert transfer_data["status"] == "COMPLETADO"
        assert transfer_data["received_at"] is not None
        assert transfer_data["received_by_name"] is not None

        # Verificar que ahora sí se incrementó el stock en destino
        stock_b_post = client.get(f"/api/inventory/branches/{branch_b}", headers=headers).json()["data"]
        item_b_post = next((item for item in stock_b_post if item["variant_id"] == variant_id), None)
        assert item_b_post["quantity"] == qty_b_prev + 7

    def test_03_insufficient_stock_prevents_transfer(self, elegance_admin_auth, elegance_branches_and_variant):
        headers = elegance_admin_auth["headers"]
        branch_a = elegance_branches_and_variant["branch_a"]
        branch_b = elegance_branches_and_variant["branch_b"]
        variant_id = elegance_branches_and_variant["variant_id"]

        transfer_payload = {
            "from_branch_id": branch_a,
            "to_branch_id": branch_b,
            "items": [
                {"variant_id": variant_id, "quantity": 999999}
            ],
            "notes": "Intento de traslado imposible por exceso de cantidad",
        }
        resp = client.post("/api/inventory/transfers", headers=headers, json=transfer_payload)
        assert resp.status_code == 400
        msg = resp.json().get("detail") or resp.json().get("message", "")
        assert "Stock insuficiente" in msg

    def test_04_cross_tenant_transfer_rejected(self, elegance_admin_auth, modaurbana_admin_auth, elegance_branches_and_variant):
        headers = elegance_admin_auth["headers"]
        branch_a = elegance_branches_and_variant["branch_a"]
        variant_id = elegance_branches_and_variant["variant_id"]

        # Obtener una sucursal de Moda Urbana
        urbana_headers = modaurbana_admin_auth["headers"]
        urbana_branches_resp = client.get("/api/branches/", headers=urbana_headers)
        assert urbana_branches_resp.status_code == 200
        urbana_branch_id = urbana_branches_resp.json()["data"][0]["id"]

        # Intentar transferir desde Boutique Elegance hacia Moda Urbana
        transfer_payload = {
            "from_branch_id": branch_a,
            "to_branch_id": urbana_branch_id,
            "items": [
                {"variant_id": variant_id, "quantity": 2}
            ],
            "notes": "Intento de fuga multitenant",
        }
        resp = client.post("/api/inventory/transfers", headers=headers, json=transfer_payload)
        assert resp.status_code == 400
        msg = resp.json().get("detail") or resp.json().get("message", "")
        assert "no pertenece a tu empresa" in msg

    def test_05_cancel_transfer_restores_origin_stock(self, elegance_admin_auth, elegance_branches_and_variant):
        headers = elegance_admin_auth["headers"]
        branch_a = elegance_branches_and_variant["branch_a"]
        branch_b = elegance_branches_and_variant["branch_b"]
        variant_id = elegance_branches_and_variant["variant_id"]

        # Stock antes del traslado
        stock_a_prev = client.get(f"/api/inventory/branches/{branch_a}", headers=headers).json()["data"]
        item_a_prev = next((item for item in stock_a_prev if item["variant_id"] == variant_id), None)
        qty_a_prev = item_a_prev["quantity"] if item_a_prev else 0

        # Crear traslado para 4 unidades
        create_resp = client.post("/api/inventory/transfers", headers=headers, json={
            "from_branch_id": branch_a,
            "to_branch_id": branch_b,
            "items": [{"variant_id": variant_id, "quantity": 4}],
            "notes": "Traslado a cancelar",
        })
        assert create_resp.status_code == 201
        transfer_id = create_resp.json()["data"]["id"]

        # Stock en origen se descontó 4
        stock_a_mid = client.get(f"/api/inventory/branches/{branch_a}", headers=headers).json()["data"]
        item_a_mid = next((item for item in stock_a_mid if item["variant_id"] == variant_id), None)
        assert item_a_mid["quantity"] == qty_a_prev - 4

        # Cancelar traslado
        cancel_resp = client.post(
            f"/api/inventory/transfers/{transfer_id}/cancel",
            headers=headers,
            json={"reason": "Vehículo de transporte descompuesto"},
        )
        assert cancel_resp.status_code == 200
        assert cancel_resp.json()["data"]["status"] == "CANCELADO"

        # Stock en origen fue restituido en 4
        stock_a_restored = client.get(f"/api/inventory/branches/{branch_a}", headers=headers).json()["data"]
        item_a_restored = next((item for item in stock_a_restored if item["variant_id"] == variant_id), None)
        assert item_a_restored["quantity"] == qty_a_prev
