from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_branch_id, get_current_user, require_roles
from app.core.database import get_db
from app.core.tenant_context import get_tenant_id_from_header
from app.schemas.enums import RolEnum
from app.packages.p1_gestion_usuarios_acceso.models.user import User
from app.packages.p4_gestion_compras_reservas.schemas.order_schema import OrderDispatchRequest, OrderDispatchResponse
from app.packages.p4_gestion_compras_reservas.schemas.payment_schema import CollectCashRequest
from app.packages.p4_gestion_compras_reservas.services.order_service import (
    cancel_order,
    collect_cash,
    dispatch_order,
    get_order,
    get_order_by_tracking,
    list_orders,
    list_orders_by_branch,
    mark_order_ready,
)
from app.utils.response import response


router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("/me")
async def list_my_orders_route(
    db: Session = Depends(get_db),
    tenant_id: UUID | None = Depends(get_tenant_id_from_header),
    current_user: dict = Depends(require_roles(RolEnum.cliente)),
):
    orders = list_orders(db, UUID(current_user["sub"]), tenant_id=tenant_id)
    return response(status_code=200, message="Pedidos obtenidos exitosamente", data=orders)


@router.get("/branch")
async def list_branch_orders_route(
    db: Session = Depends(get_db),
    tenant_id: UUID | None = Depends(get_tenant_id_from_header),
    current_branch_id: UUID | None = Depends(get_current_branch_id),
    _: dict = Depends(require_roles(RolEnum.encargado)),
):
    if current_branch_id is None:
        raise HTTPException(status_code=422, detail="El encargado no tiene sucursal asignada")
    return response(status_code=200, message="Pedidos de sucursal obtenidos", data=list_orders_by_branch(db, current_branch_id, tenant_id=tenant_id))


@router.get("/tracking/{tracking_number}")
async def track_order_route(
    tracking_number: str,
    db: Session = Depends(get_db),
    tenant_id: UUID | None = Depends(get_tenant_id_from_header),
):
    """
    CU12: Consulta pública/cliente de rastreo de pedido por guía tracking_number.
    """
    order = get_order_by_tracking(db, tracking_number, tenant_id=tenant_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No se encontró ningún pedido con la guía '{tracking_number}'")
    return response(status_code=200, message="Seguimiento de pedido obtenido exitosamente", data=order)


@router.get("/{order_id}")
async def get_order_route(
    order_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID | None = Depends(get_tenant_id_from_header),
    current_user: dict = Depends(require_roles(RolEnum.cliente)),
):
    order = get_order(db, UUID(current_user["sub"]), order_id, tenant_id=tenant_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Pedido con id {order_id} no encontrado")
    return response(status_code=200, message="Pedido obtenido exitosamente", data=order)


@router.post("/{order_id}/cancel")
async def cancel_order_route(
    order_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID | None = Depends(get_tenant_id_from_header),
    current_user: dict = Depends(require_roles(RolEnum.cliente)),
):
    try:
        order = cancel_order(db, UUID(current_user["sub"]), order_id, tenant_id=tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
    return response(status_code=200, message="Pedido cancelado", data=order)


@router.post("/{order_id}/ready")
async def mark_order_ready_route(
    order_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID | None = Depends(get_tenant_id_from_header),
    current_branch_id: UUID | None = Depends(get_current_branch_id),
    _: dict = Depends(require_roles(RolEnum.encargado)),
):
    if current_branch_id is None:
        raise HTTPException(status_code=422, detail="El encargado no tiene sucursal asignada")
    try:
        order = mark_order_ready(db, order_id, current_branch_id, tenant_id=tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado en tu sucursal")
    return response(status_code=200, message="Pedido marcado como listo", data=order)


@router.post("/{order_id}/dispatch")
async def dispatch_order_route(
    order_id: UUID,
    payload: OrderDispatchRequest | None = None,
    db: Session = Depends(get_db),
    tenant_id: UUID | None = Depends(get_tenant_id_from_header),
    current_user: User = Depends(get_current_user),
    _: dict = Depends(require_roles(RolEnum.administrador, RolEnum.encargado)),
):
    """
    CU12: Despachar pedido con validación estricta de Política de Negocio 3 (Condicionado a pago previo en Stripe).
    """
    effective_tenant_id = tenant_id or current_user.tenant_id
    shipping_notes = payload.shipping_notes if payload else None
    try:
        dispatch_result = dispatch_order(
            db=db,
            order_id=order_id,
            dispatcher_id=current_user.id,
            tenant_id=effective_tenant_id,
            shipping_notes=shipping_notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return response(
        status_code=200,
        message="Pedido despachado exitosamente",
        data=OrderDispatchResponse(**dispatch_result).model_dump(),
    )


@router.post("/{order_id}/collect-cash")
async def collect_cash_route(
    order_id: UUID,
    payload: CollectCashRequest,
    db: Session = Depends(get_db),
    tenant_id: UUID | None = Depends(get_tenant_id_from_header),
    cashier: User = Depends(get_current_user),
    _: dict = Depends(require_roles(RolEnum.cajero)),
):
    try:
        order = collect_cash(db, order_id, payload.pickup_code, cashier.branch_id, cashier.id, tenant_id=tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return response(status_code=200, message="Pedido cobrado y entregado", data=order)
