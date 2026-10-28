import { Injectable, inject } from '@angular/core';

import { ApiResponse } from '../../../core/models/api.model';
import { ApiService } from '../../../core/services/api.service';
import { Order, OrderDispatchResponse } from '../models/order.model';

export interface CheckoutRequestPayload {
  pickup_branch_id?: string;
  delivery_type?: 'RETIRO_TIENDA' | 'ENVIO_DOMICILIO' | string;
  shipping_address?: string;
}

export interface StripeCheckoutResponseData {
  order_id: string;
  client_secret: string;
  payment_intent_id: string;
  pickup_expires_at: string;
  delivery_type?: string;
  shipping_address?: string | null;
  tracking_number?: string | null;
}

@Injectable({ providedIn: 'root' })
export class CheckoutApiService {
  private readonly api = inject(ApiService);

  checkoutCash(payload: CheckoutRequestPayload) {
    return this.api.post<ApiResponse<Order>>('/payments/cash/checkout', payload);
  }

  checkoutStripe(payload: CheckoutRequestPayload) {
    return this.api.post<ApiResponse<StripeCheckoutResponseData>>('/payments/stripe/checkout', payload);
  }

  getOrder(orderId: string) {
    return this.api.get<ApiResponse<Order>>(`/orders/${orderId}`);
  }

  listOrders() {
    return this.api.get<ApiResponse<Order[]>>('/orders/me');
  }

  listBranchOrders() {
    return this.api.get<ApiResponse<Order[]>>('/orders/branch');
  }

  markReady(orderId: string) {
    return this.api.post<ApiResponse<Order>>(`/orders/${orderId}/ready`, {});
  }

  dispatchOrder(orderId: string, payload: { shipping_notes?: string } = {}) {
    return this.api.post<ApiResponse<OrderDispatchResponse>>(`/orders/${orderId}/dispatch`, payload);
  }

  trackOrder(trackingNumber: string) {
    return this.api.get<ApiResponse<Order>>(`/orders/tracking/${trackingNumber}`);
  }
}
