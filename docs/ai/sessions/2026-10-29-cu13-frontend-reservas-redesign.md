# Sesión: 2026-10-29 — CU13 Frontend Web: Rediseño Estético, Branding y Reservas con Vencimiento

**Autor/Rol:** Arquitecto de Software & Diseñador Frontend Lead
**Caso de Uso:** CU13 – Crear Reserva de Prendas con Vencimiento (Online y Contingencia Offline)
**Skills Utilizadas:** `/frontend-design`, `/design-taste-frontend`, `/codebase-design`

---

## 1. 🎯 Objetivos de la Sesión

1. **Rediseño Estético de CU13:**
   - Implementar la interfaz de usuario en Angular 21 para la reserva de prendas en tienda física, integrando la paleta de marca oficial (`#f8baa3` light peach, `#E07A5F` terracotta accent, `#191c21` dark obsidian) con layout responsivo y transiciones suaves.
2. **Branding e Identidad de Marca:**
   - Sustituir el texto "ACID Web" en el sidebar por el imagotipo oficial del carrito de compras FashionStore y la leyenda "FashionStore — Plataforma SaaS".
   - Sustituir el favicon predeterminado del escudo de Angular por el favicon vectorial en SVG de FashionStore (`favicon.svg`) y actualizar el `<title>` del documento a `FashionStore — SaaS Multitenant`.
   - Asegurar que la tipografía de las secciones del sidebar sea **Montserrat Regular** (`font-weight: 400`), eliminando la apariencia excesivamente delgada (`weight: 300`) observada en botones del componente Spartan UI.
