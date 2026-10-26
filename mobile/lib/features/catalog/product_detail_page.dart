import 'package:flutter/material.dart';

import '../../core/network/api_exception.dart';
import '../auth/auth_controller.dart';
import '../auth/login_dialog.dart';
import '../cart/cart_api.dart';
import '../reservations/reservation_models.dart';
import '../../shared/widgets/app_button.dart';
import '../../shared/widgets/app_card.dart';
import '../../shared/widgets/app_section_title.dart';
import '../../shared/widgets/app_snack_bar.dart';
import '../../shared/widgets/product_image.dart';
import '../../shared/widgets/product_price.dart';
import '../../shared/widgets/quantity_selector.dart';
import '../../shared/widgets/variant_selector.dart';
import 'catalog_api.dart';
import 'catalog_models.dart';
import 'virtual_try_on_page.dart';

class ProductDetailArguments {
  const ProductDetailArguments({
    required this.product,
    this.sizes = const [],
    this.colors = const [],
    this.branches = const [],
    this.branchId,
    this.reservationArguments,
  });

  final Product product;
  final List<Size> sizes;
  final List<CatalogColor> colors;
  final List<Branch> branches;
  final String? branchId;
  final ReservationArguments? reservationArguments;
}

class ProductDetailPage extends StatefulWidget {
  const ProductDetailPage({
    super.key,
    this.arguments,
    this.authController,
    this.cartApi,
    this.onAddToCart,
  });

  final ProductDetailArguments? arguments;
  final AuthController? authController;
  final CartApi? cartApi;
  final VoidCallback? onAddToCart;

  @override
  State<ProductDetailPage> createState() => _ProductDetailPageState();
}

class _ProductDetailPageState extends State<ProductDetailPage> {
  int _selectedVariantIndex = 0;
  int _quantity = 1;
  bool _addingToCart = false;
  bool _loadingAvailability = false;

  Product? get _product => widget.arguments?.product;

  List<ProductVariant> get _variants => _product?.variants ?? const [];

  ProductVariant? get _selectedVariant => _variants.isEmpty
      ? null
      : _variants[_selectedVariantIndex.clamp(0, _variants.length - 1).toInt()];

  @override
  Widget build(BuildContext context) {
    final product = _product;
    if (product == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Detalle de producto')),
        body: const Center(
          child: Padding(
            padding: EdgeInsets.all(20),
            child: Text('El detalle reutilizará el producto del catálogo.'),
          ),
        ),
      );
    }

    final variant = _selectedVariant;
    final imageUrl = variant?.imageUrl ?? product.imageUrl;
    final price = variant?.price ?? 0;
    final status = variant?.status ?? product.status;
    final quantity = variant?.branchQuantity ?? product.branchQuantity;
    final branch = _branchName(widget.arguments!);

