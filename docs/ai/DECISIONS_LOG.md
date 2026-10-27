# DECISIONS LOG — FASHIONSTORE SAAS MULTITENANT

## Registro Histórico de Decisiones de Arquitectura y Negocio

### Registro 01: 2026-10-20
* **Decisión:** Reestructuración de la base de código del backend de *Package by Layer* a **Arquitectura por Paquetes de Dominio (Módulos Profundos)**.
* **Motivo:** La estructura original horizontal (`models/`, `routes/`, `schemas/`, `services/`) provocaba dispersión (*lack of locality*) e impedía la evolución hacia SaaS sin generar acoplamientos inmanejables.
* **Impacto:** Creación de los paquetes `p1_gestion_usuarios_acceso`, `p2_gestion_productos_catalogo`, `p3_gestion_inventario_disponibilidad`, `p4_gestion_compras_reservas`, `p5_gestion_ventas_pos` y `p6_inteligencia_analitica`. Montaje limpio en `main.py` y conservación de *shims* para retrocompatibilidad total.

### Registro 02: 2026-10-20
* **Decisión:** Desacoplamiento estricto de los archivos `__init__.py` raíz de cada paquete.
* **Motivo:** Al importar rutas dentro del `__init__.py` raíz de cada paquete, cualquier importación de un modelo desde otro paquete forzaba la carga prematura de dependencias FastAPI y controladores, desatando dependencias circulares complejas.
* **Impacto:** Los `__init__.py` raíz se mantienen vacíos o únicamente con docstring. El archivo maestro `main.py` importa explícitamente desde `.router` de cada paquete. Compilación limpia y 96 endpoints OpenAPI validados.

### Registro 03: 2026-10-24
* **Decisión:** Adopción de la lista unificada de **28 Casos de Uso (12 modificados del 1er parcial + 16 nuevos/extras del 2do parcial)** bajo la metodología ICONIX.
* **Motivo:** La docente indicó explícitamente que el segundo examen parcial no es un sistema nuevo desde cero, sino una evolución. Esta lista de 28 CU preserva formalmente los logros del 1er parcial (vestidor virtual AR, compra digital con Stripe, catálogo por atributos) adaptándolos a multitenancy, e incorpora los desafíos obligatorios (PWA offline, Flutter con SQLite, idempotencia, sync, cambios de prenda y ML).
* **Impacto:** Trazabilidad completa con los Requisitos Funcionales del examen sin perder los componentes ya construidos.

### Registro 04: 2026-10-24
* **Decisión:** Regla de modelado estricta para diagramas de robustez ICONIX: **los ciclos (loops), validaciones y flujos alternativos nacen obligatoriamente en el objeto Controlador**.
* **Motivo:** Directriz técnica de la docente en clase. La frontera (*Boundary*) solo recibe la intención del actor y la traslada; el controlador evalúa la regla de negocio y decide si invoca una frontera de éxito o una frontera de error.
* **Impacto:** Homogeneidad y rigor metodológico en todos los diagramas de robustez del informe.

### Registro 05: 2026-10-24
* **Decisión:** Política de negocio para **Cambios de Prendas con Diferencia de Precio (CU19)**.
* **Motivo:** Explicación de la docente: al cambiar una talla o modelo por otro de mayor precio (ej. talla M a Bs 50 por talla L a Bs 70), el cambio se consolida **única y exclusivamente si el cliente abona la diferencia de precio** (Bs 20). Si no abona, el cambio se cancela y se restituye la prenda o el monto.
* **Impacto:** Modelo `garment_exchanges` con campos `price_difference`, `difference_paid (bool)` y lógica de validación previa al movimiento de stock.

### Registro 06: 2026-10-24
* **Decisión:** Política de negocio para **Devoluciones de Prendas y Reembolso (CU20)**.
* **Motivo:** Regla comercial del pliego: ante la devolución de una prenda dentro del plazo, la empresa retiene entre el 20% y el 50% por acondicionamiento y gastos operativos, y devuelve al cliente entre el 50% y el 80% del importe pagado.
* **Impacto:** Modelo `garment_returns` con cálculo automático de retención y emisión de comprobante / nota de crédito.

### Registro 07: 2026-10-24
* **Decisión:** Incorporación de **OpenStreetMap / OpenRouteService en Flutter (CU21)** como aporte extra de geolocalización.
* **Motivo:** Cumplir el requerimiento de "Aportes propios" del pliego (Pág. 5) y enriquecer la experiencia móvil permitiendo ubicar sucursales físicas y calcular distancias sin depender de servicios privativos.
* **Impacto:** Integración del paquete `flutter_map` y capa de servicios de mapa en la aplicación móvil.

