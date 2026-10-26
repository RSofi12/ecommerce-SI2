import { Injectable } from '@angular/core';
import { CatalogProduct } from '../../features/shared/models/catalog.model';

export interface OfflineSyncMeta {
  key: string;
  version: number;
  synced_at: string;
  total_products: number;
  tenant_id: string | null;
  branch_id: string | null;
}

export interface OfflinePackData {
  version: number;
  tenant_id: string | null;
  branch_id: string | null;
  total_products: number;
  products: CatalogProduct[];
  synced_at: string;
}

@Injectable({ providedIn: 'root' })
export class IdbCatalogService {
  private readonly dbName = 'fashionstore_local_db';
  private readonly dbVersion = 1;
  private dbPromise: Promise<IDBDatabase> | null = null;

  isAvailable(): boolean {
    return typeof window !== 'undefined' && 'indexedDB' in window;
  }

  private getDb(): Promise<IDBDatabase> {
    if (!this.isAvailable()) {
      return Promise.reject(new Error('IndexedDB no está soportado en este entorno.'));
    }

    if (!this.dbPromise) {
      this.dbPromise = new Promise((resolve, reject) => {
        const request = window.indexedDB.open(this.dbName, this.dbVersion);

        request.onupgradeneeded = (event: IDBVersionChangeEvent) => {
          const db = (event.target as IDBOpenDBRequest).result;

          // Object store para productos de catálogo offline
          if (!db.objectStoreNames.contains('catalog_products')) {
            const productStore = db.createObjectStore('catalog_products', { keyPath: 'id' });
            productStore.createIndex('by_name', 'name', { unique: false });
            productStore.createIndex('by_category', 'category_id', { unique: false });
          }

          // Object store para metadatos de sincronización
          if (!db.objectStoreNames.contains('catalog_meta')) {
            db.createObjectStore('catalog_meta', { keyPath: 'key' });
          }
        };

        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
      });
    }

    return this.dbPromise;
  }

  async saveOfflinePack(pack: OfflinePackData): Promise<void> {
    const db = await this.getDb();

    return new Promise((resolve, reject) => {
      const transaction = db.transaction(['catalog_products', 'catalog_meta'], 'readwrite');
      const productStore = transaction.objectStore('catalog_products');
      const metaStore = transaction.objectStore('catalog_meta');

      // Limpiar catálogo previo e insertar nuevos productos
      productStore.clear();

      for (const product of pack.products) {
        productStore.put(product);
      }

      // Guardar metadatos de sincronización
      const meta: OfflineSyncMeta = {
        key: 'sync_info',
        version: pack.version,
        synced_at: pack.synced_at,
        total_products: pack.total_products,
        tenant_id: pack.tenant_id,
        branch_id: pack.branch_id,
      };
      metaStore.put(meta);

      transaction.oncomplete = () => resolve();
      transaction.onerror = () => reject(transaction.error);
    });
  }

  async getOfflineProducts(filters?: {
    q?: string;
    category_id?: string;
    size_id?: string;
    color_id?: string;
  }): Promise<CatalogProduct[]> {
    const db = await this.getDb();

    return new Promise((resolve, reject) => {
      const transaction = db.transaction('catalog_products', 'readonly');
      const store = transaction.objectStore('catalog_products');
      const request = store.getAll();

      request.onsuccess = () => {
        let products = (request.result as CatalogProduct[]) || [];

        // Aplicar filtros en memoria sobre la base local IndexedDB
        if (filters?.q) {
          const query = filters.q.toLowerCase().trim();
          products = products.filter(
            (p) =>
              p.name.toLowerCase().includes(query) ||
              (p.description && p.description.toLowerCase().includes(query)) ||
              (p.sku && p.sku.toLowerCase().includes(query)),
          );
        }

        if (filters?.category_id) {
          products = products.filter((p) => p.category_id === filters.category_id);
        }

        if (filters?.size_id) {
          products = products.filter((p) =>
            p.variants?.some((v) => v.size_id === filters.size_id && v.status === 'active'),
          );
        }

        if (filters?.color_id) {
          products = products.filter((p) =>
            p.variants?.some((v) => v.color_id === filters.color_id && v.status === 'active'),
          );
        }

        resolve(products);
      };

      request.onerror = () => reject(request.error);
    });
  }

  async getSyncMeta(): Promise<OfflineSyncMeta | null> {
    const db = await this.getDb();

    return new Promise((resolve, reject) => {
      const transaction = db.transaction('catalog_meta', 'readonly');
      const store = transaction.objectStore('catalog_meta');
      const request = store.get('sync_info');

      request.onsuccess = () => resolve((request.result as OfflineSyncMeta) || null);
      request.onerror = () => reject(request.error);
    });
  }

  async clearCache(): Promise<void> {
    const db = await this.getDb();

    return new Promise((resolve, reject) => {
      const transaction = db.transaction(['catalog_products', 'catalog_meta'], 'readwrite');
      transaction.objectStore('catalog_products').clear();
      transaction.objectStore('catalog_meta').clear();

      transaction.oncomplete = () => resolve();
      transaction.onerror = () => reject(transaction.error);
    });
  }
}