3. **Resiliencia y Modo Contingencia Offline (PWA):**
   - Implementar [`IdbReservationsService`](file:///c:/Users/PERSONAL/ecommerce-SI2/frontend/src/app/core/offline/idb-reservations.service.ts) para almacenar reservas localmente con UUIDv4 idempotente cuando el usuario no tenga conexión de red.
   - Diseñar la pantalla de "Mis Reservas" con tickets boutique y sincronización masiva con un clic hacia el backend al restablecerse la conectividad.

---

## 2. 🛠️ Archivos Creados y Modificados

### A. Branding, Identidad y Tipografía
* **[`frontend/public/favicon.ico`](file:///c:/Users/PERSONAL/ecommerce-SI2/frontend/public/favicon.ico) & [`frontend/public/favicon.png`](file:///c:/Users/PERSONAL/ecommerce-SI2/frontend/public/favicon.png):**
  - Generado nuevo contenedor ICO y copia PNG a partir de [`frontend/src/assets/logo-fashionstore.png`](file:///c:/Users/PERSONAL/ecommerce-SI2/frontend/src/assets/logo-fashionstore.png) reemplazando el escudo de Angular antiguo.
* **[`frontend/src/index.html`](file:///c:/Users/PERSONAL/ecommerce-SI2/frontend/src/index.html):**
  - Enlaces de ícono actualizados con soporte multipropósito y busteo de caché agresivo del navegador (`?v=2`):
    - `<link rel="icon" type="image/png" sizes="192x192" href="/assets/logo-fashionstore.png?v=2">`
    - `<link rel="shortcut icon" type="image/x-icon" href="/favicon.ico?v=2">`
    - `<link rel="apple-touch-icon" href="/assets/logo-fashionstore.png?v=2">`
  - Actualizado `<title>` a `FashionStore — SaaS Multitenant`.
* **[`frontend/src/app/core/layouts/app-shell.component.html`](file:///c:/Users/PERSONAL/ecommerce-SI2/frontend/src/app/core/layouts/app-shell.component.html):**
  - Encabezado del sidebar actualizado integrando directamente la imagen oficial `src="/assets/logo-fashionstore.png"` junto al título "FashionStore" y subtítulo "Plataforma SaaS".
* **[`frontend/src/app/features/landing/pages/landing-page.component.html`](file:///c:/Users/PERSONAL/ecommerce-SI2/frontend/src/app/features/landing/pages/landing-page.component.html):**
  - Reemplazada la moneda local ARS por dólares estadounidenses en la sección de planes de la página principal: `$0 USD/mes` y `Primer mes GRATIS, luego $29 USD/mes`, alineado con la entidad `Plan` del backend.
* **[`frontend/src/styles.css`](file:///c:/Users/PERSONAL/ecommerce-SI2/frontend/src/styles.css):**
  - Selectores explícitos `[hlmSidebarMenu] a, [hlmSidebarMenu] button` forzando `font-family: 'Montserrat' !important` y `font-weight: 400 !important` (regular), elevando a `font-weight: 600 !important` en estado activo.
  - Clase `.btn-brand` con fondo `#f8baa3`, texto `#191c21`, elevación en `:hover` y sombreado con resplandor peach.

### B. Lógica y Componentes de Reserva (CU13)
* **[`frontend/src/app/features/shared/models/reservation.model.ts`](file:///c:/Users/PERSONAL/ecommerce-SI2/frontend/src/app/features/shared/models/reservation.model.ts):**
  - Modelos enriquecidos con `tenant_id`, `reservation_code` (`RES-XXXXXXXX`), `qr_payload` (`FS-RES:UUID`), `client_reservation_id` (UUIDv4) y metadatos de auditoría.
* **[`frontend/src/app/core/offline/idb-reservations.service.ts`](file:///c:/Users/PERSONAL/ecommerce-SI2/frontend/src/app/core/offline/idb-reservations.service.ts):**
  - Servicio singleton para persistencia local de reservas en contingencia offline con métodos `getPending()`, `savePending()`, `removePending()` y `clearAll()`.
* **[`frontend/src/app/features/cliente/pages/reservations-page.component.ts`](file:///c:/Users/PERSONAL/ecommerce-SI2/frontend/src/app/features/cliente/pages/reservations-page.component.ts) & [`.html`](file:///c:/Users/PERSONAL/ecommerce-SI2/frontend/src/app/features/cliente/pages/reservations-page.component.html):**
  - **Banner de Contingencia:** Alerta amber reactiva ante desconexión de red (`NetworkStatusService`).
  - **Formulario de Filtros:** Búsqueda textual y selector de sucursal con verificación obligatoria de stock local.
  - **Cards de Prendas:** Carrusel de imágenes, tags flotantes y **pills dinámicas de disponibilidad**:
    - *Emerald:* "N disponibles en sucursal" (cuando stock > 0).
    - *Rose:* "Sin existencias en esta sede" (cuando stock == 0).
    - *Slate:* "Selecciona sucursal para verificar stock".
  - **Dossier Flotante (Sticky Sidebar):** Selector de fecha limitado al intervalo de hoy a 7 días (`[min]="todayIso"` y `[max]="maxDateIso"`), recordatorio de la Política 6 (vencimiento y liberación tras 24 horas), borrador dinámico con cálculo de totales y botón de confirmación con micro-interacción.
  - **Modal Voucher de Reserva:** Diálogo con código de reserva destacado (`RES-XXXXXXXX`), botón de copiado al portapapeles y código QR interactivo (`https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=...`).
* **[`frontend/src/app/features/cliente/pages/my-reservations-page.component.ts`](file:///c:/Users/PERSONAL/ecommerce-SI2/frontend/src/app/features/cliente/pages/my-reservations-page.component.ts) & [`.html`](file:///c:/Users/PERSONAL/ecommerce-SI2/frontend/src/app/features/cliente/pages/my-reservations-page.component.html):**
  - Bandeja de reservas offline con botón de sincronización masiva hacia el backend.
  - Tarjetas con formato de ticket boutique para cada reserva (código, fechas de visita y vencimiento, estado, desglose de prendas e importe).
  - Modal interactivo de tarjeta QR para presentar al vendedor en tienda física.
  - Acciones del flujo: cancelar reserva (libera stock en backend), decidir compra tras prueba en tienda y transferir al carrito de compras.

---

## 3. 🧪 Verificaciones y Pruebas Realizadas

1. **Chequeo de Tipos y Plantillas de Angular:**
   ```bash
   cd frontend
   npx tsc --noEmit
   # Salida: Código 0 (cero errores de compilación TypeScript)
   ```
2. **Consistencia de Rutas y Menú:**
   - La ruta `/app/cliente/reservations` abre la pantalla de creación con catálogo facetado.
   - La ruta `/app/cliente/my-reservations` permite consultar las reservas registradas, ver tarjetas QR y sincronizar borradores offline.

---

## 4. 🚀 Próximos Pasos

1. Implementar la interfaz correspondiente en **Mobile Flutter** para CU13 (`reservations_screen.dart` con SQLite local y selector de sucursal).
2. Proceder con el Caso de Uso **CU14** (Atender y Resolver Conflictos de Reservas) para el perfil de encargado de tienda.
