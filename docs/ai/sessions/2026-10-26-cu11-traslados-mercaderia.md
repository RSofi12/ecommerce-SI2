# Sesión de Implementación: CU11 — Registrar y Autorizar Traslados de Mercadería entre Sucursales

- **Fecha:** 26 de Octubre de 2026
- **Autor / Rol:** Antigravity (Senior Architect) & Developer
- **Objetivo:** Implementación completa del Caso de Uso 11 (**CU11: Registrar y Autorizar Traslados de Mercadería entre Sucursales**) perteneciente a la **Presentación 2 (meta: 21 CUs acumulados)**, cubriendo base de datos, backend FastAPI, modelos SQLAlchemy, schemas Pydantic, servicios de dominio, endpoints REST protegidos con aislamiento multitenant, suite de pruebas automatizadas y Frontend Web en Angular 21 (PWA).

---

## 1. 🎯 Alcance del Caso de Uso (CU11 - ICONIX)
- **Actores:** Encargado de Sucursal (Principal), Administrador de Empresa (Principal en Backoffice), Backend API (Secundario).
- **Plataforma:** Web (Backoffice Administrativo y Operativo de Sucursal).
- **Regla de Negocio Sagrada:**
  1. El despacho crea la orden en estado `EN_TRANSITO` y descuenta inmediatamente el stock disponible de la sucursal emisora para evitar sobreventas o duplicidades ($StockDisponible = \max(quantity - reserved, 0)$).
  2. La mercadería en tránsito NO incrementa el stock de la sucursal destino hasta que el encargado receptor confirme físicamente la recepción (`POST /api/inventory/transfers/{id}/receive`), pasando la orden a `COMPLETADO`.
  3. Si la orden se cancela antes de su recepción (`POST /api/inventory/transfers/{id}/cancel`), el stock se restituye íntegramente a la sucursal de origen (`CANCELADO`).
  4. Aislamiento multitenant estricto: Una sucursal solo puede trasladar mercadería hacia otra sucursal de su propia empresa (`tenant_id`).

---

