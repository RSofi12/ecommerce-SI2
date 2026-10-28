# NEXT STEPS — FASHIONSTORE SAAS MULTITENANT

## Tareas Inmediatas de Implementación (Presentación 1: 25/10/2026)

### Hito 1: Núcleo SaaS Multitenant, Planes y Catálogo (CU01 a CU07 COMPLETADOS)
1. **CU01, CU02, CU03, CU04 & CU05 (Plataforma y Acceso):**
   - [x] Portal Superadmin con alta de empresas y Downgrade Guard en planes.
   - [x] Autenticación JWT con inyección obligatoria de `tenant_id`, `rol`, `branch_id`.
   - [x] Gestión de sucursales bloqueando el límite del plan (2 vs 10) con widget reactivo en Angular 21.
   - [x] Endpoints `/api/users/me` para consulta y edición de perfil.
2. **CU06 & CU07: Catálogo de Prendas y Variantes Multitenant (COMPLETADOS):**
   - [x] Migración `0041` aplicada en PostgreSQL con `tenant_id` en `products`, `product_variants` e `inventory`.
   - [x] Backend `p2_gestion_productos_catalogo`: inyección estricta de `tenant_id` desde JWT en `create_product()`, `update_product()`, `delete_product()` y `list_admin_products()`.
   - [x] Precios diferenciados por talla en variantes (fundamento para cambios de prenda con diferencia en CU19).
   - [x] Consolidación transaccional con `db.commit()` en `catalog_service.py`.
   - [x] Filtro facetado por `tenant_id` en catálogo público (`/api/catalog/products?tenant_id=...`).
   - [x] Suite de pruebas `test_cu06_cu07_multitenant_catalog.py` (4/4 PASSED).

---

### Hito 2: Consulta de Disponibilidad de Inventario por Sucursal (CU10 - COMPLETADO)
1. **Backend `p3_gestion_inventario_disponibilidad` y `p2_gestion_productos_catalogo`:**
   - [x] Consolidar endpoint `/api/inventory/consolidated` y `/api/inventory/branches/{branch_id}` con filtrado estricto por `tenant_id`.
   - [x] Extender `/api/catalog/availability` para soporte multisede (desglose por sucursales activas del tenant, stock disponible real $StockDisponible = \max(quantity - reserved, 0)$ y total disponible).
   - [x] Suite de pruebas unitarias e integración en `test_cu10_stock_availability.py` (4/4 PASSED).
2. **Frontend Web (Angular 21):**
   - [x] Implementar modal de disponibilidad por sucursales físicas en `ProductDetailPageComponent` bajo lineamientos de `frontend-design`.
   - [x] Integrar método `getVariantMultiBranchAvailability` en `CatalogApiService`.
   - [x] Compilación validada con `ng build` (0 errores).
3. **Limpieza de Repositorio:**
   - [x] Eliminada carpeta `scratch/` de la raíz del proyecto.

---

### Hito 3: Persistencia Local y Modo Offline del Catálogo (CU08 & CU09 - COMPLETADOS)
1. **Frontend PWA (Angular 21):**
   - [x] Crear [`idb-catalog.service.ts`](file:///c:/Users/PERSONAL/ecommerce-SI2/frontend/src/app/core/offline/idb-catalog.service.ts) sobre API IndexedDB nativa (`fashionstore_local_db` v1 con almacenes `catalog_products` y `catalog_meta`).
   - [x] Crear [`network-status.service.ts`](file:///c:/Users/PERSONAL/ecommerce-SI2/frontend/src/app/core/offline/network-status.service.ts) con escucha de eventos de red y soporte de simulación desconectada.
   - [x] Conmutación transparente a IndexedDB en [`catalog-page.component.ts`](file:///c:/Users/PERSONAL/ecommerce-SI2/frontend/src/app/features/cliente/pages/catalog-page.component.ts) con filtrado multicriterio en memoria.
   - [x] Banner visual en ámbar/pizarra con timestamp de sincronización y badge dinámico de conteo en caché.
   - [x] Botón explícito de descarga / refresco de catálogo local (`CU08`).
   - [x] Refinamiento estético y funcional en matriz de variantes de [`admin-catalog-page.component.html`](file:///c:/Users/PERSONAL/ecommerce-SI2/frontend/src/app/features/admin/pages/admin-catalog-page.component.html) (`frontend-design`).
   - [x] Compilación validada con `ng build` (0 errores de TypeScript y plantillas).

---

### Hito 4: Presentación 2 — Traslados Multisede y Pagos con Stripe (CU11 y CU12 BACKEND COMPLETADOS)
1. **CU11: Registrar y Autorizar Traslados de Mercadería (COMPLETADO):**
   - [x] Migración Alembic `0042_add_inventory_transfers.py` con tablas `inventory_transfers` e `inventory_transfer_items`.
   - [x] Endpoints en `p3_gestion_inventario_disponibilidad` (`POST /api/inventory/transfers`, `GET /api/inventory/transfers`, `POST /api/inventory/transfers/{id}/receive`, `POST /api/inventory/transfers/{id}/cancel`).
   - [x] Reglas de negocio sagradas: descuento preventivo en origen al despachar (`EN_TRANSITO`), retención en carretera sin tocar destino, acreditación al confirmar recepción (`COMPLETADO`) y restitución a origen al anular (`CANCELADO`).
   - [x] Suite de pruebas automatizadas en `backend/tests/test_cu11_inventory_transfers.py` (5/5 PASSED).
   - [x] Frontend Web en Angular 21: [`transfers-page.component.ts`](file:///c:/Users/PERSONAL/ecommerce-SI2/frontend/src/app/features/encargado/pages/transfers-page.component.ts) en `/app/encargado/transfers` y `/app/admin/transfers`.

2. **CU12: Comprar Prendas con Stripe y Despacho Condicionado (BACKEND & BD CONSOLIDADO):**
   - [x] Migración Alembic `0043_add_order_tenant_and_dispatch.py` aplicada (`tenant_id`, `delivery_type`, `shipping_address`, `tracking_number`, `dispatched_at`, `dispatched_by` en `orders`, y `tenant_id` en `order_items`, `carts`, `cart_items`, `payment_attempts`).
   - [x] Enum `fulfillmentstatusenum` ampliado en PostgreSQL (`ready_for_dispatch`, `dispatched`, `delivered`).
   - [x] **Política de Negocio 3 (Inviolable):** Bloqueo estricto de despacho en `order_service.py` (`dispatch_order`) si `payment_status != 'paid'`.
   - [x] Webhook `process_stripe_event` generando guía única `DSP-YYYYMMDD-XXXX` al recibir `payment_intent.succeeded`.
   - [x] Endpoints `POST /api/orders/{order_id}/dispatch` y `GET /api/orders/tracking/{tracking_number}` implementados y protegidos por rol y multitenant.
   - [x] Suite automatizada `test_cu12_stripe_conditioned_dispatch.py` (5/5 PASSED).

3. **Próximos Pasos Inmediatos:**
   - [ ] Frontend Web (Angular 21): Vista de Checkout con pasarela Stripe Elements para el cliente y pantalla de Despacho/Rastreo para administración.
   - [ ] CU13 – Registrar Reserva de Prendas (Online y Offline).
   - [ ] CU14 – Atender Reserva y Resolver Conflictos de Stock.
