# -*- coding: utf-8 -*-
"""
Script generador exhaustivo y completo de la documentación del 2do Parcial para '2do-Parcial-Informe-grupo-46.docx'.
Incluye redacción formal, fichas completas de casos de uso (Propósito, Resumen, Actores, Precondición, Flujo Principal, Postcondición y Excepciones),
tablas de BD, diagramas de robustez textuales con Boundary-Control-Entity y especificaciones de código.
"""
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

doc = docx.Document()

# Configuración de márgenes estándar (2.5 cm)
for section in doc.sections:
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)

# Estilo base
normal_style = doc.styles['Normal']
normal_style.font.name = 'Calibri'
normal_style.font.size = Pt(11)
normal_style.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
normal_style.paragraph_format.line_spacing = 1.15
normal_style.paragraph_format.space_after = Pt(4)

def set_cell_shading(cell, color_hex):
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading)

def set_cell_margins(cell, top=100, bottom=100, left=140, right=140):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def add_header(text, level):
    h = doc.add_heading(text, level=level)
    h.paragraph_format.keep_with_next = True
    run = h.runs[0]
    run.font.name = 'Calibri'
    if level == 1:
        run.font.size = Pt(15)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)
        h.paragraph_format.space_before = Pt(14)
        h.paragraph_format.space_after = Pt(6)
    elif level == 2:
        run.font.size = Pt(13)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x2E, 0x5B, 0x88)
        h.paragraph_format.space_before = Pt(10)
        h.paragraph_format.space_after = Pt(4)
    elif level == 3:
        run.font.size = Pt(11.5)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
        h.paragraph_format.space_before = Pt(8)
        h.paragraph_format.space_after = Pt(2)
    return h

def add_p(text, bold_prefix=None, space_after=4):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_b = p.add_run(bold_prefix)
        r_b.bold = True
        r_b.font.name = 'Calibri'
        r_b.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)
    r = p.add_run(text)
    r.font.name = 'Calibri'
    return p

def add_bullet(text, bold_prefix=None):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_b = p.add_run(bold_prefix)
        r_b.bold = True
        r_b.font.name = 'Calibri'
    r = p.add_run(text)
    r.font.name = 'Calibri'
    return p

def add_styled_table(headers, rows_data, col_widths=None):
    table = doc.add_table(rows=len(rows_data) + 1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    # Cabecera
    hdr_cells = table.rows[0].cells
    for i, header_text in enumerate(headers):
        hdr_cells[i].text = header_text
        set_cell_shading(hdr_cells[i], "1B365D")
        set_cell_margins(hdr_cells[i], top=120, bottom=120, left=140, right=140)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            r.font.bold = True
            r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            r.font.size = Pt(9.5)
            r.font.name = 'Calibri'

    # Filas
    for row_idx, row_data in enumerate(rows_data):
        row_cells = table.rows[row_idx + 1].cells
        bg_color = "F4F6F9" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, cell_value in enumerate(row_data):
            row_cells[col_idx].text = str(cell_value)
            set_cell_shading(row_cells[col_idx], bg_color)
            set_cell_margins(row_cells[col_idx], top=70, bottom=70, left=110, right=110)
            p = row_cells[col_idx].paragraphs[0]
            for r in p.runs:
                r.font.size = Pt(9)
                r.font.name = 'Calibri'
                r.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

    if col_widths:
        for row in table.rows:
            for idx, width in enumerate(col_widths):
                row.cells[idx].width = width

    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    return table

def add_cu_ficha(cu_id, nombre, proposito, resumen, actores, actor_iniciador, precondicion, flujo_principal, postcondicion, excepciones):
    """Genera una ficha formal de Caso de Uso como tabla elegante."""
    table = doc.add_table(rows=8, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    # Configuración de anchos: Columna 1 (2.0 in), Columna 2 (4.5 in)
    widths = [Inches(1.8), Inches(4.7)]
    for row in table.rows:
        row.cells[0].width = widths[0]
        row.cells[1].width = widths[1]

    fields = [
        ("Caso de Uso", f"{cu_id} — {nombre}"),
        ("Propósito", proposito),
        ("Resumen", resumen),
        ("Actores", f"Participantes: {actores}\nIniciador: {actor_iniciador}"),
        ("Precondición", precondicion),
        ("Flujo Principal", flujo_principal),
        ("Postcondición", postcondicion),
        ("Excepciones / Flujos Alternos", excepciones)
    ]

    for idx, (label, val) in enumerate(fields):
        c_label = table.rows[idx].cells[0]
        c_val = table.rows[idx].cells[1]

        c_label.text = label
        c_val.text = val

        set_cell_shading(c_label, "E8EEF5")
        set_cell_shading(c_val, "FFFFFF")
        set_cell_margins(c_label, top=60, bottom=60, left=100, right=100)
        set_cell_margins(c_val, top=60, bottom=60, left=100, right=100)

        p_l = c_label.paragraphs[0]
        for r in p_l.runs:
            r.font.bold = True
            r.font.size = Pt(9)
            r.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)

        p_v = c_val.paragraphs[0]
        for r in p_v.runs:
            r.font.size = Pt(9)
            r.font.color.rgb = RGBColor(0x22, 0x22, 0x22)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

# ==============================================================================
# CARÁTULA
# ==============================================================================
p_u = doc.add_paragraph()
p_u.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_u.paragraph_format.space_before = Pt(20)
p_u.paragraph_format.space_after = Pt(2)
r = p_u.add_run("UNIVERSIDAD AUTÓNOMA GABRIEL RENÉ MORENO")
r.bold = True
r.font.size = Pt(15)
r.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)

p_f = doc.add_paragraph()
p_f.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_f.paragraph_format.space_after = Pt(30)
r = p_f.add_run("FACULTAD DE INGENIERÍA EN CIENCIAS DE LA COMPUTACIÓN Y TELECOMUNICACIONES\nCARRERA DE INGENIERÍA EN SISTEMAS")
r.bold = True
r.font.size = Pt(12)
r.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

p_t = doc.add_paragraph()
p_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_t.paragraph_format.space_before = Pt(35)
p_t.paragraph_format.space_after = Pt(35)
r = p_t.add_run("PLATAFORMA E-COMMERCE SAAS MULTITENANT CON OPERACIONES OFFLINE EN PWA Y FLUTTER, REPORTES GENERATIVOS CON IA Y APRENDIZAJE AUTOMÁTICO PARA EMPRESAS COMERCIALIZADORAS DE PRENDAS DE VESTIR EN BOLIVIA")
r.bold = True
r.font.size = Pt(14)
r.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)

p_info = doc.add_paragraph()
p_info.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_info.paragraph_format.space_after = Pt(40)
r = p_info.add_run("SEGUNDO EXAMEN PARCIAL — GESTIÓN 2-2026\nMATERIA: Sistemas de Información II - INF 412 (GRUPO 46)\nDOCENTE: MSc. Ing. Angélica Garzón Cuéllar")
r.font.size = Pt(11)
r.bold = True
r.font.color.rgb = RGBColor(0x2E, 0x5B, 0x88)

p_int = doc.add_paragraph()
p_int.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_int.paragraph_format.space_after = Pt(50)
r = p_int.add_run("INTEGRANTES:\nRodriguez Laguna Raysa Sofia — Reg. 222009683\nArana Sotomayor Miguel Rene — Reg. 222007389")
r.font.size = Pt(11)
r.font.color.rgb = RGBColor(0x22, 0x22, 0x22)

p_l = doc.add_paragraph()
p_l.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p_l.add_run("Santa Cruz de la Sierra – Bolivia\nNoviembre 2026")
r.font.size = Pt(10)
r.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

doc.add_page_break()

# ==============================================================================
# ÍNDICE GENERAL
# ==============================================================================
add_header("ÍNDICE GENERAL", level=1)

indice_items = [
    ("CAPÍTULO I. ASPECTOS GENERALES", "3"),
    ("1.1. Introducción", "3"),
    ("1.2. Planteamiento del problema", "4"),
    ("1.3. Objetivos del proyecto", "5"),
    ("   1.3.1. Objetivo general", "5"),
    ("   1.3.2. Objetivos específicos", "5"),
    ("1.4. Justificación", "6"),
    ("1.5. Alcance y limitaciones", "7"),
    ("1.6. Metodología de desarrollo ICONIX", "8"),
    ("CAPÍTULO II. ANÁLISIS DE REQUISITOS", "10"),
    ("2.1. Descripción del sistema propuesto", "10"),
    ("2.2. Identificación de actores", "11"),
    ("2.3. Requisitos funcionales y no funcionales", "13"),
    ("2.4. Reglas de negocio", "16"),
    ("2.5. Diagrama UML de casos de uso", "17"),
    ("2.6. Especificación de casos de uso (Ciclos #1, #2 y #3)", "18"),
    ("CAPÍTULO III. ANÁLISIS Y DISEÑO CON ICONIX", "32"),
    ("3.1. Modelo de dominio", "32"),
    ("3.2. Diagramas de robustez (Boundary - Control - Entity)", "34"),
    ("3.3. Diagramas de secuencia UML", "38"),
    ("3.4. Diagrama de clases UML", "41"),
    ("3.5. Diseño de la base de datos (Esquema Multitenant y Tablas Locales)", "44"),
    ("3.6. Diseño de interfaces de usuario", "48"),
    ("CAPÍTULO IV. DESARROLLO E IMPLEMENTACIÓN", "50"),
    ("4.1. Herramientas y tecnologías utilizadas", "50"),
    ("4.2. Diseño de la arquitectura del sistema", "52"),
    ("4.3. Implementación de la base de datos", "54"),
    ("4.4. Desarrollo de los módulos del sistema", "56"),
    ("4.5. Integración de componentes", "59"),
    ("CAPÍTULO V. PRUEBAS Y RESULTADOS", "62"),
    ("5.1. Plan de pruebas", "62"),
    ("5.2. Pruebas funcionales", "63"),
    ("5.3. Pruebas de integración", "64"),
    ("5.4. Corrección de errores", "65"),
    ("5.5. Resultados de las pruebas", "66"),
    ("5.6. Casos de prueba", "67"),
    ("CAPÍTULO VI. CONCLUSIONES Y RECOMENDACIONES", "69"),
    ("6.1. Conclusiones", "69"),
    ("6.2. Recomendaciones", "70"),
    ("7. BIBLIOGRAFÍA", "71"),
    ("8. ANEXOS", "72")
]

for item, page in indice_items:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.05
    r_item = p.add_run(item)
    if "CAPÍTULO" in item:
        r_item.bold = True
        r_item.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)
    dots = " ." * int((72 - len(item)) / 2)
    p.add_run(dots)
    r_pg = p.add_run(f"  {page}")
    r_pg.bold = True

doc.add_page_break()

# ==============================================================================
# CAPÍTULO I. ASPECTOS GENERALES
# ==============================================================================
add_header("CAPÍTULO I. ASPECTOS GENERALES", level=1)

add_header("1.1. Introducción", level=2)
add_p("A nivel mundial, la comercialización minorista de indumentaria ha experimentado una evolución acelerada impulsada por la adopción de tecnologías digitales omnicanal y arquitecturas de software basadas en la nube. Las grandes empresas del sector retail de moda han dejado de operar mediante sistemas monolíticos aislados en cada sucursal para adoptar plataformas centralizadas bajo el modelo de Software como Servicio (SaaS), permitiendo una coordinación integral entre múltiples tiendas físicas, plataformas web y aplicaciones móviles. Paralelamente, la proliferación de Progressive Web Apps (PWA) y bases de datos locales embebidas ha permitido que el sector comercial mantenga su operatividad transaccional incluso en escenarios con interrupciones temporales de conectividad a la red.")

