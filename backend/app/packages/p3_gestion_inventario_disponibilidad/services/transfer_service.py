from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc

from app.packages.p1_gestion_usuarios_acceso.models.branch import Branch
from app.packages.p1_gestion_usuarios_acceso.models.user import User
from app.packages.p2_gestion_productos_catalogo.models.product import Product
from app.packages.p2_gestion_productos_catalogo.models.product_variant import ProductVariant
from app.packages.p2_gestion_productos_catalogo.models.size import Size
from app.packages.p2_gestion_productos_catalogo.models.color import Color
from app.packages.p3_gestion_inventario_disponibilidad.models.inventory import Inventory
from app.packages.p3_gestion_inventario_disponibilidad.models.inventory_movement import InventoryMovement
from app.packages.p3_gestion_inventario_disponibilidad.models.inventory_transfer import (
    InventoryTransfer,
    InventoryTransferItem,
)
from app.packages.p3_gestion_inventario_disponibilidad.schemas.inventory_schema import InventoryMovementTypeEnum
from app.packages.p3_gestion_inventario_disponibilidad.schemas.transfer_schema import (
    InventoryTransferCancel,
    InventoryTransferCreate,
    InventoryTransferItemRead,
    InventoryTransferRead,
    InventoryTransferReceive,
)
from app.schemas.enums import RolEnum


def _get_or_create_inventory(db: Session, variant_id: UUID, branch_id: UUID, tenant_id: UUID | None = None) -> Inventory:
    inventory = (
        db.query(Inventory)
        .filter(Inventory.variant_id == variant_id, Inventory.branch_id == branch_id)
        .first()
    )
    if not inventory:
        inventory = Inventory(
            variant_id=variant_id,
            branch_id=branch_id,
            tenant_id=tenant_id,
            quantity=0,
            reserved_quantity=0,
            minimum_stock=0,
        )
        db.add(inventory)
        db.flush()
    return inventory


def create_and_dispatch_transfer(
    db: Session,
    payload: InventoryTransferCreate,
    current_user: dict,
) -> InventoryTransfer:
    tenant_id_str = current_user.get("tenant_id")
    if not tenant_id_str:
        raise ValueError("Tenant ID requerido en la sesión")
    tenant_id = UUID(str(tenant_id_str))

    user_id_str = current_user.get("sub")
    user_id = UUID(str(user_id_str)) if user_id_str else None
    user_role = current_user.get("rol")

    if payload.from_branch_id == payload.to_branch_id:
        raise ValueError("La sucursal origen y destino no pueden ser iguales")

    # 1. Validar que ambas sucursales pertenezcan al mismo tenant
    from_branch = db.query(Branch).filter(Branch.id == payload.from_branch_id, Branch.tenant_id == tenant_id).first()
    if not from_branch:
        raise ValueError("La sucursal origen no existe o no pertenece a tu empresa")
    if not from_branch.is_active:
        raise ValueError("La sucursal origen está inactiva")

    to_branch = db.query(Branch).filter(Branch.id == payload.to_branch_id, Branch.tenant_id == tenant_id).first()
    if not to_branch:
        raise ValueError("La sucursal destino no existe o no pertenece a tu empresa")
    if not to_branch.is_active:
        raise ValueError("La sucursal destino está inactiva")

    # 2. Si el rol es encargado, validar que pertenezca a la sucursal emisora
    if user_role == RolEnum.encargado.value:
        assigned_branch = current_user.get("branch_id")
        if not assigned_branch or UUID(str(assigned_branch)) != payload.from_branch_id:
            raise PermissionError("Solo puedes despachar traslados desde tu sucursal asignada")

    # 3. Generar número de transferencia correlativo
    year = datetime.now(timezone.utc).year
    total_transfers = db.query(InventoryTransfer).filter(InventoryTransfer.tenant_id == tenant_id).count()
    transfer_number = f"TRF-{year}-{(total_transfers + 1):04d}"

    # 4. Validar stock disponible de cada variante y descontar de origen
    transfer_items = []
    try:
        for item in payload.items:
            variant = (
                db.query(ProductVariant)
                .join(Product, Product.id == ProductVariant.product_id)
                .filter(
                    ProductVariant.id == item.variant_id,
                    Product.tenant_id == tenant_id,
                )
                .first()
            )
            if not variant:
                raise ValueError(f"Variante {item.variant_id} no encontrada en esta empresa")

            inv = _get_or_create_inventory(db, item.variant_id, payload.from_branch_id, tenant_id=tenant_id)
            available = max((inv.quantity or 0) - (inv.reserved_quantity or 0), 0)
            if available < item.quantity:
                raise ValueError(
                    f"Stock insuficiente para {variant.sku or 'prenda'}. Disponible: {available}, Solicitado: {item.quantity}"
                )

            # Descontar del origen
            inv.quantity -= item.quantity

            # Asentar movimiento de salida en auditoría
            movement = InventoryMovement(
                variant_id=item.variant_id,
                branch_id=payload.from_branch_id,
                movement_type=InventoryMovementTypeEnum.transfer_out,
                quantity=item.quantity,
                reference_branch_id=payload.to_branch_id,
                note=f"Despacho de traslado {transfer_number} hacia {to_branch.name}",
                created_by=user_id,
            )
            db.add(movement)

            transfer_item = InventoryTransferItem(
                variant_id=item.variant_id,
                quantity=item.quantity,
            )
            transfer_items.append(transfer_item)

        # 5. Crear orden de traslado en estado EN_TRANSITO
        transfer = InventoryTransfer(
            tenant_id=tenant_id,
            transfer_number=transfer_number,
            from_branch_id=payload.from_branch_id,
            to_branch_id=payload.to_branch_id,
            status="EN_TRANSITO",
            requested_by=user_id,
            notes=payload.notes,
            items=transfer_items,
        )
        db.add(transfer)
        db.commit()
        db.refresh(transfer)
        return transfer
    except Exception:
        db.rollback()
        raise


