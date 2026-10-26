/* =================================================================================
 * PROYECTO: FashionStore - Plataforma E-Commerce SaaS Multitenant
 * DIAGRAMA: Diagrama de Despliegue (Deployment Diagram - Flujo Vertical UML 2.5+)
 * DESCRIPCIÓN: Modelo de despliegue físico y lógico estructurado verticalmente:
 *              - Capa 1 (Superior): Dispositivos Cliente y Terminales Sucursal / POS Tenant.
 *              - Capa 2: Red Internet (WAN / Telecomunicaciones con TLS 1.3).
 *              - Capa 3: Servidor Web Frontend (Render Cloud Platform - Angular 21 PWA).
 *              - Capa 4: Servidor Backend SaaS (Render Cloud Platform - Docker / FastAPI).
 *              - Capa 5 (Inferior): Servidor Base de Datos (Cloud PostgreSQL 15+ - Render / Neon).
 *              - Capa Lateral Derecha: Servicios Cloud, IA y Pasarelas (Lucy VTON, Cloudinary, Gemini AI, Stripe).
 *              
 *              * Todos los artefactos y entornos de ejecución se generan como
 *                elementos UML independientes (Artifacts / Execution Environments)
 *                anidados visual y jerárquicamente dentro de sus Nodos.
 *
 * ENTORNO: Enterprise Architect 15.0+ / 16.0+
 * LENGUAJE: JScript (Motor nativo WSH / JScript en Enterprise Architect)
 * ================================================================================= */

var DEFAULT_PACKAGE_NAME = "CUdiagrams";
var DIAGRAM_NAME = "Diagrama de Despliegue - FashionStore SaaS";

function log(msg) {
    Session.Output("[Despliegue-FashionStore] " + msg);
}

/**
 * Obtiene el paquete de destino en el Project Browser o lo crea si no existe.
 */
function getTargetPackage() {
    var selectedPkg = Repository.GetTreeSelectedPackage();
    if (selectedPkg != null) {
        log("Usando paquete seleccionado en Project Browser: " + selectedPkg.Name);
        return selectedPkg;
    }

    var roots = Repository.Models;
    var root = (roots.Count > 0) ? roots.GetAt(0) : null;
    if (root == null) {
        Session.Prompt("No se encontró ningún modelo raíz en Enterprise Architect.", 0);
        return null;
    }

    for (var i = 0; i < root.Packages.Count; i++) {
        var p = root.Packages.GetAt(i);
        if (p.Name == DEFAULT_PACKAGE_NAME) {
            return p;
        }
    }

    var newPkg = root.Packages.AddNew(DEFAULT_PACKAGE_NAME, "Package");
    newPkg.Update();
    root.Packages.Refresh();
    log("Paquete creado: " + DEFAULT_PACKAGE_NAME);
    return newPkg;
}

/**
 * Recrea el diagrama de despliegue limpio.
 */
function recreateDiagram(pkg) {
    for (var i = pkg.Diagrams.Count - 1; i >= 0; i--) {
        var d = pkg.Diagrams.GetAt(i);
        if (d.Name == DIAGRAM_NAME) {
            try {
                pkg.Diagrams.Delete(i);
                pkg.Diagrams.Refresh();
                log("Diagrama previo eliminado para regeneración limpia.");
            } catch (e) {
                log("Aviso al eliminar: " + e.message);
            }
            break;
        }
    }

    var diagram = pkg.Diagrams.AddNew(DIAGRAM_NAME, "Deployment");
    diagram.Update();
    pkg.Diagrams.Refresh();
    return diagram;
}

/**
 * Crea un Nodo UML (Device o Node) y lo posiciona en el diagrama.
 */
function addNode(pkg, diagram, name, stereotype, notes, l, r, t, b) {
    var el = pkg.Elements.AddNew(name, "Node");
    if (stereotype && stereotype.length > 0) {
        el.Stereotype = stereotype;
    }
    if (notes && notes.length > 0) {
        el.Notes = notes;
    }
    el.Update();
    pkg.Elements.Refresh();

    var dObj = diagram.DiagramObjects.AddNew("l=" + l + ";r=" + r + ";t=" + t + ";b=" + b + ";", "");
    dObj.ElementID = el.ElementID;
    dObj.Update();

    return el;
}

/**
 * Crea un Artefacto UML como elemento hijo dentro de un Nodo y lo posiciona en el diagrama.
 */
function addArtifact(parentNode, diagram, name, stereotype, l, r, t, b) {
    var art = parentNode.Elements.AddNew(name, "Artifact");
    if (stereotype && stereotype.length > 0) {
        art.Stereotype = stereotype;
    }
    art.Update();
    parentNode.Elements.Refresh();

    var dObj = diagram.DiagramObjects.AddNew("l=" + l + ";r=" + r + ";t=" + t + ";b=" + b + ";", "");
    dObj.ElementID = art.ElementID;
    dObj.Update();

    return art;
}

/**
 * Crea un Entorno de Ejecución (Execution Environment) dentro de un Nodo y lo posiciona en el diagrama.
 */
