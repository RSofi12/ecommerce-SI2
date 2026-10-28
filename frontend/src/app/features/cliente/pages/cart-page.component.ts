import { CommonModule } from '@angular/common';
import { Component, ElementRef, ViewChild, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { Stripe, StripeElements, StripePaymentElement, loadStripe } from '@stripe/stripe-js';

import { toast } from '@spartan-ng/brain/sonner';

import { HlmBadgeImports } from '../../../components/badge/src';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmInputImports } from '../../../components/input/src';
import { HlmTable } from '../../../components/table/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { requestWithToast } from '../../../core/utils/request-toast.util';
import { downloadSimplePdf } from '../../../core/utils/simple-pdf.util';
import { Cart } from '../../shared/models/cart.model';
import { CatalogBranch } from '../../shared/models/catalog.model';
import { CartApiService } from '../../shared/services/cart-api.service';
import { CatalogApiService } from '../../shared/services/catalog-api.service';
import { Order } from '../../shared/models/order.model';
import { CheckoutApiService, CheckoutRequestPayload } from '../../shared/services/checkout-api.service';
import { environment } from '../../../../environments/environment';

type StripeCheckout = {
  orderId: string;
  pickupExpiresAt: string;
  trackingNumber?: string | null;
  deliveryType?: string;
  shippingAddress?: string | null;
};

@Component({
  selector: 'app-cart-page',
  standalone: true,
  imports: [CommonModule, RouterLink, HlmButton, HlmTable, ...HlmBadgeImports, ...HlmCardImports, ...HlmInputImports],
  templateUrl: './cart-page.component.html',
})
export class CartPageComponent {
  private readonly cartApi = inject(CartApiService);
  private readonly catalogApi = inject(CatalogApiService);
  private readonly checkoutApi = inject(CheckoutApiService);
  private stripe: Stripe | null = null;
  private stripeElements: StripeElements | null = null;
  private stripePaymentElement: StripePaymentElement | null = null;

  @ViewChild('paymentElement')
  private set paymentElementHost(host: ElementRef<HTMLDivElement> | undefined) {
    if (host && this.stripePaymentElement) this.stripePaymentElement.mount(host.nativeElement);
  }

  protected readonly cart = signal<Cart | null>(null);
  protected readonly branches = signal<CatalogBranch[]>([]);
  protected readonly lastOrder = signal<Order | null>(null);
  protected readonly stripeCheckout = signal<StripeCheckout | null>(null);
  protected readonly stripePaymentStatus = signal<string | null>(null);
  protected readonly loading = signal(false);
  protected readonly updatingItemId = signal<string | null>(null);
  protected readonly checkoutMethod = signal<'cash' | 'stripe'>('stripe');
  protected readonly deliveryType = signal<'RETIRO_TIENDA' | 'ENVIO_DOMICILIO'>('ENVIO_DOMICILIO');
  protected readonly shippingAddress = signal<string>('');
  protected readonly pickupBranchId = signal('');
  protected readonly checkingOut = signal(false);
  protected readonly couponCode = signal('');

  constructor() {
    void this.loadCart();
    void this.loadBranches();
  }

  protected get itemCount(): number {
    return this.cart()?.item_count ?? 0;
  }

  protected get subtotal(): string {
    return this.cart()?.subtotal ?? '0.00';
  }

  protected get discount(): string {
    return this.cart()?.discount_amount ?? '0.00';
  }

  protected get total(): string {
    return this.cart()?.total_amount ?? '0.00';
  }

  protected async refresh(): Promise<void> {
    await this.loadCart();
  }

  protected selectDeliveryType(type: 'RETIRO_TIENDA' | 'ENVIO_DOMICILIO'): void {
    this.deliveryType.set(type);
    if (type === 'ENVIO_DOMICILIO' && this.checkoutMethod() === 'cash') {
      this.checkoutMethod.set('stripe');
    }
  }

  protected selectCheckoutMethod(method: 'cash' | 'stripe'): void {
    if (method === 'cash' && this.deliveryType() === 'ENVIO_DOMICILIO') {
      toast.info('Para pago en efectivo, la entrega es por retiro presencial en sucursal.');
      this.deliveryType.set('RETIRO_TIENDA');
    }
    this.checkoutMethod.set(method);
  }

  protected async increase(itemId: string, quantity: number): Promise<void> {
    await this.updateQuantity(itemId, quantity + 1);
  }

  protected async decrease(itemId: string, quantity: number): Promise<void> {
    await this.updateQuantity(itemId, quantity - 1);
  }

  protected async remove(itemId: string): Promise<void> {
    this.updatingItemId.set(itemId);
    try {
      const response = await requestWithToast(
        this.cartApi.removeItem(itemId),
        { loading: 'Eliminando item...', success: 'Item eliminado.', error: 'No se pudo eliminar el item.' },
      );
      this.cart.set(response.data ?? null);
    } catch {
      // toast handled by requestWithToast
    } finally {
      this.updatingItemId.set(null);
    }
  }

