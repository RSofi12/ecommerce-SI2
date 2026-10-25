# -*- coding: utf-8 -*-
with open('create_document.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Reemplazo del bloque de actores
old_actores_sub = """actores_data = [
    ("Superadmin Plataforma", "Humano (Nivel SaaS)", "Responsable máximo de la plataforma. Administra el registro de empresas contratantes (tenants), gestiona los planes de suscripción, asigna administradores y supervisa métricas globales de la infraestructura."),
    ("Administrador Tenant", "Humano (Nivel Empresa)", "Usuario responsable de una empresa cliente específica. Administra las sucursales dentro de los límites de su plan, gestiona el catálogo de productos, empleados, consulta suscripciones y solicita reportes generativos."),
    ("Encargado de Sucursal", "Humano (Nivel Empresa)", "Personal a cargo de una tienda física. Gestiona inventario local, supervisa preparación de reservas, resuelve administrativamente conflictos de sincronización offline y autoriza cambios de prendas."),
    ("Cajero / Vendedor", "Humano (Nivel Empresa)", "Operador del punto de venta físico (POS). Consulta disponibilidad local, registra ventas de contado en modo offline, encola operaciones y activa la sincronización con el servidor central."),
    ("Cliente", "Humano (Nivel Empresa)", "Consumidor final. Consulta catálogo y disponibilidad local de prendas en la PWA o móvil incluso sin conexión, y registra reservas de prendas con vigencia temporal."),
    ("Sistema (Background Sync)", "Sistema (Automatizado)", "Servicio en segundo plano (Service Worker / WorkManager) que monitoriza la conectividad a red, disparando reintentos y envío de la cola de transacciones locales pendientes."),
    ("Backend (API Sync & Tx)", "Sistema (Automatizado)", "Servicio central en FastAPI que procesa el lote de sincronización, garantiza idempotencia mediante UUIDs, aplica transaccionalidad ACID y detecta colisiones de stock."),
    ("Módulo de IA & ML", "Sistema (Automatizado)", "Servicio analítico que interpreta lenguaje natural (NLP), genera reportes generativos y entrena/evalúa modelos de Machine Learning (supervisados y no supervisados).")
]"""

new_actores_sub = """actores_data = [
    ("Superadmin Plataforma", "Humano (Nivel SaaS)", "Administrador general de la plataforma SaaS. Registra empresas contratantes (tenants), configura planes comerciales (Básico vs Profesional), supervisa límites de recursos y evalúa la analítica global del sistema."),
    ("Administrador Tenant", "Humano (Nivel Empresa)", "Responsable general de la empresa cliente. Administra sus sucursales (respetando el límite del plan), empleados, catálogo de productos, promociones, entrena y evalúa modelos de analítica inteligente (Machine Learning), solicita reportes generativos por texto/voz y audita el estado de sincronización de sus sucursales."),
    ("Encargado de Sucursal", "Humano (Nivel Empresa)", "Responsable operativo de una tienda física. Administra reservas de prendas, resuelve administrativamente conflictos de inventario derivados de ventas offline, autoriza cambios y devoluciones de prendas, y supervisa existencias locales."),
    ("Cajero / Vendedor", "Humano (Nivel Empresa)", "Operador del punto de venta físico (POS). Consulta disponibilidad local, registra ventas de contado en modo offline, encola operaciones, dispara la sincronización al recuperar conexión, y tramita cambios físicos y devoluciones de prendas con comprobante."),
    ("Cliente", "Humano (Nivel Empresa)", "Consumidor final. Consulta catálogo y existencias locales de prendas incluso sin conexión, realiza reservas de prendas para probador/tienda y solicita devoluciones o cambios de prendas adquiridas dentro del plazo comercial establecido.")
]"""

if old_actores_sub in code:
    code = code.replace(old_actores_sub, new_actores_sub)
    print("Actores actualizados en el script.")
else:
    print("No se encontró old_actores_sub.")

# 2. Reemplazo de CU12
old_cu12 = """# CU12
add_cu_ficha(
    "CU12", "Procesar y Confirmar Operaciones con Idempotencia",
    "Garantizar en el backend que el reenvío múltiple de una misma operación offline no genere registros de venta duplicados ni descuadres dobles de inventario en la base de datos central.",
    "El endpoint de sincronización recibe cada operación acompañada de su UUID. El backend consulta la tabla sync_audit_logs; si el UUID ya existe y fue confirmado, omite la inserción y retorna el resultado exitoso previo. Si es nuevo, ejecuta la venta dentro de una transacción ACID descontando stock.",
    "Backend (API Sync & Tx).", "Backend automatizado.",
    "Petición de sincronización recibida con token JWT válido y payload estructurado.",
    "1. El backend recibe la operación con {sync_uuid, tenant_id, branch_id, items, total}.\\n"
    "2. El backend busca sync_uuid en la tabla sync_audit_logs.\\n"
    "3. Caso duplicado: Si existe, retorna HTTP 200 con el estado guardado previamente sin alterar nada.\\n"
    "4. Caso nuevo: Inicia bloque transaccional en PostgreSQL.\\n"
    "5. Descuenta el inventario central de cada variante verificando existencia disponible.\\n"
    "6. Inserta el registro en la tabla sales y sale_items.\\n"
    "7. Inserta el registro en sync_audit_logs con estado 'CONFIRMADA'.\\n"
    "8. Ejecuta commit de la transacción y responde confirmación al cliente.",
    "Se garantiza consistencia transaccional e idempotencia total (RNF04 y RNF05).",
    "- Violación de concurrencia: Rollback inmediato y marcado como conflicto."
)"""

new_cu12 = """# CU12
add_cu_ficha(
    "CU12", "Auditar Historial y Estado de Sincronización",
    "Permitir al Administrador Tenant y Encargado de Sucursal supervisar y auditar el historial de operaciones comerciales recibidas desde las terminales offline, verificando la consistencia transaccional y la ausencia de duplicados.",
    "El Administrador Tenant o el Encargado accede a la vista de auditoría de sincronizaciones. El sistema lista las transacciones recibidas con su UUID, terminal de origen, hora de recepción y estado final confirmado. El usuario puede filtrar operaciones confirmadas o en conflicto para validar que no existan cobros duplicados ni inconsistencias contables.",
    "Administrador Tenant, Encargado de Sucursal.", "Administrador Tenant o Encargado de Sucursal.",
    "Usuario con rol ADMIN_TENANT o ENCARGADO_SUCURSAL autenticado.",
    "1. El usuario accede al módulo 'Auditoría de Sincronización'.\\n"
    "2. El sistema consulta la bitácora central de sincronizaciones filtrada por el tenant_id del usuario.\\n"
    "3. El sistema muestra la tabla con sync_uuid, terminal de caja, fecha/hora de venta local, fecha/hora de confirmación central, monto y estado.\\n"
    "4. El usuario selecciona una transacción para inspeccionar el detalle de prendas y movimientos de stock aplicados.\\n"
    "5. El usuario verifica que los reintentos de red no hayan generado registros duplicados (idempotencia confirmada).\\n"
    "6. El usuario puede exportar el reporte de auditoría de sincronización.",
    "El usuario obtiene trazabilidad completa sobre el impacto de las ventas offline en la base de datos central.",
    "- Discrepancia detectada: El usuario reporta la transacción para revisión técnica."
)"""

if old_cu12 in code:
    code = code.replace(old_cu12, new_cu12)
    print("CU12 actualizado a actor humano.")
else:
    print("No se encontró old_cu12.")

# 3. Incorporación de Devoluciones (CU15) y desplazamiento de códigos promocionales a CU16
old_cu14_15 = """# CU14
add_cu_ficha(
    "CU14", "Gestionar Cambios de Prendas de Vestir",
    "Permitir al cajero registrar la devolución y cambio de una prenda adquirida por un cliente dentro del plazo comercial establecido, actualizando el inventario de la sucursal.",
    "El cliente acude a la sucursal con una prenda dentro de los 7 días de compra. El cajero ingresa el número de comprobante, selecciona la prenda devuelta e ingresa la nueva prenda solicitada (talla o color diferente). El sistema reintegra la prenda devuelta al inventario y rebaja la nueva prenda entregada.",
    "Cajero / Vendedor, Encargado de Sucursal.", "Cajero / Vendedor.",
    "Comprobante de venta válido y dentro del plazo de 7 días (RN-06).",
    "1. El cliente presenta el comprobante y la prenda a cambiar.\\n"
    "2. El cajero accede a 'Gestión de Cambios' e introduce el código del comprobante.\\n"
    "3. El sistema valida la fecha de la venta original.\\n"
    "4. El cajero selecciona el ítem devuelto y escanea la nueva variante entregada.\\n"
    "5. Si existe diferencia de precio, el sistema liquida el saldo a favor o en contra.\\n"
    "6. El sistema reingresa 1 unidad de la prenda original y descuenta 1 unidad de la nueva prenda en el inventario de la sucursal.\\n"
    "7. Se emite comprobante de cambio de mercadería.",
    "El inventario de la sucursal queda cuadrado y el cambio queda registrado formalmente.",
    "- Plazo vencido (> 7 días): Sistema advierte que el cambio requiere autorización expresa del Encargado.\\n"
    "- Prenda nueva sin stock: Sugerir otra talla o sucursal cercana."
)

# CU15
add_cu_ficha(
    "CU15", "Gestionar Códigos Promocionales y Cupones por Tenant",
    "Permitir al Administrador Tenant crear cupones de descuento (porcentaje o monto fijo) con alcance global o por sucursal, y aplicarlos durante el cálculo de ventas o carritos.",
    "El Administrador define códigos de descuento con vigencia, monto mínimo de compra y sucursales habilitadas. Los cajeros y clientes pueden aplicar el código para obtener el beneficio en el total a pagar.",
    "Administrador Tenant, Encargado, Cliente, Cajero.", "Administrador Tenant o Cliente/Cajero.",
    "Usuario con permisos para crear cupones o cliente en proceso de compra.",
    "1. El Administrador define código (ej. VERANO2026), descuento (ej. 15%), vigencia y sucursal.\\n"
    "2. Al registrar una venta, el cajero o cliente introduce el código promocional.\\n"
    "3. El sistema valida vigencia, tenant_id y condiciones de uso.\\n"
    "4. El sistema descuenta el valor promocional del total a cobrar.\\n"
    "5. El comprobante refleja el descuento aplicado de forma desglosada.",
    "La venta se liquida con el beneficio promocional y se contabiliza el uso del cupón.",
    "- Cupón vencido o inexistente: Notifica 'Código no válido o expirado'."
)"""

new_cu14_15_16 = """# CU14
add_cu_ficha(
    "CU14", "Gestionar Cambios de Prendas de Vestir",
    "Permitir al cajero registrar el cambio de una prenda adquirida por un cliente por otra talla o color dentro del plazo comercial establecido, actualizando el inventario de la sucursal.",
    "El cliente acude a la sucursal con una prenda dentro de los 7 días de compra. El cajero ingresa el número de comprobante, selecciona la prenda entregada e ingresa la nueva prenda solicitada. El sistema reintegra la prenda entregada al inventario y rebaja la nueva prenda retirada.",
    "Cajero / Vendedor, Encargado de Sucursal, Cliente.", "Cliente (iniciador presencial), Cajero / Vendedor.",
    "Comprobante de venta válido y dentro del plazo de 7 días (RN-06).",
    "1. El cliente presenta el comprobante de venta y la prenda a cambiar en buen estado.\\n"
    "2. El cajero accede a 'Gestión de Cambios' e introduce el código del comprobante.\\n"
    "3. El sistema valida la fecha de compra original.\\n"
    "4. El cajero selecciona el ítem a cambiar y escanea la nueva variante requerida.\\n"
    "5. Si existe diferencia de precio, el sistema liquida el saldo a favor o en contra.\\n"
    "6. El sistema reingresa 1 unidad de la prenda original y descuenta 1 unidad de la nueva prenda en el inventario local.\\n"
    "7. Se emite comprobante de cambio de mercadería al cliente.",
    "El inventario de la sucursal queda actualizado y el cambio queda registrado formalmente.",
    "- Plazo vencido (> 7 días): Requiere autorización expresa del Encargado de Sucursal.\\n"
    "- Prenda requerida sin stock: Se sugiere otra talla, modelo o sucursal cercana."
)

# CU15
add_cu_ficha(
    "CU15", "Gestionar Devoluciones de Prendas y Reembolsos",
    "Permitir al cliente solicitar y al cajero registrar la devolución total de una prenda adquirida por fallas o retracto comercial, reintegrando la prenda al stock y emitiendo la nota de crédito o reembolso.",
    "El cliente acude a la tienda solicitando la devolución de una prenda. El cajero inspecciona el producto y comprueba el ticket de compra. El Encargado de Sucursal autoriza la devolución en el sistema. El cajero confirma la operación, el sistema reincorpora la unidad al inventario físico de la empresa y se emite la nota de crédito o reembolso de efectivo correspondiente.",
    "Cliente, Cajero / Vendedor, Encargado de Sucursal.", "Cliente (solicitante), Cajero / Vendedor.",
    "Comprobante de venta original y prenda sin señales de uso indebido.",
    "1. El cliente solicita la devolución de una prenda presentando el comprobante original.\\n"
    "2. El cajero verifica físicamente la prenda e ingresa el comprobante en 'Devoluciones'.\\n"
    "3. El sistema comprueba que la compra pertenece al tenant activo y esté dentro del plazo normativo.\\n"
    "4. El cajero solicita la autorización al Encargado de Sucursal.\\n"
    "5. El Encargado valida la inspección y autoriza la devolución en el sistema con sus credenciales.\\n"
    "6. El cajero procesa la devolución seleccionando la modalidad: Efectivo o Nota de Crédito.\\n"
    "7. El sistema reingresa la prenda devuelta al stock de la sucursal y descuenta el monto de las ventas brutas.\\n"
    "8. El sistema imprime el comprobante de devolución para el cliente.",
    "La prenda queda reingresada en el inventario y el monto comercial queda debidamente regularizado.",
    "- Prenda dañada por mal uso: Encargado rechaza la devolución con justificación técnica.\\n"
    "- Comprobante no corresponde a la empresa: Se deniega la operación."
)

# CU16
add_cu_ficha(
    "CU16", "Gestionar Códigos Promocionales y Cupones por Tenant",
    "Permitir al Administrador Tenant crear cupones de descuento (porcentaje o monto fijo) con alcance global o por sucursal, y aplicarlos durante el cálculo de ventas o carritos.",
    "El Administrador define códigos de descuento con vigencia, monto mínimo de compra y sucursales habilitadas. Los cajeros y clientes pueden aplicar el código para obtener el beneficio en el total a pagar.",
    "Administrador Tenant, Encargado de Sucursal, Cliente, Cajero / Vendedor.", "Administrador Tenant o Cliente/Cajero.",
    "Usuario con permisos para crear cupones o cliente en proceso de compra.",
    "1. El Administrador define código (ej. VERANO2026), descuento (ej. 15%), vigencia y sucursal.\\n"
    "2. Al registrar una venta, el cajero o cliente introduce el código promocional.\\n"
    "3. El sistema valida vigencia, tenant_id y condiciones de uso.\\n"
    "4. El sistema descuenta el valor promocional del total a cobrar.\\n"
    "5. El comprobante refleja el descuento aplicado de forma desglosada.",
    "La venta se liquida con el beneficio promocional y se contabiliza el uso del cupón.",
    "- Cupón vencido o inexistente: Notifica 'Código no válido o expirado'."
)"""

if old_cu14_15 in code:
    code = code.replace(old_cu14_15, new_cu14_15_16)
    print("CU14, CU15 (Devoluciones) y CU16 (Cupones) actualizados.")
else:
    print("No se encontró old_cu14_15.")

# 4. Reemplazo del Ciclo 3 (CU17, CU18, CU19, CU20, CU21, CU22)
old_ciclo3 = """# CICLO #3
add_p("C. CICLO #3: INTELIGENCIA ARTIFICIAL GENERATIVA, MACHINE LEARNING Y ANALÍTICA", bold_prefix="")

# CU16
add_cu_ficha(
    "CU16", "Solicitar Reportes Generativos en Lenguaje Natural (Texto/Voz)",
    "Permitir a usuarios autorizados de la empresa solicitar reportes comerciales complejos utilizando lenguaje natural mediante escritura en teclado o comandos de voz en la web.",
    "El usuario accede al panel de analítica y formula preguntas empresariales (ej. 'Comparar las ventas de las sucursales en los últimos 3 meses' o 'Prendas con menor stock en Cochabamba'). En comandos de voz, la Web Speech API transcribe el audio a texto. La consulta es enviada al backend para su interpretación semántica.",
    "Administrador Tenant, Superadmin.", "Administrador Tenant.",
    "Usuario autenticado en una empresa con suscripción a plan Profesional (con IA activa).",
    "1. El usuario abre el módulo 'Reportes con Inteligencia Artificial'.\\n"
    "2. El usuario escribe su consulta o presiona el botón de micrófono para dictarla.\\n"
    "3. En caso de voz, el navegador captura el audio y transcribe el texto en tiempo real.\\n"
    "4. El usuario presiona 'Consultar'.\\n"
    "5. La aplicación envía el texto de la solicitud junto con el JWT del usuario al backend.\\n"
    "6. La interfaz muestra un indicador de procesamiento inteligente.",
    "La solicitud de lenguaje natural es recibida por el backend para su análisis e inferencia.",
    "- Plan sin módulo de IA (Básico): Muestra mensaje informativo indicando que su plan no incluye reportes generativos con IA."
)

# CU17
add_cu_ficha(
    "CU17", "Ejecutar Consulta Controlada y Segura de Datos con IA",
    "Interpretar la intención del usuario mediante un modelo de lenguaje, generando consultas SQL parametrizadas de solo lectura restringidas obligatoriamente al tenant del usuario autenticado.",
    "El backend procesa la orden mediante prompt engineering guiado por el esquema relacional. La IA extrae filtros (fechas, sucursales, categorías) y construye una consulta SELECT. El backend audita que no existan instrucciones destructivas (DROP, INSERT, UPDATE) e inyecta obligatoriamente 'WHERE tenant_id = :current_tenant' antes de ejecutarla en PostgreSQL.",
    "Backend (Módulo IA), Módulo de IA & ML.", "Backend automatizado.",
    "Texto de consulta en lenguaje natural recibido con tenant_id autenticado.",
    "1. El backend recibe la solicitud de reporte y extrae el tenant_id del token.\\n"
    "2. El módulo de IA mapea la semántica de la pregunta contra las tablas de la base de datos.\\n"
    "3. Se genera la estructura de consulta con agregaciones (COUNT, SUM, GROUP BY, DENSE_RANK).\\n"
    "4. El validador de seguridad verifica que la sentencia sea exclusivamente de tipo SELECT.\\n"
    "5. Se inyecta la cláusula de seguridad 'tenant_id = :user_tenant_id'.\\n"
    "6. Se ejecuta la consulta en la base de datos PostgreSQL.\\n"
    "7. Se obtienen los datos tabulares reales y se devuelven al frontend en formato JSON.",
    "Los datos reales del tenant son extraídos de forma segura sin riesgo de inyecciones maliciosas ni fugas entre empresas (RNF02).",
    "- Solicitud ambigua o no entendida: La IA responde amablemente solicitando reformular la consulta.\\n"
    "- Intento de consulta no autorizada: El backend rechaza la ejecución y registra la alerta de seguridad."
)

# CU18
add_cu_ficha(
    "CU18", "Presentar y Exportar Reportes Dinámicos (PDF / Excel)",
    "Renderizar en pantalla el reporte resultante en tablas interactivas y gráficos seleccionados dinámicamente según los datos, permitiendo exportar el reporte formal en formatos PDF y Excel.",
    "El cliente web recibe los datos de la consulta IA. El componente evalúa los datos y genera el gráfico adecuado (barras para comparar sucursales, líneas para ventas en el tiempo, pastel para categorías). El usuario puede filtrar columnas y pulsar 'Descargar PDF' o 'Descargar Excel' obteniendo el reporte con encabezados corporativos.",
    "Administrador Tenant, Superadmin.", "Administrador Tenant.",
    "Consulta generativa ejecutada exitosamente con resultados disponibles.",
    "1. La interfaz web recibe los datos tabulares y metadatos del reporte.\\n"
    "2. La aplicación selecciona automáticamente el tipo de gráfico más representativo y lo dibuja.\\n"
    "3. Se despliega una tabla con paginación, ordenamiento y totales calculados.\\n"
    "4. El usuario selecciona 'Exportar a PDF' o 'Exportar a Excel'.\\n"
    "5. El generador construye el archivo incorporando el nombre de la empresa, fecha, parámetros aplicados y firma del reporte.\\n"
    "6. El navegador descarga el archivo generado.",
    "El usuario obtiene un informe ejecutivo formal para la toma de decisiones comerciales.",
    "- Reporte con cero resultados: Muestra 'No se encontraron registros para los filtros solicitados'."
)

# CU19
add_cu_ficha(
    "CU19", "Generar y Preparar Datos Sintéticos para Modelos de ML",
    "Generar un conjunto de datos sintéticos representativo de transacciones de ventas, temporadas y clientes de tiendas de moda para entrenar y evaluar modelos de Machine Learning.",
    "Para garantizar un entrenamiento riguroso de los algoritmos sin depender exclusivamente del histórico inicial, se ejecuta un generador de datos que sintetiza miles de registros de compra con variaciones realistas de temporada, tallas y preferencias. Los datos se limpian, normalizan y separan en conjuntos de entrenamiento y prueba.",
    "Sistema, Data Engineer / Módulo IA & ML.", "Sistema / Script automatizado.",
    "Esquema de variables definido (precios, categorías, estacionalidad, frecuencias).",
    "1. Se ejecuta el script generador de datos sintéticos en Python.\\n"
    "2. Se crean registros distribuidos por temporadas comerciales (Primavera-Verano, Otoño-Invierno).\\n"
    "3. Se aplican correlaciones realistas (ej. mayor demanda de abrigos en invierno).\\n"
    "4. Se normalizan variables continuas (MinMaxScaler / StandardScaler) y se codifican categorías (One-Hot Encoding).\\n"
    "5. Se guarda el dataset procesado en formato estructurado para alimentar los modelos.",
    "Dataset sintético limpio y estructurado disponible para entrenamiento de modelos supervisados y no supervisados.",
    "- Inconsistencia de datos: El script recalibra las correlaciones antes de generar el lote final."
)

# CU20
add_cu_ficha(
    "CU20", "Ejecutar Modelo Supervisado (Predicción de Demanda / Ventas)",
    "Entrenar y ejecutar un modelo de aprendizaje supervisado (Regresión / Random Forest / Gradient Boosting) para predecir el volumen de ventas y demanda futura de prendas por sucursal y categoría.",
    "El sistema entrena un modelo predictivo sobre el histórico de ventas. El Administrador Tenant puede ingresar parámetros futuros (semana, temporada, sucursal) y el modelo proyecta la cantidad estimada de prendas que se venderán, permitiendo planificar las compras a proveedores con anticipación.",
    "Módulo de IA & ML, Administrador Tenant.", "Módulo IA & ML.",
    "Dataset de entrenamiento preparado (CU19).",
    "1. El módulo de ML carga los datos y entrena el modelo predictivo supervisado.\\n"
    "2. Se evalúa el desempeño mediante métricas de error (RMSE, MAE y R²).\\n"
    "3. El modelo se persiste en formato serializado (joblib / pickle).\\n"
    "4. El Administrador consulta las proyecciones de demanda para el próximo mes.\\n"
    "5. El modelo infiere y presenta las cantidades pronosticadas por categoría de prendas.\\n"
    "6. La interfaz grafica la curva de ventas históricas junto con la proyección estimada.",
    "La administración dispone de predicciones fundamentadas para optimizar inventarios y compras.",
    "- Error de modelo elevado: El sistema reentrena con ajuste de hiperparámetros."
)

# CU21
add_cu_ficha(
    "CU21", "Ejecutar Modelo No Supervisado (Segmentación / Detección de Anomalías)",
    "Entrenar y ejecutar un modelo de aprendizaje no supervisado (K-Means Clustering) para clasificar a los clientes en segmentos según su comportamiento de compra y detectar anomalías en inventarios.",
    "El algoritmo agrupa a los clientes en clusters (compradores frecuentes, cazadores de ofertas, clientes estacionales) sin requerir etiquetas previas, basándose en ticket promedio, frecuencia y categorías preferidas. Asimismo, identifica desviaciones atípicas de stock en sucursales.",
    "Módulo de IA & ML, Administrador Tenant.", "Módulo IA & ML.",
    "Datos de clientes y transacciones procesados.",
    "1. El algoritmo K-Means procesa los vectores de características de los clientes.\\n"
    "2. Se determina el número óptimo de clusters mediante el método del codo (Elbow Method).\\n"
    "3. Se asigna cada cliente a su segmento correspondiente.\\n"
    "4. Se generan las etiquetas descriptivas de cada grupo identificado.\\n"
    "5. El sistema detecta transacciones anómalas (outliers) que se desvían de los patrones estándar.\\n"
    "6. Los resultados se exponen en el dashboard analítico mediante gráficos de dispersión.",
    "Segmentación de clientes y detección de anomalías disponibles para estrategias de marketing y control de inventario.",
    "- Datos dispersos sin convergencia: Normalización y recalibración de distancias euclidianas."
)

# CU22
add_cu_ficha(
    "CU22", "Visualizar Dashboard Analítico Inteligente",
    "Presentar un cuadro de mando unificado y responsivo que consolida indicadores clave de desempeño (KPIs), proyecciones de demanda, segmentación y resultados de modelos inteligentes.",
    "El Administrador Tenant accede al dashboard principal donde observa: total facturado, sucursales más rentables, porcentaje de cumplimiento de inventario, gráfico de predicción de ventas futuras y distribución de clientes por clusters de Machine Learning.",
    "Administrador Tenant, Superadmin Plataforma.", "Administrador Tenant.",
    "Usuario autenticado con permisos de visualización ejecutiva.",
    "1. El usuario accede a la sección 'Dashboard Analítico'.\\n"
    "2. El sistema consulta las vistas agregadas de PostgreSQL filtradas por su tenant_id.\\n"
    "3. Se cargan los resultados más recientes de los modelos de ML.\\n"
    "4. Se despliegan tarjetas de métricas (KPIs), gráficas interactivas y alertas preventivas de stock.\\n"
    "5. El usuario puede filtrar por rango de fechas o sucursal específica.",
    "Visión global y estratégica del estado operativo y comercial de la empresa.",
    "- Falla de conexión a servicios de ML: Muestra las métricas transaccionales con aviso de actualización diferida de analítica."
)"""

new_ciclo3 = """# CICLO #3
add_p("C. CICLO #3: INTELIGENCIA ARTIFICIAL GENERATIVA, MACHINE LEARNING Y ANALÍTICA", bold_prefix="")

# CU17
add_cu_ficha(
    "CU17", "Solicitar Reportes Generativos en Lenguaje Natural (Texto y Voz)",
    "Permitir al Administrador Tenant solicitar reportes empresariales complejos utilizando lenguaje natural mediante escritura en teclado o comandos de voz en la web, obteniendo datos reales de su empresa.",
    "El usuario accede al panel de analítica y formula preguntas empresariales (ej. 'Mostrame las ventas de septiembre agrupadas por sucursal' o '¿Cuáles fueron los diez productos más vendidos este mes?'). El usuario habla o escribe, el sistema identifica los filtros solicitados y le presenta el reporte dinámico generado a partir de sus datos reales.",
    "Administrador Tenant, Superadmin Plataforma.", "Administrador Tenant.",
    "Usuario autenticado en una empresa con suscripción a plan Profesional (con IA habilitada).",
    "1. El usuario abre el módulo 'Reportes con Inteligencia Artificial'.\\n"
    "2. El usuario escribe su consulta o presiona el botón de micrófono para dictarla verbalmente.\\n"
    "3. En caso de voz, el navegador captura el audio y transcribe la orden en tiempo real.\\n"
    "4. El usuario presiona 'Consultar'.\\n"
    "5. La aplicación envía la solicitud al backend, el cual valida que la consulta no sea arbitraria y pertenezca al tenant.\\n"
    "6. La interfaz presenta los resultados tabulares y gráficos dinámicos construidos a partir de los datos reales.",
    "El Administrador visualiza el reporte empresarial generado sin necesidad de conocer SQL.",
    "- Plan sin módulo de IA (Básico): Notifica que el plan no incluye reportes generativos con IA.\\n"
    "- Solicitud ambigua: El sistema solicita al usuario especificar fechas o sucursales."
)

# CU18
add_cu_ficha(
    "CU18", "Presentar y Exportar Reportes Dinámicos (PDF / Excel)",
    "Permitir al Administrador Tenant visualizar en pantalla el reporte interactivo y exportarlo formalmente a formatos convencionales de hoja de cálculo Excel o documento PDF.",
    "El usuario interactúa con la vista del reporte generativo. Puede ordenar columnas, alternar entre tabla y gráficos de barras o líneas, y presionar los botones de exportación para descargar el archivo formal con formato corporativo.",
    "Administrador Tenant, Superadmin Plataforma.", "Administrador Tenant.",
    "Reporte generativo consultado con resultados disponibles en pantalla.",
    "1. La interfaz web recibe los datos del reporte solicitado por el usuario.\\n"
    "2. El sistema dibuja el gráfico dinámico seleccionado automáticamente y despliega la tabla.\\n"
    "3. El usuario revisa los totales, agrupaciones y gráficos en pantalla.\\n"
    "4. El usuario pulsa 'Exportar a PDF' o 'Exportar a Excel'.\\n"
    "5. El sistema construye el documento incluyendo membrete de la empresa, fecha de emisión y firma de reporte.\\n"
    "6. El navegador descarga el archivo generado.",
    "El Administrador Tenant cuenta con un informe físico o digital formal para reuniones gerenciales.",
    "- Sin registros: Se notifica que los filtros aplicados no arrojaron resultados."
)

# CU19
add_cu_ficha(
    "CU19", "Gestionar Preparación de Datos y Parámetros para Machine Learning",
    "Permitir al Administrador Tenant o Superadmin configurar los parámetros de entrenamiento, rangos temporales y generar el conjunto de datos necesario para alimentar los modelos de Machine Learning.",
    "El Administrador accede a la sección de configuración de Machine Learning. Define las temporadas, sucursales y categorías a incluir, y activa la preparación del dataset (combinando el historial transaccional con datos sintéticos para calibrar estacionalidades). El usuario valida las variables seleccionadas antes de proceder al entrenamiento.",
    "Administrador Tenant, Superadmin Plataforma.", "Administrador Tenant o Superadmin.",
    "Usuario con permisos administrativos y acceso a módulos de analítica avanzada.",
    "1. El Administrador accede a 'Configuración de Machine Learning'.\\n"
    "2. El usuario selecciona las variables de análisis: sucursales, periodos comerciales y categorías de ropa.\\n"
    "3. El usuario activa la opción 'Generar y Preparar Datos de Entrenamiento'.\\n"
    "4. El sistema ejecuta el preprocesamiento, normalización y síntesis de datos representativos.\\n"
    "5. El usuario visualiza el resumen del dataset generado: cantidad de muestras, variables procesadas y balance de datos.\\n"
    "6. El usuario confirma la aprobación del dataset para entrenamiento.",
    "El conjunto de datos queda verificado por el usuario y preparado para los modelos de ML.",
    "- Datos insuficientes: El sistema alerta al usuario y sugiere ampliar el rango de fechas."
)

# CU20
add_cu_ficha(
    "CU20", "Entrenar y Evaluar Modelo Predictivo de Demanda de Ventas (Supervisado)",
    "Permitir al Administrador Tenant entrenar el modelo de aprendizaje supervisado, evaluar sus métricas de error y consultar las proyecciones futuras de demanda de prendas para la toma de decisiones.",
    "El usuario pulsa el botón para iniciar el entrenamiento del modelo supervisado de regresión/demanda. La interfaz le presenta las métricas de evaluación obtenidas (RMSE, R²). El Administrador interactúa con simuladores ingresando semanas futuras y visualiza la curva de ventas esperadas por categoría y sucursal.",
    "Administrador Tenant.", "Administrador Tenant.",
    "Dataset de datos preparado y validado en CU19.",
    "1. El Administrador accede a 'Predicción de Demanda de Ventas'.\\n"
    "2. El usuario presiona 'Entrenar Modelo Supervisado'.\\n"
    "3. El sistema entrena el algoritmo y muestra el cuadro de evaluación con métricas de precisión.\\n"
    "4. El usuario selecciona la sucursal y el mes futuro que desea proyectar.\\n"
    "5. El sistema presenta la gráfica comparativa entre histórico real y la demanda estimada.\\n"
    "6. El Administrador utiliza los resultados para emitir órdenes de abastecimiento a proveedores.",
    "El usuario cuenta con pronósticos de demanda confiables para evitar quiebres o excesos de inventario.",
    "- Precisión baja: El sistema sugiere ajustar hiperparámetros o enriquecer el dataset."
)

# CU21
add_cu_ficha(
    "CU21", "Analizar Segmentos de Clientes y Patrones de Compra (No Supervisado)",
    "Permitir al Administrador Tenant ejecutar el análisis de agrupamiento (K-Means) sobre el comportamiento de sus clientes, explorando los clusters identificados y detectando patrones o anomalías de venta.",
    "El Administrador ejecuta el modelo no supervisado. La interfaz le presenta un diagrama de dispersión interactivo con los grupos de clientes descubiertos (ej. clientes de alta frecuencia, compradores de ofertas, clientes estacionales) y destaca anomalías de inventario, permitiendo al Administrador diseñar estrategias comerciales dirigidas.",
    "Administrador Tenant.", "Administrador Tenant.",
    "Historial de clientes y compras disponible en el sistema.",
    "1. El Administrador accede a 'Segmentación y Patrones de Compra'.\\n"
    "2. El usuario presiona 'Ejecutar Análisis de Segmentación'.\\n"
    "3. El sistema ejecuta el clustering K-Means y genera las agrupaciones de clientes.\\n"
    "4. El usuario visualiza las tarjetas de cada segmento con su ticket promedio, prendas favoritas y frecuencia.\\n"
    "5. El usuario explora el panel de anomalías que señala discrepancias o comportamientos atípicos.\\n"
    "6. El Administrador exporta la lista de clientes por segmento para campañas promocionales.",
    "El usuario obtiene conocimiento estratégico sobre sus clientes sin necesidad de etiquetado previo.",
    "- Sin patrones definidos: El sistema notifica dispersión excesiva y sugiere agrupar por mes."
)

# CU22
add_cu_ficha(
    "CU22", "Consultar Cuadro de Mando y Dashboard Analítico Ejecutivo",
    "Permitir al Administrador Tenant (o Superadmin para visión global) consultar un cuadro de mando integral e interactivo con indicadores comerciales (KPIs), gráficas de rotación y síntesis de los modelos de IA.",
    "El usuario accede a la pantalla principal de analítica ejecutiva. Visualiza tarjetas dinámicas con volumen de ventas, sucursales más rentables, estado de sincronización y los resúmenes de los modelos de predicción y clustering, aplicando filtros por fecha o sucursal.",
    "Administrador Tenant, Superadmin Plataforma.", "Administrador Tenant o Superadmin.",
    "Usuario con perfil gerencial o directivo autenticado.",
    "1. El usuario accede al menú 'Dashboard Ejecutivo'.\\n"
    "2. El sistema carga las tarjetas de métricas consolidadas del tenant.\\n"
    "3. El usuario revisa los KPIs: Facturación mensual, cumplimiento de inventario y estado de tiendas.\\n"
    "4. El usuario interactúa con los filtros interactivos seleccionando una sucursal específica.\\n"
    "5. El dashboard refresca los gráficos de tendencias, comparativas de sucursales y alertas inteligentes.\\n"
    "6. El usuario visualiza la síntesis de recomendaciones emitidas por los modelos de ML.",
    "El usuario directivo cuenta con una visión 360° en tiempo real del desempeño de su empresa.",
    "- Falla de comunicación con servicios de analítica: Muestra los datos transaccionales con aviso de analítica diferida."
)"""

if old_ciclo3 in code:
    code = code.replace(old_ciclo3, new_ciclo3)
    print("Ciclo 3 completamente actualizado con actores humanos.")
else:
    print("No se encontró old_ciclo3.")

with open('create_document.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Modificaciones completadas.")
