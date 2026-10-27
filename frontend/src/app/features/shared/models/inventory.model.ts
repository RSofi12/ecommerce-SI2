export interface InventoryBranch {
  id: string;
  name: string;
  city: string;
  is_default: boolean;
}

export interface InventoryBranchStock {
  variant_id: string;
  branch_id: string;
  branch_name: string;
  product_id: string;
  product_name: string;
  variant_sku: string;
  variant_price: string;
  image_url: string | null;
  image_public_id: string | null;
  status: string;
  size_id: string | null;
  color_id: string | null;
  size_name: string | null;
  color_name: string | null;
  quantity: number;
  reserved_quantity: number;
  minimum_stock: number;
  available_quantity: number;
}

export interface InventoryConsolidatedBranch {
  branch_id: string;
  branch_name: string;
  quantity: number;
  reserved_quantity: number;
  available_quantity: number;
  minimum_stock: number;
}

export interface InventoryConsolidatedStock {
  variant_id: string;
  product_id: string;
  product_name: string;
  variant_sku: string;
  variant_price: string;
  image_url: string | null;
  image_public_id: string | null;
  status: string;
  size_id: string | null;
  color_id: string | null;
  size_name: string | null;
  color_name: string | null;
  quantity: number;
  reserved_quantity: number;
  available_quantity: number;
  branches: InventoryConsolidatedBranch[];
}

export interface InventoryMovement {
  id: string;
  variant_id: string;
  branch_id: string;
  movement_type: 'income' | 'outcome' | 'transfer_in' | 'transfer_out';
  quantity: number;
  reference_branch_id: string | null;
  note: string | null;
  created_by: string | null;
  created_at: string;
}

export interface InventoryMovementRequest {
  variant_id: string;
  branch_id: string;
  quantity: number;
  note?: string;
}

export interface InventoryTransferRequest {
  variant_id: string;
  from_branch_id: string;
  to_branch_id: string;
  quantity: number;
  note?: string;
}

export interface InventoryThresholdUpdate {
  variant_id: string;
  branch_id: string;
  minimum_stock: number;
}

export interface InventoryMutationResponse {
  movement?: string;
  movements?: string[];
  variant_id: string;
  branch_id?: string;
  from_branch_id?: string;
  to_branch_id?: string;
  quantity?: number;
  minimum_stock?: number;
}


export type TransferStatus = 'SOLICITADO' | 'EN_TRANSITO' | 'COMPLETADO' | 'CANCELADO';

export interface InventoryTransferItem {
  id: string;
  transfer_id: string;
  variant_id: string;
  variant_sku?: string | null;
  product_name?: string | null;
  size_name?: string | null;
  color_name?: string | null;
  quantity: number;
  received_quantity?: number | null;
  created_at: string;
}

export interface InventoryTransfer {
  id: string;
  tenant_id: string;
  transfer_number: string;
  from_branch_id: string;
  from_branch_name?: string | null;
  to_branch_id: string;
  to_branch_name?: string | null;
  status: TransferStatus;
  requested_by: string;
  requested_by_name?: string | null;
  received_by?: string | null;
  received_by_name?: string | null;
  requested_at: string;
  received_at?: string | null;
  notes?: string | null;
  items: InventoryTransferItem[];
  created_at: string;
  updated_at?: string;
}

export interface CreateTransferPayload {
  from_branch_id: string;
  to_branch_id: string;
  items: {
    variant_id: string;
    quantity: number;
  }[];
  notes?: string;
}

export interface ReceiveTransferPayload {
  received_quantities?: Record<string, number>;
  notes?: string;
}

export interface CancelTransferPayload {
  reason?: string;
}
