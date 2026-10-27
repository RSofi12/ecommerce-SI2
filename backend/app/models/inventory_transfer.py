# Legacy re-export for backward compatibility
from app.packages.p3_gestion_inventario_disponibilidad.models.inventory_transfer import (
    InventoryTransfer,
    InventoryTransferItem,
)

__all__ = ["InventoryTransfer", "InventoryTransferItem"]
