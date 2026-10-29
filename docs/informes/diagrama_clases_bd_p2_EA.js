// ============================================================================
// Diagrama de Clases (Modelo Físico y Relacional) para Enterprise Architect — JScript
// FashionStore — Plataforma SaaS Multitenant (2do Parcial)
//
// CARACTERÍSTICAS UML 2.5+:
//   - 46 Entidades: 41 tablas físicas + 5 especializaciones de roles de usuario.
//   - 9 «association class»: Tablas asociativas que resuelven relaciones M:N con atributos propios.
//   - 10 Relaciones de COMPOSICIÓN («Aggregation» fuerte, rombo negro en el Todo, sin flechas).
//   - 6 Relaciones de HERENCIA / GENERALIZACIÓN («Generalization», triángulo cerrado en el Padre).
//   - 63 Asociaciones estándar con cardinalidades explícitas y líneas simples sin flechas.
//   - Geometría compacta (165 x 110 px) en grilla de 6 columnas para legibilidad óptima.
// ============================================================================

var Repo = (typeof Repository != "undefined") ? Repository : null;
if (Repo == null) {
    var eaApp = new ActiveXObject("EA.App");
    Repo = eaApp.Repository;
}

function Log(msg) {
    try { Session.Output("[FashionStore-EA] " + msg); } catch (e) { WScript.Echo(msg); }
}

// ---------------------------------------------------------------------------
// Mapeo de tipos SQL a tipos nativos de Enterprise Architect
// ---------------------------------------------------------------------------
function eaType(sqlType) {
    var t = (sqlType + "").toLowerCase();
    if (t.indexOf("uuid") >= 0) return "Guid";
    if (t.indexOf("boolean") >= 0) return "Boolean";
    if (t.indexOf("integer") >= 0 || t.indexOf("serial") >= 0) return "Integer";
    if (t.indexOf("numeric") >= 0 || t.indexOf("decimal") >= 0 || t.indexOf("money") >= 0) return "Currency";
    if (t.indexOf("timestamp") >= 0 || t.indexOf("datetime") >= 0 || t.indexOf("date") >= 0) return "Date";
    if (t.indexOf("json") >= 0) return "String";
    if (t.indexOf("text") >= 0 || t.indexOf("character") >= 0 || t.indexOf("char") >= 0 || t.indexOf("varchar") >= 0) return "String";
    return "String";
}

