import 'package:flutter/material.dart';

import '../../app/routes.dart';
import '../../shared/widgets/app_button.dart';
import '../../shared/widgets/app_card.dart';
import '../../shared/widgets/app_empty_view.dart';
import '../../shared/widgets/app_error_view.dart';
import '../../shared/widgets/app_loading.dart';
import '../../shared/widgets/app_section_title.dart';
import '../../shared/widgets/app_snack_bar.dart';
import '../../shared/widgets/product_image.dart';
import '../../shared/widgets/product_price.dart';
import '../auth/auth_controller.dart';
import '../auth/login_dialog.dart';
import 'order_controller.dart';
import 'order_models.dart';

class OrdersPage extends StatefulWidget {
  const OrdersPage({
    super.key,
    required this.authController,
    this.initialOrderId,
    this.controller,
  });

  final AuthController authController;
  final String? initialOrderId;
  final OrderController? controller;

  @override
  State<OrdersPage> createState() => _OrdersPageState();
}

class _OrdersPageState extends State<OrdersPage> {
  late final OrderController _controller;
  late final bool _ownsController;
  final TextEditingController _trackingSearchController = TextEditingController();
  String? _loadedToken;
  bool _initialDetailOpened = false;

  @override
  void initState() {
    super.initState();
    _ownsController = widget.controller == null;
    _controller =
        widget.controller ??
        OrderController(authController: widget.authController);
    widget.authController.addListener(_handleAuthChanged);
    WidgetsBinding.instance.addPostFrameCallback((_) => _handleAuthChanged());
  }

  @override
  void dispose() {
    widget.authController.removeListener(_handleAuthChanged);
    _trackingSearchController.dispose();
    if (_ownsController) _controller.dispose();
    super.dispose();
  }

  void _handleAuthChanged() {
    if (!mounted) return;
    if (!widget.authController.isAuthenticated) {
      _loadedToken = null;
      return;
    }
    final token = widget.authController.accessToken;
    if (token == null || token == _loadedToken) return;
    _loadedToken = token;
    _loadOrders();
  }

  Future<void> _loadOrders() async {
    await _controller.load();
    if (!mounted ||
        _initialDetailOpened ||
        widget.initialOrderId == null ||
        _controller.status != OrderControllerStatus.ready) {
      return;
    }
    _initialDetailOpened = true;
    await _showDetails(widget.initialOrderId!);
  }