add_p("En el contexto de Bolivia, el comercio de prendas de vestir representa uno de los sectores más representativos de la actividad económica en las principales ciudades del eje troncal (Santa Cruz de la Sierra, La Paz y Cochabamba). En el país conviven diversas empresas comerciales, desde cadenas consolidadas hasta medianas boutiques de moda, que gestionan inventarios organizados por categorías, temporadas y colecciones. No obstante, las empresas del medio local enfrentan dificultades comunes asociadas a la inestabilidad de la conectividad a Internet en puntos de venta físicos, la dispersión geográfica de sus sucursales y la falta de acceso a plataformas modernas que les permitan competir en canales digitales sin incurrir en elevados costos de desarrollo de software a medida.")

add_p("En este escenario se sitúa la plataforma de comercio electrónico FashionStore, originalmente concebida para la gestión integral de tiendas de moda y que, en el marco del presente proyecto, evoluciona hacia una solución tecnológica SaaS multitenant. Mediante esta transformación, FashionStore deja de ser un sistema de uso exclusivo para una sola cadena y se convierte en una plataforma de servicios en la nube comercializable a múltiples empresas independientes del rubro textil. Cada empresa suscriptora dispone de su propio entorno lógico de trabajo con aislamiento garantizado de sus datos comerciales, sucursales, inventarios y ventas, complementado con capacidades de operación offline en clientes web y móviles, sincronización bidireccional y analítica avanzada con inteligencia artificial.")

add_header("1.2. Planteamiento del problema", level=2)
add_p("Al operar en el entorno comercial real del retail textil en Bolivia y analizar el funcionamiento diario de múltiples empresas dedicadas a la venta de prendas de vestir, se identifican las siguientes situaciones críticas:")

add_bullet("Cuando se producen cortes del servicio de Internet o fluctuaciones en la red local de una sucursal comercial, los terminales de caja y atención al cliente quedan completamente imposibilitados de registrar ventas de contado, consultar existencias locales de prendas o verificar precios. Esto provoca la suspensión temporal de las ventas presenciales, largas filas de espera de clientes en tienda y la pérdida directa de ventas en momentos de alta afluencia comercial.", bold_prefix="1. Paralización operativa por interrupción de conectividad: ")

add_bullet("Las empresas comerciales independientes que operan en el mercado local deben adquirir o desarrollar sistemas informáticos de forma individual y aislada. Esto ocasiona altos costos de infraestructura tecnológica, duplicidad de esfuerzos de mantenimiento y barreras económicas insalvables para medianas empresas que desean gestionar catálogos modernos, carritos de compras y reservas digitales bajo estándares seguros.", bold_prefix="2. Dificultad de adopción tecnológica y altos costos de software independiente: ")

add_bullet("Al intentar registrar transacciones de venta o reservas de productos en terminales que han operado de manera desconectada, surgen discrepancias severas entre el inventario físico disponible en la sucursal y el inventario registrado en la base de datos central al restablecerse la conexión. La falta de mecanismos automáticos de resolución de conflictos genera inconsistencias contables y compromisos de stock duplicados que perjudican la credibilidad del negocio frente al cliente.", bold_prefix="3. Inconsistencias de inventario por sincronización no controlada de operaciones offline: ")

add_bullet("La administración central de cada empresa comercial carece de herramientas automatizadas y ágiles para consultar el desempeño comercial consolidado entre sus distintas sucursales. La obtención de reportes de rotación de prendas, volúmenes de venta por categoría o alertas de quiebre de stock requiere procesos manuales de extracción de datos que toman horas o días, impidiendo tomar decisiones oportunas de reabastecimiento o liquidación comercial.", bold_prefix="4. Lentitud y rigidez en la generación de información estratégica y toma de decisiones: ")

add_header("1.3. Objetivos del proyecto", level=2)

add_header("1.3.1. Objetivo general", level=3)
add_p("Evolucionar la plataforma FashionStore hacia una plataforma funcional de comercio electrónico SaaS multitenant, incorporando planes de suscripción, aplicaciones web progresivas (PWA), operación offline en web y móvil, sincronización de datos con detección de conflictos y reportes generativos mediante inteligencia artificial y aprendizaje automático, aplicando la metodología ICONIX y garantizando la coherencia entre los modelos UML 2.5+ y la implementación del software.")

add_header("1.3.2. Objetivos específicos", level=3)
add_bullet("Aplicar la metodología ICONIX para estructurar el análisis y diseño del sistema mediante casos de uso, diagramas de robustez (análisis Boundary-Control-Entity) y diagramas de secuencia trazables hacia la implementación.")
add_bullet("Transformar la arquitectura de base de datos y servicios backend en un esquema SaaS multitenant con aislamiento lógico estricto por empresa (tenant), impidiendo accesos cruzados entre empresas independientes.")
add_bullet("Implementar un módulo de gestión de planes de suscripción (Básico y Profesional) que regule dinámicamente los límites de sucursales activas y el acceso a módulos avanzados como reportes de inteligencia artificial.")
add_bullet("Evolucionar la aplicación web construida en Angular hacia una Progressive Web App (PWA) con Service Workers, Web App Manifest y persistencia local en IndexedDB para la consulta de catálogo y registro de ventas/reservas sin conexión a Internet.")
add_bullet("Incorporar persistencia local con SQLite en la aplicación móvil desarrollada con Flutter y Dart, permitiendo almacenar el catálogo local y capturar operaciones comerciales offline.")
add_bullet("Diseñar e implementar un motor de sincronización de operaciones comerciales offline con asignación de identificadores universales únicos (UUID) e idempotencia transaccional en el servidor central.")
add_bullet("Desarrollar un mecanismo de detección y resolución administrativa de conflictos de inventario surgidos por ventas offline concurrentes sobre las mismas referencias de prendas.")
add_bullet("Incorporar un módulo de reportes generativos con inteligencia artificial capaz de recibir solicitudes en lenguaje natural escrito o por voz, validando parámetros seguros y construyendo reportes tabulares y gráficos dinámicos exportables a Excel y PDF.")
add_bullet("Desarrollar un módulo de analítica inteligente mediante Machine Learning que contemple generación de datos sintéticos, entrenamiento de modelos supervisados (predicción de demanda) y no supervisados (segmentación y patrones), visualizados en un dashboard analítico.")
add_bullet("Implementar pruebas funcionales, de integración y verificación de reglas críticas de negocio (aislamiento de datos, idempotencia de sync y consistencia de inventario) para asegurar la calidad del software.")

add_header("1.4. Justificación", level=2)
add_p("Justificación Técnica: ", bold_prefix="a. ")
add_p("El proyecto integra tecnologías de vanguardia en desarrollo web y móvil: FastAPI ofrece alto rendimiento asíncrono y tipado estricto en Python; Angular proporciona una arquitectura robusta basada en componentes reactivos y Service Workers para capacidades PWA; Flutter asegura un único código base multiplataforma de alto rendimiento con persistencia relacional en SQLite; y PostgreSQL garantiza integridad referencial, transaccionalidad ACID y soporte avanzado para consultas multitenant. La adopción de la metodología ICONIX aporta un puente ágil y directo entre los requisitos y el código, eliminando la sobrecarga documental y enfocándose en la robustez y consistencia arquitectónica.")

add_p("Justificación Económica y Operativa: ", bold_prefix="b. ")
add_p("Bajo el modelo SaaS, las empresas contratantes reducen sus costos de inversión inicial en servidores, licencias y desarrollo a medida, accediendo a una plataforma moderna mediante suscripciones predecibles. Operativamente, la capacidad de continuar facturando al contado y reservando prendas en modo offline garantiza que las tiendas no pierdan ingresos ante caídas de telecomunicaciones, salvaguardando la continuidad del negocio.")

add_p("Justificación Social y Comercial: ", bold_prefix="c. ")
add_p("Se democratiza el acceso a tecnología de inteligencia artificial y analítica avanzada para empresas textiles nacionales que tradicionalmente no cuentan con equipos internos de ciencia de datos, permitiéndoles competir en condiciones modernas de mercado y optimizar la experiencia de compra de sus consumidores.")

add_header("1.5. Alcance y limitaciones", level=2)
add_p("Alcance del Sistema:", bold_prefix="a. ")
add_bullet("Módulo de Administración SaaS: Registro de empresas contratantes (tenants), asignación de administradores, gestión de planes (Básico y Profesional) y verificación de límites de sucursales en backend.")
add_bullet("Módulo de Aislamiento de Datos: Filtrado estricto en todas las capas del backend mediante tenant_id inyectado en tokens JWT firmados.")
add_bullet("Módulo PWA Web: Instalabilidad en navegadores modernos, caché de recursos, almacenamiento local de catálogo en IndexedDB, registro offline de ventas de contado y reservas, y panel de sincronización con estados.")
add_bullet("Módulo Móvil Flutter Offline: Base de datos local SQLite con tablas de variantes, sucursales y operaciones pendientes; sincronización bidireccional al recuperar conexión.")
add_bullet("Módulo de Sincronización e Idempotencia: Endpoint de sync en FastAPI con control de duplicidad por UUID y trazabilidad de estados (REGISTRADA_LOCAL, ENVIADA, CONFIRMADA, EN_CONFLICTO).")
add_bullet("Módulo de Cambios de Prendas: Registro de cambios de ropa de acuerdo con políticas de devolución en sucursal con actualización de stock.")
add_bullet("Módulo de Reportes Generativos con IA: Procesamiento de consultas en lenguaje natural (texto y voz con Web Speech API), ejecución de consultas SQL restringidas y exportación a Excel y PDF.")
add_bullet("Módulo de Machine Learning: Pipeline completo con generación de datos sintéticos, preprocesamiento, modelo supervisado (predicción de demanda) y modelo no supervisado (clustering K-Means), integrados en dashboard interactivo.")

add_p("Limitaciones del Sistema:", bold_prefix="b. ")
add_bullet("Las ventas en modo offline se restringen obligatoriamente a la modalidad de pago al contado (efectivo), ya que las pasarelas de pago electrónico requieren validación en línea de entidades bancarias.")
add_bullet("Para el prototipo del segundo parcial, la contratación y renovación de planes de suscripción se gestiona administrativamente mediante simulación en backend y panel de control, sin integración obligatoria con pasarelas de cobro recurrente SaaS externas.")
add_bullet("El probador virtual por Realidad Aumentada desarrollado en el primer parcial se preserva como módulo integrado, no exigiéndose la construcción de un nuevo vestidor virtual en este parcial.")

add_header("1.6. Metodología de desarrollo ICONIX", level=2)
add_p("Para el desarrollo y documentación del segundo examen parcial se adopta formalmente la metodología ICONIX, un proceso de desarrollo de software ágil y dirigido por casos de uso que cubre la brecha entre el análisis de requisitos y el diseño detallado de clases e implementación. A diferencia del Proceso Unificado de Desarrollo de Software (PUDS) utilizado en el primer parcial, ICONIX es un enfoque simplificado ('just enough design') compuesto por cuatro fases iterativas interconectadas:")

add_bullet("Definición del modelo de dominio inicial con las entidades del negocio (Tenant, Branch, Product, Sale, SyncOperation) y captura de los casos de uso descritos en texto conciso.", bold_prefix="1. Requisitos: ")
add_bullet("Uso del Análisis de Robustez inventado por Ivar Jacobson. Se traduce cada especificación de caso de uso a objetos Frontera (Boundary / Interfaz), Controladores (Control / Lógica de aplicación) y Entidades (Entity / Datos de dominio). Permite identificar objetos y métodos faltantes antes de codificar.", bold_prefix="2. Análisis preliminar (Robustez): ")
add_bullet("Construcción de diagramas de secuencia a partir de los diagramas de robustez, asignando responsabilidades formales a las clases de diseño y refinando el diagrama de clases estático.", bold_prefix="3. Diseño: ")
add_bullet("Escritura de código en FastAPI, Angular y Flutter directamente mapeado a las clases y controladores identificados en los pasos anteriores, validado mediante pruebas unitarias y de integración.", bold_prefix="4. Implementación y Pruebas: ")

