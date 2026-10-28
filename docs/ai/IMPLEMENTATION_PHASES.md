# FASES DE IMPLEMENTACIÓN Y CHECKLIST OFICIAL — FASHIONSTORE

Documento oficial de control de avance de los **28 Casos de Uso** organizados por presentación acumulativa según la metodología ICONIX.

---

## 🎯 Presentación 1: Domingo 25/10/2026 (Meta: 10 Casos de Uso)
**Objetivo Técnico:** Base de la Plataforma SaaS Multitenant, Planes, Aislamiento de Datos y Catálogo Offline (IndexedDB / SQLite).

- [x] **CU01 – Gestionar Empresas Contratantes (Tenants)** [2do Parcial - NUEVO]
  - *Criterio de éxito:* Superadmin da de alta una empresa cliente con Razón Social, NIT y Administrador inicial.
- [x] **CU02 – Gestionar Planes de Suscripción y Límites Comerciales** [2do Parcial - NUEVO]
  - *Criterio de éxito:* Planes Básico (máx. 2 sucursales) y Profesional (máx. 10 sucursales) configurables.
- [x] **CU03 – Autenticar Usuario en Contexto Multitenant** [1er Parcial - MODIFICADO]
  - *Criterio de éxito:* Token JWT inyecta obligatoriamente `tenant_id`, `role` y `branch_id`.
- [x] **CU04 – Gestionar Sucursales bajo Reglas de Suscripción** [1er Parcial - MODIFICADO]
  - *Criterio de éxito:* El backend rechaza la creación de una 3ra sucursal si la empresa tiene Plan Básico.
- [x] **CU05 – Consultar y Actualizar Perfil de Usuario** [1er Parcial - MODIFICADO]
  - *Criterio de éxito:* Edición de datos del cliente/empleado aislada por tenant.
- [x] **CU06 – Gestionar Catálogo de Productos y Variantes por Tenant** [1er Parcial - MODIFICADO]
  - *Criterio de éxito:* CRUD de prendas y variantes (talla, color, precio diferenciado) restringido a la empresa.
- [x] **CU07 – Consultar y Filtrar Catálogo en Línea** [1er Parcial - MODIFICADO]
  - *Criterio de éxito:* Búsqueda multicriterio de prendas de la marca activa.
- [x] **CU08 – Descargar y Almacenar Catálogo en Caché Local (IDB/SQLite)** [2do Parcial - NUEVO]
  - *Criterio de éxito:* Descarga de catálogo a IndexedDB (web) y SQLite (móvil).
- [x] **CU09 – Consultar Catálogo y Disponibilidad Local en Modo Offline** [2do Parcial - NUEVO]
  - *Criterio de éxito:* Navegación y búsqueda de prendas sin internet con advertencia visual de datos locales.
- [x] **CU10 – Consultar Disponibilidad de Prendas por Sucursal** [1er Parcial - MODIFICADO]
  - *Criterio de éxito:* Stock físico y reservado visible por sucursal en tiempo real.

---

## 🎯 Presentación 2: Domingo 01/11/2026 (Meta: 21 Casos de Uso Acumulados)
**Objetivo Técnico:** Ventas Offline, Cola de Sincronización, Idempotencia, Stripe, Devoluciones, Cambios de Prenda y Mapas.

- [x] **CU11 – Registrar Movimiento de Inventario y Traspasos** [1er Parcial - MODIFICADO]
- [x] **CU12 – Gestionar Carrito y Compra Digital con Pasarela Stripe y Despacho Condicionado** [1er Parcial - MODIFICADO - 100% Implementado (Backend, BD y Frontend Web)]
  - *Regla de negocio:* El envío/entrega solo se autoriza con pago confirmado en Stripe (Política 3).
- [ ] **CU13 – Registrar Reserva de Prendas (Online y Offline)** [2do Parcial - NUEVO]
- [ ] **CU14 – Atender Reserva y Resolver Conflictos de Stock** [1er Parcial - MODIFICADO]
- [ ] **CU15 – Registrar Venta Presencial en Caja POS (Online)** [1er Parcial - MODIFICADO]
- [ ] **CU16 – Registrar Venta de Contado en Modo Offline** [2do Parcial - NUEVO]
  - *Regla de negocio:* Pago de contado (efectivo), generación de UUIDv4 local y rebaja preventiva de stock.
- [ ] **CU17 – Consultar Bandeja de Operaciones Locales Pendientes** [2do Parcial - NUEVO]
  - *Criterio de éxito:* Lista persistente que sobrevive al cierre y reinicio de la aplicación.
- [ ] **CU18 – Sincronizar Operaciones Comerciales Locales con Idempotencia** [2do Parcial - NUEVO]
  - *Criterio de éxito:* Transmisión en lote al volver la red; reintentos no duplican ventas ni inventario.
- [ ] **CU19 – Gestionar Cambios de Prendas con Diferencia de Precio** [2do Parcial - EXTRA]
  - *Regla de negocio:* El cambio SOLO se consolida si el cliente abona la diferencia de precio (ej. M a Bs 50 por L a Bs 70).
- [ ] **CU20 – Gestionar Devoluciones de Prendas y Reembolso (50%-80%)** [2do Parcial - NUEVO]
  - *Regla de negocio:* Retención de 20%-50% por acondicionamiento; reintegro de 50%-80% en nota de crédito o efectivo.
- [ ] **CU21 – Visualizar Ubicación de Sucursales con OpenStreetMap en Móvil** [2do Parcial - EXTRA]
  - *Criterio de éxito:* Mapa interactivo en Flutter con OpenStreetMap y cálculo de rutas con OpenRouteService.

---

## 🎯 Presentación 3: Domingo 08/11/2026 (Meta: 28 Casos de Uso TOTALES)
**Objetivo Técnico:** Inteligencia Artificial Generativa (Texto y Voz), Machine Learning (Supervisado/No Supervisado), Realidad Aumentada y Dashboard Ejecutivo.

- [ ] **CU22 – Usar Vestidor Virtual mediante Realidad Aumentada** [1er Parcial - PRESERVADO]
- [ ] **CU23 – Solicitar Reportes Generativos en Lenguaje Natural (Texto y Voz)** [2do Parcial - NUEVO]
  - *Criterio de éxito:* Dictado por voz (Web Speech API) y generación de reportes con Gemini sobre datos reales del tenant.
- [ ] **CU24 – Presentar y Exportar Reportes Dinámicos (PDF / Excel)** [2do Parcial - NUEVO]
- [ ] **CU25 – Gestionar Preparación de Datos Sintéticos para Machine Learning** [2do Parcial - NUEVO]
- [ ] **CU26 – Entrenar y Evaluar Modelo Predictivo de Demanda (Supervisado)** [2do Parcial - NUEVO]
- [ ] **CU27 – Analizar Segmentos de Clientes y Anomalías (K-Means)** [2do Parcial - NUEVO]
- [ ] **CU28 – Consultar Cuadro de Mando y Dashboard Analítico Ejecutivo** [1er Parcial - MODIFICADO]

---

## 🏆 Defensa Final: Martes 10 de Noviembre de 2026 (07:00 AM)
- [ ] Verificación integral de los 28 Casos de Uso en ambiente productivo en la nube.
- [ ] Coherencia documental 100% entre modelos UML (ICONIX), base de datos y código fuente.
