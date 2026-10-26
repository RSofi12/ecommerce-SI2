import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { firstValueFrom } from 'rxjs';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { lucideShoppingCart } from '@ng-icons/lucide';

import { toast } from '@spartan-ng/brain/sonner';

import { HlmBadgeImports } from '../../../components/badge/src';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmFieldImports } from '../../../components/field/src';
import { HlmInput } from '../../../components/input/src';
import { HlmSelectImports } from '../../../components/select/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { requestWithToast } from '../../../core/utils/request-toast.util';
import {
  CatalogBranch,
  CatalogCollectionItem,
  CatalogColorItem,
  CatalogNameItem,
  CatalogProduct,
  CatalogProductVariant,
} from '../../shared/models/catalog.model';
import { CatalogApiService } from '../../shared/services/catalog-api.service';
import { CartApiService } from '../../shared/services/cart-api.service';
import { SessionService } from '../../shared/services/session.service';
import { IdbCatalogService, OfflineSyncMeta } from '../../../core/offline/idb-catalog.service';
import { NetworkStatusService } from '../../../core/offline/network-status.service';

@Component({
  selector: 'app-catalog-page',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    ReactiveFormsModule,
    NgIcon,
    HlmButton,
    HlmInput,
    ...HlmBadgeImports,
    ...HlmCardImports,
    ...HlmFieldImports,
    ...HlmSelectImports,
  ],
  providers: [provideIcons({ lucideShoppingCart })],
  templateUrl: './catalog-page.component.html',
})
export class CatalogPageComponent {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(CatalogApiService);
  private readonly cartApi = inject(CartApiService);
  private readonly session = inject(SessionService);
  private readonly router = inject(Router);
  private readonly idb = inject(IdbCatalogService);
  protected readonly network = inject(NetworkStatusService);

  protected readonly branches = signal<CatalogBranch[]>([]);
  protected readonly categories = signal<CatalogNameItem[]>([]);
  protected readonly sizes = signal<CatalogNameItem[]>([]);
  protected readonly colors = signal<CatalogColorItem[]>([]);
  protected readonly seasons = signal<CatalogNameItem[]>([]);
  protected readonly collections = signal<CatalogCollectionItem[]>([]);
  protected readonly products = signal<CatalogProduct[]>([]);
  protected readonly recommendedProducts = signal<CatalogProduct[]>([]);
  protected readonly selectedVariantByProduct = signal<Record<string, string>>({});
  protected readonly selectedImageByProduct = signal<Record<string, number>>({});
  protected readonly addingToCartByProduct = signal<Record<string, boolean>>({});
  protected readonly loading = signal(false);
  protected readonly downloadingOffline = signal(false);
  protected readonly syncMeta = signal<OfflineSyncMeta | null>(null);
  protected readonly isOfflineActive = signal(false);
  private recommendationsRequestVersion = 0;

  protected readonly form = this.fb.nonNullable.group({
    q: [''],
    branch_id: [''],
    category_id: [''],
    size_id: [''],
    color_id: [''],
    season_id: [''],
    collection_id: [''],
  });

  protected readonly branchSelectLabel = (branchId: string | null | undefined): string => {
    if (!branchId) return 'Sucursal';
    const branch = this.branches().find((item) => item.id === branchId);
    return branch ? `${branch.name} - ${branch.city}` : branchId;
  };

  protected readonly categorySelectLabel = (categoryId: string | null | undefined): string => {
    if (!categoryId) return 'Categoría';
    return this.categories().find((category) => category.id === categoryId)?.name ?? categoryId;
  };

  protected readonly sizeSelectLabel = (sizeId: string | null | undefined): string => {
    if (!sizeId) return 'Talla';
    return this.sizes().find((size) => size.id === sizeId)?.name ?? sizeId;
  };

  protected readonly colorSelectLabel = (colorId: string | null | undefined): string => {
    if (!colorId) return 'Color';
    return this.colors().find((color) => color.id === colorId)?.name ?? colorId;
  };