// ---------------------------------------------------------------------------
// 1. RELACIONES: [Origen, Destino, Verbo, CardOrigen, CardDestino, TipoRelacion]
// TipoRelacion:
//   - "Composition":    Composición UML (Rombo negro en Origen, Parte en Destino, sin flechas)
//   - "Generalization": Herencia UML (Origen = Subclase, Destino = Superclase)
//   - "Association":    Asociación estándar UML (Línea simple sin flechas)
// ---------------------------------------------------------------------------
var RELACIONES = [
    // === COMPOSICIONES FUERTES (Todo -> Parte, Rombo Negro) ===
    ["companies",                     "subscriptions",        "posee_suscripciones",  "1", "1..*", "Composition"],
    ["products",                      "product_variants",     "compone_variantes",    "1", "1..*", "Composition"],
    ["sales",                         "sale_items",           "compone_items",        "1", "1..*", "Composition"],
    ["orders",                        "order_items",          "compone_items",        "1", "1..*", "Composition"],
    ["inventory_transfers",           "inventory_transfer_items","compone_traspaso",  "1", "1..*", "Composition"],
    ["replenishment_requests",        "replenishment_request_items","compone_reposicion","1","1..*","Composition"],
    ["carts",                         "cart_items",           "contiene_items",       "1", "0..*", "Composition"],
    ["reservations",                  "reservation_items",    "reserva_items",        "1", "1..*", "Composition"],
    ["users",                         "user_body_profiles",   "posee_perfil_medidas", "1", "0..1", "Composition"],
    ["conversations",                 "conversation_messages","contiene_mensajes",    "1", "0..*", "Composition"],

    // === HERENCIA / GENERALIZACIÓN (Subclase -> Superclase, Triángulo Cerrado) ===
    ["providers",                     "users",                "",                     "",  "",     "Generalization"],
    ["Superadministrador",            "users",                "",                     "",  "",     "Generalization"],
    ["AdministradorTenant",           "users",                "",                     "",  "",     "Generalization"],
    ["EncargadoSucursal",             "users",                "",                     "",  "",     "Generalization"],
    ["Cajero",                        "users",                "",                     "",  "",     "Generalization"],
    ["Cliente",                       "users",                "",                     "",  "",     "Generalization"],

    // === ASOCIACIONES CON CLASES ASOCIADAS (Resolución de relaciones M:N) ===
    ["sale_items",                    "product_variants",     "vende_variante",       "0..*", "1", "Association"],
    ["order_items",                   "product_variants",     "detalla_variante",     "0..*", "1", "Association"],
    ["inventory",                     "branches",             "almacenado_en",        "0..*", "1", "Association"],
    ["inventory",                     "product_variants",     "posee_stock_de",       "0..*", "1", "Association"],
    ["cart_items",                    "product_variants",     "incluye_variante",     "0..*", "1", "Association"],
    ["reservation_items",             "product_variants",     "reserva_prenda",       "0..*", "1", "Association"],
    ["inventory_transfer_items",      "product_variants",     "transfiere_prenda",    "0..*", "1", "Association"],
    ["replenishment_request_items",   "product_variants",     "solicita_variante",    "0..*", "1", "Association"],
    ["provider_variant_availability", "providers",            "declara_abastecimiento","0..*", "1", "Association"],
    ["provider_variant_availability", "product_variants",     "para_variante",        "0..*", "1", "Association"],
    ["promotion_code_usages",         "promotion_codes",      "registra_uso_de",      "0..*", "1", "Association"],
    ["promotion_code_usages",         "users",                "usado_por",            "0..*", "1", "Association"],

    // === ASOCIACIONES REGULARES DEL SISTEMA (Líneas simples sin flechas) ===
    // --- Núcleo SaaS Multitenant (p0) ---
    ["subscriptions",                 "plans",                "asigna_plan",          "0..*", "1", "Association"],
    ["branches",                      "companies",            "pertenece_a_tenant",   "0..*", "1", "Association"],
    ["users",                         "companies",            "pertenece_a_tenant",   "0..*", "1", "Association"],
    ["products",                      "companies",            "propiedad_de_tenant",  "0..*", "1", "Association"],
    ["product_variants",              "companies",            "es_de_tenant",         "0..*", "1", "Association"],
    ["inventory",                     "companies",            "stock_de_tenant",      "0..*", "1", "Association"],
    ["inventory_transfers",           "companies",            "traspaso_de_tenant",   "0..*", "1", "Association"],
    ["offline_operations",            "companies",            "audita_offline",       "0..*", "0..1","Association"],
    ["catalog_cache",                 "companies",            "cache_de_tenant",      "0..*", "0..1","Association"],

    // --- Usuarios, Sucursales y Asignaciones (p1) ---
    ["users",                         "branches",             "asignado_a",           "0..*", "0..1","Association"],

    // --- Catálogo Textil y Clasificación (p2) ---
    ["collections",                   "seasons",              "pertenece_a",          "0..*", "1", "Association"],
    ["products",                      "collections",          "se_asocia_a",          "0..*", "0..1","Association"],
    ["products",                      "categories",           "se_clasifica_en",      "0..*", "1", "Association"],
    ["products",                      "providers",            "abastecido_por",       "0..*", "0..1","Association"],
    ["product_variants",              "sizes",                "tiene_talla",          "0..*", "1", "Association"],
    ["product_variants",              "colors",               "tiene_color",          "0..*", "1", "Association"],

    // --- Inventario, Movimientos y Kardex (p3) ---
    ["inventory_movements",           "product_variants",     "afecta_stock_de",      "0..*", "1", "Association"],
    ["inventory_movements",           "branches",             "se_ejecuta_en",        "0..*", "1", "Association"],
    ["inventory_movements",           "branches",             "transfiere_a",         "0..*", "0..1","Association"],
    ["inventory_movements",           "users",                "es_registrado_por",    "0..*", "0..1","Association"],
    ["inventory_transfers",           "branches",             "sale_de_sucursal",     "0..*", "1", "Association"],
    ["inventory_transfers",           "branches",             "llega_a_sucursal",     "0..*", "1", "Association"],
    ["inventory_transfers",           "users",                "solicitado_por",       "0..*", "1", "Association"],
    ["inventory_transfers",           "users",                "recibido_por",         "0..*", "0..1","Association"],
    ["offline_operations",            "branches",             "ejecuta_en_sucursal",  "0..*", "0..1","Association"],

    // --- Reposición con Proveedores (p3) ---
    ["replenishment_requests",        "providers",            "solicita_a_proveedor", "0..*", "1", "Association"],
    ["replenishment_requests",        "branches",             "se_destina_a_sucursal","0..*", "1", "Association"],
    ["replenishment_requests",        "users",                "solicitado_por",       "0..*", "1", "Association"],
    ["replenishment_requests",        "users",                "aceptado_por",         "0..*", "0..1","Association"],
    ["replenishment_requests",        "users",                "preparado_por",        "0..*", "0..1","Association"],
    ["replenishment_requests",        "users",                "recibido_por",         "0..*", "0..1","Association"],
    ["replenishment_requests",        "users",                "entregado_por",        "0..*", "0..1","Association"],

    // --- Carrito, Promociones y Reservas (p4) ---
    ["carts",                         "users",                "posee_carrito",        "0..1", "1", "Association"],
    ["carts",                         "promotion_codes",      "aplica_cupon",         "0..*", "0..1","Association"],
    ["cart_items",                    "reservations",         "asocia_reserva",       "0..*", "0..1","Association"],
    ["reservations",                  "branches",             "se_solicita_en",       "0..*", "1", "Association"],
    ["reservations",                  "users",                "es_solicitada_por",    "0..*", "1", "Association"],
    ["reservations",                  "carts",                "proviene_de_carrito",  "0..1", "0..1","Association"],
    ["promotion_codes",               "branches",             "es_valido_en",         "0..*", "0..1","Association"],
    ["promotion_codes",               "users",                "creado_por",           "0..*", "1", "Association"],

    // --- Compras Stripe y Órdenes (p4) ---
    ["orders",                        "users",                "realiza_pedido",       "0..*", "1", "Association"],
    ["orders",                        "promotion_codes",      "aplica_descuento",     "0..*", "0..1","Association"],
    ["orders",                        "branches",             "se_recoge_en",         "0..*", "0..1","Association"],
    ["order_items",                   "reservations",         "origina_de_reserva",   "0..*", "0..1","Association"],
    ["payment_attempts",              "orders",               "procesa_pago_de",      "0..*", "0..1","Association"],
    ["payment_attempts",              "carts",                "valida_pago_carrito",  "0..*", "0..1","Association"],

    // --- Ventas POS y Políticas Comerciales (p5) ---
    ["sales",                         "branches",             "se_registra_en",       "0..*", "1", "Association"],
    ["sales",                         "users",                "es_atendida_por",      "0..*", "1", "Association"],
    ["sales",                         "reservations",         "convierte_reserva",    "0..*", "0..1","Association"],

    // --- IA, Recomendaciones, Chatbot y Push (p6) ---
    ["user_product_interactions",     "users",                "generada_por",         "0..*", "1", "Association"],
    ["user_product_interactions",     "products",             "interactua_con",       "0..*", "1", "Association"],
    ["user_product_interactions",     "orders",               "asociada_a_orden",     "0..*", "0..1","Association"],
    ["user_product_interactions",     "product_variants",     "variante_interactuada","0..*", "0..1","Association"],
    ["user_product_interactions",     "branches",             "ocurre_en_sucursal",   "0..*", "0..1","Association"],
    ["conversations",                 "users",                "iniciada_por",         "0..*", "1", "Association"],
    ["notifications",                 "users",                "notifica_a_usuario",   "0..*", "1", "Association"],
    ["device_tokens",                 "users",                "dispositivo_de_usuario","0..*","1", "Association"]
];