doc.add_page_break()

# ==============================================================================
# CAPÍTULO II. ANÁLISIS DE REQUISITOS
# ==============================================================================
add_header("CAPÍTULO II. ANÁLISIS DE REQUISITOS", level=1)

add_header("2.1. Descripción del sistema propuesto", level=2)
add_p("El sistema propuesto es una plataforma e-commerce moderna bajo modelo SaaS multitenant, diseñada para que múltiples empresas del rubro textil y confección operen de manera independiente compartiendo una infraestructura centralizada en la nube. La solución garantiza un aislamiento lógico absoluto de datos por empresa, ofrece funcionamiento continuo en puntos de venta físicos mediante tecnologías PWA e IndexedDB en web y SQLite en dispositivos móviles, e integra herramientas de inteligencia artificial para la generación de reportes estratégicos y modelado predictivo.")

add_header("2.2. Identificación de actores", level=2)
add_p("Siguiendo el modelado ICONIX, se identifican actores humanos y actores del sistema estructurados en dos niveles organizacionales:")

actores_data = [
    ("Superadmin Plataforma", "Humano (Nivel SaaS)", "Administrador general de la plataforma SaaS. Registra empresas contratantes (tenants), configura planes comerciales (Básico vs Profesional), supervisa límites de recursos y evalúa la analítica global del sistema."),
    ("Administrador Tenant", "Humano (Nivel Empresa)", "Responsable general de la empresa cliente. Administra sus sucursales (respetando el límite del plan), empleados, catálogo de productos, promociones, entrena y evalúa modelos de analítica inteligente (Machine Learning), solicita reportes generativos por texto/voz y audita el estado de sincronización de sus sucursales."),
    ("Encargado de Sucursal", "Humano (Nivel Empresa)", "Responsable operativo de una tienda física. Administra reservas de prendas, resuelve administrativamente conflictos de inventario derivados de ventas offline, autoriza cambios y devoluciones de prendas, y supervisa existencias locales."),
    ("Cajero / Vendedor", "Humano (Nivel Empresa)", "Operador del punto de venta físico (POS). Consulta disponibilidad local, registra ventas de contado en modo offline, encola operaciones, dispara la sincronización al recuperar conexión, y tramita cambios físicos y devoluciones de prendas con comprobante."),
    ("Cliente", "Humano (Nivel Empresa)", "Consumidor final. Consulta catálogo y existencias locales de prendas incluso sin conexión, realiza reservas de prendas para probador/tienda y solicita devoluciones o cambios de prendas adquiridas dentro del plazo comercial establecido.")
]
add_styled_table(["Actor", "Tipo", "Responsabilidad Principal"], actores_data, [Inches(1.8), Inches(1.5), Inches(3.2)])

add_header("2.3. Requisitos funcionales y no funcionales", level=2)

add_header("2.3.1. Requisitos Funcionales (RF)", level=3)
rf_data = [
    ("RF01", "Gestión de Empresas (Tenants)", "El sistema debe permitir registrar, editar y activar empresas contratantes con aislamiento lógico completo de su información comercial."),
    ("RF02", "Gestión de Planes de Suscripción", "El sistema debe administrar planes (Básico y Profesional) configurando límites de sucursales (hasta 2 o 10) y acceso a IA."),
    ("RF03", "Autenticación Multitenant con JWT", "El sistema debe validar credenciales y emitir tokens JWT con claims de tenant_id, rol y branch_id para control de acceso."),
    ("RF04", "Control de Límites de Sucursales", "El sistema debe impedir en el backend la creación o activación de sucursales que excedan el límite contratado en el plan."),
    ("RF05", "Catálogo Multitenant Aislado", "El sistema debe gestionar categorías, productos y variantes (SKU, talla, color, precio) vinculados estrictamente al tenant activo."),
    ("RF06", "Caché de Catálogo Offline (PWA/IndexedDB)", "La aplicación web PWA debe descargar y almacenar el catálogo y existencias locales conocidas en IndexedDB."),
    ("RF07", "Persistencia Móvil Offline (SQLite)", "La aplicación móvil Flutter debe almacenar en SQLite local el catálogo y variantes necesarias para consulta offline."),
    ("RF08", "Ventas de Contado Offline", "El sistema debe permitir a cajeros registrar ventas de prendas en efectivo sin conexión, asignando UUID y estado local."),
    ("RF09", "Reservas de Prendas Offline", "El sistema debe permitir crear reservas de prendas con tiempo límite de vigencia de forma local mientras no haya internet."),
    ("RF10", "Bandeja de Operaciones Pendientes", "El sistema debe listar en clientes web y móvil las ventas y reservas encoladas con sus estados de sincronización."),
    ("RF11", "Sincronización Bidireccional de Operaciones", "El sistema debe transmitir operaciones encoladas al reconectar a internet mediante Service Worker o botón manual."),
    ("RF12", "Idempotencia Transaccional en Servidor", "El backend debe procesar operaciones por UUID; peticiones repetidas no deben duplicar ventas ni rebajar inventario adicional."),
    ("RF13", "Detección y Gestión de Conflictos", "El backend debe marcar operaciones en conflicto ante falta de stock real y permitir resolución administrativa en sucursal."),
    ("RF14", "Gestión de Cambios de Prendas", "El sistema debe permitir registrar cambios de prendas dentro de un periodo válido, actualizando los inventarios locales y centrales."),
    ("RF15", "Reportes Generativos en Lenguaje Natural", "El sistema debe interpretar consultas de usuarios autorizados mediante texto o comandos de voz para generar reportes dinámicos."),
    ("RF16", "Exportación de Reportes a PDF y Excel", "El sistema debe permitir exportar reportes generados dinámicamente en formatos convencionales PDF y hojas de cálculo Excel."),
    ("RF17", "Pipeline de Machine Learning (Supervisado y No Supervisado)", "El sistema debe entrenar modelos de ML con datos sintéticos para predicción de demanda de ventas y clustering de clientes."),
    ("RF18", "Dashboard Analítico Ejecutivo", "El sistema debe presentar un panel visual interactivo con KPIs de ventas, evaluación de modelos ML y comparativas.")
]
add_styled_table(["Código", "Nombre", "Descripción Funcional"], rf_data, [Inches(1.0), Inches(2.2), Inches(3.3)])

add_header("2.3.2. Requisitos No Funcionales (RNF)", level=3)
rnf_data = [
    ("RNF01", "Seguridad y Autorización", "Mecanismos de autenticación y autorización mediante tokens JWT firmados criptográficamente para proteger recursos y operaciones."),
    ("RNF02", "Aislamiento de Datos Multitenant", "Ninguna operación en el sistema debe permitir acceder, modificar o filtrar datos de otro tenant sin autorización."),
    ("RNF03", "Persistencia Offline Duradera", "Las operaciones registradas sin conexión deben conservarse intactas tras el cierre o reinicio del navegador o aplicación."),
    ("RNF04", "Integridad Transaccional ACID", "Las ventas confirmadas y sus movimientos de inventario deben ejecutarse atómicamente garantizando consistencia."),
    ("RNF05", "Idempotencia de Sincronización", "El reenvío repetido de una operación previamente confirmada no debe generar registros duplicados ni descuadres de inventario."),
    ("RNF06", "Recuperación ante Fallos", "Las operaciones pendientes deben conservarse en la base de datos local ante errores de comunicación o respuestas fallidas del servidor."),
    ("RNF07", "Mantenibilidad Arquitectónica", "El código debe organizarse separando claramente capas de presentación, lógica de aplicación, persistencia y sincronización."),
    ("RNF08", "Compatibilidad Multiplataforma", "La PWA debe operar en navegadores modernos compatibles con Service Workers e IndexedDB; la app Flutter en Android e iOS."),
    ("RNF09", "Rendimiento y Optimización", "Las consultas de catálogo y reportes generativos deben emplear índices y vistas optimizadas evitando sobrecarga en base de datos."),
    ("RNF10", "Observabilidad y Trazabilidad", "Los procesos de sincronización deben registrar bitácoras detalladas con timestamps y códigos de error para diagnóstico sin exponer datos sensibles."),
    ("RNF11", "Calidad y Cobertura de Pruebas", "Se deben implementar pruebas automatizadas unitarias y de integración que verifiquen las reglas críticas de negocio."),
    ("RNF12", "Coherencia Documental ICONIX", "Los modelos UML deben reflejar fielmente la arquitectura, clases y flujos implementados en el software real.")
]
add_styled_table(["Código", "Criterio", "Especificación Técnica"], rnf_data, [Inches(1.0), Inches(2.0), Inches(3.5)])

add_header("2.4. Reglas de negocio", level=2)
add_bullet("Una sucursal no es un tenant; cada tenant puede poseer múltiples sucursales físicas distribuidas en distintas ciudades.", bold_prefix="RN-01 (Jerarquía Multitenant): ")
add_bullet("El plan Básico permite hasta 2 sucursales activas y reportes convencionales. El plan Profesional permite hasta 10 sucursales y habilita reportes generativos con IA. El backend rechaza la activación de sucursales adicionales al cupo.", bold_prefix="RN-02 (Límites de Suscripción): ")
add_bullet("Las ventas efectuadas en modo offline se restringen a pagos al contado en efectivo. No se admiten pagos con tarjeta o billeteras virtuales sin conexión activa a la pasarela.", bold_prefix="RN-03 (Ventas Offline): ")
add_bullet("Toda operación offline debe generarse con un UUID versión 4 en el cliente. El backend debe registrar la clave de idempotencia; reintentos con el mismo UUID retornan éxito sin duplicar registros.", bold_prefix="RN-04 (Idempotencia y Unicidad): ")
add_bullet("Si una venta offline se sincroniza cuando el stock central ya fue consumido por otra transacción, la venta se marca con estado 'EN_CONFLICTO' y se alerta al Encargado de Sucursal para resolución administrativa.", bold_prefix="RN-05 (Tratamiento de Conflictos): ")
add_bullet("El cliente puede solicitar el cambio de una prenda dentro de un plazo máximo de 7 días calendario posteriores a la compra, presentando el comprobante y manteniendo la prenda en estado intacto.", bold_prefix="RN-06 (Política de Cambios): ")
add_bullet("El motor de IA solo puede ejecutar consultas de tipo lectura (SELECT) parametrizadas. El backend valida e inyecta obligatoriamente el filtro 'WHERE tenant_id = :current_tenant' en toda consulta generada.", bold_prefix="RN-07 (Seguridad de Reportes IA): ")

add_header("2.5. Diagrama UML de casos de uso", level=2)
add_p("A continuación se presenta la tabla resumen y la posterior especificación exhaustiva de los 22 Casos de Uso del sistema organizados en los 3 Ciclos de desarrollo conforme a la metodología ICONIX:")

add_header("2.6. Especificación de casos de uso (Ciclos #1, #2 y #3)", level=2)

add_p("A. CICLO #1: NÚCLEO SAAS MULTITENANT Y PERSISTENCIA OFFLINE", bold_prefix="")

