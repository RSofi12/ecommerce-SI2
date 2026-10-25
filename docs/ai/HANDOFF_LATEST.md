# HANDOFF LATEST — FASHIONSTORE SAAS MULTITENANT

## Estado de Relevo Operativo al 25/10/2026

### 1. Avances Consolidados en esta Sesión
1. **CU01 – Registrar y Gestionar Empresas (Tenants):**
   - Backend `p0_saas_plataforma`: endpoints `/api/saas/companies`, aislamiento por `tenant_id`.
   - Frontend Web: Portal Superadmin en `/app/superadmin/tenants` con modal de creación y conmutación de estado.
2. **CU02 – Gestionar Planes de Suscripción y Límites Comerciales:**
   - Migración Alembic `0039` con descripciones comerciales y timestamps.
   - Endpoints `/api/saas/plans` y `/api/saas/subscriptions` con regla *Downgrade Guard*.
   - Frontend Web: [`subscription-modal.component.ts`](file:///c:/Users/PERSONAL/ecommerce-SI2/frontend/src/app/features/superadmin/components/subscription-modal.component.ts) integrado en `/app/superadmin/tenants` (botón "Gestionar Plan").
3. **CU04 – Gestionar Sucursales Bajo Límites del Plan:**
   - Migración Alembic `0040`: campos `address`, `phone`, `opening_hours`, `latitude`, `longitude` y auditoría en `branches`.
   - Backend `p1_gestion_usuarios_acceso`:
     - Servicio `branch_service.py` con `get_branch_quota()` y `validate_branch_quota()`.
     - Endpoints `/api/branches/quota`, `/api/branches/` con aislamiento estricto por `tenant_id`.
     - Bloqueo de creación o reactivación que exceda el límite del plan (HTTP 400).
   - Frontend Web Angular 21:
     - [`admin-branch.model.ts`](file:///c:/Users/PERSONAL/ecommerce-SI2/frontend/src/app/features/admin/models/admin-branch.model.ts) y [`admin-branch.service.ts`](file:///c:/Users/PERSONAL/ecommerce-SI2/frontend/src/app/features/admin/services/admin-branch.service.ts) con soporte para `BranchQuota`.
     - [`admin-branch-page.component.ts`](file:///c:/Users/PERSONAL/ecommerce-SI2/frontend/src/app/features/admin/pages/admin-branch-page.component.ts) y template con widget visual de consumo de cuotas del plan, alerta de saturación de capacidad, coordenadas GPS y modal extendido.
   - Tests de regresión y validación ejecutados exitosamente (`scratch/test_cu04_quota_enforcement.py`).
4. **Resolución de Autenticación Multitenant y Rediseño de Login:**
   - Desacoplamiento de entorno externo mediante [`frontend/public/runtime-config.js`](file:///c:/Users/PERSONAL/ecommerce-SI2/frontend/public/runtime-config.js) y detección dinámica de localhost en [`environment.ts`](file:///c:/Users/PERSONAL/ecommerce-SI2/frontend/src/environments/environment.ts), eliminando el bloqueo Cloudflare 403.
   - Rediseño del login con conmutador de 2 actores (`Clientes` vs `Administrativos`), botón toggle para mostrar/ocultar contraseña (Lucide icons) y paleta de diseño peach/coral.
   - Autenticación limpia con `rol` opcional en `UserLogin` extrayendo el rol real desde la base de datos.
5. **Revisión General de Implementación de CU08 (ICONIX):**
   - Completada la revisión previa oficial bajo las 8 secciones de la cátedra para `CU08: Descargar Catálogo a Base Local (IndexedDB / SQLite)`.

---

### 2. Credenciales Oficiales de Prueba (Sembradas en BD Central)
* **Superadmin Global (CU01 / CU02):** `superadmin@fashionstore.com` / `SuperAdmin2026!` (Portal: `/app/superadmin/tenants`)
* **Admin Boutique Elegance (CU04 / CU06 / CU10):** `admin@elegance.com` / `AdminElegance2026!` (Portal: `/app/admin/branch`)
* **Admin Moda Urbana (CU04 / CU06 / CU10):** `admin@modaurbana.com` / `AdminUrbana2026!` (Portal: `/app/admin/branch`)

---

### 3. Estado de Servicios Locales
* **Backend FastAPI (Puerto 8000):** DETENIDO (apagado a solicitud del usuario).
  - Comando para reiniciar cuando se retome la sesión:
    ```powershell
    cd backend; .\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
    ```
* **Frontend Angular (Puerto 4200):** Activo en terminal del usuario (`ng serve`).

---

### 4. Próxima Tarea Inmediata (Presentación 1: 25/10/2026)
* **CU08 – Descargar Catálogo a Base Local (IndexedDB / SQLite):**
  1. Backend: Implementar endpoint `GET /api/catalog/offline-pack?branch_id={uuid}` con empaquetado optimizado de prendas, variantes de precio por talla y existencias de sucursal.
  2. Frontend: Implementar `idb.service.ts` en Angular para almacenamiento estructurado en `fashionstore_local_db` (Object Stores: `catalog_products`, `catalog_variants`, `sync_meta`).