  protected readonly seasonSelectLabel = (seasonId: string | null | undefined): string => {
    if (!seasonId) return 'Temporada';
    return this.seasons().find((season) => season.id === seasonId)?.name ?? seasonId;
  };

  protected readonly collectionSelectLabel = (collectionId: string | null | undefined): string => {
    if (!collectionId) return 'Colección';
    const collection = this.collections().find((item) => item.id === collectionId);
    if (!collection) return collectionId;
    return `${collection.name} - ${this.seasonName(collection.season_id)}`;
  };

  protected productDetailOrigin(): string {
    return this.router.url.startsWith('/app/cliente/catalog') ? 'catalog' : 'catalog-home';
  }

  constructor() {
    void this.loadData();
  }

  protected async search(): Promise<void> {
    this.loading.set(true);
    const value = this.form.getRawValue();

    if (!this.network.effectiveOnline()) {
      await this.loadFromIndexedDb(value);
      this.loading.set(false);
      return;
    }

    try {
      const response = await firstValueFrom(
        this.api.listProducts({
          q: value.q || undefined,
          branch_id: value.branch_id || undefined,
          category_id: value.category_id || undefined,
          size_id: value.size_id || undefined,
          color_id: value.color_id || undefined,
          season_id: value.season_id || undefined,
          collection_id: value.collection_id || undefined,
        }),
      );
      this.products.set(response.data ?? []);
      this.isOfflineActive.set(false);
      this.ensureSelectedVariants();
      void this.loadRecommendations();
    } catch (error) {
      toast.info('Sin conexión al servidor. Cargando catálogo desde base local.');
      await this.loadFromIndexedDb(value);
    } finally {
      this.loading.set(false);
    }
  }

  protected async loadFromIndexedDb(filters: { q?: string; category_id?: string; size_id?: string; color_id?: string }): Promise<void> {
    try {
      const offlineProducts = await this.idb.getOfflineProducts({
        q: filters.q || undefined,
        category_id: filters.category_id || undefined,
        size_id: filters.size_id || undefined,
        color_id: filters.color_id || undefined,
      });
      this.products.set(offlineProducts);
      this.isOfflineActive.set(true);
      this.ensureSelectedVariants();
      const meta = await this.idb.getSyncMeta();
      this.syncMeta.set(meta);
    } catch {
      toast.error('No se pudo acceder a la base local IndexedDB.');
    }
  }

  protected async downloadOfflineCatalog(): Promise<void> {
    if (!this.network.effectiveOnline()) {
      toast.warning('Necesitas conexión a internet para descargar el paquete de catálogo.');
      return;
    }

    this.downloadingOffline.set(true);
    try {
      const branchId = this.form.controls.branch_id.value || undefined;
      const resp = await firstValueFrom(this.api.getOfflineCatalogPack(branchId));
      if (resp.data) {
        await this.idb.saveOfflinePack(resp.data);
        const meta = await this.idb.getSyncMeta();
        this.syncMeta.set(meta);
        toast.success(`Catálogo local descargado (${resp.data.total_products} prendas disponibles sin conexión).`);
      }
    } catch (err) {
      toast.error(getErrorMessage(err, 'No se pudo descargar el paquete offline.'));
    } finally {
      this.downloadingOffline.set(false);
    }
  }

  protected resetFilters(): void {
    this.form.reset({
      q: '',
      branch_id: '',
      category_id: '',
      size_id: '',
      color_id: '',
      season_id: '',
      collection_id: '',
    });
    void this.search();
  }

  protected async updateBranchAvailability(): Promise<void> {
    await this.search();
  }

  protected async addSelectedVariantToCart(product: CatalogProduct): Promise<void> {
    const variant = this.selectedVariant(product);
    if (!variant) {
      toast.warning('Selecciona una variante primero.');
      return;
    }

    this.addingToCartByProduct.update((current) => ({ ...current, [product.id]: true }));
    try {
      void this.recordProductView(product.id);
      await requestWithToast(this.cartApi.addItem({ variant_id: variant.id, branch_id: this.form.getRawValue().branch_id || undefined, quantity: 1 }), {
        loading: 'Agregando al carrito...',
        success: 'Producto agregado al carrito.',
        error: 'No se pudo agregar al carrito.',
      });
    } catch {
      // El toast de error ya se mostró con requestWithToast
    } finally {
      this.addingToCartByProduct.update((current) => ({ ...current, [product.id]: false }));
    }
  }