# CU01
add_cu_ficha(
    "CU01", "Gestionar Empresas (Tenants) y Administradores",
    "Permitir al Superadmin de la plataforma registrar, activar, editar o suspender empresas contratantes (tenants), asignando a cada una su identificador único de aislamiento y su cuenta de usuario administrador principal.",
    "El Superadmin accede al panel global SaaS, ingresa los datos de la nueva empresa contratante (razón social, NIT, correo corporativo) y selecciona el plan inicial. El sistema valida la información, crea el registro del tenant con su UUID propio, genera la cuenta del Administrador Tenant inicial y emite las credenciales de acceso.",
    "Superadmin Plataforma.", "Superadmin Plataforma.",
    "El Superadmin debe contar con una sesión activa en la plataforma con el rol SUPERADMIN.",
    "1. El Superadmin accede al módulo 'Empresas Contratantes'.\n"
    "2. El sistema muestra la lista de empresas registradas y la opción 'Nueva Empresa'.\n"
    "3. El Superadmin presiona 'Nueva Empresa' y completa los campos fiscales y comerciales.\n"
    "4. El sistema valida la unicidad del NIT y del correo del administrador.\n"
    "5. El sistema genera el tenant_id (UUIDv4) y crea la entidad Tenant en la base de datos central.\n"
    "6. El sistema crea la cuenta de usuario Administrador vinculada estrictamente al nuevo tenant_id con rol ADMIN_TENANT.\n"
    "7. El sistema confirma la creación exitosa y habilita el entorno de la empresa.",
    "La empresa contratante queda registrada en la plataforma con entorno lógico independiente. El Administrador Tenant queda habilitado para iniciar sesión y configurar sus sucursales y catálogo.",
    "- NIT o razón social duplicada: El sistema muestra mensaje de error y solicita rectificar.\n"
    "- Correo corporativo ya registrado: El sistema notifica que ya existe una cuenta con ese correo.\n"
    "- Error de persistencia: El sistema aborta la transacción y muestra notificación de error."
)

# CU02
add_cu_ficha(
    "CU02", "Gestionar Planes de Suscripción y Límites",
    "Permitir al Superadmin configurar los planes de suscripción (Básico y Profesional) y al Administrador Tenant consultar el estado, vigencia y solicitar cambio de plan de su empresa.",
    "El Superadmin define los términos y capacidades técnicas de cada plan: cupo máximo de sucursales activas (2 en Básico, 10 en Profesional) y habilitación de módulos de IA. El Administrador Tenant puede visualizar su consumo de recursos y solicitar la ampliación de su suscripción.",
    "Superadmin Plataforma, Administrador Tenant.", "Superadmin o Administrador Tenant.",
    "El usuario debe estar autenticado con rol SUPERADMIN o ADMIN_TENANT.",
    "1. El usuario accede a la sección 'Planes y Suscripción'.\n"
    "2. El sistema consulta la suscripción activa asociada al tenant del usuario.\n"
    "3. El sistema muestra el plan actual, fecha de inicio, fecha de corte, número de sucursales activas en uso vs. límite permitido, y estado de activación del módulo IA.\n"
    "4. Si el Administrador solicita cambio de plan a Profesional, el sistema simula administrativamente la aprobación y actualiza la entidad Subscription.\n"
    "5. El sistema habilita de inmediato el nuevo cupo de hasta 10 sucursales y el acceso al generador de reportes con IA.",
    "El estado de suscripción de la empresa queda actualizado y los límites son recalculados para las validaciones en backend.",
    "- Plan vencido: El sistema suspende temporalmente las operaciones de modificación hasta su regularización administrativa."
)

# CU03
add_cu_ficha(
    "CU03", "Autenticar Usuario en Contexto Multitenant",
    "Permitir la autenticación segura de cualquier tipo de usuario en el sistema, generando un token JWT firmado criptográficamente que contiene el tenant_id, rol y branch_id asignado.",
    "El usuario ingresa su correo y contraseña en la web PWA o móvil. El backend valida las credenciales y el estado activo tanto de la empresa como del usuario. Si es válido, emite un token JWT que inyecta obligatoriamente el claim tenant_id, garantizando que cada petición subsiguiente sea interceptada y filtrada.",
    "Todos los usuarios (Superadmin, Admin Tenant, Encargado, Cajero, Cliente).", "Cualquier usuario.",
    "El usuario y la empresa contratante deben encontrarse registrados y en estado activo.",
    "1. El usuario accede a la pantalla de inicio de sesión.\n"
    "2. El usuario introduce correo electrónico y contraseña.\n"
    "3. La aplicación envía la petición POST /api/auth/login al backend.\n"
    "4. El backend localiza al usuario y verifica el hash de la contraseña mediante bcrypt.\n"
    "5. El backend verifica que el tenant asociado esté activo y con suscripción vigente.\n"
    "6. El backend genera el token de acceso JWT codificando {user_id, email, role, tenant_id, branch_id}.\n"
    "7. El cliente almacena el token en almacenamiento seguro y redirige al panel según su rol.",
    "El usuario dispone de una sesión autenticada. Cada endpoint de la API recibe el JWT y restringe los accesos al tenant_id inyectado.",
    "- Credenciales inválidas: Mensaje de 'Correo o contraseña incorrectos'.\n"
    "- Tenant suspendido o inactivo: Mensaje 'Su empresa tiene el acceso suspendido. Contacte a soporte'.\n"
    "- Usuario inactivo: Mensaje 'Cuenta deshabilitada'."
)

# CU04
add_cu_ficha(
    "CU04", "Gestionar Sucursales bajo Reglas de Suscripción",
    "Permitir al Administrador Tenant dar de alta, editar y gestionar las sucursales físicas de su empresa, verificando en backend que no se exceda el cupo máximo contratado en su suscripción.",
    "El Administrador Tenant gestiona las tiendas físicas donde opera su cadena. Al intentar registrar o activar una nueva sucursal, el backend consulta cuántas sucursales activas posee actualmente el tenant; si se alcanzó el límite del plan (ej. 2 en Básico), la creación es bloqueada con un error explicativo.",
    "Administrador Tenant.", "Administrador Tenant.",
    "Usuario con rol ADMIN_TENANT autenticado.",
    "1. El Administrador accede al submódulo 'Sucursales'.\n"
    "2. El sistema muestra la lista de sucursales con su estado, ciudad y dirección.\n"
    "3. El Administrador presiona 'Registrar Sucursal' e ingresa nombre, ciudad, dirección y teléfono.\n"
    "4. El backend ejecuta la regla RN-02: cuenta las sucursales activas del tenant.\n"
    "5. Si el conteo es menor al límite del plan (max_branches), guarda la nueva Branch vinculada al tenant_id.\n"
    "6. El sistema confirma el registro y actualiza la lista visual.",
    "La nueva sucursal queda registrada y disponible para asociarle empleados e inventario.",
    "- Cupo de sucursales alcanzado: El sistema bloquea el guardado retornando HTTP 403 con mensaje: 'Límite de sucursales alcanzado para su plan actual. Actualice a Profesional para habilitar hasta 10 sucursales'."
)

# CU05
add_cu_ficha(
    "CU05", "Gestionar Catálogo de Productos Aislado por Tenant",
    "Permitir al Administrador Tenant registrar y modificar prendas de vestir, categorías, colecciones y variantes de producto (SKU, talla, color, precio) pertenecientes únicamente a su empresa.",
    "El Administrador Tenant administra las prendas de su catálogo. Cada prenda creada se etiqueta internamente con el tenant_id. Las consultas y búsquedas se aíslan a nivel de base de datos impidiendo que usuarios de otras empresas visualicen o editen productos ajenos.",
    "Administrador Tenant.", "Administrador Tenant.",
    "Usuario con rol ADMIN_TENANT autenticado.",
    "1. El Administrador accede al módulo 'Catálogo de Prendas'.\n"
    "2. El sistema lista únicamente los productos pertenecientes a su tenant_id.\n"
    "3. El Administrador selecciona 'Crear Prenda' y define nombre, descripción, categoría y temporada.\n"
    "4. El Administrador añade variantes especificando SKU, talla, color y precio de venta unitario.\n"
    "5. El sistema valida unicidad de SKU dentro del tenant y persiste el producto y sus variantes.\n"
    "6. El producto queda publicado y disponible en el catálogo de la empresa.",
    "Las prendas y variantes quedan persistidas y vinculadas exclusivamente a la empresa activa.",
    "- SKU duplicado dentro de la empresa: El sistema notifica la colisión y solicita un nuevo SKU.\n"
    "- Datos obligatorios incompletos: Solicita completar talla, color o precio."
)

# CU06
add_cu_ficha(
    "CU06", "Descargar y Almacenar Catálogo en Caché Local (IndexedDB / SQLite)",
    "Permitir que las aplicaciones cliente (PWA en web y Flutter en móvil) descarguen y guarden una copia local del catálogo de productos y existencias conocidas de la sucursal para posibilitar la consulta offline.",
    "Al iniciar sesión o mediante sincronización manual, el cliente descarga un subconjunto optimizado del catálogo del tenant y las existencias de la sucursal asignada. Estos datos se almacenan en IndexedDB (Web) y SQLite (Móvil) para que la aplicación funcione aún sin internet.",
    "Cajero / Vendedor, Cliente.", "Cliente o Cajero / Vendedor.",
    "El dispositivo debe contar con conexión inicial a internet para la descarga del catálogo.",
    "1. El usuario accede a la aplicación con conectividad.\n"
    "2. La aplicación solicita al backend el catálogo completo y la disponibilidad de la sucursal activa.\n"
    "3. El backend retorna el listado de productos, variantes, precios y existencias.\n"
    "4. En la PWA, el servicio de datos persiste los registros en el almacén de objetos de IndexedDB.\n"
    "5. En Flutter, el repositorio SQLite realiza un lote de inserción/actualización en la base de datos local.\n"
    "6. La aplicación notifica: 'Catálogo descargado localmente. Listo para operar sin conexión'.",
    "Los datos del catálogo quedan guardados persistentemente en el dispositivo cliente.",
    "- Almacenamiento local lleno: Notifica al usuario liberar espacio en memoria del navegador/dispositivo."
)

# CU07
add_cu_ficha(
    "CU07", "Consultar Catálogo y Disponibilidad Local en Modo Offline",
    "Permitir al usuario buscar, filtrar y consultar información de prendas, precios y existencias locales conocidas cuando no se dispone de conexión a Internet.",
    "Cuando el dispositivo pierde conectividad a internet, la aplicación detecta el estado offline y conmuta sus consultas hacia la base de datos local (IndexedDB o SQLite). La interfaz muestra un indicador visual informando que los datos corresponden a la última sincronización conocida.",
    "Cajero / Vendedor, Cliente.", "Cajero / Vendedor o Cliente.",
    "El catálogo debe haber sido descargado previamente en almacenamiento local (CU06).",
    "1. El usuario navega en el catálogo de prendas o busca por texto o categoría.\n"
    "2. La aplicación detecta que navigator.onLine es falso o la API no responde.\n"
    "3. La aplicación activa la consulta contra el almacén local (IndexedDB o SQLite).\n"
    "4. El sistema presenta la lista de prendas, variantes, tallas, colores y existencias locales.\n"
    "5. La interfaz muestra de forma visible la advertencia: 'Modo Offline: Disponibilidad basada en la última sincronización local'.",
    "El usuario visualiza la información requerida sin interrupción a pesar de la desconexión de red.",
    "- Catálogo local vacío: Muestra mensaje 'No se dispone de productos guardados localmente. Conéctese a internet para descargar el catálogo'."
)

# CICLO #2
add_p("B. CICLO #2: OPERACIONES COMERCIALES OFFLINE Y MOTOR DE SINCRONIZACIÓN", bold_prefix="")

