# Registro de Sesión: 2026-10-25 — Implementación y Blindaje de CU10 (Disponibilidad de Prendas por Sucursal)

## 1. Caso de Uso Implementado
* **CU10 – Consultar Disponibilidad de Prendas por Sucursal** [1er Parcial - Modificado / Consolidado]
* **Objetivo:** Permitir a los clientes y administradores consultar la disponibilidad de stock real (físico vs reservado: $\text{StockDisponible} = \max(quantity - reserved\_quantity, 0)$) de una prenda o variante en las diferentes sucursales activas de una empresa SaaS, garantizando aislamiento multitenant estricto y una experiencia visual de alta calidad (`frontend-design`) sin componentes genéricos.

---

## 2. Cambios en Backend

### Aislamiento Multitenant en Paquete de Inventario (`p3_gestion_inventario_disponibilidad`)
1. **[`inventory_service.py`](file:///c:/Users/PERSONAL/ecommerce-SI2/backend/app/packages/p3_gestion_inventario_disponibilidad/services/inventory_service.py):**
   - `get_consolidated_stock(db, tenant_id=None)`: Incorporación de filtro estricto por `tenant_id` en las entidades `Branch` y `Product`, impidiendo que un administrador de una empresa visualice inventario de otras compañías.
   - `get_branch_stock(db, branch_id, tenant_id=None)`: Verificación de pertenencia de la sucursal al tenant antes de entregar desglose de stock.
   - `_get_or_create_inventory(db, variant_id, branch_id)`: Asignación automática del claim `tenant_id` a nuevos registros de inventario a partir de la variante o sucursal.
2. **[`inventory_routes.py`](file:///c:/Users/PERSONAL/ecommerce-SI2/backend/app/packages/p3_gestion_inventario_disponibilidad/routes/inventory_routes.py):**
   - `GET /api/inventory/consolidated`: Inyección y extracción del `tenant_id` desde el token JWT del usuario autenticado.
   - `GET /api/inventory/branches/{branch_id}`: Validación de que la sucursal solicitada pertenezca a la empresa del usuario; en caso contrario, responde con `HTTP 404 Not Found`.

### Consulta Multisede en Paquete de Catálogo (`p2_gestion_productos_catalogo`)
1. **[`catalog_routes.py`](file:///c:/Users/PERSONAL/ecommerce-SI2/backend/app/packages/p2_gestion_productos_catalogo/routes/catalog_routes.py):**
   - `GET /api/catalog/availability`:
     - **Modo Multisede (`branch_id` omitido):** Obtiene todas las sucursales activas de la empresa del producto/variante, calcula el stock disponible por cada tienda física y computa el `total_available` en toda la red comercial.
     - **Modo Histórico / Específico (`branch_id` provisto):** Mantiene retrocompatibilidad devolviendo `{"variant_id": ..., "branch_id": ..., "quantity": ...}`.
     - **Validación:** Si no se suministra ni `variant_id` ni `product_id`, retorna `HTTP 422 Unprocessable Entity`.
2. **[`catalog_service.py`](file:///c:/Users/PERSONAL/ecommerce-SI2/backend/app/packages/p2_gestion_productos_catalogo/services/catalog_service.py):**
   - `create_or_update_inventory`: Garantiza que la entidad `Inventory` persista el `tenant_id` asociado.
3. **[`backend/app/services/inventory_service.py`](file:///c:/Users/PERSONAL/ecommerce-SI2/backend/app/services/inventory_service.py):**
   - Re-exportación explícita de `_inventory_available` para preservar la regla de **Zero Breakage** en los *shims* de compatibilidad legados.

---

## 3. Cambios en Frontend Web (Angular 21 PWA)

1. **Modelos ([`catalog.model.ts`](file:///c:/Users/PERSONAL/ecommerce-SI2/frontend/src/app/features/shared/models/catalog.model.ts)):**
   - Definición de interfaces fuertemente tipadas: `BranchStockItem` y `VariantMultiBranchAvailability`.
2. **Servicio API ([`catalog-api.service.ts`](file:///c:/Users/PERSONAL/ecommerce-SI2/frontend/src/app/features/shared/services/catalog-api.service.ts)):**
   - Implementación del método reactivo `getVariantMultiBranchAvailability(variantId: string)`.
3. **Página de Detalle de Prenda ([`product-detail-page.component.ts`](file:///c:/Users/PERSONAL/ecommerce-SI2/frontend/src/app/features/cliente/pages/product-detail-page.component.ts) & `.html`):**
   - Integración de botón interactivo `"Ver disponibilidad en tiendas"`.
   - Implementación de modal responsivo diseñado con principios de `frontend-design`:
     - Resumen visual en cabecera con el total disponible en la red de tiendas de la empresa.
     - Badges semánticos por niveles de inventario:
       - Verde suave para `Disponible (> 5 unid.)`.
       - Ámbar suave para `Últimas unidades (1 - 5 unid.)`.
       - Gris/neutro para `Sin stock en tienda (0 unid.)`.
     - Datos geográficos y de contacto de cada sucursal física: dirección con pin icon, teléfono y horarios de atención al público.
     - Esqueleto de carga (`pulse skeleton shimmer`) mientras se resuelven las peticiones asíncronas.

---

## 4. Limpieza del Repositorio
* **Remoción de `scratch/`:** Se eliminó la carpeta no versionada `scratch/` que residía en la raíz del proyecto, dejando el espacio de trabajo limpio de scripts temporales.

---

## 5. Pruebas y Verificaciones Ejecutadas

### Pruebas Unitarias e Integración Backend
* **Suite Específica CU10 ([`backend/tests/test_cu10_stock_availability.py`](file:///c:/Users/PERSONAL/ecommerce-SI2/backend/tests/test_cu10_stock_availability.py)):**
  - `test_cu10_missing_parameters_returns_422`: PASSED.
  - `test_cu10_single_branch_availability_compatibility`: PASSED (Stock disponible = 12).
  - `test_cu10_multi_branch_availability_for_variant`: PASSED (Desglose en 2 sucursales del Tenant A, aislamiento de Tenant B, stock total = 17).
  - `test_cu10_consolidated_stock_multitenant_isolation`: PASSED (Aislamiento entre Tenant A y Tenant B).
  - **Resultado:** **4/4 PASSED (100%)**.

### Pruebas de Regresión
* **Comando:** `pytest tests/test_cu06_cu07_multitenant_catalog.py tests/test_cu06_cu10_catalog_offline.py tests/test_business_rules.py -v`
* **Resultado:** **18/18 PASSED (100%)**.

### Compilación Frontend
* **Comando:** `cd frontend && npm run build`
* **Resultado:** Compilación exitosa de todos los bundles (0 errores).