  private async loadData(): Promise<void> {
    try {
      const meta = await this.idb.getSyncMeta();
      this.syncMeta.set(meta);
    } catch {
      // Ignorar fallo de lectura idb inicial
    }

    if (!this.network.effectiveOnline()) {
      await this.loadFromIndexedDb(this.form.getRawValue());
      return;
    }

    try {
      const [branches, categories, sizes, colors, seasons, collections, products] =
        await Promise.all([
          firstValueFrom(this.api.listPublicBranches()),
          firstValueFrom(this.api.listCategories()),
          firstValueFrom(this.api.listSizes()),
          firstValueFrom(this.api.listColors()),
          firstValueFrom(this.api.listSeasons()),
          firstValueFrom(this.api.listCollections()),
          firstValueFrom(this.api.listProducts()),
        ]);
      this.branches.set(branches.data ?? []);
      this.categories.set(categories.data ?? []);
      this.sizes.set(sizes.data ?? []);
      this.colors.set(colors.data ?? []);
      this.seasons.set(seasons.data ?? []);
      this.collections.set(collections.data ?? []);
      this.products.set(products.data ?? []);
      this.isOfflineActive.set(false);
      this.ensureSelectedVariants();
      void this.loadRecommendations();
    } catch (error) {
      console.warn('Error cargando catálogo online, intentando fallback a IndexedDB', error);
      await this.loadFromIndexedDb(this.form.getRawValue());
    }
  }

  protected branchName(branchId: string | null): string {
    if (!branchId) return 'Sin sucursal';
    return this.branches().find((branch) => branch.id === branchId)?.name ?? branchId;
  }

  protected categoryName(categoryId: string | null | undefined): string {
    if (!categoryId) return 'Sin categoría';
    return this.categories().find((category) => category.id === categoryId)?.name ?? categoryId;
  }

  protected sizeName(sizeId: string | null | undefined): string {
    if (!sizeId) return 'Sin talla';
    return this.sizes().find((size) => size.id === sizeId)?.name ?? sizeId;
  }

  protected colorName(colorId: string | null | undefined): string {
    if (!colorId) return 'Sin color';
    return this.colors().find((color) => color.id === colorId)?.name ?? colorId;
  }

  protected seasonName(seasonId: string | null | undefined): string {
    if (!seasonId) return 'Sin temporada';
    return this.seasons().find((season) => season.id === seasonId)?.name ?? seasonId;
  }

  protected collectionName(collectionId: string | null | undefined): string {
    if (!collectionId) return 'Sin colección';
    return (
      this.collections().find((collection) => collection.id === collectionId)?.name ?? collectionId
    );
  }

  protected collectionSeasonName(collectionId: string | null | undefined): string {
    if (!collectionId) return 'Sin temporada';
    const collection = this.collections().find((item) => item.id === collectionId);
    return this.seasonName(collection?.season_id);
  }

  protected productVariants(product: CatalogProduct): CatalogProductVariant[] {
    return product.variants ?? [];
  }

  protected selectedVariant(product: CatalogProduct): CatalogProductVariant | null {
    const variants = this.productVariants(product);
    if (!variants.length) {
      return null;
    }
    const selectedId = this.selectedVariantByProduct()[product.id];
    return variants.find((variant) => variant.id === selectedId) ?? variants[0] ?? null;
  }

  protected setSelectedVariant(productId: string, variantId: string | null | undefined): void {
    if (!variantId) {
      return;
    }

    this.selectedVariantByProduct.update((current) => ({
      ...current,
      [productId]: variantId,
    }));
  }

  protected variantLabel(variant: CatalogProductVariant): string {
    return `${this.sizeName(variant.size_id)} / ${this.colorName(variant.color_id)}`;
  }

