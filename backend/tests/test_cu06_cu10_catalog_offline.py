import uuid
import pytest
from fastapi.testclient import TestClient

try:
    from backend.main import app
except ModuleNotFoundError:
    from main import app

client = TestClient(app)


def test_cu07_filter_catalog():
    # CU07: Filtrar catálogo público con parámetros de búsqueda
    resp = client.get("/api/catalog/products?q=Camisa")
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert isinstance(data["data"], list)


def test_cu08_download_offline_pack():
    # CU08: Descargar paquete de catálogo completo para almacenamiento offline (IndexedDB / SQLite)
    resp = client.get("/api/catalog/offline-pack")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "products" in data
    assert "version" in data
    assert "synced_at" in data
    assert isinstance(data["products"], list)


def test_cu09_offline_sync_and_idempotency():
    # CU09: Modo offline y sincronización idempotente
    unique_op_id = f"op-{uuid.uuid4()}"
    payload = {
        "operations": [
            {
                "client_operation_id": unique_op_id,
                "operation_type": "OFFLINE_CART_VIEW",
                "payload": {"product_name": "Test Product Offline", "quantity": 1}
            }
        ]
    }

    # Primera sincronización: debe procesarse
    resp1 = client.post("/api/catalog/offline-sync", json=payload)
    assert resp1.status_code == 201
    data1 = resp1.json()["data"]
    assert data1["processed_count"] == 1
    assert data1["skipped_count"] == 0
    assert unique_op_id in data1["processed"]

    # Segunda sincronización con el mismo ID: debe omitirse por idempotencia
    resp2 = client.post("/api/catalog/offline-sync", json=payload)
    assert resp2.status_code == 201
    data2 = resp2.json()["data"]
    assert data2["processed_count"] == 0
    assert data2["skipped_count"] == 1
    assert data2["skipped"][0]["client_operation_id"] == unique_op_id
    assert data2["skipped"][0]["reason"] == "ALREADY_SYNCED"


def test_cu10_availability_missing_param():
    # CU10: Consultar disponibilidad requiere branch_id
    resp = client.get("/api/catalog/availability")
    assert resp.status_code == 422