// ---------------------------------------------------------------------------
// 2. TABLAS Y CLASES: [nombre, [ [columna, tipoSQL, estereotipo] ], estereotipo_clase]
// Total: 46 entidades (41 físicas + 5 roles especializados)
// ---------------------------------------------------------------------------
var TABLAS = [
    // --- PAQUETE P0: PLATAFORMA SAAS Y TENANCY ---
    ["companies", [
        ["id", "UUID", "PK"], ["name", "VARCHAR(150)", null], ["business_name", "VARCHAR(200)", null],
        ["nit_rut", "VARCHAR(50)", null], ["subdomain", "VARCHAR(63)", null],
        ["status", "VARCHAR(20)", null], ["email", "VARCHAR(120)", null],
        ["phone", "VARCHAR(30)", null], ["created_at", "TIMESTAMP", null], ["updated_at", "TIMESTAMP", null]
    ], "table"],
    ["plans", [
        ["id", "UUID", "PK"], ["name", "VARCHAR(50)", null], ["code", "VARCHAR(30)", null],
        ["max_branches", "INTEGER", null], ["has_ai_access", "BOOLEAN", null],
        ["price_monthly", "NUMERIC(10,2)", null], ["is_active", "BOOLEAN", null],
        ["created_at", "TIMESTAMP", null], ["updated_at", "TIMESTAMP", null]
    ], "table"],
    ["subscriptions", [
        ["id", "UUID", "PK"], ["company_id", "UUID", "FK"], ["plan_id", "UUID", "FK"],
        ["status", "VARCHAR(20)", null], ["current_period_start", "TIMESTAMP", null],
        ["current_period_end", "TIMESTAMP", null], ["cancel_at_period_end", "BOOLEAN", null],
        ["created_at", "TIMESTAMP", null], ["updated_at", "TIMESTAMP", null]
    ], "table"],
    ["catalog_cache", [
        ["id", "UUID", "PK"], ["company_id", "UUID", "FK"], ["version", "INTEGER", null],
        ["payload", "JSON", null], ["generated_at", "TIMESTAMP", null]
    ], "table"],

    // --- PAQUETE P1: GESTIÓN DE USUARIOS, ACCESO Y PROVEEDORES ---
    ["users", [
        ["id", "UUID", "PK"], ["tenant_id", "UUID", "FK"], ["branch_id", "UUID", "FK"],
        ["email", "VARCHAR(120)", null], ["hashed_password", "VARCHAR(255)", null],
        ["first_name", "VARCHAR(50)", null], ["last_name", "VARCHAR(50)", null],
        ["role", "VARCHAR(30)", "enum"], ["is_active", "BOOLEAN", null],
        ["created_at", "TIMESTAMP", null], ["updated_at", "TIMESTAMP", null]
    ], "table"],
    ["branches", [
        ["id", "UUID", "PK"], ["tenant_id", "UUID", "FK"], ["code", "VARCHAR(20)", null],
        ["name", "VARCHAR(100)", null], ["address", "VARCHAR(255)", null],
        ["phone", "VARCHAR(30)", null], ["latitude", "NUMERIC(10,7)", null],
        ["longitude", "NUMERIC(10,7)", null], ["is_active", "BOOLEAN", null],
        ["created_at", "TIMESTAMP", null], ["updated_at", "TIMESTAMP", null]
    ], "table"],
    ["providers", [
        ["id", "UUID", "PK"], ["user_id", "UUID", "FK"], ["company_name", "VARCHAR(150)", null],
        ["contact_name", "VARCHAR(100)", null], ["phone", "VARCHAR(30)", null],
        ["address", "VARCHAR(255)", null], ["tax_id", "VARCHAR(50)", null],
        ["created_at", "TIMESTAMP", null], ["updated_at", "TIMESTAMP", null]
    ], "table"],
    ["user_body_profiles", [
        ["id", "UUID", "PK"], ["user_id", "UUID", "FK"], ["height_cm", "NUMERIC(5,2)", null],
        ["weight_kg", "NUMERIC(5,2)", null], ["chest_cm", "NUMERIC(5,2)", null],
        ["waist_cm", "NUMERIC(5,2)", null], ["hip_cm", "NUMERIC(5,2)", null],
        ["preferred_fit", "VARCHAR(30)", null], ["created_at", "TIMESTAMP", null], ["updated_at", "TIMESTAMP", null]
    ], "table"],

    // --- ESPECIALIZACIONES DE ROLES (HERENCIA UML DE USERS) ---
    ["Superadministrador", [
        ["permisos_globales", "String", null],
        ["audita_tenants", "Boolean", null]
    ], "role"],
    ["AdministradorTenant", [
        ["cargo_empresa", "String", null],
        ["gestiona_sucursales", "Boolean", null]
    ], "role"],
    ["EncargadoSucursal", [
        ["codigo_empleado", "String", null],
        ["turno", "String", null]
    ], "role"],
    ["Cajero", [
        ["numero_caja", "String", null],
        ["limite_efectivo", "Currency", null]
    ], "role"],
    ["Cliente", [
        ["puntos_fidelidad", "Integer", null],
        ["preferencia_notificacion", "String", null]
    ], "role"],

    // --- CLASE ASOCIADA: PROVEEDOR - VARIANTE ---
    ["provider_variant_availability", [
        ["id", "UUID", "PK"], ["provider_id", "UUID", "FK"], ["variant_id", "UUID", "FK"],
        ["cost_price", "NUMERIC(10,2)", null], ["available_quantity", "INTEGER", null],
        ["lead_time_days", "INTEGER", null], ["updated_at", "TIMESTAMP", null]
    ], "association class"],

    // --- PAQUETE P2: CATÁLOGO DE PRENDAS Y VARIANTES ---
    ["categories", [
        ["id", "UUID", "PK"], ["name", "VARCHAR(100)", null], ["slug", "VARCHAR(120)", null],
        ["description", "TEXT", null], ["parent_id", "UUID", "FK"], ["is_active", "BOOLEAN", null]
    ], "table"],
    ["seasons", [
        ["id", "UUID", "PK"], ["name", "VARCHAR(50)", null], ["year", "INTEGER", null],
        ["start_date", "DATE", null], ["end_date", "DATE", null]
    ], "table"],
    ["collections", [
        ["id", "UUID", "PK"], ["season_id", "UUID", "FK"], ["name", "VARCHAR(100)", null],
        ["description", "TEXT", null], ["is_active", "BOOLEAN", null]
    ], "table"],
    ["sizes", [
        ["id", "UUID", "PK"], ["name", "VARCHAR(20)", null], ["order", "INTEGER", null]
    ], "table"],
    ["colors", [
        ["id", "UUID", "PK"], ["name", "VARCHAR(50)", null], ["hex_code", "VARCHAR(7)", null]
    ], "table"],
    ["products", [
        ["id", "UUID", "PK"], ["company_id", "UUID", "FK"], ["category_id", "UUID", "FK"],
        ["collection_id", "UUID", "FK"], ["provider_id", "UUID", "FK"],
        ["name", "VARCHAR(150)", null], ["code", "VARCHAR(50)", null],
        ["description", "TEXT", null], ["base_price", "NUMERIC(10,2)", null],
        ["is_active", "BOOLEAN", null], ["created_at", "TIMESTAMP", null], ["updated_at", "TIMESTAMP", null]
    ], "table"],
    ["product_variants", [
        ["id", "UUID", "PK"], ["company_id", "UUID", "FK"], ["product_id", "UUID", "FK"],
        ["size_id", "UUID", "FK"], ["color_id", "UUID", "FK"],
        ["sku", "VARCHAR(60)", null], ["price", "NUMERIC(10,2)", null],
        ["is_active", "BOOLEAN", null], ["created_at", "TIMESTAMP", null], ["updated_at", "TIMESTAMP", null]
    ], "table"],

    // --- PAQUETE P3: INVENTARIO, MOVIMIENTOS Y TRASLADOS ---
    ["inventory", [
        ["id", "UUID", "PK"], ["company_id", "UUID", "FK"], ["branch_id", "UUID", "FK"],
        ["variant_id", "UUID", "FK"], ["stock", "INTEGER", null],
        ["min_stock", "INTEGER", null], ["max_stock", "INTEGER", null],
        ["created_at", "TIMESTAMP", null], ["updated_at", "TIMESTAMP", null]
    ], "association class"],
    ["inventory_movements", [
        ["id", "UUID", "PK"], ["variant_id", "UUID", "FK"], ["branch_id", "UUID", "FK"],
        ["reference_branch_id", "UUID", "FK"], ["user_id", "UUID", "FK"],
        ["quantity", "INTEGER", null], ["movement_type", "VARCHAR(20)", "enum"],
        ["reason", "VARCHAR(255)", null], ["created_at", "TIMESTAMP", null]
    ], "table"],
    ["inventory_transfers", [
        ["id", "UUID", "PK"], ["company_id", "UUID", "FK"], ["from_branch_id", "UUID", "FK"],
        ["to_branch_id", "UUID", "FK"], ["status", "VARCHAR(20)", "enum"],
        ["requested_by", "UUID", "FK"], ["received_by", "UUID", "FK"],
        ["notes", "TEXT", null], ["created_at", "TIMESTAMP", null], ["updated_at", "TIMESTAMP", null]
    ], "table"],
    ["inventory_transfer_items", [
        ["id", "UUID", "PK"], ["transfer_id", "UUID", "FK"], ["variant_id", "UUID", "FK"],
        ["quantity", "INTEGER", null]
    ], "association class"],
    ["replenishment_requests", [
        ["id", "UUID", "PK"], ["provider_id", "UUID", "FK"], ["branch_id", "UUID", "FK"],
        ["status", "VARCHAR(20)", "enum"], ["requested_by", "UUID", "FK"],
        ["accepted_by", "UUID", "FK"], ["prepared_by", "UUID", "FK"],
        ["received_by", "UUID", "FK"], ["delivered_by", "UUID", "FK"],
        ["created_at", "TIMESTAMP", null], ["updated_at", "TIMESTAMP", null]
    ], "table"],
    ["replenishment_request_items", [
        ["id", "UUID", "PK"], ["request_id", "UUID", "FK"], ["variant_id", "UUID", "FK"],
        ["quantity_requested", "INTEGER", null], ["quantity_received", "INTEGER", null]
    ], "association class"],
    ["offline_operations", [
        ["id", "UUID", "PK"], ["client_operation_id", "VARCHAR(64)", null],
        ["company_id", "UUID", "FK"], ["branch_id", "UUID", "FK"],
        ["operation_type", "VARCHAR(30)", null], ["payload", "JSON", null],
        ["status", "VARCHAR(20)", null], ["synced_at", "TIMESTAMP", null], ["created_at", "TIMESTAMP", null]
    ], "table"],

    // --- PAQUETE P4: CARRITO, RESERVAS Y COMPRAS STRIPE ---
    ["carts", [
        ["id", "UUID", "PK"], ["user_id", "UUID", "FK"], ["promotion_code_id", "UUID", "FK"],
        ["status", "VARCHAR(20)", null], ["created_at", "TIMESTAMP", null], ["updated_at", "TIMESTAMP", null]
    ], "table"],
    ["cart_items", [
        ["id", "UUID", "PK"], ["cart_id", "UUID", "FK"], ["variant_id", "UUID", "FK"],
        ["reservation_id", "UUID", "FK"], ["quantity", "INTEGER", null],
        ["unit_price", "NUMERIC(10,2)", null], ["created_at", "TIMESTAMP", null]
    ], "association class"],
    ["reservations", [
        ["id", "UUID", "PK"], ["user_id", "UUID", "FK"], ["branch_id", "UUID", "FK"],
        ["cart_id", "UUID", "FK"], ["status", "VARCHAR(20)", "enum"],
        ["expires_at", "TIMESTAMP", null], ["pickup_code", "VARCHAR(20)", null],
        ["created_at", "TIMESTAMP", null], ["updated_at", "TIMESTAMP", null]
    ], "table"],
    ["reservation_items", [
        ["id", "UUID", "PK"], ["reservation_id", "UUID", "FK"], ["variant_id", "UUID", "FK"],
        ["quantity", "INTEGER", null]
    ], "association class"],
    ["promotion_codes", [
        ["id", "UUID", "PK"], ["branch_id", "UUID", "FK"], ["created_by", "UUID", "FK"],
        ["code", "VARCHAR(30)", null], ["discount_type", "VARCHAR(20)", null],
        ["discount_value", "NUMERIC(10,2)", null], ["is_active", "BOOLEAN", null],
        ["valid_from", "TIMESTAMP", null], ["valid_until", "TIMESTAMP", null], ["created_at", "TIMESTAMP", null]
    ], "table"],
    ["promotion_code_usages", [
        ["id", "UUID", "PK"], ["promotion_code_id", "UUID", "FK"], ["user_id", "UUID", "FK"],
        ["used_at", "TIMESTAMP", null]
    ], "association class"],
    ["orders", [
        ["id", "UUID", "PK"], ["user_id", "UUID", "FK"], ["promotion_code_id", "UUID", "FK"],
        ["pickup_branch_id", "UUID", "FK"], ["status", "VARCHAR", "enum"],
        ["payment_method", "VARCHAR", "enum"], ["payment_status", "VARCHAR", "enum"],
        ["stripe_payment_intent_id", "VARCHAR", null], ["cash_reference", "VARCHAR", null],
        ["pickup_expires_at", "TIMESTAMP", null], ["pickup_code", "VARCHAR", null],
        ["fulfillment_status", "VARCHAR", "enum"], ["subtotal", "NUMERIC(10,2)", null],
        ["discount_amount", "NUMERIC(10,2)", null], ["total_amount", "NUMERIC(10,2)", null],
        ["currency", "VARCHAR", null], ["created_at", "TIMESTAMP", null], ["updated_at", "TIMESTAMP", null]
    ], "table"],
    ["order_items", [
        ["id", "UUID", "PK"], ["order_id", "UUID", "FK"], ["reservation_id", "UUID", "FK"],
        ["variant_id", "UUID", "FK"], ["quantity", "INTEGER", null], ["unit_price", "NUMERIC(10,2)", null],
        ["line_total", "NUMERIC(10,2)", null], ["product_id", "UUID", null],
        ["product_name", "VARCHAR", null], ["variant_sku", "VARCHAR", null], ["size_id", "UUID", null],
        ["color_id", "UUID", null], ["image_url", "VARCHAR", null], ["image_public_id", "VARCHAR", null]
    ], "association class"],
    ["payment_attempts", [
        ["id", "UUID", "PK"], ["order_id", "UUID", "FK"], ["cart_id", "UUID", "FK"],
        ["stripe_payment_intent_id", "VARCHAR", null], ["status", "VARCHAR", null],
        ["idempotency_key", "VARCHAR", null], ["created_at", "TIMESTAMP", null], ["updated_at", "TIMESTAMP", null]
    ], "table"],
    ["stripe_events", [
        ["id", "UUID", "PK"], ["stripe_event_id", "VARCHAR", null], ["created_at", "TIMESTAMP", null]
    ], "table"],

    // --- PAQUETE P5: VENTAS POS Y POLÍTICAS COMERCIALES ---
    ["sales", [
        ["id", "UUID", "PK"], ["branch_id", "UUID", "FK"], ["user_id", "UUID", "FK"],
        ["reservation_id", "UUID", "FK"], ["status", "VARCHAR", "enum"],
        ["payment_method", "VARCHAR", "enum"], ["total_amount", "NUMERIC(10,2)", null],
        ["cash_received", "NUMERIC(10,2)", null], ["cash_change", "NUMERIC(10,2)", null],
        ["customer_name", "VARCHAR", null], ["customer_phone", "VARCHAR", null],
        ["created_at", "TIMESTAMP", null]
    ], "table"],
    ["sale_items", [
        ["id", "UUID", "PK"], ["sale_id", "UUID", "FK"], ["variant_id", "UUID", "FK"],
        ["quantity", "INTEGER", null], ["unit_price", "NUMERIC(10,2)", null],
        ["total_price", "NUMERIC(10,2)", null]
    ], "association class"],

    // --- PAQUETE P6: INTELIGENCIA ANALÍTICA, RECOMENDACIONES Y PUSH ---
    ["user_product_interactions", [
        ["id", "UUID", "PK"], ["user_id", "UUID", "FK"], ["product_id", "UUID", "FK"],
        ["variant_id", "UUID", "FK"], ["branch_id", "UUID", "FK"], ["order_id", "UUID", "FK"],
        ["interaction_type", "VARCHAR(30)", null], ["rating", "INTEGER", null],
        ["metadata", "JSON", null], ["created_at", "TIMESTAMP", null]
    ], "table"],
    ["collaborative_embeddings", [
        ["id", "UUID", "PK"], ["subject_type", "VARCHAR(16)", null], ["subject_id", "UUID", null],
        ["vector", "TEXT", null], ["updated_at", "TIMESTAMP", null]
    ], "table"],
    ["conversations", [
        ["id", "UUID", "PK"], ["user_id", "UUID", "FK"], ["title", "VARCHAR(150)", null],
        ["created_at", "TIMESTAMP", null], ["updated_at", "TIMESTAMP", null]
    ], "table"],
    ["conversation_messages", [
        ["id", "UUID", "PK"], ["conversation_id", "UUID", "FK"], ["role", "VARCHAR(20)", null],
        ["content", "TEXT", null], ["created_at", "TIMESTAMP", null]
    ], "table"],
    ["notifications", [
        ["id", "UUID", "PK"], ["user_id", "UUID", "FK"], ["title", "VARCHAR(150)", null],
        ["body", "TEXT", null], ["is_read", "BOOLEAN", null],
        ["data", "JSON", null], ["created_at", "TIMESTAMP", null]
    ], "table"],
    ["device_tokens", [
        ["id", "UUID", "PK"], ["user_id", "UUID", "FK"], ["token", "VARCHAR(255)", null],
        ["platform", "VARCHAR(20)", null], ["is_active", "BOOLEAN", null],
        ["created_at", "TIMESTAMP", null], ["updated_at", "TIMESTAMP", null]
    ], "table"]
];

