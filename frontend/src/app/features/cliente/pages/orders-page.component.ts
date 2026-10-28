import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { firstValueFrom } from 'rxjs';
import { toast } from '@spartan-ng/brain/sonner';

import { HlmBadgeImports } from '../../../components/badge/src';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmInputImports } from '../../../components/input/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { downloadSimplePdf } from '../../../core/utils/simple-pdf.util';
import { CheckoutApiService } from '../../shared/services/checkout-api.service';
import { Order, FulfillmentStatusEnum } from '../../shared/models/order.model';

@Component({
  selector: 'app-orders-page',
  standalone: true,
  imports: [CommonModule, FormsModule, HlmButton, ...HlmBadgeImports, ...HlmCardImports, ...HlmInputImports],
  templateUrl: './orders-page.component.html',
})
export class OrdersPageComponent {
  private readonly api = inject(CheckoutApiService);
  protected readonly orders = signal<Order[]>([]);
  protected readonly loading = signal(false);
  protected readonly error = signal<string | null>(null);

  // Tracking modal & search
  protected readonly trackingQuery = signal('');
  protected readonly trackingSearchLoading = signal(false);
  protected readonly activeTrackingOrder = signal<Order | null>(null);
  protected readonly showTrackingModal = signal(false);

  constructor() {
    void this.load();
  }

  protected statusLabel(status: FulfillmentStatusEnum | string): string {
    const labels: Record<string, string> = {
      pending_pickup: 'En preparación para retiro',
      ready_for_pickup: 'Listo para retiro',
      ready_for_dispatch: 'Listo para despacho',
      dispatched: 'Despachado en camino',
      delivered: 'Entregado',
      collected: 'Cobrado / Retirado',
      expired: 'Vencido',
      cancelled: 'Cancelado',
    };
    return labels[status] ?? status;
  }

  protected statusBadgeClass(status: FulfillmentStatusEnum | string): string {
    switch (status) {
      case 'dispatched':
      case 'ready_for_dispatch':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'delivered':
      case 'collected':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'ready_for_pickup':
        return 'bg-indigo-50 text-indigo-700 border-indigo-200';
      case 'pending_pickup':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'cancelled':
      case 'expired':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  }

  protected paymentStatusLabel(status: Order['payment_status']): string {
    return {
      pending: 'Pendiente de pago',
      paid: 'Pago confirmado',
      failed: 'Pago fallido',
    }[status] ?? status;
  }

  protected paymentStatusClass(status: Order['payment_status']): string {
    switch (status) {
      case 'paid':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'pending':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'failed':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  }

  protected formatItemVariant(item: { size_name?: string | null; color_name?: string | null; variant_sku?: string | null }): string {
    const parts = [item.size_name, item.color_name].filter((v): v is string => !!v);
    return parts.length > 0 ? parts.join(' / ') : (item.variant_sku || 'Estándar');
  }

  protected openTracking(order: Order): void {
    this.activeTrackingOrder.set(order);
    this.showTrackingModal.set(true);
  }

  protected closeTracking(): void {
    this.activeTrackingOrder.set(null);
    this.showTrackingModal.set(false);
  }

  protected async searchTracking(): Promise<void> {
    const code = this.trackingQuery().trim().toUpperCase();
    if (!code) {
      toast.warning('Ingresa un número de guía de despacho (ej. DSP-20261028-...)');
      return;
    }

    this.trackingSearchLoading.set(true);
    try {
      const response = await firstValueFrom(this.api.trackOrder(code));
      if (response.data) {
        this.activeTrackingOrder.set(response.data);
        this.showTrackingModal.set(true);
      } else {
        toast.error('No se encontró ningún pedido con esa guía.');
      }
    } catch (err) {
      toast.error(getErrorMessage(err, 'No se pudo localizar el pedido con esa guía de despacho.'));
    } finally {
      this.trackingSearchLoading.set(false);
    }
  }

  protected isStepDone(order: Order, step: 'created' | 'paid' | 'prepared' | 'dispatched' | 'delivered'): boolean {
    if (step === 'created') return true;
    if (step === 'paid') return order.payment_status === 'paid';
    if (step === 'prepared') {
      return ['ready_for_dispatch', 'dispatched', 'delivered', 'ready_for_pickup', 'collected'].includes(order.fulfillment_status);
    }
    if (step === 'dispatched') {
      return ['dispatched', 'delivered'].includes(order.fulfillment_status);
    }
    if (step === 'delivered') {
      return ['delivered', 'collected'].includes(order.fulfillment_status);
    }
    return false;
  }

  protected downloadSalesNote(order: Order): void {
    downloadSimplePdf({
      filename: `nota-venta-${order.id.slice(0, 8)}.pdf`,
      title: 'Nota de Venta — FashionStore',
      generatedAt: new Date().toLocaleString('es-BO'),
      filters: [
        ['ID Pedido', order.id],
        ['Fecha', new Date(order.created_at).toLocaleString('es-BO')],
        ['Modalidad', order.delivery_type === 'ENVIO_DOMICILIO' ? 'Envío a Domicilio' : 'Retiro en Tienda'],
        ...(order.tracking_number ? [['Guía Despacho', order.tracking_number]] : []),
        ...(order.shipping_address ? [['Dirección Envío', order.shipping_address]] : []),
        ...(order.pickup_code ? [['Código Retiro', order.pickup_code]] : []),
        ['Estado Pago', this.paymentStatusLabel(order.payment_status)],
        ['Método Pago', order.payment_method === 'stripe' ? 'Tarjeta (Stripe Elements)' : 'Efectivo'],
        ['Estado Despacho', this.statusLabel(order.fulfillment_status)],
        ['Subtotal', `${order.subtotal} ${order.currency}`],
        ['Descuento', `${order.discount_amount} ${order.currency}`],
        ['Total Pagado', `${order.total_amount} ${order.currency}`],
      ],
      columns: ['Producto', 'Detalle / Variante', 'Cant.', 'Precio Unit.', 'Subtotal'],
      rows: order.items.map((item) => [
        item.product_name,
        [item.size_name, item.color_name].filter(Boolean).join(' / ') || item.variant_sku,
        String(item.quantity),
        `${item.unit_price} ${order.currency}`,
        `${item.line_total} ${order.currency}`,
      ]),
    });
  }

  protected async load(): Promise<void> {
    this.loading.set(true);
    try {
      const response = await firstValueFrom(this.api.listOrders());
      this.orders.set(response.data ?? []);
      this.error.set(null);
    } catch (error) {
      this.error.set(getErrorMessage(error, 'No se pudieron cargar los pedidos.'));
    } finally {
      this.loading.set(false);
    }
  }
}
