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

### Hito 2: Consulta de Disponibilidad de Inventario por Sucursal (CU10 - TAREA INMEDIATA)
1. **Backend `p3_gestion_inventario_disponibilidad`:**
   - [ ] Consolidar endpoint `/api/inventory/consolidated` y `/api/catalog/availability`.
   - [ ] Asegurar consulta real de `quantity` (stock físico) y `reserved_quantity` (stock reservado) por variante, talla y sucursal.
   - [ ] Suite de pruebas de disponibilidad real multisede (eliminando el falso positivo de test previo).

---

### Hito 3: Persistencia Local y Modo Offline del Catálogo (CU08 & CU09)
1. **Frontend PWA (Angular 21):**
   - [ ] Configurar `@angular/pwa`, Service Worker y Web App Manifest.
   - [ ] Crear `src/app/core/offline/idb.service.ts` para consumir `/api/catalog/offline-pack` y almacenar catálogo en IndexedDB.
   - [ ] Banner visual de estado de conectividad con advertencia de datos locales en caché.
2. **Aplicación Móvil (Flutter / Dart):**
   - [ ] Persistencia local en SQLite (`sqflite`) consumiendo `/api/catalog/offline-pack`.
