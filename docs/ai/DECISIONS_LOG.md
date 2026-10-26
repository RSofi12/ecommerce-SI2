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