function addExecutionEnv(parentNode, diagram, name, stereotype, l, r, t, b) {
    var env = parentNode.Elements.AddNew(name, "ExecutionEnvironment");
    if (stereotype && stereotype.length > 0) {
        env.Stereotype = stereotype;
    }
    env.Update();
    parentNode.Elements.Refresh();

    var dObj = diagram.DiagramObjects.AddNew("l=" + l + ";r=" + r + ";t=" + t + ";b=" + b + ";", "");
    dObj.ElementID = env.ElementID;
    dObj.Update();

    return env;
}

/**
 * Crea una vía de comunicación (CommunicationPath) con etiqueta de protocolo.
 * NOTA: Se omite el estereotipo en las flechas para evitar la sobrecarga visual de «communication»,
 * manteniendo de forma limpia el nombre del protocolo y puerto.
 */
function addCommunication(src, dst, protocolLabel) {
    var con = src.Connectors.AddNew(protocolLabel, "CommunicationPath");
    con.SupplierID = dst.ElementID;
    con.Update();
    return con;
}

function main() {
    log("Iniciando generación del Diagrama de Despliegue (FashionStore SaaS Multitenant)...");

    var pkg = getTargetPackage();
    if (pkg == null) return;

    var diagram = recreateDiagram(pkg);

    /* =========================================================================
     * 1. NIVEL 1: CAPA DE DISPOSITIVOS CLIENTES Y SUCURSALES (Y = -40 .. -250)
     * ========================================================================= */
    // Dispositivo Cliente Final (E-Commerce B2C / Probador AR)
    var nodoCliente = addNode(
        pkg, diagram,
        "Dispositivo Cliente\n(PC / Laptop / Smartphone)",
        "device",
        "Dispositivo del cliente final para acceso al catálogo multitenant, carrito de compra, pagos online y probador virtual AR.",
        60, 420, -40, -250
    );
    addArtifact(nodoCliente, diagram, "Web Client App\n(Angular 21 PWA)", "artifact", 90, 390, -100, -160);
    addArtifact(nodoCliente, diagram, "Mobile Client App\n(Flutter / Dart + SQLite)", "artifact", 90, 390, -175, -235);

    // Dispositivo Sucursal / Punto de Venta (POS) / Admin
    var nodoAdmin = addNode(
        pkg, diagram,
        "Dispositivo Sucursal / Admin\n(PC Escritorio / Terminal POS)",
        "device",
        "Terminal de trabajo en sucursal para administradores, encargados y cajeros (POS Online/Offline con sincronización).",
        480, 840, -40, -250
    );
    addArtifact(nodoAdmin, diagram, "Admin & POS Dashboard\n(Angular 21 PWA + IndexedDB)", "artifact", 510, 810, -125, -210);

    /* =========================================================================
     * 2. NIVEL 2: RED INTERNET (WAN / Tránsito Seguro: Y = -300 .. -420)
     * ========================================================================= */
    var nodoInternet = addNode(
        pkg, diagram,
        "Red Internet\n(WAN / Red Pública Segura)",
        "device",
        "Infraestructura pública de telecomunicaciones protegida mediante protocolos seguros (TCP/IP - TLS 1.3 / HTTPS).",
        270, 630, -300, -420
    );

    /* =========================================================================
     * 3. NIVEL 3: SERVIDOR WEB FRONTEND - RENDER CLOUD (Y = -480 .. -690)
     * ========================================================================= */
    var nodoFrontend = addNode(
        pkg, diagram,
        "Servidor Web Frontend\n(Render Cloud Platform)",
        "device",
        "Plataforma Cloud de Render encargada del alojamiento de la aplicación PWA, CDN perimetral y entrega de bundles estáticos.",
        250, 650, -480, -690
    );
    var envRenderWeb = addExecutionEnv(nodoFrontend, diagram, "Render Static / Node.js Engine", "executionEnvironment", 280, 620, -540, -670);
    addArtifact(nodoFrontend, diagram, "FashionStore Web Bundle\n(Angular 21 PWA + Service Worker)", "artifact", 300, 600, -590, -655);

    /* =========================================================================
     * 4. NIVEL 4: SERVIDOR BACKEND SAAS - RENDER CLOUD (Y = -750 .. -980)
     * ========================================================================= */
    var nodoBackend = addNode(
        pkg, diagram,
        "Servidor Backend SaaS\n(Render Cloud Platform - Web Service)",
        "device",
        "Servicio Web en Render ejecutado en contenedor Docker con FastAPI, validación JWT de tenant_id y lógica de 7 paquetes de dominio.",
        250, 650, -750, -980
    );
    var envDocker = addExecutionEnv(nodoBackend, diagram, "Docker Container Runtime\n(Python 3.11 + FastAPI / Uvicorn)", "executionEnvironment", 280, 620, -810, -960);
    addArtifact(nodoBackend, diagram, "FashionStore Core REST API\n(FastAPI - 7 Paquetes p0 a p6)", "artifact", 300, 600, -870, -945);

    /* =========================================================================
     * 5. NIVEL 5: SERVIDOR BASE DE DATOS - POSTGRESQL (Y = -1040 .. -1250)
     * ========================================================================= */
    var nodoDatabase = addNode(
        pkg, diagram,
        "Servidor Base de Datos\n(Cloud PostgreSQL 15+ - Render / Neon)",
        "device",
        "Servidor PostgreSQL relacional gestionado con soporte multitenant (tenant_id), transacciones ACID y tabla de idempotencia sync_operations.",
        250, 650, -1040, -1250
    );
    var envPostgres = addExecutionEnv(nodoDatabase, diagram, "PostgreSQL 15+ DBMS Engine\n(Aislamiento Multitenant)", "executionEnvironment", 280, 620, -1100, -1230);
    addArtifact(nodoDatabase, diagram, "Esquema BD Multitenant\n(FashionStore_DB - 28 Casos de Uso)", "artifact", 300, 600, -1155, -1215);

    /* =========================================================================
     * 6. COLUMNA DERECHA: SERVICIOS CLOUD, IA Y PASARELAS (X = 930 .. 1280)
     * ========================================================================= */
    // Servicio 1: Lucy VTON (Probador Virtual / RA)
    var nodoLucy = addNode(
        pkg, diagram,
        "Lucy VTON Service\n(Probador Virtual / RA)",
        "node",
        "Servicio de Inteligencia Artificial para probador virtual y renderizado predictivo de prendas sobre silueta humana.",
        930, 1280, -40, -220
    );
    addArtifact(nodoLucy, diagram, "Lucy VTON Inference API", "artifact", 960, 1250, -110, -190);

    // Servicio 2: Cloudinary Media Cloud
    var nodoCloudinary = addNode(
        pkg, diagram,
        "Cloudinary Media Cloud\n(Gestión y CDN de Multimedia)",
        "node",
        "Almacenamiento en la nube y optimización de imágenes y catálogos multimedia por tenant.",
        930, 1280, -280, -460
    );
    addArtifact(nodoCloudinary, diagram, "Cloudinary REST & CDN API", "artifact", 960, 1250, -350, -430);

    // Servicio 3: Google Gemini AI
    var nodoGemini = addNode(
        pkg, diagram,
        "Google Cloud - Gemini AI\n(Asistente Inteligente & RAG Voz)",
        "node",
        "Modelos de lenguaje multimodal para consultas en lenguaje natural, RAG asistido por voz y analítica predictiva (p6).",
        930, 1280, -520, -700
    );
    addArtifact(nodoGemini, diagram, "Gemini 1.5 / 2.0 Flash API", "artifact", 960, 1250, -590, -670);

    // Servicio 4: Stripe Payments
    var nodoStripe = addNode(
        pkg, diagram,
        "Pasarela de Pago\n(Stripe Payments Gateway)",
        "node",
        "Infraestructura segura de cobros PCI-DSS para planes de suscripción SaaS y transacciones de pedidos online.",
        930, 1280, -760, -940
    );
    addArtifact(nodoStripe, diagram, "Stripe Payments & Webhooks API", "artifact", 960, 1250, -830, -910);

    /* =========================================================================
     * 7. VÍAS DE COMUNICACIÓN (Communication Paths - Sin estereotipo «communication»)
     * ========================================================================= */
    // Flujo Vertical Principal
    addCommunication(nodoCliente, nodoInternet, "HTTPS :443\n(TLS 1.3 / WSS)");
    addCommunication(nodoAdmin, nodoInternet, "HTTPS :443\n(TLS 1.3)");
    addCommunication(nodoInternet, nodoFrontend, "HTTPS :443\n(HTTP/2 - Render CDN)");
    addCommunication(nodoFrontend, nodoBackend, "HTTPS / REST JSON\n(API Calls con JWT tenant_id)");
    addCommunication(nodoBackend, nodoDatabase, "SQLAlchemy / TCP :5432\n(SSL Encrypted - Pool)");

    // Conexiones a Servicios Externos
    addCommunication(nodoCliente, nodoLucy, "HTTPS :443\n(AR Video Stream)");
    addCommunication(nodoBackend, nodoLucy, "HTTPS :443\n(Inference API)");
    addCommunication(nodoCliente, nodoCloudinary, "HTTPS :443\n(CDN Image Fetch)");
    addCommunication(nodoBackend, nodoCloudinary, "HTTPS :443\n(Media Upload API)");
    addCommunication(nodoBackend, nodoGemini, "HTTPS :443\n(REST API - Gemini RAG)");
    addCommunication(nodoBackend, nodoStripe, "HTTPS :443\n(Payment Intents & Webhooks)");

    /* =========================================================================
     * 8. GUARDAR, REFRESCAR Y ABRIR DIAGRAMA
     * ========================================================================= */
    diagram.Update();
    Repository.SaveDiagram(diagram.DiagramID);
    Repository.ReloadDiagram(diagram.DiagramID);
    Repository.OpenDiagram(diagram.DiagramID);

    log("Diagrama vertical '" + DIAGRAM_NAME + "' generado exitosamente con artefactos independientes.");
    Session.Prompt("¡Diagrama de Despliegue (FashionStore SaaS en Render) generado con éxito en Enterprise Architect!", 0);
}

main();