  protected async clear(): Promise<void> {
    try {
      const response = await requestWithToast(
        this.cartApi.clearCart(),
        { loading: 'Vaciando carrito...', success: 'Carrito vaciado.', error: 'No se pudo vaciar el carrito.' },
      );
      this.cart.set(response.data ?? null);
    } catch {
      // toast handled by requestWithToast
    }
  }

  protected async applyCoupon(): Promise<void> {
    const code = this.couponCode().trim();
    if (!code) {
      toast.warning('Ingresa un código promocional.');
      return;
    }
    try {
      const response = await requestWithToast(
        this.cartApi.applyCoupon(code),
        { loading: 'Aplicando cupón...', success: 'Cupón aplicado.', error: 'No se pudo aplicar el cupón.' },
      );
      this.cart.set(response.data ?? null);
    } catch {
      // toast handled by requestWithToast
    }
  }

  protected async removeCoupon(): Promise<void> {
    try {
      const response = await requestWithToast(
        this.cartApi.removeCoupon(),
        { loading: 'Retirando cupón...', success: 'Cupón retirado.', error: 'No se pudo retirar el cupón.' },
      );
      this.cart.set(response.data ?? null);
    } catch {
      // toast handled by requestWithToast
    }
  }

  protected async checkout(): Promise<void> {
    if (!this.cart()?.items?.length) {
      toast.warning('Tu carrito está vacío.');
      return;
    }

    const isHomeDelivery = this.deliveryType() === 'ENVIO_DOMICILIO';
    const address = this.shippingAddress().trim();
    const pickupBranchId = this.pickupBranchId();

    if (isHomeDelivery && !address) {
      toast.warning('Ingresa la dirección completa para el envío a domicilio.');
      return;
    }

    if (!isHomeDelivery && !pickupBranchId) {
      toast.warning('Selecciona la sucursal donde recogerás tu pedido.');
      return;
    }

    const payload: CheckoutRequestPayload = {
      delivery_type: this.deliveryType(),
      pickup_branch_id: pickupBranchId || undefined,
      shipping_address: isHomeDelivery ? address : undefined,
    };

    this.checkingOut.set(true);
    try {
      if (this.checkoutMethod() === 'cash') {
        const response = await requestWithToast(
          this.checkoutApi.checkoutCash(payload),
          { loading: 'Creando pedido...', success: 'Pedido para retiro en tienda creado.', error: 'No se pudo crear el pedido.' },
        );
        this.lastOrder.set(response.data ?? null);
        this.clearStripeCheckout();
      } else {
        await this.startStripeCheckout(payload);
      }
      await this.loadCart();
    } catch {
      // toast handled by requestWithToast
    } finally {
      this.checkingOut.set(false);
    }
  }

  protected lineTotal(item: { line_total: string }): string {
    return item.line_total;
  }

  protected orderLabel(): string {
    return this.lastOrder() ? `Pedido #${this.lastOrder()!.id}` : 'Sin pedido todavía';
  }

  protected downloadSalesNote(order: Order): void {
    downloadSimplePdf({
      filename: `nota-venta-${order.id}.pdf`,
      title: 'Nota de venta — FashionStore',
      generatedAt: new Date().toLocaleString('es-BO'),
      filters: [
        ['Pedido ID', order.id],
        ['Fecha', new Date(order.created_at).toLocaleString('es-BO')],
        ['Modalidad', order.delivery_type === 'ENVIO_DOMICILIO' ? 'Envío a domicilio' : 'Retiro en sucursal'],
        ...(order.shipping_address ? [['Dirección de entrega', order.shipping_address]] : []),
        ...(order.tracking_number ? [['Guía de seguimiento', order.tracking_number]] : []),
        ['Estado de pago', ({ pending: 'Pendiente', paid: 'Pagado', failed: 'Fallido', cancelled: 'Cancelado' } as Record<string, string>)[order.payment_status] ?? order.payment_status],
        ['Método de pago', order.payment_method === 'stripe' ? 'Tarjeta (Stripe)' : 'Efectivo'],
        ...(order.pickup_code ? [['Código de retiro', order.pickup_code]] : []),
        ['Subtotal', `${order.subtotal} ${order.currency.toUpperCase()}`],
        ['Descuento', `${order.discount_amount} ${order.currency.toUpperCase()}`],
        ['Total pagado', `${order.total_amount} ${order.currency.toUpperCase()}`],
      ],
      columns: ['Producto', 'Variante', 'Cantidad', 'Precio unitario', 'Total'],
      rows: order.items.map((item) => [
        item.product_name,
        [item.size_name, item.color_name].filter(Boolean).join(' / ') || item.variant_sku,
        String(item.quantity),
        `${item.unit_price} ${order.currency.toUpperCase()}`,
        `${item.line_total} ${order.currency.toUpperCase()}`,
      ]),
    });
  }