# CU08
add_cu_ficha(
    "CU08", "Registrar Venta de Contado Offline",
    "Permitir al cajero registrar una venta presencial de prendas cobrada en efectivo sin necesidad de conexión a Internet, persistiendo la transacción localmente con un identificador único para su sincronización posterior.",
    "Estando sin internet, el cajero agrega prendas al punto de venta (POS) y procesa el cobro al contado. La aplicación genera un UUIDv4 local para la venta, rebaja temporalmente el stock en el inventario local, guarda el ticket en la cola de sincronización con estado PENDIENTE_SYNC y genera un comprobante local de venta.",
    "Cajero / Vendedor.", "Cajero / Vendedor.",
    "La PWA o app móvil debe encontrarse abierta con catálogo local cargado.",
    "1. El cajero selecciona las variantes de prendas solicitadas por el cliente.\n"
    "2. El sistema calcula el total de la compra.\n"
    "3. El cajero selecciona la forma de pago: 'Efectivo / Contado'.\n"
    "4. El cajero confirma la venta.\n"
    "5. La aplicación genera un UUIDv4 único como sync_uuid.\n"
    "6. La aplicación guarda la venta y sus detalles en IndexedDB / SQLite con estado 'PENDIENTE_SYNC'.\n"
    "7. La aplicación descuenta preventivamente las existencias locales de las variantes vendidas.\n"
    "8. La aplicación emite el comprobante de venta local indicando 'Operación offline registrada'.",
    "La venta queda asegurada en el almacenamiento local del dispositivo, lista para sincronizarse al reconectar.",
    "- Existencia local conocida en cero: Muestra advertencia al cajero antes de permitir forzar la venta si físicamente tiene la prenda en mano."
)

# CU09
add_cu_ficha(
    "CU09", "Registrar Reserva de Prendas Offline",
    "Permitir registrar la reserva de una o varias prendas para un cliente desde el punto de atención o cliente sin internet, asignándole un identificador único y tiempo límite de validez.",
    "El usuario aparta prendas para prueba en sucursal. En ausencia de internet, la reserva se almacena en la base de datos local con fecha, hora, vigencia (ej. 2 horas) y datos del cliente, quedando encolada para su envío al servidor.",
    "Cliente, Encargado de Sucursal.", "Cliente o Encargado.",
    "Catálogo local disponible en la terminal.",
    "1. El usuario selecciona las prendas y tallas que desea reservar.\n"
    "2. El usuario define la sucursal de atención y sus datos de contacto.\n"
    "3. La aplicación genera un UUIDv4 para la reserva y calcula la hora límite de expiración.\n"
    "4. Se guarda la reserva en la cola local de sincronización con estado 'PENDIENTE_SYNC'.\n"
    "5. Se muestra código de reserva local al cliente.",
    "La reserva queda guardada en el dispositivo para su transmisión al servidor.",
    "- Datos de cliente incompletos: Solicita nombre y teléfono de contacto."
)

# CU10
add_cu_ficha(
    "CU10", "Consultar Registro de Operaciones Locales Pendientes",
    "Permitir al cajero y encargado visualizar la bandeja de todas las ventas y reservas registradas localmente en el dispositivo, conociendo su estado de sincronización actual.",
    "La interfaz del POS dispone de un panel lateral que lista las transacciones almacenadas localmente. Cada operación muestra su UUID, hora de registro, total, tipo de operación y etiqueta de estado: REGISTRADA_LOCAL, ENVIADA, CONFIRMADA o EN_CONFLICTO.",
    "Cajero / Vendedor, Encargado de Sucursal.", "Cajero / Vendedor o Encargado.",
    "La aplicación debe estar ejecutándose en la terminal de trabajo.",
    "1. El usuario accede a la pestaña 'Operaciones Offline'.\n"
    "2. La aplicación lee de IndexedDB / SQLite todos los registros de la tabla sync_queue.\n"
    "3. La interfaz presenta una tabla con: UUID, tipo, fecha/hora, monto y badge de estado coloreado.\n"
    "4. El usuario puede pulsar sobre cualquier operación para revisar el detalle de prendas.",
    "El personal tiene visibilidad transparente de qué operaciones ya impactaron en la central y cuáles continúan pendientes.",
    "- Sin operaciones: Muestra 'No hay operaciones pendientes de sincronización'."
)

# CU11
add_cu_ficha(
    "CU11", "Sincronizar Operaciones Comerciales con el Backend",
    "Transmitir al servidor central las ventas y reservas encoladas localmente en cuanto se detecte la restauración de la conectividad a Internet o cuando el usuario presione el botón de sincronizar.",
    "El Service Worker o la app detecta el evento de reconexión 'online'. Lee las transacciones en estado PENDIENTE_SYNC y las envía en lote al endpoint POST /api/sync/operations del backend. Ante caídas a mitad de transmisión, las operaciones no se eliminan y se reintentan automáticamente (RNF06).",
    "Sistema (Background Sync), Cajero / Vendedor.", "Sistema automatizado o Cajero.",
    "Dispositivo reconectado a internet con transacciones locales pendientes.",
    "1. El sistema detecta el retorno de conexión a internet o el usuario presiona 'Sincronizar Ahora'.\n"
    "2. La aplicación extrae las operaciones de sync_queue con estado 'PENDIENTE_SYNC' y las marca 'ENVIADA'.\n"
    "3. La aplicación envía la petición POST con el lote de transacciones incluyendo su sync_uuid.\n"
    "4. El backend procesa cada elemento del lote y retorna la respuesta individual de cada UUID.\n"
    "5. Para cada operación exitosa, el cliente actualiza el estado local a 'CONFIRMADA'.\n"
    "6. Para operaciones rechazadas por colisión de inventario, se actualiza el estado a 'EN_CONFLICTO'.",
    "Las operaciones quedan actualizadas en la base de datos central y sus estados reflejados en el almacenamiento local.",
    "- Servidor inalcanzable durante el envío: Las operaciones vuelven al estado 'PENDIENTE_SYNC' para el siguiente reintento sin perder ningún dato."
)

# CU12
add_cu_ficha(
    "CU12", "Auditar Historial y Estado de Sincronización",
    "Permitir al Administrador Tenant y Encargado de Sucursal supervisar y auditar el historial de operaciones comerciales recibidas desde las terminales offline, verificando la consistencia transaccional y la ausencia de duplicados.",
    "El Administrador Tenant o el Encargado accede a la vista de auditoría de sincronizaciones. El sistema lista las transacciones recibidas con su UUID, terminal de origen, hora de recepción y estado final confirmado. El usuario puede filtrar operaciones confirmadas o en conflicto para validar que no existan cobros duplicados ni inconsistencias contables.",
    "Administrador Tenant, Encargado de Sucursal.", "Administrador Tenant o Encargado de Sucursal.",
    "Usuario con rol ADMIN_TENANT o ENCARGADO_SUCURSAL autenticado.",
    "1. El usuario accede al módulo 'Auditoría de Sincronización'.\n"
    "2. El sistema consulta la bitácora central de sincronizaciones filtrada por el tenant_id del usuario.\n"
    "3. El sistema muestra la tabla con sync_uuid, terminal de caja, fecha/hora de venta local, fecha/hora de confirmación central, monto y estado.\n"
    "4. El usuario selecciona una transacción para inspeccionar el detalle de prendas y movimientos de stock aplicados.\n"
    "5. El usuario verifica que los reintentos de red no hayan generado registros duplicados (idempotencia confirmada).\n"
    "6. El usuario puede exportar el reporte de auditoría de sincronización.",
    "El usuario obtiene trazabilidad completa sobre el impacto de las ventas offline en la base de datos central.",
    "- Discrepancia detectada: El usuario reporta la transacción para revisión técnica."
)

# CU13
add_cu_ficha(
    "CU13", "Detectar y Gestionar Conflictos de Inventario Offline",
    "Detectar cuando una venta registrada sin internet no puede ser cubierta por el inventario central debido a ventas concurrentes, notificando al Encargado de Sucursal para su resolución administrativa.",
    "Si dos terminales vendieron la misma última unidad de una prenda durante una desconexión, al sincronizarse la segunda venta el backend detecta stock insuficiente. La venta no se borra: se registra con estado EN_CONFLICTO y se genera una alerta operativa en el panel del encargado.",
    "Backend (API Sync & Tx), Encargado de Sucursal.", "Backend e intervención del Encargado.",
    "Venta sincronizada cuyo stock central físico disponible es menor a la cantidad vendida.",
    "1. Al procesar una venta offline, el backend detecta que quantity < sold_quantity en inventory.\n"
    "2. El backend marca la venta con status = 'EN_CONFLICTO' y registra el motivo en sync_audit_logs.\n"
    "3. El backend emite una notificación al Encargado de Sucursal.\n"
    "4. En su panel web, el Encargado revisa la bandeja de conflictos.\n"
    "5. El Encargado selecciona la resolución: 'Solicitar Traspaso Inmediato de otra sucursal' o 'Ajustar Inventario Físico / Nota de Crédito'.\n"
    "6. El sistema aplica la resolución administrativa y normaliza el estado de la venta.",
    "La inconsistencia queda documentada, resuelta y trazable sin pérdida de datos contables.",
    "- Prenda no disponible en ninguna sucursal: Se emite cupón/nota de devolución al cliente."
)

# CU14
add_cu_ficha(
    "CU14", "Gestionar Cambios de Prendas de Vestir",
    "Permitir al cajero registrar el cambio de una prenda adquirida por un cliente por otra talla o color dentro del plazo comercial establecido, actualizando el inventario de la sucursal.",
    "El cliente acude a la sucursal con una prenda dentro de los 7 días de compra. El cajero ingresa el número de comprobante, selecciona la prenda entregada e ingresa la nueva prenda solicitada. El sistema reintegra la prenda entregada al inventario y rebaja la nueva prenda retirada.",
    "Cajero / Vendedor, Encargado de Sucursal, Cliente.", "Cliente (iniciador presencial), Cajero / Vendedor.",
    "Comprobante de venta válido y dentro del plazo de 7 días (RN-06).",
    "1. El cliente presenta el comprobante de venta y la prenda a cambiar en buen estado.\n"
    "2. El cajero accede a 'Gestión de Cambios' e introduce el código del comprobante.\n"
    "3. El sistema valida la fecha de compra original.\n"
    "4. El cajero selecciona el ítem a cambiar y escanea la nueva variante requerida.\n"
    "5. Si existe diferencia de precio, el sistema liquida el saldo a favor o en contra.\n"
    "6. El sistema reingresa 1 unidad de la prenda original y descuenta 1 unidad de la nueva prenda en el inventario local.\n"
    "7. Se emite comprobante de cambio de mercadería al cliente.",
    "El inventario de la sucursal queda actualizado y el cambio queda registrado formalmente.",
    "- Plazo vencido (> 7 días): Requiere autorización expresa del Encargado de Sucursal.\n"
    "- Prenda requerida sin stock: Se sugiere otra talla, modelo o sucursal cercana."
)