## 2. 🗄️ Base de Datos y Persistencia (Alembic Migration 0042)
- **Migración:** [`backend/alembic/versions/0042_add_inventory_transfers.py`](file:///c:/Users/PERSONAL/ecommerce-SI2/backend/alembic/versions/0042_add_inventory_transfers.py).
- **Tablas Creadas:**
  - `inventory_transfers`:
    - `id` (UUID PK)
    - `tenant_id` (UUID FK `companies.id` CASCADE)
    - `transfer_number` (VARCHAR(32) UNIQUE, formato `TRF-YYYYMMDD-XXXX`)
    - `from_branch_id` (UUID FK `branches.id`)
    - `to_branch_id` (UUID FK `branches.id`)
    - `status` (VARCHAR(20), `'SOLICITADO'`, `'EN_TRANSITO'`, `'COMPLETADO'`, `'CANCELADO'`)
    - `requested_by` (UUID FK `users.id`)
    - `received_by` (UUID FK `users.id` NULLABLE)
    - `requested_at` (TIMESTAMPTZ)
    - `received_at` (TIMESTAMPTZ NULLABLE)
    - `notes` (TEXT NULLABLE)
    - `created_at`, `updated_at` (TIMESTAMPTZ)
  - `inventory_transfer_items`:
    - `id` (UUID PK)
    - `transfer_id` (UUID FK `inventory_transfers.id` CASCADE)
    - `variant_id` (UUID FK `product_variants.id`)
    - `quantity` (INTEGER > 0)
    - `received_quantity` (INTEGER NULLABLE)
    - `created_at` (TIMESTAMPTZ)

---

## 3. ⚙️ Backend (FastAPI + SQLAlchemy)

### Módulos y Arquitectura Profunda:
- **Modelo:** [`backend/app/packages/p3_gestion_inventario_disponibilidad/models/inventory_transfer.py`](file:///c:/Users/PERSONAL/ecommerce-SI2/backend/app/packages/p3_gestion_inventario_disponibilidad/models/inventory_transfer.py)
  - Definición de `InventoryTransfer` e `InventoryTransferItem` con relaciones a `from_branch`, `to_branch`, `requester`, `receiver`, e `items`.
- **Schemas:** [`backend/app/packages/p3_gestion_inventario_disponibilidad/schemas/transfer_schema.py`](file:///c:/Users/PERSONAL/ecommerce-SI2/backend/app/packages/p3_gestion_inventario_disponibilidad/schemas/transfer_schema.py)
  - DTOs tipados: `TransferStatusEnum`, `TransferItemCreate`, `InventoryTransferCreate`, `InventoryTransferReceive`, `InventoryTransferCancel`, `InventoryTransferRead`.
- **Servicios:** [`backend/app/packages/p3_gestion_inventario_disponibilidad/services/transfer_service.py`](file:///c:/Users/PERSONAL/ecommerce-SI2/backend/app/packages/p3_gestion_inventario_disponibilidad/services/transfer_service.py)
  - `create_and_dispatch_transfer`: Valida `tenant_id`, chequea disponibilidad de stock, decrementa inventario origen, asienta movimiento `transfer_out` y crea orden en `EN_TRANSITO`.
  - `receive_transfer`: Valida sucursal receptora y estado `EN_TRANSITO`, incrementa inventario destino, asienta movimiento `transfer_in` y marca `COMPLETADO`.
  - `cancel_transfer`: Restituye inventario origen, asienta movimiento de restitución y marca `CANCELADO`.
  - `list_transfers` & `get_transfer_detail`: Consulta filtrada por sucursal y estado con serialización completa.
- **Rutas REST:** [`backend/app/packages/p3_gestion_inventario_disponibilidad/routes/transfer_routes.py`](file:///c:/Users/PERSONAL/ecommerce-SI2/backend/app/packages/p3_gestion_inventario_disponibilidad/routes/transfer_routes.py)
  - `POST /api/inventory/transfers`: Despachar nuevo traslado (administrador y encargado).
  - `GET /api/inventory/transfers`: Listar traslados con filtros por sucursal y estado.
  - `GET /api/inventory/transfers/{transfer_id}`: Ver detalle de traslado.
  - `POST /api/inventory/transfers/{transfer_id}/receive`: Confirmar recepción de mercadería.
  - `POST /api/inventory/transfers/{transfer_id}/cancel`: Cancelar traslado y restituir inventario.
- **Shims Zero-Breakage:**
  - [`backend/app/models/inventory_transfer.py`](file:///c:/Users/PERSONAL/ecommerce-SI2/backend/app/models/inventory_transfer.py)
  - [`backend/app/schemas/transfer_schema.py`](file:///c:/Users/PERSONAL/ecommerce-SI2/backend/app/schemas/transfer_schema.py)
  - [`backend/app/services/transfer_service.py`](file:///c:/Users/PERSONAL/ecommerce-SI2/backend/app/services/transfer_service.py)
  - [`backend/app/routes/transfer_routes.py`](file:///c:/Users/PERSONAL/ecommerce-SI2/backend/app/routes/transfer_routes.py)

---

## 4. 🧪 Suite de Pruebas Automatizadas (Pytest)
- **Archivo:** [`backend/tests/test_cu11_inventory_transfers.py`](file:///c:/Users/PERSONAL/ecommerce-SI2/backend/tests/test_cu11_inventory_transfers.py)
- **Resultados de Ejecución:**
  1. `test_01_create_transfer_in_transit_decrements_origin_stock`: **PASSED** (Verifica orden en `EN_TRANSITO`, descuento de stock en origen y sin alteración en destino).
  2. `test_02_receive_transfer_increments_destination_stock`: **PASSED** (Verifica recepción, incremento de stock en destino y estado `COMPLETADO`).
  3. `test_03_insufficient_stock_prevents_transfer`: **PASSED** (Verifica bloqueo con `HTTP 400` y mensaje "Stock insuficiente").
  4. `test_04_cross_tenant_transfer_rejected`: **PASSED** (Verifica rechazo con `HTTP 400` ante intento de envío a sucursal de otra empresa multitenant).
  5. `test_05_cancel_transfer_restores_origin_stock`: **PASSED** (Verifica cancelación y restitución íntegra de stock al origen).
- **Total:** **5/5 PASSED (100% de efectividad)**.

---

## 5. 💻 Frontend Web (Angular 21 PWA)
- **Modelos:** Tipos `InventoryTransfer`, `InventoryTransferItem`, `TransferStatus`, `CreateTransferPayload`, `ReceiveTransferPayload`, `CancelTransferPayload` en [`frontend/src/app/features/shared/models/inventory.model.ts`](file:///c:/Users/PERSONAL/ecommerce-SI2/frontend/src/app/features/shared/models/inventory.model.ts).
- **Servicios:** Endpoints de traslados agregados en [`frontend/src/app/features/shared/services/inventory-api.service.ts`](file:///c:/Users/PERSONAL/ecommerce-SI2/frontend/src/app/features/shared/services/inventory-api.service.ts).
- **Página de Traslados:** [`frontend/src/app/features/encargado/pages/transfers-page.component.ts`](file:///c:/Users/PERSONAL/ecommerce-SI2/frontend/src/app/features/encargado/pages/transfers-page.component.ts) y [`transfers-page.component.html`](file:///c:/Users/PERSONAL/ecommerce-SI2/frontend/src/app/features/encargado/pages/transfers-page.component.html):
  - KPIs: En Tránsito, Por Recibir, Completados, Total Histórico.
  - Filtros: Tabs Salientes / Entrantes y selector de estado.
  - Tabla de operaciones con badges semánticos (`EN_TRANSITO`, `COMPLETADO`, `CANCELADO`).
  - Modal reactivo "Nuevo Traslado" con validación de stock disponible en origen y bloqueo de autofacturación / traslados inválidos.
  - Modal "Confirmar Recepción" para incorporar prendas a la tienda física destino.
  - Modal "Cancelar Traslado" con advertencia de restitución de stock a origen.
- **Rutas y Navegación:**
  - Registrado en [`frontend/src/app/app.routes.ts`](file:///c:/Users/PERSONAL/ecommerce-SI2/frontend/src/app/app.routes.ts) en `/app/encargado/transfers` y `/app/admin/transfers`.
  - Agregado en el sidebar de navegación en [`frontend/src/app/core/layouts/app-shell.component.ts`](file:///c:/Users/PERSONAL/ecommerce-SI2/frontend/src/app/core/layouts/app-shell.component.ts).

---

## 6. 📱 Aplicación Móvil
- Conforme a la especificación oficial de [`docs/ACTORS_AND_USE_CASES.md`](file:///c:/Users/PERSONAL/ecommerce-SI2/docs/ACTORS_AND_USE_CASES.md), CU11 es una operación estrictamente de **Web Backoffice** (Encargado y Admin). No requiere pantallas operativas en la aplicación móvil de clientes/cajeros.
