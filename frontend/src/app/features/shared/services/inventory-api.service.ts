import { Injectable, inject } from '@angular/core';

import { ApiResponse } from '../../../core/models/api.model';
import { ApiService } from '../../../core/services/api.service';
import {
  CancelTransferPayload,
  CreateTransferPayload,
  InventoryBranchStock,
  InventoryConsolidatedStock,
  InventoryMovement,
  InventoryMovementRequest,
  InventoryMutationResponse,
  InventoryThresholdUpdate,
  InventoryTransfer,
  InventoryTransferRequest,
  ReceiveTransferPayload,
} from '../models/inventory.model';

@Injectable({ providedIn: 'root' })
export class InventoryApiService {
  private readonly api = inject(ApiService);

  getConsolidatedStock() {
    return this.api.get<ApiResponse<InventoryConsolidatedStock[]>>('/inventory/consolidated');
  }

  getBranchStock(branchId: string) {
    return this.api.get<ApiResponse<InventoryBranchStock[]>>(`/inventory/branches/${branchId}`);
  }

  getMovements(params?: { branch_id?: string; variant_id?: string; movement_type?: string; limit?: number }) {
    const query = params
      ? '?' +
        Object.entries(params)
          .filter(([, value]) => value !== undefined && value !== '')
          .map(([key, value]) => `${key}=${encodeURIComponent(String(value))}`)
          .join('&')
      : '';
    return this.api.get<ApiResponse<InventoryMovement[]>>(`/inventory/movements${query}`);
  }

  registerIncome(payload: InventoryMovementRequest) {
    return this.api.post<ApiResponse<InventoryMutationResponse>>('/inventory/movements/income', payload);
  }

  registerOutcome(payload: InventoryMovementRequest) {
    return this.api.post<ApiResponse<InventoryMutationResponse>>('/inventory/movements/outcome', payload);
  }

  registerTransfer(payload: InventoryTransferRequest) {
    return this.api.post<ApiResponse<InventoryMutationResponse>>('/inventory/movements/transfer', payload);
  }

  updateMinimumStock(payload: InventoryThresholdUpdate) {
    return this.api.patch<ApiResponse<InventoryMutationResponse>>('/inventory/threshold', payload);
  }

  // Métodos CU11: Traslado de Mercadería entre Sucursales (Presentación 2)
  getTransfers(params?: { branch_id?: string; status?: string }) {
    const query = params
      ? '?' +
        Object.entries(params)
          .filter(([, value]) => value !== undefined && value !== '')
          .map(([key, value]) => `${key}=${encodeURIComponent(String(value))}`)
          .join('&')
      : '';
    return this.api.get<ApiResponse<InventoryTransfer[]>>(`/inventory/transfers${query}`);
  }

  getTransferDetail(transferId: string) {
    return this.api.get<ApiResponse<InventoryTransfer>>(`/inventory/transfers/${transferId}`);
  }

  createTransfer(payload: CreateTransferPayload) {
    return this.api.post<ApiResponse<InventoryTransfer>>('/inventory/transfers', payload);
  }

  receiveTransfer(transferId: string, payload?: ReceiveTransferPayload) {
    return this.api.post<ApiResponse<InventoryTransfer>>(`/inventory/transfers/${transferId}/receive`, payload ?? {});
  }

  cancelTransfer(transferId: string, reason?: string) {
    return this.api.post<ApiResponse<InventoryTransfer>>(`/inventory/transfers/${transferId}/cancel`, {
      reason: reason || 'Cancelado por el usuario',
    });
  }
}