### Registro 08: 2026-10-24
* **Decisión:** Adopción del sistema de memoria viva en `docs/ai/` y de bitácoras obligatorias en `docs/ai/sessions/`.
* **Motivo:** Asegurar la continuidad operativa de los agentes de IA y los desarrolladores entre sesiones, registrando bitácoras técnicas únicamente cuando se modifique código o persistencia.
* **Impacto:** Creación de `AGENTS.md` y estructura de relevos `HANDOFF_LATEST.md`, `CURRENT_STATE.md` e `IMPLEMENTATION_PHASES.md`.

### Registro 09: 2026-10-24
* **Decisión:** Estandarización del nombre del paquete SaaS en español: `p0_saas_plataforma`.
* **Motivo:** Mantener coherencia idiomática absoluta con el resto de paquetes de dominio del backend (`p1_gestion_usuarios_acceso`, `p2_gestion_productos_catalogo`, etc.).
* **Impacto:** Creación del paquete `backend/app/packages/p0_saas_plataforma/` conteniendo los modelos `Company`, `Plan`, `Subscription`, esquemas Pydantic v2, servicios de tenant y validación de cuotas (`quota_service.py`), router `p0_router` montado en `backend/main.py`, y dependencia de contexto multitenant en `backend/app/core/tenant_context.py`.

### Registro 10: 2026-10-25
* **Decisión:** Sincronización e Idempotencia Offline con `offline-pack` y `offline-sync` (CU08/CU09).
* **Motivo:** Facilitar la descarga del catálogo completo por tenant en un paquete snapshot JSON unificado y garantizar la persistencia de operaciones creadas sin conexión con deduplicación por `client_operation_id`.
* **Impacto:** Migración `0041_add_tenant_and_offline_tables.py` que incorpora `tenant_id` a `products`, `product_variants` e `inventory`, crea tablas `offline_operations` y `catalog_cache`. Endpoints `GET /api/catalog/offline-pack` y `POST /api/catalog/offline-sync`.


### Registro 11: 2026-10-25
* **Decisión:** Enforzamiento estricto de `tenant_id` y persistencia transaccional con `db.commit()` en el Catálogo Multitenant (CU06 / CU07).
* **Motivo:** Auditoría de arquitectura detectó dos fallas críticas en el commit anterior: (1) Ausencia de aislamiento en endpoints de catálogo, pues `create_product`, `update_product`, `delete_product` y `list_admin_products` no recibían ni filtraban por `tenant_id`, provocando fuga cruzada de datos entre empresas. (2) Ausencia de `db.commit()` en las funciones de `catalog_service.py` (usaban `with db.begin_nested():` sin consolidar), provocando que las prendas creadas se revirtieran silenciosamente en cada petición HTTP. Adicionalmente, la migración `0041` no se había ejecutado en PostgreSQL.
* **Impacto:**
  - Ejecución formal de `alembic upgrade head` (revisión 0041 aplicada en base de datos).
  - Inyección y extracción mandatoria de `tenant_id` desde el JWT verificado en `catalog_routes.py`.
  - Soporte de precios diferenciados por talla en `ProductVariant` asociados al tenant.
  - Inclusión de `db.commit()` en `create_product()`, `update_product()` y `delete_product()`.
  - Serialización de `tenant_id` en `ProductRead` y `ProductVariantRead`.
  - Filtro opcional por `tenant_id` en `GET /api/catalog/products` para tiendas públicas.
  - Creación de la suite de pruebas de aislamiento multitenant `backend/tests/test_cu06_cu07_multitenant_catalog.py` con 4/4 pruebas pasando en verde.

### Registro 12 (2026-10-25) — Blindaje Multitenant y Consulta Multisede de Disponibilidad de Inventario (CU10)
- **Problema Detectado:**
  1. `get_consolidated_stock()` y `get_branch_stock()` en `inventory_service.py` no filtraban por `tenant_id`, mezclando inventarios de diferentes empresas en consultas administrativas y reportes.
  2. El endpoint `/api/catalog/availability` exigía obligatoriamente `branch_id`, impidiendo al cliente consultar la disponibilidad global o multisede de una prenda/variante en las diferentes tiendas de la marca.
  3. En la interfaz web de cliente (`ProductDetailPageComponent`), no existía mecanismo visual para consultar disponibilidad en sucursales físicas.
  4. La carpeta `scratch/` en la raíz del repositorio contenía scripts temporales de depuración que violaban las directrices de limpieza del proyecto.