  protected variantSelectLabel(
    product: CatalogProduct,
  ): (variantId: string | null | undefined) => string {
    return (variantId: string | null | undefined): string => {
      if (!variantId) return 'Variante';
      const variant = this.productVariants(product).find((item) => item.id === variantId);
      return variant ? `${this.variantLabel(variant)} - ${variant.price}` : variantId;
    };
  }

  protected availabilityLabel(
    variant: CatalogProductVariant | null,
    branchId: string | null,
  ): string {
    if (!branchId) {
      return 'Selecciona una sucursal para ver stock';
    }
    if (!variant) {
      return 'Sin variante seleccionada';
    }
    return `${variant.branch_quantity ?? 0} unidades`;
  }

  protected variantStock(variant: CatalogProductVariant | null): number | null {
    return variant?.branch_quantity ?? null;
  }

  protected isAddingToCart(productId: string): boolean {
    return this.addingToCartByProduct()[productId] ?? false;
  }

  protected productImages(product: CatalogProduct): string[] {
    const images = new Set<string>();
    for (const variant of product.variants ?? []) {
      if (variant.image_url) {
        images.add(variant.image_url);
      }
    }
    if (product.image_url) {
      images.add(product.image_url);
    }
    return [...images];
  }

  protected currentProductImage(product: CatalogProduct): string | null {
    const images = this.productImages(product);
    if (!images.length) {
      return null;
    }
    return images[this.currentProductImageIndex(product)] ?? null;
  }

  protected currentProductImageIndex(product: CatalogProduct): number {
    const images = this.productImages(product);
    if (!images.length) {
      return 0;
    }
    const index = this.selectedImageByProduct()[product.id] ?? 0;
    return ((index % images.length) + images.length) % images.length;
  }

  protected previousProductImage(productId: string, total: number): void {
    this.selectedImageByProduct.update((current) => ({
      ...current,
      [productId]: ((current[productId] ?? 0) - 1 + total) % total,
    }));
  }

  protected nextProductImage(productId: string, total: number): void {
    this.selectedImageByProduct.update((current) => ({
      ...current,
      [productId]: ((current[productId] ?? 0) + 1) % total,
    }));
  }

  private ensureSelectedVariants(): void {
    const current = { ...this.selectedVariantByProduct() };
    for (const product of this.products()) {
      const variants = product.variants ?? [];
      if (!variants.length) continue;
      if (!current[product.id] || !variants.some((variant) => variant.id === current[product.id])) {
        current[product.id] = variants[0].id;
      }
    }
    this.selectedVariantByProduct.set(current);
  }

  private async loadRecommendations(): Promise<void> {
    const requestVersion = ++this.recommendationsRequestVersion;
    const user = this.session.user();
    if (!user || user.rol !== 'cliente') return;
    try {
      const response = await firstValueFrom(
        this.api.getCollaborativeRecommendations(user.id, {
          branch_id: this.form.getRawValue().branch_id || undefined,
        }),
      );
      const catalog = await firstValueFrom(this.api.listProducts({ branch_id: this.form.getRawValue().branch_id || undefined }));
      const productById = new Map((catalog.data ?? []).map((product) => [product.id, product]));
      if (requestVersion !== this.recommendationsRequestVersion) return;
      this.recommendedProducts.set(
        (response.data?.recommendations ?? [])
          .map((recommendation) => productById.get(recommendation.product_id))
          .filter((product): product is CatalogProduct => !!product),
      );
    } catch {
      if (requestVersion !== this.recommendationsRequestVersion) return;
      this.recommendedProducts.set([]);
    }
  }

  protected async recordProductView(productId: string): Promise<void> {
    try {
      const product = this.products().find((item) => item.id === productId);
      await firstValueFrom(this.api.recordProductView(productId, {
        variant_id: product ? this.selectedVariant(product)?.id : undefined,
        branch_id: this.form.getRawValue().branch_id || undefined,
      }));
    } catch {
      // View telemetry must never block the normal cart flow.
    }
  }
}
