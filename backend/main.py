import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from app.packages.p0_saas_plataforma.router import p0_router
from app.packages.p1_gestion_usuarios_acceso.router import p1_router
from app.packages.p2_gestion_productos_catalogo.router import p2_router
from app.packages.p3_gestion_inventario_disponibilidad.router import p3_router
from app.packages.p4_gestion_compras_reservas.router import p4_router
from app.packages.p5_gestion_ventas_pos.router import p5_router
from app.packages.p6_inteligencia_analitica.router import p6_router
from app.core.error_handlers import register_error_handlers
from app.core.database import SessionLocal
from app.services.expiration_service import run_daily_expiration
from app.services.order_service import expire_due_orders


async def _expire_orders_loop() -> None:
    while True:
        await asyncio.sleep(60)
        db = SessionLocal()
        try:
            expire_due_orders(db)
        except Exception:
            db.rollback()
        finally:
            db.close()


async def _daily_expiration_loop() -> None:
    while True:
        now = datetime.now()
        next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        await asyncio.sleep(max((next_midnight - now).total_seconds(), 1))
        try:
            run_daily_expiration()
        except Exception:
            pass


@asynccontextmanager
async def lifespan(_: FastAPI):
    task = asyncio.create_task(_expire_orders_loop())
    daily_task = asyncio.create_task(_daily_expiration_loop())
    try:
        yield
    finally:
        task.cancel()
        daily_task.cancel()
        await asyncio.gather(task, daily_task, return_exceptions=True)


app = FastAPI(title="FashionStore SaaS Multitenant API", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers estructurados por paquetes de dominio (ICONIX)
api_router = APIRouter(prefix="/api")

# Paquete 0: Plataforma SaaS, Gestión de Tenants y Suscripciones (CU01–CU02)
api_router.include_router(p0_router)

# Paquete 1: Gestión de usuarios y acceso (CU03–CU05)
api_router.include_router(p1_router)

# Paquete 2: Gestión de productos y catálogo (CU06–CU07)
api_router.include_router(p2_router)

# Paquete 3: Gestión de inventario y disponibilidad (CU08–CU11)
api_router.include_router(p3_router)

# Paquete 4: Gestión de compras y reservas (CU12–CU14)
api_router.include_router(p4_router)

# Paquete 5: Ventas, POS, Sincronización y Políticas (CU15–CU20)
api_router.include_router(p5_router)

# Paquete 6: Inteligencia, analítica y visión móvil (CU21–CU28)
api_router.include_router(p6_router)

app.include_router(api_router)

register_error_handlers(app)