    return Scaffold(
      appBar: AppBar(title: const Text('Detalle de producto')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          AspectRatio(
            aspectRatio: 1,
            child: ProductImage(
              imageUrl: imageUrl,
              borderRadius: const BorderRadius.all(Radius.circular(12)),
            ),
          ),
          if (_variants.length > 1) ...[
            const SizedBox(height: 12),
            _imageGallery(),
          ],
          const SizedBox(height: 24),
          AppSectionTitle(
            title: product.name,
            subtitle: product.sku ?? 'Producto FashionStore',
          ),
          const SizedBox(height: 12),
          ProductPrice(price: price, originalPrice: variant?.originalPrice),
          if (product.description != null &&
              product.description!.isNotEmpty) ...[
            const SizedBox(height: 16),
            Text(product.description!),
          ],
          const SizedBox(height: 20),
          if (_variants.isNotEmpty) _variantOptions(),
          const SizedBox(height: 20),
          AppCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Información de la variante',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 12),
                _detailLine(
                  'SKU',
                  variant?.sku ?? product.sku ?? 'No disponible',
                ),
                _detailLine(
                  'Talla',
                  _sizeName(variant?.sizeId ?? product.sizeId),
                ),
                _detailLine(
                  'Color',
                  _colorName(variant?.colorId ?? product.colorId),
                ),
                _detailLine('Estado', _statusName(status)),
                _detailLine('Disponibilidad', _availability(quantity, branch)),
              ],
            ),
          ),
          const SizedBox(height: 20),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Cantidad', style: Theme.of(context).textTheme.titleMedium),
              QuantitySelector(
                value: _quantity,
                max: _quantityLimit(quantity),
                onChanged: (value) => setState(() => _quantity = value),
              ),
            ],
          ),
          const SizedBox(height: 20),
          AppButton(
            label: 'Agregar al carrito',
            icon: const Icon(Icons.shopping_bag_outlined),
            onPressed:
                widget.onAddToCart ??
                (_canAddToCart(variant, quantity) ? _addToCart : null),
            isLoading: _addingToCart,
            expand: true,
          ),
          const SizedBox(height: 12),
          AppButton(
            label: 'Reservar prenda',
            icon: const Icon(Icons.bookmark_add_outlined),
            onPressed: _canReserve(product, variant) ? _reserveGarment : null,
            variant: AppButtonVariant.outlined,
            expand: true,
          ),
          const SizedBox(height: 12),
          AppButton(
            label: 'Ver disponibilidad en tiendas',
            icon: const Icon(Icons.storefront_outlined),
            onPressed: () => _checkMultiBranchAvailability(
              variant?.id ?? product.variants?.firstOrNull?.id,
            ),
            isLoading: _loadingAvailability,
            variant: AppButtonVariant.outlined,
            expand: true,
          ),
          if (imageUrl != null && imageUrl.trim().isNotEmpty) ...[
            const SizedBox(height: 12),
            AppButton(
              label: 'Probar prenda',
              icon: const Icon(Icons.checkroom_outlined),
              onPressed: () {
                Navigator.of(context).push(
                  MaterialPageRoute<void>(
                    builder: (_) => VirtualTryOnPage(
                      productName: product.name,
                      garmentImageUrl: imageUrl,
                    ),
                  ),
                );
              },
              variant: AppButtonVariant.outlined,
              expand: true,
            ),
          ],
        ],
      ),
    );
  }

  Widget _imageGallery() {
    return SizedBox(
      height: 76,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: _variants.length,
        separatorBuilder: (_, _) => const SizedBox(width: 8),
        itemBuilder: (context, index) {
          final variant = _variants[index];
          return InkWell(
            onTap: () => _selectVariant(index),
            borderRadius: BorderRadius.circular(8),
            child: SizedBox(
              width: 76,
              child: ProductImage(
                imageUrl: variant.imageUrl,
                borderRadius: BorderRadius.circular(8),
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _variantOptions() {
    return AppVariantSelector(
      options: [
        for (var index = 0; index < _variants.length; index++)
          AppVariantOption(
            id: _variants[index].id,
            label: _variantLabel(_variants[index]),
          ),
      ],
      selectedId: _selectedVariant?.id,
      onChanged: (variantId) {
        final index = _variants.indexWhere(
          (variant) => variant.id == variantId,
        );
        if (index >= 0) _selectVariant(index);
      },
    );
  }

  void _selectVariant(int index) {
    final maxQuantity = _quantityLimit(_variants[index].branchQuantity);
    setState(() {
      _selectedVariantIndex = index;
      if (_quantity > maxQuantity) _quantity = maxQuantity;
    });
  }

  String _variantLabel(ProductVariant variant) {
    final labels = [
      _sizeName(variant.sizeId),
      _colorName(variant.colorId),
    ].where((label) => label != 'No disponible');
    final suffix = labels.isEmpty ? '' : '${labels.join(' · ')} · ';
    return '$suffix${variant.sku}';
  }

  String _sizeName(String? id) {
    if (id == null) return 'No disponible';
    return widget.arguments!.sizes
            .where((size) => size.id == id)
            .firstOrNull
            ?.name ??
        id;
  }

  String _colorName(String? id) {
    if (id == null) return 'No disponible';
    return widget.arguments!.colors
            .where((color) => color.id == id)
            .firstOrNull
            ?.name ??
        id;
  }

  String _statusName(ProductStatus? status) {
    return switch (status) {
      ProductStatus.active => 'Activo',
      ProductStatus.pending => 'Pendiente',
      ProductStatus.inactive => 'Inactivo',
      null => 'No disponible',
    };
  }

  String _availability(int? quantity, String? branch) {
    final suffix = branch == null ? '' : ' en $branch';
    return switch (quantity) {
      null => 'No consultada$suffix',
      > 0 => 'Disponible ($quantity)$suffix',
      _ => 'Agotado$suffix',
    };
  }

  int _quantityLimit(int? quantity) {
    if (quantity == null) return 99;
    return quantity > 0 ? quantity : 1;
  }

  bool _canAddToCart(ProductVariant? variant, int? quantity) {
    return widget.authController != null &&
        variant != null &&
        (quantity == null || quantity > 0);
  }

  bool _canReserve(Product? product, ProductVariant? variant) {
    return widget.authController != null && product != null && variant != null;
  }

  void _reserveGarment() {
    final product = _product;
    final variant = _selectedVariant;
    if (!_canReserve(product, variant)) return;

    final selectedItem = ReservationDraftItem(
      variantId: variant!.id,
      quantity: _quantity,
      productName: product!.name,
      variantSku: variant.sku.isEmpty ? product.sku : variant.sku,
      imageUrl: variant.imageUrl ?? product.imageUrl,
    );
    final items = [...?widget.arguments?.reservationArguments?.items];
    final existingIndex = items.indexWhere(
      (item) => item.variantId == selectedItem.variantId,
    );
    if (existingIndex == -1) {
      items.add(selectedItem);
    } else {
      final existing = items[existingIndex];
      items[existingIndex] = ReservationDraftItem(
        variantId: existing.variantId,
        quantity: existing.quantity + selectedItem.quantity,
        productName: selectedItem.productName ?? existing.productName,
        variantSku: selectedItem.variantSku ?? existing.variantSku,
        imageUrl: selectedItem.imageUrl ?? existing.imageUrl,
      );
    }

    final updatedArguments = ReservationArguments(items: items);
    Navigator.of(context).pop(updatedArguments);
  }

  Future<void> _addToCart() async {
    final product = _product;
    final variant = _selectedVariant;
    final authController = widget.authController;
    if (product == null || variant == null || authController == null) return;

    setState(() => _addingToCart = true);
    try {
      if (!authController.isAuthenticated) {
        final loggedIn = await LoginDialog.show(
          context: context,
          controller: authController,
        );
        if (!mounted || loggedIn != true || !authController.isAuthenticated) {
          return;
        }
      }

      final api =
          widget.cartApi ??
          CartApi(
            tokenProvider: () => authController.accessToken,
            onUnauthorized: authController.handleUnauthorized,
          );
      final result = await api.addItem(
        variantId: variant.id,
        quantity: _quantity,
      );
      if (mounted) {
        AppSnackBar.show(
          context,
          result.message,
          tone: AppSnackBarTone.success,
        );
      }
    } catch (error) {
      if (mounted) {
        final message = error is ApiException
            ? error.message
            : 'No se pudo agregar el producto al carrito.';
        AppSnackBar.show(context, message, tone: AppSnackBarTone.error);
      }
    } finally {
      if (mounted) setState(() => _addingToCart = false);
    }
  }

  String? _branchName(ProductDetailArguments arguments) {
    final id = arguments.branchId;
    if (id == null) return null;
    return arguments.branches
        .where((branch) => branch.id == id)
        .firstOrNull
        ?.name;
  }

  Future<void> _checkMultiBranchAvailability(String? variantId) async {
    if (variantId == null || variantId.isEmpty) {
      AppSnackBar.show(context, 'Selecciona una talla o variante primero.');
      return;
    }

    setState(() => _loadingAvailability = true);
    try {
      final api = CatalogApi(
        tokenProvider: () => widget.authController?.accessToken,
        onUnauthorized: widget.authController?.handleUnauthorized,
      );
      final availability = await api.getVariantAvailability(variantId: variantId);
      if (!mounted) return;
      _showAvailabilityBottomSheet(availability);
    } catch (e) {
      if (!mounted) return;
      AppSnackBar.show(context, 'No se pudo consultar el stock por sucursal.');
    } finally {
      if (mounted) setState(() => _loadingAvailability = false);
    }
  }

  void _showAvailabilityBottomSheet(MultiBranchAvailability availability) {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return DraggableScrollableSheet(
          initialChildSize: 0.55,
          minChildSize: 0.35,
          maxChildSize: 0.85,
          expand: false,
          builder: (context, scrollController) {
            return Padding(
              padding: const EdgeInsets.fromLTRB(20, 12, 20, 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Center(
                    child: Container(
                      width: 40,
                      height: 4,
                      decoration: BoxDecoration(
                        color: Colors.grey.shade300,
                        borderRadius: BorderRadius.circular(2),
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'Stock en Sucursales',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: Colors.blue.shade50,
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: Colors.blue.shade200),
                        ),
                        child: Text(
                          'Total Red: ${availability.totalAvailable}',
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w700,
                            color: Colors.blue.shade800,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  const Text(
                    'Disponibilidad física inmediata en las tiendas de la marca.',
                    style: TextStyle(fontSize: 12, color: Colors.grey),
                  ),
                  const Divider(height: 24),
                  Expanded(
                    child: availability.branches.isEmpty
                        ? const Center(
                            child: Text('No hay sucursales activas registradas.'),
                          )
                        : ListView.separated(
                            controller: scrollController,
                            itemCount: availability.branches.length,
                            separatorBuilder: (_, __) => const Divider(height: 16),
                            itemBuilder: (context, index) {
                              final branch = availability.branches[index];
                              final isAvail = branch.availableQuantity > 5;
                              final isLow = branch.availableQuantity > 0 && branch.availableQuantity <= 5;

                              final badgeColor = isAvail
                                  ? Colors.green.shade50
                                  : isLow
                                      ? Colors.amber.shade50
                                      : Colors.red.shade50;
                              final textColor = isAvail
                                  ? Colors.green.shade800
                                  : isLow
                                      ? Colors.amber.shade900
                                      : Colors.red.shade800;
                              final borderColor = isAvail
                                  ? Colors.green.shade200
                                  : isLow
                                      ? Colors.amber.shade300
                                      : Colors.red.shade200;
                              final badgeText = isAvail
                                  ? 'Disponible (${branch.availableQuantity})'
                                  : isLow
                                      ? 'Últimas ${branch.availableQuantity}'
                                      : 'Agotado';

                              return Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          branch.branchName,
                                          style: const TextStyle(
                                            fontWeight: FontWeight.w600,
                                            fontSize: 14,
                                          ),
                                        ),
                                        if (branch.city != null)
                                          Text(
                                            branch.city!,
                                            style: TextStyle(
                                              fontSize: 12,
                                              color: Colors.grey.shade600,
                                            ),
                                          ),
                                        if (branch.address != null && branch.address!.isNotEmpty)
                                          Padding(
                                            padding: const EdgeInsets.only(top: 4),
                                            child: Row(
                                              children: [
                                                Icon(Icons.place_outlined, size: 13, color: Colors.grey.shade600),
                                                const SizedBox(width: 4),
                                                Expanded(
                                                  child: Text(
                                                    branch.address!,
                                                    style: TextStyle(
                                                      fontSize: 11,
                                                      color: Colors.grey.shade700,
                                                    ),
                                                    maxLines: 1,
                                                    overflow: TextOverflow.ellipsis,
                                                  ),
                                                ),
                                              ],
                                            ),
                                          ),
                                        if (branch.phone != null && branch.phone!.isNotEmpty)
                                          Padding(
                                            padding: const EdgeInsets.only(top: 2),
                                            child: Row(
                                              children: [
                                                Icon(Icons.phone_outlined, size: 13, color: Colors.grey.shade600),
                                                const SizedBox(width: 4),
                                                Text(
                                                  branch.phone!,
                                                  style: TextStyle(
                                                    fontSize: 11,
                                                    color: Colors.grey.shade700,
                                                  ),
                                                ),
                                              ],
                                            ),
                                          ),
                                      ],
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                                    decoration: BoxDecoration(
                                      color: badgeColor,
                                      borderRadius: BorderRadius.circular(8),
                                      border: Border.all(color: borderColor),
                                    ),
                                    child: Text(
                                      badgeText,
                                      style: TextStyle(
                                        fontSize: 11,
                                        fontWeight: FontWeight.bold,
                                        color: textColor,
                                      ),
                                    ),
                                  ),
                                ],
                              );
                            },
                          ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  Widget _detailLine(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 116,
            child: Text(
              label,
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
          ),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }
}
