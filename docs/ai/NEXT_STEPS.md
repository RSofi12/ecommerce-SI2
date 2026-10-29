# NEXT STEPS — FASHIONSTORE SAAS MULTITENANT

## Tareas de Implementación (Presentación 2)

### Hito 1: Núcleo SaaS Multitenant, Planes y Catálogo (CU01 a CU07 COMPLETADOS)
- [x] Portal Superadmin con alta de empresas y Downgrade Guard en planes.
- [x] Autenticación JWT con inyección obligatoria de `tenant_id`, `rol`, `branch_id`.
- [x] Gestión de sucursales bloqueando el límite del plan (2 vs 10) con widget reactivo en Angular 21.
- [x] Endpoints `/api/users/me` para consulta y edición de perfil.
- [x] Catálogo de prendas y variantes multitenant con aislamiento por `tenant_id`.

---

### Hito 2: Consulta de Disponibilidad y Modo Offline (CU08, CU09, CU10 COMPLETADOS)
- [x] Disponibilidad multisede en backend (`/api/catalog/availability`), modal en Angular 21 y Bottom Sheet en Flutter.
- [x] Motor IndexedDB en PWA (`fashionstore_local_db`) y SQLite nativo en Flutter (`local_catalog_db.dart`).
- [x] Resiliencia ante caídas de red y toggle de simulación offline.

---

### Hito 3: Traslados y Compra con Stripe (CU11 y CU12 COMPLETADOS FULLSTACK)
- [x] **CU11:** Traslados entre sucursales con ciclo `EN_TRANSITO` -> `COMPLETADO` / `CANCELADO` en Backend y Web (`transfers-page`).
- [x] **CU12:** Compra con Stripe y despacho condicionado (Política 3) en Backend, Frontend Web y Mobile Flutter. Línea de vida ICONIX de 5 etapas.

---

### Hito 4: Consolidación Definitiva de Base de Datos para Todos los CUs (COMPLETADO)
- [x] **Migración Maestra 0044 (`0044_complete_database_schema_all_use_cases.py`):**
  - [x] `tenant_id` y claves foráneas añadidas a todas las tablas restantes (`reservations`, `sales`, `conversations`, etc.).
  - [x] Tablas de políticas de negocio creadas: `garment_exchanges` (CU19) y `garment_returns` (CU20).
  - [x] Tabla de sincronización idempotente creada: `sync_operations` (CU18).
  - [x] Tablas de Inteligencia Artificial y Machine Learning creadas: `ml_models`, `demand_forecasts` (CU26), `customer_segments` (CU27).
  - [x] Columnas de auditoría y contingencia offline: `client_sale_id`, `is_offline`, `synced_at` en `sales`; `resolved_at`, `resolved_by`, `resolution_note` en `reservations`.
- [x] **Modelos ORM & Shims:** Modelos SQLAlchemy implementados en paquetes de dominio y re-exportados en `app/models/` sin dependencias circulares.
- [x] **Matriz de Trazabilidad:** Integrada en [`docs/ACTORS_AND_USE_CASES.md`](file:///c:/Users/PERSONAL/ecommerce-SI2/docs/ACTORS_AND_USE_CASES.md) (Sección 3).
- [x] **Base de datos congelada:** Cero migraciones DDL adicionales necesarias.

---

### Hito 5: Próximos Casos de Uso a Implementar (Presentación 2)

#### Prioridad Inmediata A: Reservas de Prendas en Tienda Física (CU13 y CU14)
1. **CU13: Crear Reserva de Prendas con Vencimiento:**
   - [x] Backend: Lógica en `reservation_service.py` (`POST /api/reservations`), incremento de `reserved_quantity` en `inventory`, validación de fechas (hoy a 7 días), temporizador de expiración (`expires_at = visit_date + 24h`), aislamiento `tenant_id`, códigos QR/amigables y suite de tests (7/7 PASSED).
   - [x] Frontend Web: Rediseño estético (/frontend-design & /design-taste-frontend), sidebar con branding FashionStore, tipografía Montserrat Regular (400), favicon y título actualizados, vista de reserva (`reservations-page`), selección de sucursal de visita, pills dinámicas de disponibilidad, dossier flotante con recordatorio de 24h, almacenamiento offline en IndexedDB ([`idb-reservations.service.ts`](file:///c:/Users/PERSONAL/ecommerce-SI2/frontend/src/app/core/offline/idb-reservations.service.ts)), modal voucher con código y QR, y vista "Mis Reservas" (`my-reservations-page`) con tickets boutique y sincronización offline masiva.
   - [ ] Mobile Flutter: Pantalla de reserva de prendas con selector de sucursal, ticket digital con código QR y persistencia SQLite offline.
2. **CU14: Atender y Resolver Conflictos de Reservas:**
   - [ ] Backend: Tarea periódica de expiración (`expire_daily.py`), endpoints de resolución `/api/reservations/{id}/resolve`.
   - [ ] Frontend Web: Panel de encargado de sucursal para liberar prendas no retiradas a stock general.

#### Prioridad Inmediata B: Ventas POS Offline y Sincronización Idempotente (CU16, CU17, CU18)
1. **CU16: Registrar Venta Offline en Efectivo con UUIDv4:**
   - [ ] Frontend/Mobile: Generación de UUIDv4 en cliente, registro en almacén local offline (`PENDIENTE_SYNC`).
2. **CU17: Bandeja Local de Operaciones Pendientes:**
   - [ ] UI de caja con contador de ventas pendientes de subir y botón de forzar sincronización.
3. **CU18: Sincronización de Lotes con Idempotencia:**
   - [ ] Backend: Endpoint `POST /api/sales/offline/batch-sync` contra tabla `sync_operations`. Si el `client_operation_id` ya fue procesado, confirmar sin duplicar venta ni descontar inventario dos veces.