def receive_transfer(
    db: Session,
    transfer_id: UUID,
    payload: InventoryTransferReceive,
    current_user: dict,
) -> InventoryTransfer:
    tenant_id_str = current_user.get("tenant_id")
    if not tenant_id_str:
        raise ValueError("Tenant ID requerido en la sesión")
    tenant_id = UUID(str(tenant_id_str))

    user_id_str = current_user.get("sub")
    user_id = UUID(str(user_id_str)) if user_id_str else None
    user_role = current_user.get("rol")

    transfer = (
        db.query(InventoryTransfer)
        .filter(InventoryTransfer.id == transfer_id, InventoryTransfer.tenant_id == tenant_id)
        .first()
    )
    if not transfer:
        raise ValueError("Orden de traslado no encontrada")

    if transfer.status != "EN_TRANSITO":
        raise ValueError(f"El traslado no puede recibirse en estado {transfer.status}")

    # Si es encargado, validar que pertenezca a la sucursal destino
    if user_role == RolEnum.encargado.value:
        assigned_branch = current_user.get("branch_id")
        if not assigned_branch or UUID(str(assigned_branch)) != transfer.to_branch_id:
            raise PermissionError("Solo el encargado de la sucursal receptora puede confirmar la recepción")

    try:
        from_branch_name = transfer.from_branch.name if transfer.from_branch else "Origen"

        for item in transfer.items:
            dest_inv = _get_or_create_inventory(db, item.variant_id, transfer.to_branch_id, tenant_id=tenant_id)
            dest_inv.quantity = (dest_inv.quantity or 0) + item.quantity
            item.received_quantity = item.quantity

            # Asentar movimiento de entrada en auditoría
            movement = InventoryMovement(
                variant_id=item.variant_id,
                branch_id=transfer.to_branch_id,
                movement_type=InventoryMovementTypeEnum.transfer_in,
                quantity=item.quantity,
                reference_branch_id=transfer.from_branch_id,
                note=f"Recepción de traslado {transfer.transfer_number} desde {from_branch_name}",
                created_by=user_id,
            )
            db.add(movement)

        transfer.status = "COMPLETADO"
        transfer.received_by = user_id
        transfer.received_at = datetime.now(timezone.utc)
        if payload.notes:
            transfer.notes = f"{transfer.notes or ''} | Recepción: {payload.notes}".strip(" |")

        db.commit()
        db.refresh(transfer)
        return transfer
    except Exception:
        db.rollback()
        raise


def cancel_transfer(
    db: Session,
    transfer_id: UUID,
    payload: InventoryTransferCancel,
    current_user: dict,
) -> InventoryTransfer:
    tenant_id_str = current_user.get("tenant_id")
    if not tenant_id_str:
        raise ValueError("Tenant ID requerido en la sesión")
    tenant_id = UUID(str(tenant_id_str))

    user_role = current_user.get("rol")
    user_id_str = current_user.get("sub")
    user_id = UUID(str(user_id_str)) if user_id_str else None

    transfer = (
        db.query(InventoryTransfer)
        .filter(InventoryTransfer.id == transfer_id, InventoryTransfer.tenant_id == tenant_id)
        .first()
    )
    if not transfer:
        raise ValueError("Orden de traslado no encontrada")

    if transfer.status not in ("EN_TRANSITO", "SOLICITADO"):
        raise ValueError(f"No se puede cancelar un traslado en estado {transfer.status}")

    if user_role == RolEnum.encargado.value:
        assigned_branch = current_user.get("branch_id")
        assigned_uuid = UUID(str(assigned_branch)) if assigned_branch else None
        if assigned_uuid not in (transfer.from_branch_id, transfer.to_branch_id):
            raise PermissionError("No tienes permisos para cancelar este traslado")

    try:
        # Restituir stock a la sucursal origen
        for item in transfer.items:
            source_inv = _get_or_create_inventory(db, item.variant_id, transfer.from_branch_id, tenant_id=tenant_id)
            source_inv.quantity = (source_inv.quantity or 0) + item.quantity

            movement = InventoryMovement(
                variant_id=item.variant_id,
                branch_id=transfer.from_branch_id,
                movement_type=InventoryMovementTypeEnum.income,
                quantity=item.quantity,
                reference_branch_id=transfer.to_branch_id,
                note=f"Restitución por traslado cancelado {transfer.transfer_number}",
                created_by=user_id,
            )
            db.add(movement)

        transfer.status = "CANCELADO"
        if payload.reason:
            transfer.notes = f"{transfer.notes or ''} | Cancelación: {payload.reason}".strip(" |")

        db.commit()
        db.refresh(transfer)
        return transfer
    except Exception:
        db.rollback()
        raise


