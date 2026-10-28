import 'package:flutter/material.dart';
import 'package:flutter_stripe/flutter_stripe.dart' hide PaymentMethod;

import '../../core/config/app_config.dart';
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

class CheckoutPage extends StatefulWidget {
  const CheckoutPage({
    super.key,
    required this.authController,
    this.orderId,
    this.controller,
  });

  final AuthController authController;
  final String? orderId;
  final OrderController? controller;

  @override
  State<CheckoutPage> createState() => _CheckoutPageState();
}

class _CheckoutPageState extends State<CheckoutPage> {
  late final OrderController _controller;
  late final bool _ownsController;
  final TextEditingController _shippingAddressController = TextEditingController();
  String? _loadedToken;
  String? _pickupBranchId;
  DeliveryType _deliveryType = DeliveryType.homeDelivery;
  PaymentMethod _paymentMethod = PaymentMethod.stripe;

  bool get _isOrderPayment => widget.orderId != null;

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
    _shippingAddressController.dispose();
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
    _loadCheckout();
  }

  Future<void> _loadCheckout() async {
    await _controller.load();
    if (!mounted || widget.orderId == null) return;
    await _controller.loadDetail(widget.orderId!);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_isOrderPayment ? 'Pagar pedido' : 'Finalizar compra'),
      ),
      body: ListenableBuilder(
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
              title: 'Pago privado',
              message: 'Inicia sesión para continuar con el pago.',
              actionLabel: 'Iniciar sesión',
              onAction: () => LoginDialog.show(
                context: context,
                controller: widget.authController,
              ),
            );
          }
          return ListenableBuilder(
            listenable: _controller,
            builder: (context, _) => _buildContent(context),
          );
        },
      ),
    );
  }

  Widget _buildContent(BuildContext context) {
    final order = _controller.selectedOrder;
    if (_controller.status == OrderControllerStatus.error &&
        (_isOrderPayment || _controller.orders.isEmpty)) {
      return AppErrorView(
        message: _controller.errorMessage ?? 'No se pudo cargar el pago.',
        onRetry: _loadCheckout,
      );
    }
    if (_controller.status == OrderControllerStatus.loading &&
        (_isOrderPayment && order == null ||
            !_isOrderPayment && _controller.orders.isEmpty)) {
      return const AppLoading(message: 'Cargando pago...');
    }
    if (_isOrderPayment && order == null) {
      return const AppErrorView(message: 'No se encontró el pedido.');
    }

    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 32),
      children: [
        if (_controller.status == OrderControllerStatus.loading)
          const LinearProgressIndicator(minHeight: 2),
        AppSectionTitle(
          title: _isOrderPayment ? 'Finalizar pedido' : 'Finalizar compra',
          subtitle: _isOrderPayment
              ? 'Completa el pago para continuar con el despacho.'
              : 'Elige modalidad de entrega y método de pago (CU12).',
        ),
        const SizedBox(height: 16),
        if (order != null) ...[
          _OrderSummary(order: order),
          const SizedBox(height: 12),
        ],
        _checkoutCard(context),
      ],
    );
  }

  Widget _checkoutCard(BuildContext context) {
    final isSaving = _controller.status == OrderControllerStatus.saving;
    final branches = _controller.pickupBranches
        .where((branch) => branch.isActive)
        .toList(growable: false);
    final pickupBranchId = _selectedBranchId(branches);

    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!_isOrderPayment) ...[
            Text(
              '1. Modalidad de Entrega',
              style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
            ),
            const SizedBox(height: 8),
            DropdownButtonFormField<DeliveryType>(
              isExpanded: true,
              value: _deliveryType,
              decoration: const InputDecoration(labelText: 'Tipo de entrega'),
              items: const [
                DropdownMenuItem(
                  value: DeliveryType.homeDelivery,
                  child: Text('🚚 Envío a domicilio'),
                ),
                DropdownMenuItem(
                  value: DeliveryType.storePickup,
                  child: Text('🏪 Retiro en sucursal'),
                ),
              ],
              onChanged: isSaving
                  ? null
                  : (value) {
                      if (value == null) return;
                      setState(() {
                        _deliveryType = value;
                        if (_deliveryType == DeliveryType.homeDelivery) {
                          _paymentMethod = PaymentMethod.stripe;
                        }
                      });
                    },
            ),
            const SizedBox(height: 12),
            if (_deliveryType == DeliveryType.homeDelivery) ...[
              TextField(
                controller: _shippingAddressController,
                decoration: const InputDecoration(
                  labelText: 'Dirección de envío *',
                  hintText: 'Zona, calle, número y referencias para el despacho',
                  prefixIcon: Icon(Icons.location_on_outlined),
                ),
                maxLines: 2,
              ),
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.blue.shade50,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.blue.shade200),
                ),
                child: Row(
                  children: [
                    Icon(Icons.info_outline, size: 16, color: Colors.blue.shade800),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        'Política 3: Los despachos se procesan previa confirmación de pago con Stripe.',
                        style: TextStyle(fontSize: 11, color: Colors.blue.shade900),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 12),
            ],
            if (_deliveryType == DeliveryType.storePickup) ...[
              DropdownButtonFormField<String>(
                isExpanded: true,
                value: pickupBranchId,
                decoration: const InputDecoration(
                  labelText: 'Sucursal de retiro *',
                ),
                hint: const Text('Selecciona una sucursal'),
                items: branches
                    .map(
                      (branch) => DropdownMenuItem(
                        value: branch.id,
                        child: Text(
                          '${branch.name} · ${branch.city}',
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    )
                    .toList(growable: false),
                onChanged: isSaving
                    ? null
                    : (value) => setState(() => _pickupBranchId = value),
              ),
              const SizedBox(height: 12),
            ],
            Text(
              '2. Método de Pago',
              style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
            ),
            const SizedBox(height: 8),
            DropdownButtonFormField<PaymentMethod>(
              isExpanded: true,
              value: _paymentMethod,
              decoration: const InputDecoration(labelText: 'Método de pago'),
              items: [
                if (_deliveryType == DeliveryType.storePickup)
                  const DropdownMenuItem(
                    value: PaymentMethod.cash,
                    child: Text('Efectivo al retirar en tienda'),
                  ),
                const DropdownMenuItem(
                  value: PaymentMethod.stripe,
                  child: Text('Tarjeta de débito / crédito (Stripe)'),
                ),
              ],
              onChanged: isSaving || _deliveryType == DeliveryType.homeDelivery
                  ? null
                  : (value) => setState(() => _paymentMethod = value!),
            ),
            const SizedBox(height: 16),
          ],
          AppButton(
            label: _isOrderPayment || _paymentMethod == PaymentMethod.stripe
                ? 'Pagar con Stripe'
                : 'Confirmar retiro en tienda',
            icon: Icon(
              _isOrderPayment || _paymentMethod == PaymentMethod.stripe
                  ? Icons.credit_card_outlined
                  : Icons.storefront_outlined,
            ),
            onPressed: isSaving ? null : () => _submit(pickupBranchId),
            isLoading: isSaving,
            expand: true,
          ),
        ],
      ),
    );
  }

  String? _selectedBranchId(List<PickupBranch> branches) {
    if (_pickupBranchId != null &&
        branches.any((branch) => branch.id == _pickupBranchId)) {
      return _pickupBranchId;
    }
    return branches.where((branch) => branch.isDefault).firstOrNull?.id ??
        branches.firstOrNull?.id;
  }

  Future<void> _submit(String? pickupBranchId) async {
    if (_isOrderPayment) {
      await _checkoutStripe();
      return;
    }

    if (_deliveryType == DeliveryType.homeDelivery) {
      final address = _shippingAddressController.text.trim();
      if (address.isEmpty) {
        AppSnackBar.show(
          context,
          'Ingresa la dirección para el envío de prendas.',
          tone: AppSnackBarTone.error,
        );
        return;
      }
      await _checkoutStripe(
        deliveryType: 'ENVIO_DOMICILIO',
        shippingAddress: address,
      );
      return;
    }

    // Retiro en sucursal
    if (pickupBranchId == null) {
      AppSnackBar.show(
        context,
        'Selecciona una sucursal para el retiro.',
        tone: AppSnackBarTone.error,
      );
      return;
    }

    if (_paymentMethod == PaymentMethod.stripe) {
      await _checkoutStripe(
        pickupBranchId: pickupBranchId,
        deliveryType: 'RETIRO_TIENDA',
      );
      return;
    }

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Confirmar compra en tienda'),
        content: const Text(
          'Se creará el pedido para retiro en sucursal con pago en efectivo.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Volver'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Confirmar'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    await _controller.checkoutCash(
      pickupBranchId: pickupBranchId,
      deliveryType: 'RETIRO_TIENDA',
    );
    if (!mounted) return;
    _showControllerFeedback();
    if (_controller.status == OrderControllerStatus.error ||
        _controller.selectedOrder == null) {
      return;
    }
    Navigator.of(context).pushReplacementNamed(
      AppRoutes.orders,
      arguments: _controller.selectedOrder!.id,
    );
  }

  Future<void> _checkoutStripe({
    String? pickupBranchId,
    String deliveryType = 'ENVIO_DOMICILIO',
    String? shippingAddress,
  }) async {
    if (AppConfig.stripePublishableKey.isEmpty) {
      AppSnackBar.show(
        context,
        'Configura STRIPE_PUBLISHABLE_KEY para pagar con tarjeta.',
        tone: AppSnackBarTone.error,
      );
      return;
    }

    final result = _isOrderPayment
        ? await _controller.payOrder(orderId: widget.orderId!)
        : await _controller.checkoutStripe(
            pickupBranchId: pickupBranchId,
            deliveryType: deliveryType,
            shippingAddress: shippingAddress,
          );
    if (!mounted) return;
    if (result == null) {
      AppSnackBar.show(
        context,
        _controller.errorMessage ?? 'No se pudo iniciar el pago con Stripe.',
        tone: AppSnackBarTone.error,
      );
      return;
    }

    try {
      await Stripe.instance.initPaymentSheet(
        paymentSheetParameters: SetupPaymentSheetParameters(
          merchantDisplayName: 'FashionStore',
          paymentIntentClientSecret: result.checkout.clientSecret,
        ),
      );
      await Stripe.instance.presentPaymentSheet();
      if (!mounted) return;

      // Mensaje de éxito con número de guía si aplica
      final tracking = result.checkout.trackingNumber;
      if (tracking != null && tracking.isNotEmpty) {
        await showDialog<void>(
          context: context,
          builder: (context) => AlertDialog(
            icon: const Icon(Icons.check_circle, color: Colors.green, size: 48),
            title: const Text('¡Compra y Pago Confirmados!'),
            content: Text(
              'Tu pago ha sido validado exitosamente en Stripe.\n\n'
              'Guía de Despacho Asignada:\n$tracking\n\n'
              'Podrás rastrear la línea de vida de tu pedido desde la sección de pedidos.',
            ),
            actions: [
              FilledButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('Entendido'),
              ),
            ],
          ),
        );
      }

      if (!mounted) return;
      Navigator.of(context).pushReplacementNamed(
        AppRoutes.orders,
        arguments: result.checkout.orderId,
      );
    } on StripeException catch (error) {
      if (!mounted) return;
      AppSnackBar.show(
        context,
        error.error.localizedMessage ?? 'No se pudo completar el pago.',
        tone: AppSnackBarTone.error,
      );
    } catch (_) {
      if (!mounted) return;
      AppSnackBar.show(
        context,
        'No se pudo completar el pago.',
        tone: AppSnackBarTone.error,
      );
    }
  }

  void _showControllerFeedback() {
    final isError = _controller.status == OrderControllerStatus.error;
    final message = isError
        ? _controller.errorMessage
        : _controller.feedbackMessage;
    if (message != null) {
      AppSnackBar.show(
        context,
        message,
        tone: isError ? AppSnackBarTone.error : AppSnackBarTone.success,
      );
    }
  }
}

class _OrderSummary extends StatelessWidget {
  const _OrderSummary({required this.order});

  final Order order;

  @override
  Widget build(BuildContext context) {
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Pedido ${order.id.substring(0, 8)}',
            style: Theme.of(
              context,
            ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 8),
          for (final item in order.items)
            ListTile(
              contentPadding: EdgeInsets.zero,
              leading: SizedBox(
                width: 40,
                height: 48,
                child: ProductImage(imageUrl: item.imageUrl),
              ),
              title: Text(item.productName),
              subtitle: Text('${item.variantSku} · Cantidad ${item.quantity}'),
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
    );
  }
}

String _currencyLabel(String currency) {
  return currency.toLowerCase() == 'bob' ? 'Bs' : currency.toUpperCase();
}
