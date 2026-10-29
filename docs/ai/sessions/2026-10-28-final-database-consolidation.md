# Sesión de Trabajo: Consolidación Definitiva del Esquema de Base de Datos para Todos los Casos de Uso (CU13 a CU28)
**Fecha:** 28 de Octubre de 2026  
**Responsable:** Agente Antigravity & Desarrollador (Pair Programming)  
**Alcance:** Base de Datos (PostgreSQL), Migración Alembic 0044, Paquetes de Dominio Backend (`p4`, `p5`, `p6`), Matriz de Trazabilidad ICONIX.

---

### 1. Resumen Ejecutivo
Para evitar la proliferación de micro-migraciones parciales y dependencias circulares durante el desarrollo incremental de los Casos de Uso restantes del semestre, se diseñó, aplicó y verificó una **Migración Maestra Definitiva** (`0044_complete_database_schema_all_use_cases.py`).

Esta migración consolida en la base de datos PostgreSQL (`ecommerce_db`) todo el soporte de datos requerido para:
- Aislamiento SaaS Multitenant integral (`tenant_id` obligatorio y foráneo a `companies.id`).
- Políticas de Negocio Inviolables (Cambios de prenda con abono de diferencia en CU19; Devoluciones con retención 20%-50% en CU20).
- Facturación offline en efectivo con reconciliación idempotente (CU16, CU18).
- Inteligencia Artificial y Machine Learning (Gemini RAG por voz en CU23; Predicción de Demanda RandomForest en CU26; Clustering K-Means en CU27).

---

### 2. Cambios en Base de Datos (Alembic y PostgreSQL)

