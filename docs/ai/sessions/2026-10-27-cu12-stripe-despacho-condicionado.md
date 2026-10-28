# Bitácora de Sesión: 2026-10-27 — Implementación Fullstack Integral CU12 (Backend, BD, Frontend Web y Mobile)

## 1. 📌 Caso de Uso Implementado
* **Caso de Uso:** **CU12 – Comprar Prendas con Stripe y Despacho Condicionado** (Presentación 2, meta: 21 CUs acumulados).
* **Alcance de la Sesión:** Implementación integral fullstack (migración Alembic, modelos SQLAlchemy, esquemas Pydantic v2, servicios de dominio, endpoints REST, suite de pruebas automatizadas y componentes en Frontend Web Angular 21 bajo `frontend-design`).
* **Política de Negocio Obligatoria (Inviolable):**
  - **Política 3:** El despacho de prendas o entrega digital se efectúa **ÚNICAMENTE** cuando el pago con Stripe está confirmado (`payment_status = 'paid'`). Si el pedido se encuentra en estado `pending`, `failed`, `cancelled` o `expired`, cualquier intento de despacho es bloqueado con error explícito HTTP 400 Bad Request en backend y bloqueado visualmente en frontend con badge explicativo.

---

## 2. 🗄️ Cambios en Base de Datos (PostgreSQL 15+)
* **Migración Alembic `0043_add_order_tenant_and_dispatch.py`:**
  - Valores incorporados al enum PostgreSQL `fulfillmentstatusenum`: `'ready_for_dispatch'`, `'dispatched'`, `'delivered'`.
  - Tabla `orders`:
    - `tenant_id UUID REFERENCES companies(id) ON DELETE CASCADE` con índice.
    - `delivery_type VARCHAR(30) NOT NULL DEFAULT 'RETIRO_TIENDA'`.
    - `shipping_address TEXT NULL`.
    - `tracking_number VARCHAR(50) UNIQUE` con índice.
    - `dispatched_at TIMESTAMPTZ NULL`.
    - `dispatched_by UUID REFERENCES users(id) ON DELETE SET NULL`.
  - Tablas `order_items`, `carts`, `cart_items`, `payment_attempts`:
    - Adición de `tenant_id UUID REFERENCES companies(id) ON DELETE CASCADE` con índices para aislamiento multitenant estricto (SaaS).

---

## 3. ⚙️ Cambios en Backend (FastAPI + SQLAlchemy)

