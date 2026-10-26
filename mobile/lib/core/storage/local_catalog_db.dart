import 'dart:convert';

import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';

import '../../features/catalog/catalog_models.dart';

class LocalCatalogDb {
  LocalCatalogDb({Database? database}) : _database = database;

  Database? _database;

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDb();
    return _database!;
  }

  Future<Database> _initDb() async {
    final dbPath = await getDatabasesPath();
    final path = p.join(dbPath, 'fashionstore_local.db');

    return openDatabase(
      path,
      version: 1,
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE local_products (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category_id TEXT,
            description TEXT,
            sku TEXT,
            image_url TEXT,
            status TEXT,
            raw_json TEXT NOT NULL
          )
        ''');

        await db.execute('''
          CREATE TABLE catalog_sync_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
          )
        ''');
      },
    );
  }

  Future<int> saveOfflinePack(Map<String, dynamic> packData) async {
    final db = await database;
    final productsRaw = packData['products'];
    final products = productsRaw is List ? productsRaw.whereType<Map>().toList() : [];

    final version = packData['version']?.toString() ?? '1.0';
    final syncedAt = packData['synced_at']?.toString() ?? DateTime.now().toIso8601String();
    final branchId = packData['branch_id']?.toString() ?? '';

    await db.transaction((txn) async {
      await txn.delete('local_products');

      final batch = txn.batch();
      for (final raw in products) {
        final productMap = Map<String, dynamic>.from(raw);
        final id = productMap['id']?.toString() ?? '';
        if (id.isEmpty) continue;

        batch.insert(
          'local_products',
          {
            'id': id,
            'name': productMap['name']?.toString() ?? '',
            'category_id': productMap['category_id']?.toString(),
            'description': productMap['description']?.toString(),
            'sku': productMap['sku']?.toString(),
            'image_url': productMap['image_url']?.toString(),
            'status': productMap['status']?.toString() ?? 'active',
            'raw_json': jsonEncode(productMap),
          },
          conflictAlgorithm: ConflictAlgorithm.replace,
        );
      }
      await batch.commit(noResult: true);

      // Metadatos de sincronización
      await txn.insert(
        'catalog_sync_meta',
        {'key': 'synced_at', 'value': syncedAt},
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
      await txn.insert(
        'catalog_sync_meta',
        {'key': 'product_count', 'value': products.length.toString()},
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
      await txn.insert(
        'catalog_sync_meta',
        {'key': 'version', 'value': version},
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
      if (branchId.isNotEmpty) {
        await txn.insert(
          'catalog_sync_meta',
          {'key': 'branch_id', 'value': branchId},
          conflictAlgorithm: ConflictAlgorithm.replace,
        );
      }
    });

    return products.length;
  }

  Future<List<Product>> queryProducts({
    String? query,
    String? categoryId,
    String? sizeId,
    String? colorId,
  }) async {
    final db = await database;
    final rows = await db.query('local_products');

    final cleanQuery = query?.trim().toLowerCase();

    final result = <Product>[];
    for (final row in rows) {
      try {
        final rawJson = row['raw_json'] as String?;
        if (rawJson == null || rawJson.isEmpty) continue;

        final map = jsonDecode(rawJson);
        if (map is! Map) continue;

        final product = Product.fromJson(Map<String, dynamic>.from(map));

        // Filtrado en memoria
        if (cleanQuery != null && cleanQuery.isNotEmpty) {
          final nameMatch = product.name.toLowerCase().contains(cleanQuery);
          final descMatch = product.description?.toLowerCase().contains(cleanQuery) ?? false;
          final skuMatch = product.sku?.toLowerCase().contains(cleanQuery) ?? false;
          if (!nameMatch && !descMatch && !skuMatch) {
            continue;
          }
        }

        if (categoryId != null && categoryId.isNotEmpty) {
          if (product.categoryId != categoryId) {
            continue;
          }
        }

        if (sizeId != null && sizeId.isNotEmpty) {
          final hasSize = product.variants?.any((v) => v.sizeId == sizeId) ?? false;
          if (!hasSize) continue;
        }

        if (colorId != null && colorId.isNotEmpty) {
          final hasColor = product.variants?.any((v) => v.colorId == colorId) ?? false;
          if (!hasColor) continue;
        }

        result.add(product);
      } catch (_) {
        // Ignorar registros corruptos
      }
    }

    return result;
  }

  Future<OfflineSyncMeta?> getSyncMeta() async {
    final db = await database;
    final rows = await db.query('catalog_sync_meta');
    if (rows.isEmpty) return null;

    final map = <String, dynamic>{};
    for (final row in rows) {
      final key = row['key']?.toString();
      final value = row['value']?.toString();
      if (key != null && value != null) {
        map[key] = value;
      }
    }

    final syncedAt = DateTime.tryParse(map['synced_at']?.toString() ?? '') ?? DateTime.now();
    final count = int.tryParse(map['product_count']?.toString() ?? '0') ?? 0;
    final version = map['version']?.toString() ?? '1.0';
    final branchId = map['branch_id']?.toString();

    return OfflineSyncMeta(
      syncedAt: syncedAt,
      productCount: count,
      version: version,
      branchId: branchId,
    );
  }

  Future<int> getCachedProductCount() async {
    final db = await database;
    final count = Sqflite.firstIntValue(
      await db.rawQuery('SELECT COUNT(*) FROM local_products'),
    );
    return count ?? 0;
  }

  Future<void> clear() async {
    final db = await database;
    await db.delete('local_products');
    await db.delete('catalog_sync_meta');
  }
}