#### Estado de Alembic:
- **Revisión anterior:** `0043`
- **Revisión actual:** `0044 (head)`
- **Archivo:** [`backend/alembic/versions/0044_complete_database_schema_all_use_cases.py`](file:///c:/Users/PERSONAL/ecommerce-SI2/backend/alembic/versions/0044_complete_database_schema_all_use_cases.py)

#### Detalle de Modificaciones por Tabla:
1. **`reservations` (CU13, CU14):**
   - Agregada columna `tenant_id UUID REFERENCES companies(id) ON DELETE CASCADE` con índice.
   - Agregadas columnas de auditoría de resolución de conflictos: `resolved_at TIMESTAMP WITH TIME ZONE`, `resolved_by UUID REFERENCES users(id) ON DELETE SET NULL`, `resolution_note TEXT`.
2. **`reservation_items` (CU13):**
   - Agregada columna `tenant_id UUID REFERENCES companies(id) ON DELETE CASCADE` con índice.
3. **`sales` (CU15, CU16, CU18):**
   - Agregada columna `tenant_id UUID REFERENCES companies(id) ON DELETE CASCADE` con índice.
   - Agregada columna `client_sale_id UUID UNIQUE` con índice (identificador generado en cliente offline).
   - Agregada columna `is_offline BOOLEAN DEFAULT FALSE`.
   - Agregada columna `synced_at TIMESTAMP WITH TIME ZONE`.
   - Agregada columna `idempotency_key VARCHAR(100)` con índice.
4. **`sale_items` (CU15, CU16):**
   - Agregada columna `tenant_id UUID REFERENCES companies(id) ON DELETE CASCADE` con índice.
5. **`conversations` & `conversation_messages` (CU23):**
   - Agregada columna `tenant_id UUID REFERENCES companies(id) ON DELETE CASCADE` con índice.
6. **`promotion_codes` & `promotion_code_usages`:**
   - Agregada columna `tenant_id UUID REFERENCES companies(id) ON DELETE CASCADE` con índice.
7. **Nueva Tabla `sync_operations` (CU17, CU18):**
   - Columnas: `id UUID PK`, `tenant_id UUID FK`, `client_operation_id VARCHAR(100) UNIQUE`, `operation_type VARCHAR(50)`, `payload JSON`, `status VARCHAR(30)`, `synced_at TIMESTAMP`, `created_at TIMESTAMP`.
8. **Nueva Tabla `garment_exchanges` (CU19 - Política de Negocio 1):**
   - Columnas: `id UUID PK`, `tenant_id UUID FK`, `branch_id UUID FK`, `cashier_id UUID FK`, `sale_id UUID FK`, `original_variant_id UUID FK`, `new_variant_id UUID FK`, `price_difference NUMERIC(10,2)`, `difference_paid BOOLEAN`, `payment_method VARCHAR(30)`, `status VARCHAR(30)`, `notes TEXT`, `created_at TIMESTAMP`.
9. **Nueva Tabla `garment_returns` (CU20 - Política de Negocio 2):**
   - Columnas: `id UUID PK`, `tenant_id UUID FK`, `branch_id UUID FK`, `cashier_id UUID FK`, `sale_id UUID FK`, `variant_id UUID FK`, `quantity INT`, `original_item_amount NUMERIC(10,2)`, `retention_percentage NUMERIC(5,2)`, `retention_amount NUMERIC(10,2)`, `refund_amount NUMERIC(10,2)`, `refund_method VARCHAR(30)`, `credit_note_code VARCHAR(64) UNIQUE`, `reason TEXT`, `created_at TIMESTAMP`.
10. **Nueva Tabla `ml_models` (CU25, CU26, CU27):**
    - Columnas: `id UUID PK`, `tenant_id UUID FK`, `name VARCHAR(100)`, `model_type VARCHAR(50)`, `version VARCHAR(30)`, `metrics JSON`, `model_path VARCHAR(255)`, `is_active BOOLEAN`, `trained_at TIMESTAMP`.
11. **Nueva Tabla `demand_forecasts` (CU26, CU28):**
    - Columnas: `id UUID PK`, `tenant_id UUID FK`, `variant_id UUID FK`, `branch_id UUID FK`, `forecast_period VARCHAR(30)`, `predicted_units INT`, `confidence_lower INT`, `confidence_upper INT`, `algorithm_used VARCHAR(50)`, `created_at TIMESTAMP`.
12. **Nueva Tabla `customer_segments` (CU27, CU28):**
    - Columnas: `id UUID PK`, `tenant_id UUID FK`, `user_id UUID FK`, `cluster_id INT`, `segment_label VARCHAR(64)`, `recency_days INT`, `frequency_count INT`, `monetary_total NUMERIC(10,2)`, `return_rate NUMERIC(5,2)`, `assigned_at TIMESTAMP`.

---

### 3. Modelos ORM y Arquitectura por Paquetes (Backend)
Se implementaron los modelos canónicos en sus paquetes correspondientes:
- `p4_gestion_compras_reservas/models/`: `reservation.py`, `reservation_item.py`, `promotion_code.py`, `promotion_code_usage.py`.
- `p5_gestion_ventas_pos/models/`: `sale.py`, `sale_item.py`, `sync_operation.py`, `garment_exchange.py`, `garment_return.py`.
- `p6_inteligencia_analitica/models/`: `conversation.py`, `conversation_message.py`, `ml_model.py`, `demand_forecast.py`, `customer_segment.py`.
- Shims de compatibilidad hacia atrás en `app/models/`:
  - `sync_operation.py`, `garment_exchange.py`, `garment_return.py`, `ml_model.py`, `demand_forecast.py`, `customer_segment.py`.

---

### 4. Pruebas y Verificaciones Ejecutadas
1. **Introspección ORM con SQLAlchemy:**
   - Script ejecutado contra PostgreSQL comprobando el mapeo de todas las tablas y modelos con resultado:
     `SUCCESS: Todos los modelos y tablas mapean perfectamente sin errores.`
2. **Suite de Regresión Pytest:**
   - `pytest tests/test_cu12_stripe_conditioned_dispatch.py` -> **5/5 PASSED (100%)**.
3. **Saneamiento de Cuentas Operativas:**
   - Hashing real de BCrypt aplicado a `cliente@elegance.com`, `encargado@elegance.com`, `cajero@elegance.com` y `cliente_cu12@test.com`.

---

### 5. Documentación de Contexto Actualizada
- [`docs/ACTORS_AND_USE_CASES.md`](file:///c:/Users/PERSONAL/ecommerce-SI2/docs/ACTORS_AND_USE_CASES.md): Sección 3 incorporando la Matriz Completa de Casos de Uso vs Tablas.
- [`docs/ai/CURRENT_STATE.md`](file:///c:/Users/PERSONAL/ecommerce-SI2/docs/ai/CURRENT_STATE.md): Estado consolidado y cuentas operativas.
- [`docs/ai/HANDOFF_LATEST.md`](file:///c:/Users/PERSONAL/ecommerce-SI2/docs/ai/HANDOFF_LATEST.md): Relevo operativo post-migración 0044.
- [`docs/ai/NEXT_STEPS.md`](file:///c:/Users/PERSONAL/ecommerce-SI2/docs/ai/NEXT_STEPS.md): Hoja de ruta para CU13/CU14 y CU16/CU17/CU18.
- [`docs/ai/DECISIONS_LOG.md`](file:///c:/Users/PERSONAL/ecommerce-SI2/docs/ai/DECISIONS_LOG.md): Registro 14 documentando el congelamiento del esquema relacional.
- [`docs/ai/IMPLEMENTATION_PHASES.md`](file:///c:/Users/PERSONAL/ecommerce-SI2/docs/ai/IMPLEMENTATION_PHASES.md): Checklist oficial actualizado.
