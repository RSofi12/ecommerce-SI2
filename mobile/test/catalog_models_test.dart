import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/features/catalog/catalog_models.dart';

void main() {
  test('parsea producto, precio decimal y variantes en el orden recibido', () {
    final product = Product.fromJson({
      'id': 'product-id',
      'name': 'Producto demo',
      'description': null,
      'price': '110.50',
      'provider_id': null,
      'category_id': 'category-id',
      'season_id': null,
      'collection_id': null,
      'sku': 'SKU-1',
      'image_url': null,
      'image_public_id': 'internal-id',
      'status': 'active',
      'size_id': null,
      'color_id': null,
      'branch_quantity': null,
      'variants': [
        {
          'id': 'variant-2',
          'product_id': 'product-id',
          'sku': 'SKU-2',
          'price': 110.50,
          'size_id': null,
          'color_id': 'color-2',
          'image_url': 'https://example.com/two.jpg',
          'image_public_id': 'internal-two',
          'status': 'active',
          'branch_quantity': 3,
        },
        {
          'id': 'variant-1',
          'product_id': 'product-id',
          'sku': 'SKU-1',
          'price': 110,
          'size_id': 'size-1',
          'color_id': null,
          'image_url': null,
          'image_public_id': null,
          'status': 'active',
          'branch_quantity': null,
        },
      ],
    });

    expect(product.variants!.first.price, 110.50);
    expect(product.status, ProductStatus.active);
    expect(product.variants, hasLength(2));
    expect(product.variants![0].id, 'variant-2');
    expect(product.variants![0].imageUrl, 'https://example.com/two.jpg');
    expect(product.variants![0].branchQuantity, 3);
  });

  test('parsea los modelos públicos de filtros y sucursales', () {
    expect(
      Category.fromJson({'id': 'category-id', 'name': 'Blusas'}).name,
      'Blusas',
    );
    expect(
      CatalogColor.fromJson({
        'id': 'color-id',
        'name': 'Negro',
        'hex_code': '#111111',
      }).hexCode,
      '#111111',
    );
    expect(
      Collection.fromJson({
        'id': 'collection-id',
        'name': 'Urbana',
        'season_id': 'season-id',
      }).seasonId,
      'season-id',
    );
    expect(
      Branch.fromJson({
        'id': 'branch-id',
        'name': 'Central',
        'city': 'La Paz',
        'is_default': true,
        'is_active': true,
      }).isDefault,
      isTrue,
    );
  });

  test('parsea disponibilidad multisede por sucursal (CU10)', () {
    final availability = MultiBranchAvailability.fromJson({
      'variant_id': 'var-123',
      'tenant_id': 'tenant-abc',
      'total_available': 15,
      'branches': [
        {
          'branch_id': 'b-1',
          'branch_name': 'Sucursal Central',
          'city': 'Santa Cruz',
          'address': 'Av. Monseñor Rivero 200',
          'phone': '70012345',
          'opening_hours': '09:00 - 20:00',
          'available_quantity': 10,
          'quantity': 12,
          'reserved_quantity': 2,
          'is_active': true,
        },
        {
          'branch_id': 'b-2',
          'branch_name': 'Sucursal Equipetrol',
          'city': 'Santa Cruz',
          'address': 'Calle 7 Este',
          'phone': '70054321',
          'opening_hours': '10:00 - 21:00',
          'available_quantity': 5,
          'quantity': 5,
          'reserved_quantity': 0,
          'is_active': true,
        },
      ],
    });

    expect(availability.variantId, 'var-123');
    expect(availability.totalAvailable, 15);
    expect(availability.branches, hasLength(2));
    expect(availability.branches[0].branchName, 'Sucursal Central');
    expect(availability.branches[0].availableQuantity, 10);
    expect(availability.branches[1].availableQuantity, 5);
  });

  test('parsea snapshot de catalogo offline y metadatos (CU08 y CU09)', () {
    final pack = OfflineCatalogPack.fromJson({
      'version': '1.0',
      'synced_at': '2026-10-26T03:00:00Z',
      'tenant_id': 'tenant-abc',
      'branch_id': 'b-1',
      'products': [
        {
          'id': 'p-1',
          'name': 'Vestido Seda',
          'category_id': 'cat-1',
          'sku': 'SKU-VEST-01',
          'status': 'active',
          'variants': [
            {
              'id': 'v-1',
              'product_id': 'p-1',
              'sku': 'SKU-VEST-01-M',
              'price': 85.0,
              'status': 'active',
              'branch_quantity': 4,
            }
          ]
        }
      ]
    });

    expect(pack.version, '1.0');
    expect(pack.products, hasLength(1));
    expect(pack.products.first.name, 'Vestido Seda');
    expect(pack.products.first.variants?.first.price, 85.0);

    final meta = OfflineSyncMeta.fromMap({
      'synced_at': '2026-10-26T03:00:00Z',
      'product_count': 1,
      'version': '1.0',
      'branch_id': 'b-1',
    });

    expect(meta.productCount, 1);
    expect(meta.version, '1.0');
    expect(meta.branchId, 'b-1');
  });
}