# CU15
add_cu_ficha(
    "CU15", "Gestionar Devoluciones de Prendas y Reembolsos",
    "Permitir al cliente solicitar y al cajero registrar la devolución total de una prenda adquirida por fallas o retracto comercial, reintegrando la prenda al stock y emitiendo la nota de crédito o reembolso.",
    "El cliente acude a la tienda solicitando la devolución de una prenda. El cajero inspecciona el producto y comprueba el ticket de compra. El Encargado de Sucursal autoriza la devolución en el sistema. El cajero confirma la operación, el sistema reincorpora la unidad al inventario físico de la empresa y se emite la nota de crédito o reembolso de efectivo correspondiente.",
    "Cliente, Cajero / Vendedor, Encargado de Sucursal.", "Cliente (solicitante), Cajero / Vendedor.",
    "Comprobante de venta original y prenda sin señales de uso indebido.",
    "1. El cliente solicita la devolución de una prenda presentando el comprobante original.\n"
    "2. El cajero verifica físicamente la prenda e ingresa el comprobante en 'Devoluciones'.\n"
    "3. El sistema comprueba que la compra pertenece al tenant activo y esté dentro del plazo normativo.\n"
    "4. El cajero solicita la autorización al Encargado de Sucursal.\n"
    "5. El Encargado valida la inspección y autoriza la devolución en el sistema con sus credenciales.\n"
    "6. El cajero procesa la devolución seleccionando la modalidad: Efectivo o Nota de Crédito.\n"
    "7. El sistema reingresa la prenda devuelta al stock de la sucursal y descuenta el monto de las ventas brutas.\n"
    "8. El sistema imprime el comprobante de devolución para el cliente.",
    "La prenda queda reingresada en el inventario y el monto comercial queda debidamente regularizado.",
    "- Prenda dañada por mal uso: Encargado rechaza la devolución con justificación técnica.\n"
    "- Comprobante no corresponde a la empresa: Se deniega la operación."
)

# CU16
add_cu_ficha(
    "CU16", "Gestionar Códigos Promocionales y Cupones por Tenant",
    "Permitir al Administrador Tenant crear cupones de descuento (porcentaje o monto fijo) con alcance global o por sucursal, y aplicarlos durante el cálculo de ventas o carritos.",
    "El Administrador define códigos de descuento con vigencia, monto mínimo de compra y sucursales habilitadas. Los cajeros y clientes pueden aplicar el código para obtener el beneficio en el total a pagar.",
    "Administrador Tenant, Encargado de Sucursal, Cliente, Cajero / Vendedor.", "Administrador Tenant o Cliente/Cajero.",
    "Usuario con permisos para crear cupones o cliente en proceso de compra.",
    "1. El Administrador define código (ej. VERANO2026), descuento (ej. 15%), vigencia y sucursal.\n"
    "2. Al registrar una venta, el cajero o cliente introduce el código promocional.\n"
    "3. El sistema valida vigencia, tenant_id y condiciones de uso.\n"
    "4. El sistema descuenta el valor promocional del total a cobrar.\n"
    "5. El comprobante refleja el descuento aplicado de forma desglosada.",
    "La venta se liquida con el beneficio promocional y se contabiliza el uso del cupón.",
    "- Cupón vencido o inexistente: Notifica 'Código no válido o expirado'."
)

# CICLO #3
add_p("C. CICLO #3: INTELIGENCIA ARTIFICIAL GENERATIVA, MACHINE LEARNING Y ANALÍTICA", bold_prefix="")

# CU17
add_cu_ficha(
    "CU17", "Solicitar Reportes Generativos en Lenguaje Natural (Texto y Voz)",
    "Permitir al Administrador Tenant solicitar reportes empresariales complejos utilizando lenguaje natural mediante escritura en teclado o comandos de voz en la web, obteniendo datos reales de su empresa.",
    "El usuario accede al panel de analítica y formula preguntas empresariales (ej. 'Mostrame las ventas de septiembre agrupadas por sucursal' o '¿Cuáles fueron los diez productos más vendidos este mes?'). El usuario habla o escribe, el sistema identifica los filtros solicitados y le presenta el reporte dinámico generado a partir de sus datos reales.",
    "Administrador Tenant, Superadmin Plataforma.", "Administrador Tenant.",
    "Usuario autenticado en una empresa con suscripción a plan Profesional (con IA habilitada).",
    "1. El usuario abre el módulo 'Reportes con Inteligencia Artificial'.\n"
    "2. El usuario escribe su consulta o presiona el botón de micrófono para dictarla verbalmente.\n"
    "3. En caso de voz, el navegador captura el audio y transcribe la orden en tiempo real.\n"
    "4. El usuario presiona 'Consultar'.\n"
    "5. La aplicación envía la solicitud al backend, el cual valida que la consulta no sea arbitraria y pertenezca al tenant.\n"
    "6. La interfaz presenta los resultados tabulares y gráficos dinámicos construidos a partir de los datos reales.",
    "El Administrador visualiza el reporte empresarial generado sin necesidad de conocer SQL.",
    "- Plan sin módulo de IA (Básico): Notifica que el plan no incluye reportes generativos con IA.\n"
    "- Solicitud ambigua: El sistema solicita al usuario especificar fechas o sucursales."
)

# CU18
add_cu_ficha(
    "CU18", "Presentar y Exportar Reportes Dinámicos (PDF / Excel)",
    "Permitir al Administrador Tenant visualizar en pantalla el reporte interactivo y exportarlo formalmente a formatos convencionales de hoja de cálculo Excel o documento PDF.",
    "El usuario interactúa con la vista del reporte generativo. Puede ordenar columnas, alternar entre tabla y gráficos de barras o líneas, y presionar los botones de exportación para descargar el archivo formal con formato corporativo.",
    "Administrador Tenant, Superadmin Plataforma.", "Administrador Tenant.",
    "Reporte generativo consultado con resultados disponibles en pantalla.",
    "1. La interfaz web recibe los datos del reporte solicitado por el usuario.\n"
    "2. El sistema dibuja el gráfico dinámico seleccionado automáticamente y despliega la tabla.\n"
    "3. El usuario revisa los totales, agrupaciones y gráficos en pantalla.\n"
    "4. El usuario pulsa 'Exportar a PDF' o 'Exportar a Excel'.\n"
    "5. El sistema construye el documento incluyendo membrete de la empresa, fecha de emisión y firma de reporte.\n"
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
    "1. El Administrador accede a 'Configuración de Machine Learning'.\n"
    "2. El usuario selecciona las variables de análisis: sucursales, periodos comerciales y categorías de ropa.\n"
    "3. El usuario activa la opción 'Generar y Preparar Datos de Entrenamiento'.\n"
    "4. El sistema ejecuta el preprocesamiento, normalización y síntesis de datos representativos.\n"
    "5. El usuario visualiza el resumen del dataset generado: cantidad de muestras, variables procesadas y balance de datos.\n"
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
    "1. El Administrador accede a 'Predicción de Demanda de Ventas'.\n"
    "2. El usuario presiona 'Entrenar Modelo Supervisado'.\n"
    "3. El sistema entrena el algoritmo y muestra el cuadro de evaluación con métricas de precisión.\n"
    "4. El usuario selecciona la sucursal y el mes futuro que desea proyectar.\n"
    "5. El sistema presenta la gráfica comparativa entre histórico real y la demanda estimada.\n"
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
    "1. El Administrador accede a 'Segmentación y Patrones de Compra'.\n"
    "2. El usuario presiona 'Ejecutar Análisis de Segmentación'.\n"
    "3. El sistema ejecuta el clustering K-Means y genera las agrupaciones de clientes.\n"
    "4. El usuario visualiza las tarjetas de cada segmento con su ticket promedio, prendas favoritas y frecuencia.\n"
    "5. El usuario explora el panel de anomalías que señala discrepancias o comportamientos atípicos.\n"
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
    "1. El usuario accede al menú 'Dashboard Ejecutivo'.\n"
    "2. El sistema carga las tarjetas de métricas consolidadas del tenant.\n"
    "3. El usuario revisa los KPIs: Facturación mensual, cumplimiento de inventario y estado de tiendas.\n"
    "4. El usuario interactúa con los filtros interactivos seleccionando una sucursal específica.\n"
    "5. El dashboard refresca los gráficos de tendencias, comparativas de sucursales y alertas inteligentes.\n"
    "6. El usuario visualiza la síntesis de recomendaciones emitidas por los modelos de ML.",
    "El usuario directivo cuenta con una visión 360° en tiempo real del desempeño de su empresa.",
    "- Falla de comunicación con servicios de analítica: Muestra los datos transaccionales con aviso de analítica diferida."
)

doc.add_page_break()

# ==============================================================================
# CAPÍTULO III. ANÁLISIS Y DISEÑO CON ICONIX
# ==============================================================================
add_header("CAPÍTULO III. ANÁLISIS Y DISEÑO CON ICONIX", level=1)

add_header("3.1. Modelo de dominio", level=2)
add_p("El Modelo de Dominio según la metodología ICONIX captura los conceptos y entidades esenciales del negocio multitenant, definiendo sus responsabilidades y relaciones estructurales de cardinalidad:")

add_bullet("Entidad raíz del modelo SaaS. Representa a cada empresa suscriptora independiente. Posee identificador único (tenant_id), razón social, NIT y clave de aislamiento.", bold_prefix="Tenant (Empresa Contratante): ")
add_bullet("Define los términos comerciales y límites técnicos contratados (Básico vs Profesional). Regula el cupo máximo de sucursales activas y la habilitación de IA.", bold_prefix="SubscriptionPlan & Subscription: ")
add_bullet("Punto de venta y atención física perteneciente a una empresa. Varias sucursales pertenecen a un mismo Tenant (relación 1 a N).", bold_prefix="Branch (Sucursal): ")
add_bullet("Usuarios del sistema asociados a un tenant_id y opcionalmente a un branch_id (cajeros y encargados). Vinculados a roles que definen permisos.", bold_prefix="User & Role: ")
add_bullet("Estructura del catálogo. Un producto posee múltiples variantes (ProductVariant) diferenciadas por SKU, talla, color y precio de venta.", bold_prefix="Product, Category & ProductVariant: ")
add_bullet("Existencias físicas por variante y por sucursal (quantity y reserved_quantity). Vinculado a movimientos de inventario.", bold_prefix="Inventory & InventoryMovement: ")
add_bullet("Transacciones comerciales registradas en tienda o en línea. Vinculadas a items vendidos (SaleItem) y al usuario cajero responsable.", bold_prefix="Sale & SaleItem: ")
add_bullet("Cola de transacciones offline almacenada temporalmente en IndexedDB o SQLite y sincronizada con el backend central.", bold_prefix="SyncQueue / OfflineOperation: ")

add_header("3.2. Diagramas de robustez (Boundary - Control - Entity)", level=2)
add_p("El Análisis de Robustez de ICONIX vincula los casos de uso con el diseño de clases, utilizando tres estereotipos fundamentales:")
add_bullet("Objetos Frontera (Boundary): Representan las pantallas, interfaces de usuario y componentes de entrada/salida (ej. InterfazVentaOffline, FormularioSucursal, DashboardIA).")
add_bullet("Objetos Control (Control): Representan la lógica de negocio, validadores y mediadores de la aplicación (ej. ControladorVenta, ValidadorPlanSuscripcion, GestorSincronizacion, MotorReportesIA).")
add_bullet("Objetos Entidad (Entity): Representan los datos persistentes del dominio (ej. Tenant, Branch, Sale, Inventory, SyncOperation).")

add_p("A continuación se especifican las tripletas de robustez para los casos de uso neurálgicos del sistema:", bold_prefix="Especificaciones de Robustez: ")

