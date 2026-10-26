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

### Hito 4: Presentación 2 — Traslados Multisede y Pagos con Stripe (CU11 & CU12 - TAREA INMEDIATA)
1. **CU11: Registrar y Autorizar Traslados de Mercadería:**
   - [ ] Endpoints en `p3_gestion_inventario_disponibilidad` para creación de orden de traslado, validación de stock en origen, estado `EN_TRANSITO` y confirmación de recepción con estado `COMPLETADO`.
   - [ ] Pantalla y flujos en Frontend Web para encargados de sucursal.
2. **CU12: Comprar Prendas con Pasarela Stripe y Despacho Condicionado:**
   - [ ] Integración con Stripe API (`PaymentIntent` y webhooks `payment_intent.succeeded`).
   - [ ] **Política Inviolable:** Generación de orden de despacho logístico condicionada estrictamente a la confirmación de pago (`status = 'paid'`).
3. **Aplicación Móvil (Flutter / Dart):**
   - [ ] Persistencia local en SQLite (`sqflite`) consumiendo `/api/catalog/offline-pack`.
   - [ ] Mapa interactivo de sucursales con OpenStreetMap y geolocalización (CU21).