def list_transfers(
    db: Session,
    tenant_id: UUID,
    branch_id: UUID | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[InventoryTransferRead]:
    query = (
        db.query(InventoryTransfer)
        .filter(InventoryTransfer.tenant_id == tenant_id)
    )

    if branch_id:
        query = query.filter(
            or_(
                InventoryTransfer.from_branch_id == branch_id,
                InventoryTransfer.to_branch_id == branch_id,
            )
        )

    if status:
        query = query.filter(InventoryTransfer.status == status)

    transfers = query.order_by(desc(InventoryTransfer.created_at)).limit(limit).all()

    results = []
    for t in transfers:
        items_read = []
        for it in t.items:
            variant = it.variant
            product = variant.product if variant else None
            size = variant.size if variant and hasattr(variant, "size") else None
            color = variant.color if variant and hasattr(variant, "color") else None
            items_read.append(
                InventoryTransferItemRead(
                    id=it.id,
                    variant_id=it.variant_id,
                    variant_sku=variant.sku if variant else "SKU-N/A",
                    product_name=product.name if product else "Prenda",
                    size_name=size.name if size else None,
                    color_name=color.name if color else None,
                    quantity=it.quantity,
                    received_quantity=it.received_quantity,
                )
            )

        results.append(
            InventoryTransferRead(
                id=t.id,
                tenant_id=t.tenant_id,
                transfer_number=t.transfer_number,
                from_branch_id=t.from_branch_id,
                from_branch_name=t.from_branch.name if t.from_branch else "N/A",
                to_branch_id=t.to_branch_id,
                to_branch_name=t.to_branch.name if t.to_branch else "N/A",
                status=t.status,
                requested_by=t.requested_by,
                requested_by_name=t.requester.name if t.requester and hasattr(t.requester, "name") else "Usuario",
                received_by=t.received_by,
                received_by_name=t.receiver.name if t.receiver and hasattr(t.receiver, "name") else None,
                requested_at=t.requested_at,
                received_at=t.received_at,
                notes=t.notes,
                items=items_read,
            )
        )
    return results


def get_transfer_detail(
    db: Session,
    transfer_id: UUID,
    tenant_id: UUID,
) -> InventoryTransferRead:
    t = (
        db.query(InventoryTransfer)
        .filter(InventoryTransfer.id == transfer_id, InventoryTransfer.tenant_id == tenant_id)
        .first()
    )
    if not t:
        raise ValueError("Traslado no encontrado")

    items_read = []
    for it in t.items:
        variant = it.variant
        product = variant.product if variant else None
        size = variant.size if variant and hasattr(variant, "size") else None
        color = variant.color if variant and hasattr(variant, "color") else None
        items_read.append(
            InventoryTransferItemRead(
                id=it.id,
                variant_id=it.variant_id,
                variant_sku=variant.sku if variant else "SKU-N/A",
                product_name=product.name if product else "Prenda",
                size_name=size.name if size else None,
                color_name=color.name if color else None,
                quantity=it.quantity,
                received_quantity=it.received_quantity,
            )
        )

    return InventoryTransferRead(
        id=t.id,
        tenant_id=t.tenant_id,
        transfer_number=t.transfer_number,
        from_branch_id=t.from_branch_id,
        from_branch_name=t.from_branch.name if t.from_branch else "N/A",
        to_branch_id=t.to_branch_id,
        to_branch_name=t.to_branch.name if t.to_branch else "N/A",
        status=t.status,
        requested_by=t.requested_by,
        requested_by_name=t.requester.name if t.requester and hasattr(t.requester, "name") else "Usuario",
        received_by=t.received_by,
        received_by_name=t.receiver.name if t.receiver and hasattr(t.receiver, "name") else None,
        requested_at=t.requested_at,
        received_at=t.received_at,
        notes=t.notes,
        items=items_read,
    )