// ============================================================================
// FUNCIÓN PRINCIPAL DE EJECUCIÓN
// ============================================================================
function Main() {
    Log("Iniciando creación de Modelo UML de Clases y Datos (FashionStore 2P)...");

    var packageDestino = Repo.GetTreeSelectedPackage();
    if (packageDestino == null) {
        if (Repo.Models.Count > 0) {
            packageDestino = Repo.Models.GetAt(0);
        } else {
            Session.Prompt("Error: No se encontró ningún modelo ni paquete seleccionado en Enterprise Architect.", 0);
            return;
        }
    }

    // Crear paquete contenedor
    var model = packageDestino.Packages.AddNew("Modelo de Clases y Datos FashionStore - 2do Parcial", "");
    model.Update();

    var elementos = {};
    var total = TABLAS.length;

    Log("Creando " + total + " entidades estereotipadas («table», «association class», «role»)...");

    // 1) Crear cada entidad con su estereotipo y atributos
    for (var i = 0; i < total; i++) {
        var tabla = TABLAS[i][0];
        var campos = TABLAS[i][1];
        var estereoClase = (TABLAS[i].length > 2 && TABLAS[i][2] != null) ? TABLAS[i][2] : "table";

        var cls = model.Elements.AddNew(tabla, "Class");
        cls.Stereotype = estereoClase;
        cls.Update();

        for (var j = 0; j < campos.length; j++) {
            var campo = campos[j][0];
            var tipo  = campos[j][1];
            var est   = campos[j][2];
            var a = cls.Attributes.AddNew(campo, eaType(tipo));
            if (est != null) a.Stereotype = est;
            a.Update();
        }
        cls.Update();
        elementos[tabla] = cls;
    }

    Log("Creando " + RELACIONES.length + " relaciones (Composiciones, Herencias y Asociaciones)...");

    // 2) Crear relaciones tipadas (Composición, Generalización, Asociación)
    var creadas = 0;
    var nComp = 0, nGen = 0, nAssoc = 0;

    for (var r = 0; r < RELACIONES.length; r++) {
        var rel = RELACIONES[r];
        var origen  = rel[0];
        var destino = rel[1];
        var verbo   = rel[2];
        var cardOrigen  = rel[3];
        var cardDestino = rel[4];
        var tipoRel = (rel.length > 5 && rel[5] != null) ? rel[5] : "Association";

        if (elementos[origen] == null || elementos[destino] == null) {
            Log("Aviso: No se pudo relacionar " + origen + " con " + destino + " (entidad no encontrada).");
            continue;
        }

        if (tipoRel == "Generalization") {
            // HERENCIA: Origen = Subclase, Destino = Superclase. Flecha triangular cerrada en Destino.
            var conn = elementos[origen].Connectors.AddNew("", "Generalization");
            conn.ClientID    = elementos[origen].ElementID;
            conn.SupplierID  = elementos[destino].ElementID;
            conn.Direction   = "Source -> Destination";
            conn.Update();
            creadas++;
            nGen++;
        } else if (tipoRel == "Composition") {
            // COMPOSICIÓN: Origen = Todo (Rombo Negro), Destino = Parte. Línea sólida sin flechas.
            var conn = elementos[origen].Connectors.AddNew(verbo, "Aggregation");
            conn.ClientID    = elementos[origen].ElementID;
            conn.SupplierID  = elementos[destino].ElementID;
            conn.Subtype     = "Strong";
            conn.ClientEnd.Aggregation = 2; // 2 = Composite (Rombo negro en Origen)
            conn.ClientEnd.Cardinality = cardOrigen;
            conn.SupplierEnd.Cardinality = cardDestino;
            conn.Direction   = "Unspecified";
            conn.Update();
            creadas++;
            nComp++;
        } else {
            // ASOCIACIÓN ESTÁNDAR: Línea simple sin flechas con cardinalidades.
            var conn = elementos[origen].Connectors.AddNew(verbo, "Association");
            conn.ClientID    = elementos[origen].ElementID;
            conn.SupplierID  = elementos[destino].ElementID;
            conn.ClientEnd.Cardinality  = cardOrigen;
            conn.SupplierEnd.Cardinality = cardDestino;
            conn.Direction   = "Unspecified";
            conn.Update();
            creadas++;
            nAssoc++;
        }
    }

    Log("Creando diagrama y posicionando elementos en grilla compacta...");

    // 3) Crear el diagrama y distribuir las entidades
    var diagram = model.Diagrams.AddNew("Diagrama de Clases BD — FashionStore 2P", "Logical");
    diagram.Update();

    // Distribución compacta en matriz de 6 columnas
    var cols = 6;
    var ancho = 165;
    var alto = 110;
    var gapX = 85;
    var gapY = 75;
    var x0 = 40;
    var y0 = 40;

    for (var k = 0; k < total; k++) {
        var nombre = TABLAS[k][0];
        var obj = elementos[nombre];
        if (obj == null) continue;

        var fila = Math.floor(k / cols);
        var col = k % cols;
        var left   = x0 + col * (ancho + gapX);
        var top    = y0 + fila * (alto + gapY);

        var dObj = diagram.DiagramObjects.AddNew("l=" + left + ";r=" + (left + ancho) + ";t=" + top + ";b=" + (top + alto) + ";", "");
        dObj.ElementID = obj.ElementID;
        dObj.Update();
    }

    diagram.Update();
    Repo.RefreshModelView(diagram.DiagramID);
    Repo.OpenDiagram(diagram.DiagramID);

    Log("¡Éxito! Generado con " + total + " entidades (" + nComp + " Composiciones, " + nGen + " Herencias, " + nAssoc + " Asociaciones).");
    try {
        Session.Prompt("¡Diagrama de Clases UML actualizado exitosamente!\n" +
                       "- Total entidades: " + total + " (incluye 9 «association class» y 5 «role»)\n" +
                       "- Composiciones (Rombo negro): " + nComp + "\n" +
                       "- Herencias (Generalización): " + nGen + "\n" +
                       "- Asociaciones simples: " + nAssoc, 0);
    } catch(e) {}
}

Main();
// ============================================================================
// FIN DEL SCRIPT
// ============================================================================