### Paquete `p4_gestion_compras_reservas`
* **Modelos SQLAlchemy:**
  - [`order.py`](file:///c:/Users/PERSONAL/ecommerce-SI2/backend/app/packages/p4_gestion_compras_reservas/models/order.py): Agregados atributos `tenant_id`, `delivery_type`, `shipping_address`, `tracking_number`, `dispatched_at`, `dispatched_by`, relaciones `company` y `dispatcher`.
  - [`order_item.py`](file:///c:/Users/PERSONAL/ecommerce-SI2/backend/app/packages/p4_gestion_compras_reservas/models/order_item.py): Agregado `tenant_id` y relación con `Company`.
  - [`cart.py`](file:///c:/Users/PERSONAL/ecommerce-SI2/backend/app/packages/p4_gestion_compras_reservas/models/cart.py): Agregado `tenant_id` y relación con `Company`.
  - [`cart_item.py`](file:///c:/Users/PERSONAL/ecommerce-SI2/backend/app/packages/p4_gestion_compras_reservas/models/cart_item.py): Agregado `tenant_id` y relación con `Company`.
  - [`payment_attempt.py`](file:///c:/Users/PERSONAL/ecommerce-SI2/backend/app/packages/p4_gestion_compras_reservas/models/payment_attempt.py): Agregado `tenant_id` y relación con `Company`.
* **Esquemas Pydantic v2:**
  - [`order_schema.py`](file:///c:/Users/PERSONAL/ecommerce-SI2/backend/app/packages/p4_gestion_compras_reservas/schemas/order_schema.py): Enumeraciones `DeliveryTypeEnum`, `FulfillmentStatusEnum` ampliado, campos `tenant_id`, `delivery_type`, `shipping_address`, `tracking_number`, `dispatched_at`, `dispatched_by` en `OrderRead` y `OrderItemRead`. Nuevos esquemas `OrderDispatchRequest` y `OrderDispatchResponse`.
  - [`payment_schema.py`](file:///c:/Users/PERSONAL/ecommerce-SI2/backend/app/packages/p4_gestion_compras_reservas/schemas/payment_schema.py): Soporte de `delivery_type`, `shipping_address` en `StripePaymentRequest` y `CashPaymentRequest`. Enriquecimiento de `StripeCheckoutResponse`.
* **Servicios de Dominio ([`order_service.py`](file:///c:/Users/PERSONAL/ecommerce-SI2/backend/app/packages/p4_gestion_compras_reservas/services/order_service.py)):**
  - `create_stripe_payment`: Resolución y asignación de `tenant_id`, soporte para `RETIRO_TIENDA` o `ENVIO_DOMICILIO`, inyección de metadata (`order_id`, `tenant_id`, `delivery_type`) en el PaymentIntent de Stripe.
  - `process_stripe_event`: Al recibir `payment_intent.succeeded`, genera automáticamente el código de seguimiento `DSP-YYYYMMDD-XXXX`, descuenta inventario y transiciona el pedido a `paid` y `ready_for_dispatch` o `ready_for_pickup`.
  - `dispatch_order`: **Validación estricta de Política 3**. Bloquea cualquier despacho si `payment_status != 'paid'`, registra fecha y usuario despachador, y asigna estado `dispatched`.
  - `get_order_by_tracking`: Consulta pública y de clientes de pedidos por guía de seguimiento con aislamiento multitenant.
* **Controladores REST:**
  - [`order_routes.py`](file:///c:/Users/PERSONAL/ecommerce-SI2/backend/app/packages/p4_gestion_compras_reservas/routes/order_routes.py):
    - `POST /api/orders/{order_id}/dispatch` (roles: `administrador`, `encargado`).
    - `GET /api/orders/tracking/{tracking_number}` (público / cliente).
  - [`payment_routes.py`](file:///c:/Users/PERSONAL/ecommerce-SI2/backend/app/packages/p4_gestion_compras_reservas/routes/payment_routes.py): Soporte de `tenant_id`, `delivery_type` y `shipping_address` en checkout de Stripe.
* **Shims de Compatibilidad:**
  - `backend/app/models/`: re-exportación transparente.
  - `backend/app/schemas/`: re-exportación transparente.
  - `backend/app/services/`: re-exportación transparente.
  - `backend/app/routes/`: re-exportación transparente.

---

## 4. 💻 Cambios en Frontend Web (Angular 21 + Tailwind CSS + Spartan UI)
* **Modelos y Tipado (`order.model.ts`):**
  - Incorporados `delivery_type`, `shipping_address`, `tracking_number`, `dispatched_at`, `dispatched_by` y `tenant_id`.
  - Ampliación de `FulfillmentStatusEnum` con `ready_for_dispatch`, `dispatched`, `delivered`.
* **Servicio API de Checkout (`checkout-api.service.ts`):**
  - Incorporado soporte de `CheckoutRequestPayload` (`delivery_type`, `shipping_address`, `pickup_branch_id`).
  - Métodos `dispatchOrder(orderId, payload)` y `trackOrder(trackingNumber)`.
* **Carrito y Checkout (`cart-page.component.ts` y `.html`):**
  - Selector interactivo de modalidad de entrega: **Envío a Domicilio** vs **Retiro en Tienda**.
  - Campo reactivo de dirección de entrega validada.
  - Pasarela integrada con **Stripe Elements** (`@stripe/stripe-js`) y soporte alternativo de efectivo en mostrador.
  - Generación y despliegue prominente de la guía de despacho `DSP-YYYYMMDD-XXXX` tras la confirmación del pago.
  - Generador de Nota de Venta PDF actualizado con número de guía y dirección.
* **Portal de Pedidos del Cliente (`orders-page.component.ts` y `.html`):**
  - Visualización enriquecida con badges semánticos de modalidad de entrega y estado de pago.
  - **Modal de Línea de Vida y Rastreo (ICONIX CU12):** Stepper visual de 5 etapas (*1. Creado → 2. Pago Verificado Stripe → 3. Preparación en Almacén → 4. Despachado en Camino → 5. Entregado*).
  - Buscador rápido de guía de despacho en la barra superior.
* **Panel de Control de Pedidos y Despachos (`encargado/orders-page.component.ts` y `.html`):**
  - Cumplimiento de **Política de Negocio 3**: Si `payment_status !== 'paid'`, el botón de despacho se bloquea visualmente y muestra advertencia roja/ámbar.
  - Cuando `payment_status === 'paid'`, habilita el botón primario *"🚚 Despachar Pedido (Generar Guía)"*.
  - Modal de confirmación de despacho con captura de notas de transporte / chofer y llamada a `dispatchOrder()`.
* **Rutas y Navegación:**
  - Registrado `/app/admin/orders` en [`app.routes.ts`](file:///c:/Users/PERSONAL/ecommerce-SI2/frontend/src/app/app.routes.ts).
  - Enlace *Pedidos / Despachos* añadido al menú de Administración en [`app-shell.component.ts`](file:///c:/Users/PERSONAL/ecommerce-SI2/frontend/src/app/core/layouts/app-shell.component.ts).

---

## 5. 📱 Cambios en Aplicación Móvil (Flutter / Dart)
* **Modelos de Dominio (order_models.dart):**
  - Enum FulfillmentStatus extendido con 
eadyForDispatch, dispatched y delivered.
  - Enum DeliveryType (storePickup, homeDelivery).
  - Entidad Order enriquecida con deliveryType, shippingAddress, 	rackingNumber, dispatchedAt y dispatchedBy.
  - Entidad StripeCheckout adaptada con metadata de despacho y expiración.
* **Capa de Servicios y API (order_api.dart y order_controller.dart):**
  - Métodos checkoutCash y checkoutStripe con soporte de deliveryType y shippingAddress.
  - Nuevo método 	rackOrder(trackingNumber) para búsqueda de órdenes por guía en tiempo real.
* **Pantalla de Checkout Móvil (checkout_page.dart):**
  - Selector de modalidad de entrega: **🚚 Envío a Domicilio** vs **🏪 Retiro en Sucursal**.
  - Captura y validación de dirección de entrega para despachos domiciliarios.
  - Bloqueo de efectivo en envíos a domicilio (exigiendo Stripe por Política de Negocio 3).
  - Inicialización y presentación de Stripe PaymentSheet (lutter_stripe) y diálogo de confirmación con guía generada DSP-....
* **Pantalla de Pedidos y Línea de Vida Móvil (orders_page.dart):**
  - Tarjetas de pedido con badge de tipo de entrega, estado de pago y guía de transporte.
  - Buscador rápido de guía de despacho en cabecera.
  - **Modal de Línea de Vida ICONIX en Bottom Sheet:** Stepper visual vertical de 5 etapas con validación explícita de pago Stripe y estado de transporte.
* **Pruebas Automatizadas Móviles:**
  - order_models_test.dart: 6/6 tests PASSED.
  - order_controller_test.dart: 3/3 tests PASSED.
  - orders_page_test.dart: 1/1 widget test PASSED.

---

## 6. 🧪 Pruebas y Verificaciones Ejecutadas
* **Suite Automatizada de CU12:** [`backend/tests/test_cu12_stripe_conditioned_dispatch.py`](file:///c:/Users/PERSONAL/ecommerce-SI2/backend/tests/test_cu12_stripe_conditioned_dispatch.py)
  1. `test_01_create_stripe_checkout_and_reservation`: Creación de checkout con Stripe, reserva temporal de stock e inclusión de `tenant_id` (**PASSED**).
  2. `test_02_policy_3_dispatch_strictly_blocked_when_unpaid`: Verificación de bloqueo absoluto de despacho físico ante pedido impago por Política de Negocio 3 (**PASSED**).
  3. `test_03_stripe_webhook_succeeded_generates_tracking_number`: Simulación de webhook `payment_intent.succeeded` de Stripe y generación de guía `DSP-...` (**PASSED**).
  4. `test_04_authorized_dispatch_success_and_tracking_lookup`: Despacho autorizado con estado pagado, auditoría de despachador y consulta por tracking (**PASSED**).
  5. `test_05_multitenant_dispatch_isolation`: Aislamiento entre empresas (`Boutique Elegance` vs `Moda Urbana`) impidiendo despachos o accesos cruzados (**PASSED**).
* **Resultado Backend:** **5/5 tests PASSED (100%)**.
* **Pruebas de Regresión Global:** 20/20 PASSED (`test_business_rules.py`, `test_cu11_inventory_transfers.py`, `test_cu12_stripe_conditioned_dispatch.py`).
* **Verificación de Tipado en Frontend:** `npx tsc --noEmit` ejecutado con **0 errores de compilación**.

---

## 7. 💻 Comandos para Reproducir
```bash
# 1. Aplicar migración de base de datos
cd backend
.venv\Scripts\alembic upgrade head

# 2. Ejecutar suite de pruebas de CU12
.venv\Scripts\pytest -o pythonpath=. tests/test_cu12_stripe_conditioned_dispatch.py -v

# 3. Compilación limpia de Frontend Web
cd ../frontend
npx tsc --noEmit
npm run build

# 4. Pruebas Móviles en Flutter
cd ../mobile
flutter test test/order_models_test.dart test/order_controller_test.dart test/orders_page_test.dart
```