robustez_data = [
    ("CU01 / CU04 Gestionar Empresas y Sucursales", "UI: PantallaGestionSucursal\nBoundary API: BranchController", "Control: ValidadorLimitesPlan\nControl: GestorSucursales", "Entity: Tenant\nEntity: Subscription\nEntity: Branch"),
    ("CU08 Registrar Venta Contado Offline", "UI: PosViewComponent\nBoundary Local: IndexedDbAdapter / SQLite", "Control: CalculadorTotalesVenta\nControl: GestorVentaOffline", "Entity: LocalProductVariant\nEntity: LocalSale\nEntity: SyncQueueItem"),
    ("CU11 / CU12 Sincronización e Idempotencia", "Boundary Sync: ServiceWorkerSync\nBoundary API: SyncApiController", "Control: ValidadorIdempotencia\nControl: DespachadorTransaccion", "Entity: SyncAuditLog\nEntity: Sale\nEntity: Inventory"),
    ("CU13 Detectar Conflictos de Inventario", "UI: BandejaConflictosComponent\nBoundary API: ConflictResolutionApi", "Control: VerificadorStockDisponible\nControl: ArbitradorConflictos", "Entity: Inventory\nEntity: ConflictRecord\nEntity: Notification"),
    ("CU16 / CU17 Reportes Generativos con IA", "UI: PanelReportesIaView\nBoundary Speech: WebSpeechAdapter", "Control: ParserLenguajeNatural\nControl: SqlSecureGenerator", "Entity: TenantAuditView\nEntity: SalesAnalytics\nEntity: GeneratedReport")
]
add_styled_table(["Caso de Uso", "Objetos Frontera (Boundary)", "Objetos de Control (Control)", "Objetos Entidad (Entity)"], robustez_data, [Inches(1.8), Inches(1.8), Inches(1.8), Inches(1.6)])

add_header("3.3. Diagramas de secuencia UML", level=2)
add_p("Los diagramas de secuencia detallan la interacción temporal entre los objetos Boundary, Control y Entity identificados en el análisis de robustez. Se describen los dos flujos temporales más críticos de la arquitectura:")

add_p("Flujo 1: Registro de Venta Offline y Sincronización con Idempotencia", bold_prefix="a. ")
add_p("1. Cajero ingresa prendas en PosViewComponent (Boundary Web/Móvil).\n2. PosView invoca a GestorVentaOffline (Control local).\n3. GestorVentaOffline genera un UUIDv4 único y rebaja el stock en LocalInventory (Entity Local).\n4. GestorVentaOffline guarda el registro en SyncQueue con estado 'PENDIENTE_SYNC'.\n5. Al detectar el evento 'online', ServiceWorkerSync lee la cola y envía POST /api/sync/sales a SyncApiController (Boundary Backend).\n6. SyncApiController pasa la carga a ValidadorIdempotencia (Control Backend).\n7. ValidadorIdempotencia verifica en SyncAuditLog si el UUID ya existe:\n   - Si ya existe: Retorna HTTP 200 con la confirmación previa sin reprocesar (Idempotencia garantizada).\n   - Si es nuevo: Inicia transacción ACID, descuenta el inventario central y confirma con estado 'CONFIRMADA'.\n8. El cliente recibe la confirmación y actualiza su estado local en IndexedDB/SQLite.")

add_p("Flujo 2: Solicitud de Reporte Generativo mediante Lenguaje Natural", bold_prefix="b. ")
add_p("1. Administrador Tenant dicta o escribe su solicitud en PanelReportesIaView.\n2. La interfaz envía el texto a ReportesIaController inyectando el JWT del usuario.\n3. El controlador obtiene el tenant_id del token y valida si el plan de suscripción tiene habilitada la funcionalidad de IA.\n4. ParserLenguajeNatural (Control IA) analiza la intención, fechas y filtros solicitados.\n5. SqlSecureGenerator construye una consulta SQL estricta de solo lectura forzando la cláusula WHERE tenant_id = :current_tenant.\n6. Base de datos ejecuta la consulta y devuelve los registros agregados.\n7. ReportesIaController envía el resultado a DynamicChartRenderer para generar la vista previa, permitiendo su exportación a PDF o Excel.")

add_header("3.4. Diagrama de clases UML", level=2)
add_p("El Diagrama de Clases consolidado refleja la estructura orientada a objetos del sistema en el backend (FastAPI/SQLAlchemy) y clientes, incorporando las clases del modelo multitenant y offline:")
add_bullet("Tenant: Atributos (id: UUID, name: String, tax_id: String, is_active: Boolean, created_at: DateTime). Relaciones: 1 a N con Branch, 1 a N con User, 1 a 1 con Subscription.", bold_prefix="Clase Tenant: ")
add_bullet("SubscriptionPlan: Atributos (id: UUID, code: String, name: String, max_branches: Integer, has_ai_reports: Boolean, price: Decimal).", bold_prefix="Clase SubscriptionPlan: ")
add_bullet("Subscription: Atributos (id: UUID, tenant_id: UUID, plan_id: UUID, status: String, start_date: Date, end_date: Date).", bold_prefix="Clase Subscription: ")
add_bullet("Branch: Atributos (id: UUID, tenant_id: UUID, name: String, city: String, address: String, is_active: Boolean).", bold_prefix="Clase Branch: ")
add_bullet("User: Atributos (id: UUID, tenant_id: UUID, branch_id: UUID, email: String, password_hash: String, role: String, is_active: Boolean).", bold_prefix="Clase User: ")
add_bullet("Product & ProductVariant: Atributos (id: UUID, tenant_id: UUID, name: String, category_id: UUID), Variant (id: UUID, sku: String, price: Decimal, size: String, color: String).", bold_prefix="Clases Product / Variant: ")
add_bullet("Inventory: Atributos (id: UUID, tenant_id: UUID, branch_id: UUID, variant_id: UUID, quantity: Integer, reserved_quantity: Integer).", bold_prefix="Clase Inventory: ")
add_bullet("Sale & SaleItem: Atributos (id: UUID, tenant_id: UUID, branch_id: UUID, client_id: UUID, total: Decimal, payment_method: String, is_offline_sync: Boolean, sync_uuid: UUID).", bold_prefix="Clase Sale: ")
add_bullet("SyncOperation: Atributos (id: UUID, sync_uuid: UUID, tenant_id: UUID, branch_id: UUID, payload: JSON, status: String, error_log: Text).", bold_prefix="Clase SyncOperation: ")

add_header("3.5. Diseño de la base de datos", level=2)
add_p("El diseño de la base de datos se implementa en PostgreSQL bajo una estrategia de base de datos compartida con aislamiento lógico por tenant. Cada tabla de negocio incluye la columna 'tenant_id' como clave foránea y criterio de particionado/indexado.")

add_p("Estructura de Tablas Centrales (PostgreSQL):", bold_prefix="a. ")
add_bullet("tenants (id UUID PK, business_name VARCHAR(255), nit VARCHAR(50), status VARCHAR(20), created_at TIMESTAMP)")
add_bullet("subscription_plans (id UUID PK, code VARCHAR(30) UNIQUE, name VARCHAR(100), max_branches INT, has_ai_reports BOOLEAN, is_active BOOLEAN)")
add_bullet("subscriptions (id UUID PK, tenant_id UUID FK, plan_id UUID FK, start_date DATE, end_date DATE, status VARCHAR(20))")
add_bullet("branches (id UUID PK, tenant_id UUID FK, name VARCHAR(150), city VARCHAR(100), address TEXT, is_active BOOLEAN)")
add_bullet("users (id UUID PK, tenant_id UUID FK, branch_id UUID FK NULL, email VARCHAR(255) UNIQUE, password_hash VARCHAR(255), role VARCHAR(50))")
add_bullet("products (id UUID PK, tenant_id UUID FK, category_id UUID FK, name VARCHAR(255), description TEXT, is_active BOOLEAN)")
add_bullet("product_variants (id UUID PK, product_id UUID FK, sku VARCHAR(100) UNIQUE, price NUMERIC(10,2), size VARCHAR(20), color VARCHAR(50))")
add_bullet("inventory (id UUID PK, tenant_id UUID FK, branch_id UUID FK, variant_id UUID FK, quantity INT, reserved_quantity INT)")
add_bullet("sales (id UUID PK, tenant_id UUID FK, branch_id UUID FK, user_id UUID FK, total_amount NUMERIC(10,2), status VARCHAR(30), sync_uuid UUID UNIQUE NULL, is_offline BOOLEAN DEFAULT FALSE)")
add_bullet("sync_audit_logs (id UUID PK, sync_uuid UUID UNIQUE, tenant_id UUID FK, branch_id UUID FK, status VARCHAR(30), received_at TIMESTAMP, response_payload JSONB)")

add_p("Estructura de Persistencia Local (IndexedDB en PWA y SQLite en Móvil):", bold_prefix="b. ")
add_bullet("local_catalog: Caché de productos y variantes con precios y existencias locales conocidas para visualización rápida.")
add_bullet("local_sales: Registro temporal de ventas efectuadas en la terminal sin conexión.")
add_bullet("local_reservations: Registro temporal de reservas tomadas en la terminal.")
add_bullet("sync_queue: Cola de operaciones con columnas (uuid, operation_type, payload, status, retry_count, last_attempt).")

add_header("3.6. Diseño de interfaces de usuario", level=2)
add_p("Las interfaces de usuario se diseñan bajo principios de diseño responsivo y pautas de usabilidad:")
add_bullet("Panel Superadmin SaaS: Vista de administración de tenants, monitoreo de suscripciones activas y configuración de planes.")
add_bullet("PWA Punto de Venta (POS): Interfaz de venta rápida con buscador local, botón de cobro de contado en efectivo, banner visual de conectividad ('Modo Offline') y contador de operaciones pendientes de sincronización.")
add_bullet("Bandeja de Sincronización y Conflictos: Panel para el encargado donde se detallan transacciones confirmadas y se resuelven discrepancias de inventario.")
add_bullet("Módulo de Reportes Generativos: Cuadro de diálogo para consultas en lenguaje natural, botón de micrófono para comandos de voz, previsualización interactiva de gráficos y botones de exportación a Excel y PDF.")

doc.add_page_break()

# ==============================================================================
# CAPÍTULO IV. DESARROLLO E IMPLEMENTACIÓN
# ==============================================================================
add_header("CAPÍTULO IV. DESARROLLO E IMPLEMENTACIÓN", level=1)

add_header("4.1. Herramientas y tecnologías utilizadas", level=2)
tec_data = [
    ("Backend API REST", "Python 3.12, FastAPI, SQLAlchemy ORM, Pydantic, Alembic", "Exposición de servicios asíncronos de alto rendimiento, migraciones de esquema y lógica transaccional multitenant."),
    ("Frontend Web & PWA", "Angular 21, TypeScript, Tailwind CSS, Spartan/Helm UI, RxJS", "Desarrollo de interfaz web corporativa, Service Workers, Web App Manifest y almacenamiento en IndexedDB."),
    ("Aplicación Móvil", "Flutter, Dart, SQLite (sqflite / drift), Provider / BLoC", "Aplicación móvil nativa multiplataforma con persistencia relacional local y sincronización offline."),
    ("Base de Datos Central", "PostgreSQL 16", "Motor relacional para persistencia compartida con integridad referencial, índices multitenant y transaccionalidad ACID."),
    ("Inteligencia Artificial & ML", "Google Gemini API / OpenAI API, Scikit-Learn, Pandas, NumPy", "Procesamiento de lenguaje natural para reportes generativos y modelos de Machine Learning (supervisados y no supervisados)."),
    ("Contenedores y Despliegue", "Docker, Docker Compose, Nginx, Uvicorn", "Empaquetamiento y despliegue del sistema en servidor en la nube accesible públicamente."),
    ("Metodología y Modelado", "Metodología ICONIX, StarUML, Draw.io", "Proceso de desarrollo guiado por casos de uso, robustez y modelos UML 2.5+.")
]
add_styled_table(["Componente", "Tecnología / Framework", "Rol en el Proyecto"], tec_data, [Inches(1.8), Inches(2.2), Inches(2.8)])

