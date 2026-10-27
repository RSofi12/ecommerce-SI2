from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.core.database import get_db
from app.packages.p3_gestion_inventario_disponibilidad.schemas.transfer_schema import (
    InventoryTransferCancel,
    InventoryTransferCreate,
    InventoryTransferReceive,
)
from app.packages.p3_gestion_inventario_disponibilidad.services.transfer_service import (
    cancel_transfer,
    create_and_dispatch_transfer,
    get_transfer_detail,
    list_transfers,
    receive_transfer,
)
from app.schemas.enums import RolEnum
from app.utils.response import response


router = APIRouter(prefix="/inventory/transfers", tags=["Inventory Transfers (CU11)"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_transfer_endpoint(
    payload: InventoryTransferCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.administrador, RolEnum.encargado)),
):
    try:
        transfer = create_and_dispatch_transfer(db, payload, current_user)
        tenant_id = UUID(str(current_user["tenant_id"]))
        result = get_transfer_detail(db, transfer.id, tenant_id)
        return response(
            status_code=status.HTTP_201_CREATED,
            message="Orden de traslado creada y despachada en tránsito exitosamente",
            data=result.model_dump(),
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("", status_code=status.HTTP_200_OK)
async def list_transfers_endpoint(
    branch_id: UUID | None = None,
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.administrador, RolEnum.encargado)),
):
    tenant_id_str = current_user.get("tenant_id")
    if not tenant_id_str:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant ID no encontrado")
    tenant_id = UUID(str(tenant_id_str))

    # Si es encargado y no especificó branch_id, filtramos por su sucursal asignada
    user_role = current_user.get("rol")
    if user_role == RolEnum.encargado.value and not branch_id:
        assigned_branch = current_user.get("branch_id")
        if assigned_branch:
            branch_id = UUID(str(assigned_branch))

    transfers = list_transfers(db, tenant_id=tenant_id, branch_id=branch_id, status=status_filter, limit=limit)
    return response(
        status_code=status.HTTP_200_OK,
        message="Órdenes de traslado obtenidas exitosamente",
        data=[t.model_dump() for t in transfers],
    )


@router.get("/{transfer_id}", status_code=status.HTTP_200_OK)
async def get_transfer_detail_endpoint(
    transfer_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.administrador, RolEnum.encargado)),
):
    tenant_id_str = current_user.get("tenant_id")
    if not tenant_id_str:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant ID no encontrado")
    tenant_id = UUID(str(tenant_id_str))

    try:
        transfer = get_transfer_detail(db, transfer_id, tenant_id)
        return response(
            status_code=status.HTTP_200_OK,
            message="Detalle de traslado obtenido exitosamente",
            data=transfer.model_dump(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{transfer_id}/receive", status_code=status.HTTP_200_OK)
async def receive_transfer_endpoint(
    transfer_id: UUID,
    payload: InventoryTransferReceive = InventoryTransferReceive(),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.administrador, RolEnum.encargado)),
):
    try:
        transfer = receive_transfer(db, transfer_id, payload, current_user)
        tenant_id = UUID(str(current_user["tenant_id"]))
        result = get_transfer_detail(db, transfer.id, tenant_id)
        return response(
            status_code=status.HTTP_200_OK,
            message="Recepción de mercadería confirmada exitosamente en destino",
            data=result.model_dump(),
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{transfer_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_transfer_endpoint(
    transfer_id: UUID,
    payload: InventoryTransferCancel = InventoryTransferCancel(),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.administrador, RolEnum.encargado)),
):
    try:
        transfer = cancel_transfer(db, transfer_id, payload, current_user)
        tenant_id = UUID(str(current_user["tenant_id"]))
        result = get_transfer_detail(db, transfer.id, tenant_id)
        return response(
            status_code=status.HTTP_200_OK,
            message="Orden de traslado cancelada y stock restituido al origen",
            data=result.model_dump(),
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
