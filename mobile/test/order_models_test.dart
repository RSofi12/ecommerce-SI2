import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/features/orders/order_models.dart';

void main() {
  test('parsea pedido, estados, moneda, totales e ítems', () {
    final order = Order.fromJson({
      'id': 'order-id',
      'user_id': 'user-id',
      'status': 'paid',
      'payment_method': 'cash',
      'payment_status': 'paid',
      'stripe_payment_intent_id': null,
      'cash_reference': 'CASH-001',
      'pickup_branch_id': 'branch-id',
      'pickup_expires_at': '2026-09-02T10:00:00Z',
      'pickup_code': 'PICKUP-001',
      'subtotal': '125.50',
      'discount_amount': '5.50',
      'total_amount': '120.00',
      'currency': 'usd',
      'created_at': '2026-09-01T10:00:00Z',
      'updated_at': null,
      'items': [
        {
          'id': 'item-id',
          'order_id': 'order-id',
          'variant_id': 'variant-id',
          'quantity': 2,
          'unit_price': '60.00',
          'line_total': '120.00',
          'product_id': 'product-id',
          'product_name': 'Blusa demo',
          'variant_sku': 'SKU-1',
          'size_id': null,
          'color_id': null,
          'size_name': 'M',
          'color_name': 'Negro',
          'image_url': null,
          'image_public_id': 'ignored',
        },
      ],
    });

    expect(order.status, OrderStatus.paid);
    expect(order.paymentMethod, PaymentMethod.cash);
    expect(order.paymentStatus, PaymentStatus.paid);
    expect(order.totalAmount, 120);
    expect(order.items.single.productName, 'Blusa demo');
    expect(order.items.single.sizeName, 'M');
    expect(order.pickupCode, 'PICKUP-001');
    expect(order.pickupExpiresAt, DateTime.utc(2026, 9, 2, 10));
    expect(order.deliveryType, 'RETIRO_TIENDA');
  });

  test('CU12: parsea pedido con envío a domicilio, guía de despacho y estados extendidos', () {
    final order = Order.fromJson({
      'id': 'order-cu12-uuid',
      'user_id': 'user-cliente-uuid',
      'status': 'paid',
      'payment_method': 'stripe',
      'payment_status': 'paid',
      'fulfillment_status': 'dispatched',
      'delivery_type': 'ENVIO_DOMICILIO',
      'shipping_address': 'Av. Ballivián #123, Calacoto, La Paz',
      'tracking_number': 'DSP-20261028-A1B2',
      'dispatched_at': '2026-10-28T12:00:00Z',
      'dispatched_by': 'admin-uuid',
      'subtotal': '250.00',
      'discount_amount': '0.00',
      'total_amount': '250.00',
      'currency': 'bob',
      'created_at': '2026-10-28T10:00:00Z',
      'items': [
        {
          'id': 'item-1',
          'order_id': 'order-cu12-uuid',
          'variant_id': 'var-1',
          'quantity': 1,
          'unit_price': '250.00',
          'line_total': '250.00',
          'product_id': 'prod-1',
          'product_name': 'Vestido Seda Gala',
          'variant_sku': 'SKU-VEST-L',
        },
      ],
    });

    expect(order.deliveryType, 'ENVIO_DOMICILIO');
    expect(order.shippingAddress, 'Av. Ballivián #123, Calacoto, La Paz');
    expect(order.trackingNumber, 'DSP-20261028-A1B2');
    expect(order.dispatchedAt, DateTime.utc(2026, 10, 28, 12));
    expect(order.dispatchedBy, 'admin-uuid');
    expect(order.fulfillmentStatus, FulfillmentStatus.dispatched);
  });

  test('CU12: parsea estados de fulfillment extendidos', () {
    expect(FulfillmentStatus.fromJson('ready_for_dispatch'), FulfillmentStatus.readyForDispatch);
    expect(FulfillmentStatus.fromJson('dispatched'), FulfillmentStatus.dispatched);
    expect(FulfillmentStatus.fromJson('delivered'), FulfillmentStatus.delivered);
  });

  test('CU12: parsea StripeCheckout con tracking y deliveryType', () {
    final checkout = StripeCheckout.fromJson({
      'order_id': 'order-123',
      'client_secret': 'pi_123_secret_456',
      'payment_intent_id': 'pi_123',
      'delivery_type': 'ENVIO_DOMICILIO',
      'shipping_address': 'Calle 21, San Miguel',
      'tracking_number': 'DSP-20261028-9999',
    });

    expect(checkout.orderId, 'order-123');
    expect(checkout.clientSecret, 'pi_123_secret_456');
    expect(checkout.deliveryType, 'ENVIO_DOMICILIO');
    expect(checkout.trackingNumber, 'DSP-20261028-9999');
  });

  test('parsea sucursal pública', () {
    final branch = PickupBranch.fromJson({
      'id': 'branch-id',
      'name': 'Sucursal Central',
      'city': 'La Paz',
      'is_default': true,
      'is_active': true,
    });

    expect(branch.name, 'Sucursal Central');
    expect(branch.isActive, isTrue);
  });

  test('rechaza estados desconocidos', () {
    expect(() => OrderStatus.fromJson('unknown'), throwsFormatException);
  });
}