add_header("4.2. Diseño de la arquitectura del sistema", level=2)
add_p("La arquitectura del sistema sigue un modelo multicapa desacoplado con soporte para clientes híbridos y servicios inteligentes:")
add_bullet("Capa de Presentación: Conformada por el cliente web Angular configurado como PWA (instalable en escritorio y dispositivos) y la aplicación móvil Flutter. Ambas implementan adaptadores locales de almacenamiento.", bold_prefix="1. ")
add_bullet("Capa de Borde y Sincronización: Service Workers en web y servicios background en Flutter que interceptan peticiones y gestionan la cola de operaciones pendientes.", bold_prefix="2. ")
add_bullet("Capa de Aplicación y Servicios (Backend): API REST en FastAPI estructurada en routers modulares (tenants, auth, catalog, sales, sync, reports, ai). Incorpora middlewares de inyección de tenant y validación de planes.", bold_prefix="3. ")
add_bullet("Capa de Datos y Persistencia: Servidor PostgreSQL centralizado con aislamiento lógico estricto por tenant_id.", bold_prefix="4. ")
add_bullet("Capa de Analítica Inteligente: Módulo integrado que acopla modelos de Machine Learning para clustering y regresión, junto con adaptadores de lenguaje natural para reportes generativos.", bold_prefix="5. ")

add_header("4.3. Implementación de la base de datos", level=2)
add_p("La base de datos se implementa ejecutando migraciones versionadas mediante Alembic en el backend de FastAPI. Se configuran índices compuestos (ej. CREATE INDEX idx_sales_tenant_branch ON sales(tenant_id, branch_id)) para garantizar que las consultas filtradas por empresa se resuelvan en tiempos submilimétricos, impidiendo cuellos de botella de concurrencia.")

add_header("4.4. Desarrollo de los módulos del sistema", level=2)
add_bullet("Módulo de Suscripciones y Multitenant: Implementado con endpoints en FastAPI para alta de tenants y middleware que extrae el tenant_id del JWT, forzando filtros a nivel de ORM.", bold_prefix="a. ")
add_bullet("Módulo PWA con IndexedDB: Implementado en Angular mediante biblioteca idb/Dexie y Service Worker para precaché de assets y operaciones comerciales en segundo plano.", bold_prefix="b. ")
add_bullet("Módulo Móvil con SQLite: Implementado en Flutter utilizando sqflite con esquemas locales equivalentes para variantes, ventas y cola de sincronización.", bold_prefix="c. ")
add_bullet("Módulo de Sincronización e Idempotencia: Implementado en backend con endpoint transaccional que valida la tabla sync_audit_logs antes de efectuar cualquier escritura.", bold_prefix="d. ")
add_bullet("Módulo de Reportes Generativos: Implementado mediante integración de API de lenguaje natural con prompt engineering restringido que genera parámetros SQL seguros, renderizado dinámicamente en frontend.", bold_prefix="e. ")

add_header("4.5. Integración de componentes", level=2)
add_p("Todos los componentes se integran a través de contratos REST documentados automáticamente con OpenAPI / Swagger en FastAPI. La comunicación entre clientes offline y el backend se realiza mediante JSON payloads estandarizados que incluyen el identificador único de operación (UUID) y metadatos de sincronización.")

doc.add_page_break()

# ==============================================================================
# CAPÍTULO V. PRUEBAS Y RESULTADOS
# ==============================================================================
add_header("CAPÍTULO V. PRUEBAS Y RESULTADOS", level=1)

add_header("5.1. Plan de pruebas", level=2)
add_p("El plan de pruebas tiene como propósito verificar la robustez funcional del sistema y la confiabilidad de las operaciones sin conexión, el aislamiento multitenant y la precisión de los modelos inteligentes:")
add_bullet("Pruebas Unitarias: Verificación de funciones de cálculo de totales, generación de UUIDs y validación de parámetros de suscripción.")
add_bullet("Pruebas de Aislamiento Multitenant: Intentos explícitos de acceso a recursos de la Empresa B utilizando tokens emitidos para la Empresa A.")
add_bullet("Pruebas de Operación Offline: Simulación de pérdida de conexión en navegador y emulador móvil durante el flujo completo de registro de ventas.")
add_bullet("Pruebas de Sincronización e Idempotencia: Envío repetido del mismo lote de transacciones para comprobar que no existan duplicaciones ni descuadres de inventario.")
add_bullet("Pruebas de Inteligencia Artificial y Machine Learning: Evaluación de precisión, matriz de confusión y tiempo de respuesta ante consultas de lenguaje natural.")

add_header("5.2. Pruebas funcionales", level=2)
add_p("Se ejecutaron pruebas funcionales sobre los 22 Casos de Uso del sistema en ambientes web y móviles, validando que las interfaces respondan correctamente a las interacciones del usuario y reporten retroalimentación clara de estado.")

add_header("5.3. Pruebas de integración", level=2)
add_p("Se validó la interoperabilidad entre el cliente Angular PWA, la app Flutter y el backend en FastAPI a través de llamadas asíncronas seguras, comprobando la persistencia adecuada de las transacciones sincronizadas en PostgreSQL.")

add_header("5.4. Corrección de errores", level=2)
add_p("Durante la fase de integración se detectaron y corrigieron incidencias menores relacionadas con bloqueos en IndexedDB ante transacciones concurrentes en múltiples pestañas, y ajustes en la normalización de datos sintéticos para el entrenamiento de los algoritmos de Machine Learning.")

add_header("5.5. Resultados de las pruebas", level=2)
add_p("El 100% de los casos de prueba críticos de aislamiento de datos e idempotencia fueron aprobados satisfactoriamente. Se verificó que dos empresas de prueba independientes ('Boutique Elegance' y 'Moda Urbana') operaron simultáneamente sin experimentar fugas de información ni interferencias cruzadas.")

add_header("5.6. Casos de prueba", level=2)
casos_prueba_data = [
    ("CP01", "Aislamiento Multitenant", "Intentar listar sucursales de Empresa B con credenciales de Empresa A.", "Acceso denegado (HTTP 403 / lista vacía).", "Aprobado"),
    ("CP02", "Control de Límite de Sucursales", "Intentar crear la 3ra sucursal en un tenant con plan Básico (máx. 2).", "Backend rechaza la operación con mensaje de límite de plan.", "Aprobado"),
    ("CP03", "Venta Offline en PWA", "Desconectar red en navegador y registrar venta de contado en POS.", "Venta guardada en IndexedDB con estado PENDIENTE_SYNC.", "Aprobado"),
    ("CP04", "Sincronización Idempotente", "Reconectar red y reenviar 3 veces consecutivas la misma venta.", "Backend confirma venta una sola vez; inventario descontado una vez.", "Aprobado"),
    ("CP05", "Detección de Conflictos", "Vender offline la última unidad física simultáneamente en dos cajas.", "Primera venta confirmada; segunda venta marcada en conflicto.", "Aprobado"),
    ("CP06", "Reporte Generativo IA", "Solicitar por voz: 'Ventas de septiembre agrupadas por sucursal'.", "Reporte tabular y gráfico generado filtrado al tenant activo.", "Aprobado")
]
add_styled_table(["ID", "Nombre", "Acción Ejecutada", "Resultado Esperado", "Estado"], casos_prueba_data, [Inches(0.8), Inches(1.8), Inches(2.2), Inches(1.8), Inches(0.8)])

doc.add_page_break()

# ==============================================================================
# CAPÍTULO VI. CONCLUSIONES Y RECOMENDACIONES
# ==============================================================================
add_header("CAPÍTULO VI. CONCLUSIONES Y RECOMENDACIONES", level=1)

add_header("6.1. Conclusiones", level=2)
add_p("En correspondencia con los objetivos específicos planteados en el presente proyecto, se establecen las siguientes conclusiones:")
add_bullet("Se aplicó rigurosamente la metodología ICONIX en el análisis, diseño y evolución del sistema, permitiendo un desarrollo ágil y trazable desde los casos de uso hacia diagramas de robustez, diagramas de secuencia e implementación directa de código sin sobrecarga documental.")
add_bullet("Se transformó exitosamente la plataforma en una arquitectura SaaS multitenant funcional con aislamiento lógico estricto en PostgreSQL y validación en backend, permitiendo a múltiples empresas independientes gestionar sus recursos con total privacidad.")
add_bullet("Se implementó un esquema flexible de planes de suscripción (Básico y Profesional) que regula eficazmente los cupos de sucursales activas y habilita módulos avanzados de analítica.")
add_bullet("Se evolucionó la aplicación web Angular hacia una Progressive Web App (PWA) instalable, con soporte completo de persistencia en IndexedDB para la consulta de catálogo y captura de ventas en efectivo sin conexión.")
add_bullet("Se incorporó la base de datos local relacional SQLite en la aplicación móvil Flutter, garantizando almacenamiento confiable y consulta offline.")
add_bullet("Se diseñó un motor de sincronización e idempotencia basado en identificadores UUID que previene registros duplicados y mantiene la consistencia transaccional del inventario central.")
add_bullet("Se integró un módulo de reportes generativos con inteligencia artificial capaz de procesar solicitudes en lenguaje natural por texto y voz, generando salidas dinámicas tabulares y gráficas exportables a PDF y Excel.")
add_bullet("Se desarrolló el pipeline de Machine Learning con datos sintéticos, modelos supervisados de predicción de ventas y no supervisados de segmentación, integrados en un dashboard analítico unificado.")

add_header("6.2. Recomendaciones", level=2)
add_bullet("Integrar a futuro una pasarela de pagos recurrentes automatizada (como Stripe Billing o pasarelas locales) para la suscripción y renovación automática de los planes SaaS.")
add_bullet("Ampliar los algoritmos de resolución de conflictos offline mediante políticas comerciales configurables por cada empresa (ej. prioridad por antigüedad de cliente o notificación automática de reabastecimiento).")
add_bullet("Incorporar redes neuronales profundas (LSTM o Transformers) en el módulo de Machine Learning para series temporales de demanda estacional a largo plazo.")

add_header("7. BIBLIOGRAFÍA", level=1)
add_p("1. Rosenberg, D., & Stephens, M. (2007). Use Case Driven Object Modeling with UML: Theory and Practice (ICONIX Process). Apress.")
add_p("2. Booch, G., Rumbaugh, J., & Jacobson, I. (2000). El Lenguaje Unificado de Modelado. Guía del Usuario (2a ed.). Addison-Wesley.")
add_p("3. Fowler, M. (2002). Patterns of Enterprise Application Architecture. Addison-Wesley Professional.")
add_p("4. Tiangolo, S. (2024). FastAPI Documentation: Modern, Fast Web Framework for Python. https://fastapi.tiangolo.com/")
add_p("5. Google. (2024). Progressive Web Apps Guide & Service Worker API. Google Developers.")
add_p("6. Flutter Team. (2024). Persistence with SQLite in Flutter. https://docs.flutter.dev/cookbook/persistence/sqlite")

add_header("8. ANEXOS", level=1)
add_p("Anexo 1: Repositorio de código fuente con implementaciones completas de Backend FastAPI, Frontend Angular PWA y Aplicación Móvil Flutter.")
add_p("Anexo 2: Colección de solicitudes y pruebas de endpoints REST exportadas en Postman / OpenAPI.")
add_p("Anexo 3: Scripts de población de base de datos multitenant con dos empresas de prueba ('Boutique Elegance' y 'Moda Urbana').")

# Guardar documento
doc_output_path = "2do-Parcial-Informe-grupo-46.docx"
try:
    doc.save(doc_output_path)
    print(f"Documento guardado exitosamente en: {doc_output_path}")
except PermissionError:
    doc_output_path = "2do-Parcial-Informe-grupo-46-actualizado.docx"
    doc.save(doc_output_path)
    print(f"Nota: El archivo original estaba abierto en Word. Se guardó exitosamente en: {doc_output_path}")
