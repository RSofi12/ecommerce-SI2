from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session, selectinload
from uuid import UUID

from app.auth.dependencies import get_current_user, require_roles
from app.core.config import settings
from app.core.database import get_db
from app.packages.p1_gestion_usuarios_acceso.models.user import User
from app.packages.p2_gestion_productos_catalogo.schemas.catalog_enums import ProductStatusEnum
from app.packages.p2_gestion_productos_catalogo.schemas.catalog_schema import (
    NameCreate,
    ColorCreate,
    CollectionCreate,
    ProductCreate,
    ProductRead,
    ProductVariantStatusUpdate,
    ProductVariantGarmentPointsUpdate,
)
from app.schemas.enums import RolEnum
from app.packages.p2_gestion_productos_catalogo.models.category import Category
from app.packages.p2_gestion_productos_catalogo.models.size import Size
from app.packages.p2_gestion_productos_catalogo.models.color import Color
from app.packages.p2_gestion_productos_catalogo.models.season import Season
from app.packages.p2_gestion_productos_catalogo.models.collection import Collection
from app.packages.p2_gestion_productos_catalogo.models.product import Product
from app.packages.p2_gestion_productos_catalogo.models.product_variant import ProductVariant
from app.models.inventory import Inventory
from app.packages.p1_gestion_usuarios_acceso.models.provider import Provider
from app.packages.p1_gestion_usuarios_acceso.models.branch import Branch
from app.packages.p2_gestion_productos_catalogo.services.catalog_service import (
    create_name_item,
    create_color,
    create_collection,
    create_product,
    update_name_item,
    delete_category,
    delete_size,
    delete_color,
    delete_season,
    delete_collection,
    update_product,
    delete_product,
    update_product_status,
    update_variant_garment_points,
    list_public_products,
    get_public_product,
    list_admin_products,
    create_or_update_inventory,
    get_branch_quantity,
    available_quantity,
    list_pending_products as list_pending_products_service,
    get_variant_by_id,
    serialize_product,
    update_variant_image,
    clear_variant_image,
)
from app.packages.p2_gestion_productos_catalogo.services.cloudinary_service import delete_image, upload_image
from app.services.recommendation_service import record_product_view
from app.utils.response import response


router = APIRouter(prefix="/catalog", tags=["Catalog"])


class ProductViewContext(BaseModel):
    variant_id: UUID | None = None
    branch_id: UUID | None = None


def _validate_product_provider_scope(db: Session, provider_id: UUID | None) -> None:
    if provider_id is None:
        return
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El proveedor no existe")


def _resolve_legacy_variant(db: Session, product_id: UUID):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return None
    return (
        db.query(ProductVariant)
        .filter(ProductVariant.product_id == product.id)
        .order_by(ProductVariant.sku.asc())
        .first()
    )


@router.get("/categories")
async def list_categories(db: Session = Depends(get_db)):
    items = db.query(Category).order_by(Category.name.asc()).all()
    return response(status_code=200, message="Categorias obtenidas exitosamente", data=[{"id": i.id, "name": i.name} for i in items])


@router.post("/categories", status_code=status.HTTP_201_CREATED)
async def create_category(payload: NameCreate, db: Session = Depends(get_db), current_user: User = Depends(require_roles(RolEnum.administrador))):
    item = create_name_item(db, Category, payload)
    return response(status_code=201, message="Categoria creada exitosamente", data={"id": item.id, "name": item.name})