- **Decisión y Solución Técnica:**
  - Se eliminó la carpeta `scratch/` de la raíz del repositorio.
  - Se refactorizó `get_consolidated_stock(db, tenant_id=None)` y `get_branch_stock(db, branch_id, tenant_id=None)` para filtrar estrictamente por empresa.
  - En `inventory_routes.py`, se extrae el claim `tenant_id` del JWT en `/consolidated` y se valida la pertenencia de la sucursal en `/branches/{branch_id}` evitando fugas multitenant.
  - Se potenció `GET /api/catalog/availability`: si se omite `branch_id`, devuelve el desglose de stock de todas las sucursales activas del tenant (`quantity`, `reserved_quantity`, `available_quantity = max(quantity - reserved, 0)`) y el total consolidado; si se especifica `branch_id`, preserva el contrato histórico de sucursal única para compatibilidad absoluta.
  - En Frontend (`ProductDetailPageComponent`), se diseñó un modal responsivo bajo lineamientos de `frontend-design`: resumen de red de tiendas, estados visuales por colores (disponible >5, últimas unidades 1-5, sin stock), dirección con geolocalización, teléfono y horario de atención.
  - Creación de la suite de pruebas unitarias y de integración `backend/tests/test_cu10_stock_availability.py` (4/4 pruebas aprobadas) y validación de 18 pruebas de regresión en verde.

### Registro 13 (2026-10-25) — Motor de Catálogo Offline en IndexedDB y Detección Reactiva de Conectividad (CU08 / CU09 / CU06 / CU07)
- **Problema Detectado:**
  1. El backend contaba con endpoints `/api/catalog/offline-pack` y `/api/catalog/offline-sync`, pero la aplicación Angular PWA carecía completamente de capa de persistencia local en cliente (IndexedDB).
  2. En modo desconectado (falla de red o modo avión), el catálogo público simplemente fallaba con error HTTP, sin mecanismo de conmutación transparente a caché ni indicador visual de estado.
  3. En el catálogo administrativo (CU06), la matriz de variantes carecía de jerarquía visual intuitiva para definir precios diferenciados por talla/color.
- **Decisión y Solución Técnica:**
  - Se implementó `IdbCatalogService` (`src/app/core/offline/idb-catalog.service.ts`) nativo sobre la API de IndexedDB del navegador (`fashionstore_local_db` v1), con almacenes para `catalog_products` y `catalog_meta` (timestamp de sincronización, total de ítems, versión).
  - Se implementó `NetworkStatusService` (`src/app/core/offline/network-status.service.ts`) con señales reactivas `isOnline`, `simulatedOffline`, `effectiveOnline`, escuchando eventos `online`/`offline` de `window` y permitiendo simulación de contingencia desde la interfaz.
  - En `CatalogPageComponent` (CU07/CU08/CU09), se configuró degradación elegante: si la red falla o está en modo desconectado, consulta automáticamente IndexedDB, aplicando motor de filtrado en memoria (búsqueda por texto, categoría, talla y color) y desplegando un banner contextual ámbar/pizarra con fecha del último snapshot.
  - Se añadió botón explícito para descargar/refrescar el catálogo local (CU08) con badge dinámico de conteo de prendas en caché.
  - En `AdminCatalogPageComponent` (CU06), se refinó la interfaz con la skill `frontend-design`: numeración clara de variantes (`#1`, `#2`), contenedor sutil con borde definido, textos de ayuda conceptuales para el precio por talla y acciones de eliminación fluidas.
  - Formato estricto ICONIX en flujos alternativos referenciando puntos del flujo principal (`2. A1:`, `4. A2:`, etc.).


### Registro 12: 2026-10-26
* **Decisión:** Implementación formal del ciclo de vida de **Traslados de Mercadería entre Sucursales (CU11)** con estados `EN_TRANSITO`, `COMPLETADO` y `CANCELADO`, y persistencia desacoplada del balance instantáneo de inventario.
* **Motivo:** En el 1er Parcial, los traspasos se realizaban como un swap inmediato de saldos en `/api/inventory/movements/transfer`. Para el 2do Parcial y la metodología ICONIX, el movimiento físico de prendas entre tiendas requiere trazabilidad temporal estricta: descuento preventivo en origen para evitar sobreventas, retención de la mercadería en tránsito sin afectar la disponibilidad de la sucursal receptora, y confirmación formal mediante acta de recepción en destino (`COMPLETADO`) o restitución a origen ante anulación (`CANCELADO`).
* **Impacto:**
  - Migración `0042_add_inventory_transfers.py` con tablas `inventory_transfers` e `inventory_transfer_items`.
  - Endpoints REST en `p3_gestion_inventario_disponibilidad` (`POST /api/inventory/transfers`, `GET /api/inventory/transfers`, `POST /api/inventory/transfers/{id}/receive`, `POST /api/inventory/transfers/{id}/cancel`).
  - Frontend Web Angular 21 en [`transfers-page.component.ts`](file:///c:/Users/PERSONAL/ecommerce-SI2/frontend/src/app/features/encargado/pages/transfers-page.component.ts) disponible en `/app/encargado/transfers` y `/app/admin/transfers`.
  - Suite automatizada de pruebas unitarias y de integración ([`test_cu11_inventory_transfers.py`](file:///c:/Users/PERSONAL/ecommerce-SI2/backend/tests/test_cu11_inventory_transfers.py)) con 5/5 pruebas PASSED.