  Future<void> _searchTracking() async {
    final code = _trackingSearchController.text.trim().toUpperCase();
    if (code.isEmpty) {
      AppSnackBar.show(
        context,
        'Ingresa un número de guía (ej. DSP-20261028-...)',
        tone: AppSnackBarTone.error,
      );
      return;
    }

    final order = await _controller.trackOrder(code);
    if (!mounted) return;
    if (order == null) {
      AppSnackBar.show(
        context,
        _controller.errorMessage ?? 'No se encontró pedido con esa guía.',
        tone: AppSnackBarTone.error,
      );
      return;
    }
    _showDetailsModal(order);
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: widget.authController,
      builder: (context, _) {
        if (widget.authController.status == AuthStatus.loading) {
          return const AppLoading(message: 'Validando sesión...');
        }
        if (widget.authController.status == AuthStatus.error) {
          return AppErrorView(
            message:
                widget.authController.errorMessage ??
                'No se pudo validar la sesión.',
            onRetry: widget.authController.restoreSession,
          );
        }
        if (!widget.authController.isAuthenticated) {
          return AppEmptyView(
            title: 'Pedidos privados',
            message: 'Inicia sesión para consultar tus pedidos y rastreos.',
            actionLabel: 'Iniciar sesión',
            onAction: () => LoginDialog.show(
              context: context,
              controller: widget.authController,
            ),
          );
        }
        return ListenableBuilder(
          listenable: _controller,
          builder: (context, _) => _buildOrders(context),
        );
      },
    );
  }

  Widget _buildOrders(BuildContext context) {
    if (_controller.status == OrderControllerStatus.error &&
        _controller.orders.isEmpty) {
      return AppErrorView(
        message:
            _controller.errorMessage ?? 'No se pudieron cargar los pedidos.',
        onRetry: _controller.load,
      );
    }
    if (_controller.status == OrderControllerStatus.loading &&
        _controller.orders.isEmpty) {
      return const AppLoading(message: 'Cargando pedidos...');
    }

    return RefreshIndicator(
      onRefresh: _controller.load,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(20, 20, 20, 32),
        children: [
          if (_controller.status == OrderControllerStatus.loading)
            const LinearProgressIndicator(minHeight: 2),
          const AppSectionTitle(
            title: 'Mis pedidos',
            subtitle: 'Historial de compras, estado de pago y despacho (CU12).',
          ),
          const SizedBox(height: 12),
          // Buscador rápido de guía de despacho
          AppCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Rastrear Guía de Despacho',
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                        fontWeight: FontWeight.w700,
                      ),
                ),
                const SizedBox(height: 4),
                Text(
                  'Consulta en tiempo real la línea de vida de tu entrega.',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Colors.grey.shade600,
                      ),
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: _trackingSearchController,
                        decoration: const InputDecoration(
                          hintText: 'DSP-YYYYMMDD-XXXX',
                          isDense: true,
                          prefixIcon: Icon(Icons.local_shipping_outlined, size: 20),
                        ),
                        textCapitalization: TextCapitalization.characters,
                        onSubmitted: (_) => _searchTracking(),
                      ),
                    ),
                    const SizedBox(width: 8),
                    FilledButton(
                      onPressed: _searchTracking,
                      child: const Text('Rastrear'),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          if (_controller.orders.isEmpty)
            const AppEmptyView(
              title: 'Aún no tienes pedidos',
              message: 'Tus compras confirmadas aparecerán aquí.',
            )
          else
            for (final order in _controller.orders) ...[
              _OrderCard(
                order: order,
                onTap: () => _showDetails(order.id),
                onPay: _canPay(order) ? () => _payOrder(order.id) : null,
              ),
              const SizedBox(height: 12),
            ],
        ],
      ),
    );
  }

  bool _canPay(Order order) {
    return order.fulfillmentStatus == FulfillmentStatus.pendingPickup &&
        order.paymentStatus == PaymentStatus.pending;
  }

  Future<void> _payOrder(String orderId) async {
    await Navigator.of(
      context,
    ).pushNamed(AppRoutes.checkout, arguments: orderId);
    if (mounted) await _controller.load();
  }

  Future<void> _showDetails(String orderId) async {
    await _controller.loadDetail(orderId);
    if (!mounted || _controller.selectedOrder == null) return;
    _showDetailsModal(_controller.selectedOrder!);
  }

  Future<void> _showDetailsModal(Order order) async {
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (context) => SafeArea(
        child: DraggableScrollableSheet(
          expand: false,
          initialChildSize: 0.85,
          minChildSize: 0.5,
          maxChildSize: 0.95,
          builder: (context, scrollController) => ListView(
            controller: scrollController,
            padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Pedido #${order.id.substring(0, 8)}',
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                              fontWeight: FontWeight.w700,
                            ),
                      ),
                      Text(
                        _displayDateTime(order.createdAt),
                        style: const TextStyle(fontSize: 12, color: Colors.grey),
                      ),
                    ],
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: order.paymentStatus == PaymentStatus.paid
                          ? Colors.green.shade50
                          : Colors.amber.shade50,
                      border: Border.all(
                        color: order.paymentStatus == PaymentStatus.paid
                            ? Colors.green.shade300
                            : Colors.amber.shade300,
                      ),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      _paymentStatusLabel(order.paymentStatus),
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                        color: order.paymentStatus == PaymentStatus.paid
                            ? Colors.green.shade800
                            : Colors.amber.shade900,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              // Guía de seguimiento si aplica
              if (order.trackingNumber != null) ...[
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.blue.shade50,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: Colors.blue.shade200),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.local_shipping, color: Colors.blue.shade700),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'Guía de Despacho Asignada',
                              style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold),
                            ),
                            Text(
                              order.trackingNumber!,
                              style: TextStyle(
                                fontSize: 14,
                                fontWeight: FontWeight.w800,
                                color: Colors.blue.shade900,
                                fontFamily: 'monospace',
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
              ],
              // Stepper ICONIX de 5 etapas
              Text(
                'Línea de Vida y Seguimiento (CU12)',
                style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
              ),
              const SizedBox(height: 10),
              _LifecycleStepper(order: order),
              const SizedBox(height: 16),
              // Modalidad y Destino
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.grey.shade50,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: Colors.grey.shade200),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text(
                          order.deliveryType == 'ENVIO_DOMICILIO'
                              ? '🚚 Envío a Domicilio'
                              : '🏪 Retiro en Sucursal',
                          style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    if (order.deliveryType == 'ENVIO_DOMICILIO' && order.shippingAddress != null)
                      Text('Dirección: ${order.shippingAddress}', style: const TextStyle(fontSize: 12))
                    else if (order.pickupCode != null)
                      Text('Código de retiro en caja: ${order.pickupCode}',
                          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              Text(
                'Prendas Adquiridas',
                style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
              ),
              const SizedBox(height: 8),
              for (final item in order.items)
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: SizedBox(
                    width: 48,
                    height: 56,
                    child: ProductImage(imageUrl: item.imageUrl),
                  ),
                  title: Text(item.productName),
                  subtitle: Text(
                    '${[item.sizeName, item.colorName].whereType<String>().join('/')} · Cant. ${item.quantity}',
                  ),
                  trailing: ProductPrice(
                    price: item.lineTotal,
                    currency: _currencyLabel(order.currency),
                  ),
                ),
              const Divider(),
              Align(
                alignment: Alignment.centerRight,
                child: ProductPrice(
                  price: order.totalAmount,
                  currency: _currencyLabel(order.currency),
                  style: Theme.of(
                    context,
                  ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _LifecycleStepper extends StatelessWidget {
  const _LifecycleStepper({required this.order});

  final Order order;

  bool _isStepDone(int step) {
    if (step == 1) return true; // Creado
    if (step == 2) return order.paymentStatus == PaymentStatus.paid; // Pago Stripe
    if (step == 3) {
      return [
        FulfillmentStatus.readyForDispatch,
        FulfillmentStatus.dispatched,
        FulfillmentStatus.delivered,
        FulfillmentStatus.readyForPickup,
        FulfillmentStatus.collected,
      ].contains(order.fulfillmentStatus);
    }
    if (step == 4) {
      return [
        FulfillmentStatus.dispatched,
        FulfillmentStatus.delivered,
      ].contains(order.fulfillmentStatus);
    }
    if (step == 5) {
      return [
        FulfillmentStatus.delivered,
        FulfillmentStatus.collected,
      ].contains(order.fulfillmentStatus);
    }
    return false;
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        _StepRow(
          number: 1,
          title: 'Pedido Creado',
          subtitle: 'Registrado en la plataforma',
          isDone: _isStepDone(1),
          isLast: false,
        ),
        _StepRow(
          number: 2,
          title: 'Pago Verificado (Stripe)',
          subtitle: order.paymentStatus == PaymentStatus.paid
              ? 'Condición cumplida: Despacho autorizado (Política 3)'
              : 'Pendiente de confirmación de Stripe',
          isDone: _isStepDone(2),
          isAlert: order.paymentStatus != PaymentStatus.paid,
          isLast: false,
        ),
        _StepRow(
          number: 3,
          title: 'Preparación en Almacén',
          subtitle: 'Empaque y verificación de prendas',
          isDone: _isStepDone(3),
          isLast: false,
        ),
        _StepRow(
          number: 4,
          title: 'Despacho y Asignación de Guía',
          subtitle: order.trackingNumber != null
              ? 'Guía: ${order.trackingNumber}'
              : 'Pendiente de emisión de transporte',
          isDone: _isStepDone(4),
          isLast: false,
        ),
        _StepRow(
          number: 5,
          title: 'Entrega Final',
          subtitle: order.deliveryType == 'ENVIO_DOMICILIO'
              ? 'Recepción en domicilio del cliente'
              : 'Retiro presencial en sucursal',
          isDone: _isStepDone(5),
          isLast: true,
        ),
      ],
    );
  }
}

class _StepRow extends StatelessWidget {
  const _StepRow({
    required this.number,
    required this.title,
    required this.subtitle,
    required this.isDone,
    this.isAlert = false,
    required this.isLast,
  });

  final int number;
  final String title;
  final String subtitle;
  final bool isDone;
  final bool isAlert;
  final bool isLast;

  @override
  Widget build(BuildContext context) {
    final color = isDone
        ? Colors.green.shade600
        : (isAlert ? Colors.amber.shade700 : Colors.grey.shade400);

    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Column(
            children: [
              CircleAvatar(
                radius: 12,
                backgroundColor: isDone ? Colors.green.shade600 : (isAlert ? Colors.amber.shade100 : Colors.grey.shade200),
                child: isDone
                    ? const Icon(Icons.check, size: 14, color: Colors.white)
                    : Text(
                        isAlert ? '!' : '$number',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          color: isAlert ? Colors.amber.shade900 : Colors.grey.shade700,
                        ),
                      ),
              ),
              if (!isLast)
                Expanded(
                  child: Container(
                    width: 2,
                    color: isDone ? Colors.green.shade400 : Colors.grey.shade200,
                  ),
                ),
            ],
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w700,
                      color: isDone ? Colors.black87 : Colors.grey.shade700,
                    ),
                  ),
                  Text(
                    subtitle,
                    style: TextStyle(fontSize: 11, color: color),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _OrderCard extends StatelessWidget {
  const _OrderCard({required this.order, required this.onTap, this.onPay});

  final Order order;
  final VoidCallback onTap;
  final VoidCallback? onPay;

  @override
  Widget build(BuildContext context) {
    final isHomeDelivery = order.deliveryType == 'ENVIO_DOMICILIO';

    return AppCard(
      onTap: onTap,
      child: Column(
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              CircleAvatar(
                backgroundColor: isHomeDelivery
                    ? Colors.blue.shade50
                    : Theme.of(context).colorScheme.primaryContainer,
                child: Icon(
                  isHomeDelivery ? Icons.local_shipping_outlined : Icons.store_outlined,
                  color: isHomeDelivery
                      ? Colors.blue.shade700
                      : Theme.of(context).colorScheme.onPrimaryContainer,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          'Pedido #${order.id.substring(0, 8)}',
                          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                fontWeight: FontWeight.w700,
                              ),
                        ),
                        ProductPrice(
                          price: order.totalAmount,
                          currency: _currencyLabel(order.currency),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: isHomeDelivery ? Colors.blue.shade50 : Colors.grey.shade100,
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Text(
                            isHomeDelivery ? '🚚 Domicilio' : '🏪 Sucursal',
                            style: TextStyle(
                              fontSize: 10,
                              fontWeight: FontWeight.w600,
                              color: isHomeDelivery ? Colors.blue.shade800 : Colors.grey.shade800,
                            ),
                          ),
                        ),
                        const SizedBox(width: 6),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: order.paymentStatus == PaymentStatus.paid
                                ? Colors.green.shade50
                                : Colors.amber.shade50,
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Text(
                            _paymentStatusLabel(order.paymentStatus),
                            style: TextStyle(
                              fontSize: 10,
                              fontWeight: FontWeight.w600,
                              color: order.paymentStatus == PaymentStatus.paid
                                  ? Colors.green.shade800
                                  : Colors.amber.shade900,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${_fulfillmentLabel(order.fulfillmentStatus)} · ${order.items.length} prenda(s)',
                      style: const TextStyle(fontSize: 12),
                    ),
                    if (order.trackingNumber != null) ...[
                      const SizedBox(height: 4),
                      Text(
                        'Guía: ${order.trackingNumber}',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          color: Colors.blue.shade700,
                          fontFamily: 'monospace',
                        ),
                      ),
                    ],
                    Text(
                      _displayDate(order.createdAt),
                      style: const TextStyle(fontSize: 11, color: Colors.grey),
                    ),
                  ],
                ),
              ),
            ],
          ),
          if (onPay != null)
            Padding(
              padding: const EdgeInsets.only(top: 12),
              child: AppButton(
                label: 'Pagar con tarjeta',
                icon: const Icon(Icons.credit_card_outlined),
                onPressed: onPay,
                variant: AppButtonVariant.outlined,
                expand: true,
              ),
            ),
        ],
      ),
    );
  }
}