  protected branchLabel(branchId: string | null | undefined): string {
    const branch = this.branches().find((item) => item.id === branchId);
    return branch ? `${branch.name} - ${branch.city}` : 'Sucursal central asignada';
  }

  protected async confirmStripePayment(): Promise<void> {
    if (!this.stripe || !this.stripeElements) {
      toast.warning('Primero inicia el pago con Stripe.');
      return;
    }

    this.checkingOut.set(true);
    try {
      const { error, paymentIntent } = await this.stripe.confirmPayment({
        elements: this.stripeElements,
        confirmParams: { return_url: window.location.href },
        redirect: 'if_required',
      });
      if (error) {
        this.stripePaymentStatus.set('error');
        toast.error(error.message ?? 'No se pudo confirmar el pago con Stripe.');
      } else if (paymentIntent?.status === 'succeeded') {
        const orderId = this.stripeCheckout()?.orderId;
        if (!orderId) return;
        const response = await firstValueFrom(this.checkoutApi.getOrder(orderId));
        const order = response.data ?? null;
        this.lastOrder.set(order);
        if (order?.payment_status === 'paid') {
          this.stripePaymentStatus.set('paid');
          toast.success(
            order.tracking_number
              ? `¡Pago confirmado por Stripe! Guía generada: ${order.tracking_number}`
              : '¡Pago confirmado por Stripe! Tu pedido está en preparación.'
          );
        } else {
          this.stripePaymentStatus.set('pending');
          toast.info('Pago enviado a Stripe. Esperando confirmación bancaria.');
        }
      } else if (paymentIntent?.status === 'canceled') {
        this.stripePaymentStatus.set('cancelled');
        toast.warning('El intento de pago fue cancelado.');
      } else {
        this.stripePaymentStatus.set('pending');
        toast.info('El pago está pendiente de confirmación bancaria.');
      }
    } catch {
      this.stripePaymentStatus.set('error');
      toast.error('No se pudo confirmar el pago con la pasarela.');
    } finally {
      this.checkingOut.set(false);
    }
  }

  private async loadCart(): Promise<void> {
    this.loading.set(true);
    try {
      const response = await firstValueFrom(this.cartApi.getCurrentCart());
      this.cart.set(response.data ?? null);
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudo cargar el carrito.'));
      this.cart.set(null);
    } finally {
      this.loading.set(false);
    }
  }

  private async loadBranches(): Promise<void> {
    try {
      const response = await firstValueFrom(this.catalogApi.listPublicBranches());
      const branchList = response.data ?? [];
      this.branches.set(branchList);
      if (branchList.length > 0 && !this.pickupBranchId()) {
        this.pickupBranchId.set(branchList[0].id);
      }
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudieron cargar las sucursales.'));
    }
  }

  private async startStripeCheckout(payload: CheckoutRequestPayload): Promise<void> {
    if (!environment.stripePublishableKey) {
      toast.error('Stripe no está configurado para esta aplicación.');
      return;
    }
    try {
      this.stripe = await loadStripe(environment.stripePublishableKey);
    } catch {
      toast.error('No se pudo cargar Stripe SDK.');
      return;
    }
    if (!this.stripe) {
      toast.error('No se pudo inicializar Stripe.');
      return;
    }
    const response = await requestWithToast(
      this.checkoutApi.checkoutStripe(payload),
      { loading: 'Inicializando sesión segura de Stripe...', success: 'Completa los datos de tu tarjeta bancaria.', error: 'No se pudo iniciar el checkout de Stripe.' },
    );
    const checkout = response.data;
    if (!checkout) return;

    this.clearStripeCheckout();
    this.stripeElements = this.stripe.elements({ clientSecret: checkout.client_secret });
    this.stripePaymentElement = this.stripeElements.create('payment');
    this.stripeCheckout.set({
      orderId: checkout.order_id,
      pickupExpiresAt: checkout.pickup_expires_at,
      trackingNumber: checkout.tracking_number,
      deliveryType: checkout.delivery_type,
      shippingAddress: checkout.shipping_address,
    });
    this.stripePaymentStatus.set('ready');
  }

  private clearStripeCheckout(): void {
    this.stripePaymentElement?.destroy();
    this.stripePaymentElement = null;
    this.stripeElements = null;
    this.stripeCheckout.set(null);
    this.stripePaymentStatus.set(null);
  }

  private async updateQuantity(itemId: string, quantity: number): Promise<void> {
    if (quantity < 0) {
      return;
    }
    this.updatingItemId.set(itemId);
    try {
      const response = await requestWithToast(
        this.cartApi.updateItem(itemId, { quantity }),
        { loading: 'Actualizando cantidad...', success: 'Carrito actualizado.', error: 'No se pudo actualizar el carrito.' },
      );
      this.cart.set(response.data ?? null);
    } catch {
      // toast handled by requestWithToast
    } finally {
      this.updatingItemId.set(null);
    }
  }
}