@router.put("/categories/{category_id}")
async def update_category(category_id: UUID, payload: NameCreate, db: Session = Depends(get_db), current_user: User = Depends(require_roles(RolEnum.administrador))):
    try:
        item = update_name_item(db, Category, category_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not item:
        raise HTTPException(status_code=404, detail=f"Categoria con id {category_id} no encontrada")
    return response(status_code=200, message="Categoria actualizada exitosamente", data={"id": item.id, "name": item.name})


@router.delete("/categories/{category_id}")
async def delete_category_route(category_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(require_roles(RolEnum.administrador))):
    try:
        deleted = delete_category(db, category_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Categoria con id {category_id} no encontrada")
    return response(status_code=200, message="Categoria eliminada exitosamente", data={"id": str(category_id)})


@router.get("/sizes")
async def list_sizes(db: Session = Depends(get_db)):
    items = db.query(Size).order_by(Size.name.asc()).all()
    return response(status_code=200, message="Tallas obtenidas exitosamente", data=[{"id": i.id, "name": i.name} for i in items])


@router.post("/sizes", status_code=status.HTTP_201_CREATED)
async def create_size(payload: NameCreate, db: Session = Depends(get_db), current_user: User = Depends(require_roles(RolEnum.administrador))):
    item = create_name_item(db, Size, payload)
    return response(status_code=201, message="Talla creada exitosamente", data={"id": item.id, "name": item.name})


@router.put("/sizes/{size_id}")
async def update_size(size_id: UUID, payload: NameCreate, db: Session = Depends(get_db), current_user: User = Depends(require_roles(RolEnum.administrador))):
    try:
        item = update_name_item(db, Size, size_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not item:
        raise HTTPException(status_code=404, detail=f"Talla con id {size_id} no encontrada")
    return response(status_code=200, message="Talla actualizada exitosamente", data={"id": item.id, "name": item.name})


@router.delete("/sizes/{size_id}")
async def delete_size_route(size_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(require_roles(RolEnum.administrador))):
    try:
        deleted = delete_size(db, size_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Talla con id {size_id} no encontrada")
    return response(status_code=200, message="Talla eliminada exitosamente", data={"id": str(size_id)})


@router.get("/colors")
async def list_colors(db: Session = Depends(get_db)):
    items = db.query(Color).order_by(Color.name.asc()).all()
    return response(status_code=200, message="Colores obtenidos exitosamente", data=[{"id": i.id, "name": i.name, "hex_code": i.hex_code} for i in items])


@router.post("/colors", status_code=status.HTTP_201_CREATED)
async def create_color_route(payload: ColorCreate, db: Session = Depends(get_db), current_user: User = Depends(require_roles(RolEnum.administrador))):
    item = create_color(db, payload)
    return response(status_code=201, message="Color creado exitosamente", data={"id": item.id, "name": item.name, "hex_code": item.hex_code})


@router.put("/colors/{color_id}")
async def update_color(color_id: UUID, payload: ColorCreate, db: Session = Depends(get_db), current_user: User = Depends(require_roles(RolEnum.administrador))):
    try:
        item = update_name_item(db, Color, color_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not item:
        raise HTTPException(status_code=404, detail=f"Color con id {color_id} no encontrado")
    return response(status_code=200, message="Color actualizado exitosamente", data={"id": item.id, "name": item.name, "hex_code": item.hex_code})


@router.delete("/colors/{color_id}")
async def delete_color_route(color_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(require_roles(RolEnum.administrador))):
    try:
        deleted = delete_color(db, color_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Color con id {color_id} no encontrado")
    return response(status_code=200, message="Color eliminado exitosamente", data={"id": str(color_id)})


@router.get("/seasons")
async def list_seasons(db: Session = Depends(get_db)):
    items = db.query(Season).order_by(Season.name.asc()).all()
    return response(status_code=200, message="Temporadas obtenidas exitosamente", data=[{"id": i.id, "name": i.name} for i in items])


@router.post("/seasons", status_code=status.HTTP_201_CREATED)
async def create_season(payload: NameCreate, db: Session = Depends(get_db), current_user: User = Depends(require_roles(RolEnum.administrador))):
    item = create_name_item(db, Season, payload)
    return response(status_code=201, message="Temporada creada exitosamente", data={"id": item.id, "name": item.name})


@router.put("/seasons/{season_id}")
async def update_season(season_id: UUID, payload: NameCreate, db: Session = Depends(get_db), current_user: User = Depends(require_roles(RolEnum.administrador))):
    try:
        item = update_name_item(db, Season, season_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not item:
        raise HTTPException(status_code=404, detail=f"Temporada con id {season_id} no encontrada")
    return response(status_code=200, message="Temporada actualizada exitosamente", data={"id": item.id, "name": item.name})


@router.delete("/seasons/{season_id}")
async def delete_season_route(season_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(require_roles(RolEnum.administrador))):
    try:
        deleted = delete_season(db, season_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Temporada con id {season_id} no encontrada")
    return response(status_code=200, message="Temporada eliminada exitosamente", data={"id": str(season_id)})


@router.get("/collections")
async def list_collections(db: Session = Depends(get_db)):
    items = db.query(Collection).order_by(Collection.name.asc()).all()
    return response(status_code=200, message="Colecciones obtenidas exitosamente", data=[{"id": i.id, "name": i.name, "season_id": i.season_id} for i in items])


@router.post("/collections", status_code=status.HTTP_201_CREATED)
async def create_collection_route(payload: CollectionCreate, db: Session = Depends(get_db), current_user: User = Depends(require_roles(RolEnum.administrador))):
    item = create_collection(db, payload)
    return response(status_code=201, message="Coleccion creada exitosamente", data={"id": item.id, "name": item.name, "season_id": item.season_id})


@router.put("/collections/{collection_id}")
async def update_collection(collection_id: UUID, payload: CollectionCreate, db: Session = Depends(get_db), current_user: User = Depends(require_roles(RolEnum.administrador))):
    try:
        item = update_name_item(db, Collection, collection_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not item:
        raise HTTPException(status_code=404, detail=f"Coleccion con id {collection_id} no encontrada")
    return response(status_code=200, message="Coleccion actualizada exitosamente", data={"id": item.id, "name": item.name, "season_id": item.season_id})


@router.delete("/collections/{collection_id}")
async def delete_collection_route(collection_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(require_roles(RolEnum.administrador))):
    try:
        deleted = delete_collection(db, collection_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Coleccion con id {collection_id} no encontrada")
    return response(status_code=200, message="Coleccion eliminada exitosamente", data={"id": str(collection_id)})


@router.get("/products")
async def list_products(
    db: Session = Depends(get_db),
    q: str | None = None,
    branch_id: UUID | None = None,
    category_id: UUID | None = None,
    size_id: UUID | None = None,
    color_id: UUID | None = None,
    season_id: UUID | None = None,
    collection_id: UUID | None = None,
    tenant_id: UUID | None = None,
):
    rows = list_public_products(db, branch_id, category_id, size_id, color_id, season_id, collection_id, q, tenant_id=tenant_id)
    return response(status_code=200, message="Productos obtenidos exitosamente", data=rows)


@router.get("/products/admin")
async def list_admin_products_route(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.administrador)),
):
    tenant_id = UUID(current_user["tenant_id"]) if current_user.get("tenant_id") else None
    return response(status_code=200, message="Productos administrativos obtenidos exitosamente", data=list_admin_products(db, tenant_id=tenant_id))


@router.get("/products/pending")
async def list_pending_products(db: Session = Depends(get_db), current_user: dict = Depends(require_roles(RolEnum.administrador))):
    tenant_id = UUID(current_user["tenant_id"]) if current_user.get("tenant_id") else None
    products = list_pending_products_service(db, tenant_id=tenant_id)
    return response(status_code=200, message="Productos pendientes obtenidos exitosamente", data=products)


@router.get("/products/{product_id}")
async def get_product(product_id: UUID, branch_id: UUID | None = None, db: Session = Depends(get_db)):
    product = get_public_product(db, product_id, branch_id)
    if not product:
        raise HTTPException(status_code=404, detail=f"Producto con id {product_id} no encontrado")
    return response(status_code=200, message="Producto obtenido exitosamente", data=product)


@router.post("/products/{product_id}/view", status_code=status.HTTP_201_CREATED)
async def record_product_view_route(
    product_id: UUID,
    payload: ProductViewContext | None = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.cliente)),
):
    if not record_product_view(db, UUID(current_user["sub"]), product_id, payload.variant_id if payload else None, payload.branch_id if payload else None):
        raise HTTPException(status_code=404, detail=f"Producto con id {product_id} no encontrado")
    return response(status_code=201, message="Product view recorded", data={"product_id": str(product_id)})


@router.post("/products", status_code=status.HTTP_201_CREATED)
async def create_product_route(payload: ProductCreate, db: Session = Depends(get_db), current_user: dict = Depends(require_roles(RolEnum.administrador))):
    _validate_product_provider_scope(db, payload.provider_id)
    tenant_id = UUID(current_user["tenant_id"]) if current_user.get("tenant_id") else None
    if not tenant_id and current_user.get("rol") != RolEnum.superadmin.value:
        raise HTTPException(status_code=400, detail="El administrador debe estar vinculado a una empresa")
    try:
        product = create_product(db, payload, provider_id=payload.provider_id, status=ProductStatusEnum.active, tenant_id=tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    serialized = serialize_product(db, product.id)
    return response(status_code=201, message="Producto creado exitosamente", data=serialized)


@router.put("/products/{product_id}")
async def update_product_route(product_id: UUID, payload: ProductCreate, db: Session = Depends(get_db), current_user: dict = Depends(require_roles(RolEnum.administrador))):
    _validate_product_provider_scope(db, payload.provider_id)
    tenant_id = UUID(current_user["tenant_id"]) if current_user.get("tenant_id") else None
    try:
        product = update_product(db, product_id, payload, tenant_id=tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not product:
        raise HTTPException(status_code=404, detail=f"Producto con id {product_id} no encontrado")
    serialized = serialize_product(db, product.id)
    return response(status_code=200, message="Producto actualizado exitosamente", data=serialized)


@router.delete("/products/{product_id}")
async def delete_product_route(product_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(require_roles(RolEnum.administrador))):
    tenant_id = UUID(current_user["tenant_id"]) if current_user.get("tenant_id") else None
    try:
        deleted = delete_product(db, product_id, tenant_id=tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Producto con id {product_id} no encontrado")
    return response(status_code=200, message="Producto eliminado exitosamente", data={"id": str(product_id)})


@router.post("/products/provider-submission", status_code=status.HTTP_201_CREATED)
async def submit_product_route(payload: ProductCreate, db: Session = Depends(get_db), current_payload: dict = Depends(require_roles(RolEnum.proveedor, RolEnum.administrador))):
    provider = db.query(Provider).filter(Provider.user_id == UUID(current_payload["sub"])).first()
    provider_id = provider.id if provider else None
    try:
        product = create_product(db, payload, provider_id=provider_id, status=ProductStatusEnum.pending)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    serialized = serialize_product(db, product.id)
    return response(status_code=201, message="Producto enviado exitosamente", data=serialized)


@router.patch("/products/{product_id}/status")
async def update_product_status_route(product_id: UUID, payload: ProductVariantStatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_roles(RolEnum.administrador))):
    variant = _resolve_legacy_variant(db, product_id)
    if not variant:
        raise HTTPException(status_code=404, detail=f"Producto con id {product_id} no encontrado")
    updated = update_product_status(db, variant.id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Producto con id {product_id} no encontrado")
    serialized = serialize_product(db, updated.product_id)
    return response(status_code=200, message="Producto actualizado exitosamente", data=serialized)


@router.patch("/variants/{variant_id}/status")
async def update_variant_status_route(variant_id: UUID, payload: ProductVariantStatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_roles(RolEnum.administrador))):
    variant = update_product_status(db, variant_id, payload)
    if not variant:
        raise HTTPException(status_code=404, detail=f"Variante con id {variant_id} no encontrada")
    serialized = serialize_product(db, variant.product_id)
    return response(status_code=200, message="Variante actualizada exitosamente", data=serialized)


@router.patch("/variants/{variant_id}/garment-points")
async def update_variant_garment_points_route(
    variant_id: UUID,
    payload: ProductVariantGarmentPointsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    variant = update_variant_garment_points(db, variant_id, payload)
    if not variant:
        raise HTTPException(status_code=404, detail=f"Variante con id {variant_id} no encontrada")
    serialized = serialize_product(db, variant.product_id)
    return response(status_code=200, message="Puntos de calibracion actualizados exitosamente", data=serialized)


@router.patch("/variants/{variant_id}/image")
async def update_variant_image_route(
    variant_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.administrador)),
):
    variant = get_variant_by_id(db, variant_id)
    if not variant:
        raise HTTPException(status_code=404, detail=f"Variante con id {variant_id} no encontrada")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="El archivo de imagen no puede estar vacio")

    old_public_id = None
    try:
        upload_result = upload_image(
            content,
            folder=f"{settings.cloudinary_folder}/product-variants/{variant.id}",
            public_id=file.filename.rsplit(".", 1)[0] if file.filename else None,
        )
        updated, old_public_id = update_variant_image(
            db,
            variant_id,
            upload_result["image_url"],
            upload_result["image_public_id"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        if "upload_result" in locals():
            delete_image(upload_result.get("image_public_id"))
        raise HTTPException(status_code=400, detail="No se pudo actualizar la imagen de la variante") from exc

    if old_public_id and old_public_id != upload_result["image_public_id"]:
        try:
            delete_image(old_public_id)
        except Exception:
            pass

    serialized = serialize_product(db, updated.product_id)
    return response(status_code=200, message="Imagen de variante actualizada exitosamente", data=serialized)


@router.delete("/variants/{variant_id}/image")
async def delete_variant_image_route(
    variant_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.administrador)),
):
    variant = get_variant_by_id(db, variant_id)
    if not variant:
        raise HTTPException(status_code=404, detail=f"Variante con id {variant_id} no encontrada")

    try:
        updated, old_public_id = clear_variant_image(db, variant_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="No se pudo eliminar la imagen de la variante") from exc

    if old_public_id:
        try:
            delete_image(old_public_id)
        except Exception:
            pass

    serialized = serialize_product(db, updated.product_id)
    return response(status_code=200, message="Imagen de variante eliminada exitosamente", data=serialized)


@router.get("/availability")
async def get_availability(
    product_id: UUID | None = None,
    variant_id: UUID | None = None,
    branch_id: UUID | None = None,
    tenant_id: UUID | None = None,
    db: Session = Depends(get_db),
):
    if not product_id and not variant_id:
        raise HTTPException(status_code=422, detail="Debes enviar product_id o variant_id")

    # Si se envía branch_id específico, mantenemos el contrato unitario histórico
    if branch_id is not None:
        if variant_id:
            quantity = get_branch_quantity(db, variant_id, branch_id)
            return response(
                status_code=200,
                message="Disponibilidad obtenida exitosamente",
                data={"variant_id": variant_id, "branch_id": branch_id, "quantity": quantity},
            )
        if product_id:
            product = db.query(Product).options(selectinload(Product.variants)).filter(Product.id == product_id).first()
            if not product:
                raise HTTPException(status_code=404, detail=f"Producto con id {product_id} no encontrado")
            variant_ids = [variant.id for variant in product.variants if variant.status == ProductStatusEnum.active]
            inventories = db.query(Inventory).filter(Inventory.variant_id.in_(variant_ids), Inventory.branch_id == branch_id).all()
            quantity = sum(available_quantity(inventory.quantity, inventory.reserved_quantity) for inventory in inventories)
            return response(
                status_code=200,
                message="Disponibilidad obtenida exitosamente",
                data={"product_id": product_id, "branch_id": branch_id, "quantity": quantity},
            )

    # CU10: branch_id is None -> Consulta de disponibilidad multisede por sucursales activas
    if variant_id:
        variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
        if not variant:
            raise HTTPException(status_code=404, detail=f"Variante con id {variant_id} no encontrada")
        product = db.query(Product).filter(Product.id == variant.product_id).first()
        target_tenant = tenant_id or getattr(variant, "tenant_id", None) or (product.tenant_id if product else None)

        branch_query = db.query(Branch).filter(Branch.is_active.is_(True))
        if target_tenant:
            branch_query = branch_query.filter(Branch.tenant_id == target_tenant)
        branches = branch_query.order_by(Branch.name.asc()).all()

        inventories = (
            db.query(Inventory)
            .filter(
                Inventory.variant_id == variant_id,
                Inventory.branch_id.in_([b.id for b in branches]),
            )
            .all()
            if branches
            else []
        )
        inv_map = {inv.branch_id: inv for inv in inventories}

        branch_list = []
        total_available = 0
        for b in branches:
            inv = inv_map.get(b.id)
            qty = inv.quantity if inv else 0
            res = inv.reserved_quantity if inv else 0
            avail = max(qty - res, 0)
            total_available += avail
            branch_list.append({
                "branch_id": b.id,
                "branch_name": b.name,
                "city": b.city,
                "address": b.address,
                "phone": b.phone,
                "opening_hours": b.opening_hours,
                "quantity": qty,
                "reserved_quantity": res,
                "available_quantity": avail,
            })

        return response(
            status_code=200,
            message="Disponibilidad en sucursales obtenida exitosamente",
            data={
                "variant_id": variant_id,
                "product_id": variant.product_id,
                "product_name": product.name if product else None,
                "sku": variant.sku,
                "total_available": total_available,
                "branches": branch_list,
            },
        )

    if product_id:
        product = db.query(Product).options(selectinload(Product.variants)).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Producto con id {product_id} no encontrado")
        target_tenant = tenant_id or product.tenant_id
        active_variant_ids = [v.id for v in product.variants if v.status == ProductStatusEnum.active]

        branch_query = db.query(Branch).filter(Branch.is_active.is_(True))
        if target_tenant:
            branch_query = branch_query.filter(Branch.tenant_id == target_tenant)
        branches = branch_query.order_by(Branch.name.asc()).all()

        inventories = (
            db.query(Inventory)
            .filter(
                Inventory.variant_id.in_(active_variant_ids),
                Inventory.branch_id.in_([b.id for b in branches]),
            )
            .all()
            if branches and active_variant_ids
            else []
        )

        branch_list = []
        total_available = 0
        for b in branches:
            b_invs = [inv for inv in inventories if inv.branch_id == b.id]
            qty = sum(inv.quantity for inv in b_invs)
            res = sum(inv.reserved_quantity for inv in b_invs)
            avail = sum(max(inv.quantity - inv.reserved_quantity, 0) for inv in b_invs)
            total_available += avail
            branch_list.append({
                "branch_id": b.id,
                "branch_name": b.name,
                "city": b.city,
                "address": b.address,
                "phone": b.phone,
                "opening_hours": b.opening_hours,
                "quantity": qty,
                "reserved_quantity": res,
                "available_quantity": avail,
            })

        return response(
            status_code=200,
            message="Disponibilidad en sucursales obtenida exitosamente",
            data={
                "product_id": product_id,
                "product_name": product.name,
                "total_available": total_available,
                "branches": branch_list,
            },
        )


@router.put("/inventory")
async def set_inventory(product_id: UUID | None = None, variant_id: UUID | None = None, branch_id: UUID | None = None, quantity: int = 0, db: Session = Depends(get_db), current_user: User = Depends(require_roles(RolEnum.administrador))):
    if branch_id is None:
        raise HTTPException(status_code=422, detail="branch_id es requerido")

    resolved_variant_id = variant_id
    if not resolved_variant_id and product_id:
        variant = _resolve_legacy_variant(db, product_id)
        if not variant:
            raise HTTPException(status_code=404, detail=f"Producto con id {product_id} no encontrado")
        resolved_variant_id = variant.id

    if not resolved_variant_id:
        raise HTTPException(status_code=422, detail="Debes enviar product_id o variant_id")

    inv = create_or_update_inventory(db, resolved_variant_id, branch_id, quantity)
    return response(status_code=200, message="Inventario actualizado exitosamente", data={"variant_id": inv.variant_id, "branch_id": inv.branch_id, "quantity": inv.quantity})


class OfflineBatchSyncRequest(BaseModel):
    tenant_id: UUID | None = None
    branch_id: UUID | None = None
    operations: list[dict]


@router.get("/offline-pack")
async def get_offline_catalog_pack(
    branch_id: UUID | None = None,
    tenant_id: UUID | None = None,
    db: Session = Depends(get_db),
):
    from app.models.catalog_cache import CatalogCache
    from datetime import datetime, timezone

    # 1. Obtener productos activos serializados filtrados por tenant
    filtered_rows = list_public_products(db, branch_id=branch_id, tenant_id=tenant_id)

    pack_data = {
        "version": 1,
        "tenant_id": str(tenant_id) if tenant_id else None,
        "branch_id": str(branch_id) if branch_id else None,
        "total_products": len(filtered_rows),
        "products": filtered_rows,
        "synced_at": datetime.now(timezone.utc).isoformat(),
    }

    # Guardar o actualizar snapshot en catalog_cache
    try:
        cache_entry = CatalogCache(
            tenant_id=tenant_id,
            version=1,
            payload=pack_data,
        )
        db.add(cache_entry)
        db.commit()
    except Exception:
        db.rollback()

    return response(
        status_code=200,
        message="Paquete de catálogo offline descargado exitosamente",
        data=pack_data,
    )


@router.post("/offline-sync", status_code=status.HTTP_201_CREATED)
async def sync_offline_operations(
    payload: OfflineBatchSyncRequest,
    db: Session = Depends(get_db),
):
    from app.models.offline_operation import OfflineOperation
    from datetime import datetime, timezone

    processed = []
    skipped = []

    for op in payload.operations:
        client_op_id = op.get("client_operation_id")
        op_type = op.get("operation_type", "GENERIC_OFFLINE")
        op_payload = op.get("payload", {})

        # Validar idempotencia si tiene client_operation_id
        if client_op_id:
            existing = db.query(OfflineOperation).filter(OfflineOperation.client_operation_id == client_op_id).first()
            if existing:
                skipped.append({"client_operation_id": client_op_id, "reason": "ALREADY_SYNCED"})
                continue

        record = OfflineOperation(
            tenant_id=payload.tenant_id,
            branch_id=payload.branch_id,
            operation_type=op_type,
            client_operation_id=client_op_id,
            payload=op_payload,
            synced=True,
            synced_at=datetime.now(timezone.utc),
        )
        db.add(record)
        processed.append(client_op_id or str(record.id))

    db.commit()

    return response(
        status_code=201,
        message="Operaciones offline sincronizadas exitosamente",
        data={
            "processed_count": len(processed),
            "skipped_count": len(skipped),
            "processed": processed,
            "skipped": skipped,
        },
    )