String _fulfillmentLabel(FulfillmentStatus status) {
  return switch (status) {
    FulfillmentStatus.pendingPickup => 'En preparación',
    FulfillmentStatus.readyForPickup => 'Listo para retiro',
    FulfillmentStatus.readyForDispatch => 'Listo para despacho',
    FulfillmentStatus.dispatched => 'Despachado en camino',
    FulfillmentStatus.delivered => 'Entregado a cliente',
    FulfillmentStatus.collected => 'Cobrado y entregado',
    FulfillmentStatus.expired => 'Expirado',
    FulfillmentStatus.cancelled => 'Cancelado',
  };
}

String _paymentStatusLabel(PaymentStatus status) {
  return switch (status) {
    PaymentStatus.pending => 'Pendiente de pago',
    PaymentStatus.paid => 'Pago confirmado',
    PaymentStatus.failed => 'Pago fallido',
  };
}

String _currencyLabel(String currency) {
  return currency.toLowerCase() == 'bob' ? 'Bs' : currency.toUpperCase();
}

String _displayDate(DateTime date) {
  final local = date.toLocal();
  return '${local.day.toString().padLeft(2, '0')}/'
      '${local.month.toString().padLeft(2, '0')}/${local.year}';
}

String _displayDateTime(DateTime date) {
  final local = date.toLocal();
  return '${_displayDate(local)} ${local.hour.toString().padLeft(2, '0')}:'
      '${local.minute.toString().padLeft(2, '0')}';
}
