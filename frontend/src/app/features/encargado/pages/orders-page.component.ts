import { CommonModule } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { firstValueFrom } from 'rxjs';
import { toast } from '@spartan-ng/brain/sonner';

import { HlmBadgeImports } from '../../../components/badge/src';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmInputImports } from '../../../components/input/src';
import { HlmTextareaImports } from '../../../components/textarea/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { requestWithToast } from '../../../core/utils/request-toast.util';
import { CheckoutApiService } from '../../shared/services/checkout-api.service';
import { Order, FulfillmentStatusEnum } from '../../shared/models/order.model';

@Component({
  selector: 'app-encargado-orders-page',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    HlmButton,
    ...HlmBadgeImports,
    ...HlmCardImports,
    ...HlmInputImports,
    ...HlmTextareaImports,
  ],
  templateUrl: './orders-page.component.html',
})
export class EncargadoOrdersPageComponent {
  private readonly api = inject(CheckoutApiService);

  protected readonly orders = signal<Order[]>([]);
  protected readonly loading = signal(false);
  protected readonly statusFilter = signal<'ALL' | 'PENDING' | 'READY' | 'DISPATCHED'>('ALL');

  // Dispatch modal (CU12 - Política 3)
  protected readonly dispatchModalOpen = signal(false);
  protected readonly selectedOrderForDispatch = signal<Order | null>(null);
  protected readonly shippingNotes = signal('');
  protected readonly dispatching = signal(false);

  protected readonly filteredOrders = computed(() => {
    const list = this.orders();
    const filter = this.statusFilter();
    if (filter === 'ALL') return list;
    if (filter === 'PENDING') {
      return list.filter((o) => ['pending_pickup', 'ready_for_dispatch'].includes(o.fulfillment_status));
    }
    if (filter === 'READY') {
      return list.filter((o) => o.fulfillment_status === 'ready_for_pickup');
    }
    if (filter === 'DISPATCHED') {
      return list.filter((o) => ['dispatched', 'delivered'].includes(o.fulfillment_status));
    }
    return list;
  });

  constructor() {
    void this.load();
  }

  protected async load(): Promise<void> {
    this.loading.set(true);
    try {
      const response = await firstValueFrom(this.api.listBranchOrders());
      this.orders.set(response.data ?? []);
    } catch (err) {
      toast.error(getErrorMessage(err, 'No se pudieron cargar los pedidos de la sucursal.'));
    } finally {
      this.loading.set(false);
    }
  }

  protected fulfillmentLabel(status: Order['fulfillment_status']): string {
    const labels: Record<FulfillmentStatusEnum, string> = {
      pending_pickup: 'Pendiente de preparación',
      ready_for_pickup: 'Listo para retiro',
      ready_for_dispatch: 'Listo para despacho',
      dispatched: 'Despachado / En camino',
      delivered: 'Entregado a cliente',
      collected: 'Cobrado y entregado',
      expired: 'Vencido',
      cancelled: 'Cancelado',
    };
    return labels[status] ?? status;
  }

  protected fulfillmentClass(status: Order['fulfillment_status']): string {
    switch (status) {
      case 'dispatched':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'delivered':
      case 'collected':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'ready_for_pickup':
      case 'ready_for_dispatch':
        return 'bg-indigo-50 text-indigo-700 border-indigo-200';
      case 'pending_pickup':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  }

  protected paymentMethodLabel(method: Order['payment_method']): string {
    return method === 'stripe' ? 'Tarjeta (Stripe)' : 'Efectivo en Caja';
  }

  protected formatItemVariant(item: { size_name?: string | null; color_name?: string | null; variant_sku?: string | null }): string {
    const parts = [item.size_name, item.color_name].filter((v): v is string => !!v);
    return parts.length > 0 ? parts.join(' / ') : (item.variant_sku || 'Estándar');
  }

  protected isDispatchAllowed(order: Order): boolean {
    // POLÍTICA DE NEGOCIO 3: Despacho condicionado a status = 'paid'
    return order.payment_status === 'paid';
  }

  protected openDispatchModal(order: Order): void {
    if (!this.isDispatchAllowed(order)) {
      toast.error('Despacho bloqueado por Política 3: Requiere pago previo confirmado en Stripe.');
      return;
    }
    this.selectedOrderForDispatch.set(order);
    this.shippingNotes.set('');
    this.dispatchModalOpen.set(true);
  }

  protected closeDispatchModal(): void {
    this.selectedOrderForDispatch.set(null);
    this.dispatchModalOpen.set(false);
  }

  protected async confirmDispatch(): Promise<void> {
    const order = this.selectedOrderForDispatch();
    if (!order) return;

    this.dispatching.set(true);
    try {
      const response = await firstValueFrom(
        this.api.dispatchOrder(order.id, {
          shipping_notes: this.shippingNotes().trim() || undefined,
        }),
      );

      toast.success(
        `Despacho autorizado exitosamente. Guía generada: ${response.data?.tracking_number}`,
      );
      this.closeDispatchModal();
      await this.load();
    } catch (err) {
      toast.error(
        getErrorMessage(err, 'No se pudo completar el despacho del pedido.'),
      );
    } finally {
      this.dispatching.set(false);
    }
  }

  protected async markReady(orderId: string): Promise<void> {
    await requestWithToast(this.api.markReady(orderId), {
      loading: 'Actualizando pedido...',
      success: 'Pedido marcado como listo para retiro.',
      error: 'No se pudo marcar el pedido.',
    });
    await this.load();
  }
}
