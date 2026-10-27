import { CommonModule } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { FormBuilder, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { firstValueFrom } from 'rxjs';

import { toast } from '@spartan-ng/brain/sonner';
import { HlmBadgeImports } from '../../../components/badge/src';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmTable } from '../../../components/table/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { CatalogBranch } from '../../shared/models/catalog.model';
import {
  InventoryBranchStock,
  InventoryTransfer,
  TransferStatus,
} from '../../shared/models/inventory.model';
import { CatalogApiService } from '../../shared/services/catalog-api.service';
import { InventoryApiService } from '../../shared/services/inventory-api.service';
import { SessionService } from '../../shared/services/session.service';

@Component({
  selector: 'app-transfers-page',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    HlmButton,
    ...HlmBadgeImports,
    ...HlmCardImports,
  ],
  templateUrl: './transfers-page.component.html',
})
export class TransfersPageComponent {
  private readonly inventoryApi = inject(InventoryApiService);
  private readonly catalogApi = inject(CatalogApiService);
  private readonly session = inject(SessionService);
  private readonly fb = inject(FormBuilder);

  protected readonly transfers = signal<InventoryTransfer[]>([]);
  protected readonly branches = signal<CatalogBranch[]>([]);
  protected readonly branchStock = signal<InventoryBranchStock[]>([]);
  protected readonly loading = signal(false);
  protected readonly submitting = signal(false);

  // Filtros
  protected readonly filterTab = signal<'all' | 'outgoing' | 'incoming'>('all');
  protected readonly statusFilter = signal<string>('ALL');

  // Modales
  protected readonly createModalOpen = signal(false);
  protected readonly receiveModalOpen = signal(false);
  protected readonly cancelModalOpen = signal(false);
  protected readonly selectedTransfer = signal<InventoryTransfer | null>(null);
  protected readonly cancelReason = signal('');

  // Formulario nuevo traslado
  protected readonly createForm = this.fb.group({
    from_branch_id: ['', Validators.required],
    to_branch_id: ['', Validators.required],
    variant_id: ['', Validators.required],
    quantity: [1, [Validators.required, Validators.min(1)]],
    notes: [''],
  });

  constructor() {
    void this.loadData();
  }

  protected readonly user = computed(() => this.session.user());
  protected readonly userBranchId = computed(() => this.session.user()?.branch_id ?? null);
  protected readonly isAdmin = computed(() => this.session.user()?.rol === 'administrador');

  protected readonly inTransitCount = computed(
    () => this.transfers().filter((t) => t.status === 'EN_TRANSITO').length
  );
  protected readonly completedCount = computed(
    () => this.transfers().filter((t) => t.status === 'COMPLETADO').length
  );
  protected readonly pendingToReceiveCount = computed(() => {
    const branchId = this.userBranchId();
    return this.transfers().filter(
      (t) => t.status === 'EN_TRANSITO' && (!branchId || t.to_branch_id === branchId)
    ).length;
  });

  protected readonly filteredTransfers = computed(() => {
    const list = this.transfers();
    const tab = this.filterTab();
    const status = this.statusFilter();
    const branchId = this.userBranchId();

    return list.filter((t) => {
      // Filtro por tab (rol y flujo)
      if (tab === 'outgoing' && branchId && t.from_branch_id !== branchId) return false;
      if (tab === 'incoming' && branchId && t.to_branch_id !== branchId) return false;

      // Filtro por status
      if (status !== 'ALL' && t.status !== status) return false;

      return true;
    });
  });

  // Stock disponible de la variante seleccionada en la sucursal de origen
  protected readonly selectedVariantStock = computed(() => {
    const variantId = this.createForm.get('variant_id')?.value;
    if (!variantId) return null;
    const item = this.branchStock().find((s) => s.variant_id === variantId);
    return item ? item.available_quantity : 0;
  });

  async loadData(): Promise<void> {
    this.loading.set(true);
    try {
      const [transfersRes, branchesRes] = await Promise.all([
        firstValueFrom(this.inventoryApi.getTransfers()),
        firstValueFrom(this.catalogApi.listPublicBranches()),
      ]);

      if (transfersRes.data) {
        this.transfers.set(transfersRes.data);
      }
      if (branchesRes.data) {
        this.branches.set(branchesRes.data);
      }

      await this.refreshOriginStock();
    } catch (error) {
      toast.error(getErrorMessage(error, 'Error al cargar datos de traslados'));
    } finally {
      this.loading.set(false);
    }
  }

  async refreshOriginStock(): Promise<void> {
    const originBranchId = this.userBranchId() || this.createForm.get('from_branch_id')?.value;
    if (!originBranchId) return;

    try {
      const stockRes = await firstValueFrom(this.inventoryApi.getBranchStock(originBranchId));
      if (stockRes.data) {
        this.branchStock.set(stockRes.data);
      }
    } catch {
      // Ignorar fallback
    }
  }

  openCreateModal(): void {
    const defaultFrom = this.userBranchId() || (this.branches().length > 0 ? this.branches()[0].id : '');
    const defaultTo = this.branches().find((b) => b.id !== defaultFrom)?.id ?? '';

    this.createForm.reset({
      from_branch_id: defaultFrom,
      to_branch_id: defaultTo,
      variant_id: '',
      quantity: 1,
      notes: '',
    });

    void this.refreshOriginStock();
    this.createModalOpen.set(true);
  }

  closeCreateModal(): void {
    this.createModalOpen.set(false);
  }

  onFromBranchChange(): void {
    void this.refreshOriginStock();
  }

  async submitCreate(): Promise<void> {
    if (this.createForm.invalid) {
      this.createForm.markAllAsTouched();
      return;
    }

    const { from_branch_id, to_branch_id, variant_id, quantity, notes } = this.createForm.value;

    if (!from_branch_id || !to_branch_id || !variant_id || !quantity) {
      toast.error('Completa los campos obligatorios');
      return;
    }

    if (from_branch_id === to_branch_id) {
      toast.error('La sucursal de destino debe ser diferente a la de origen');
      return;
    }

    const maxStock = this.selectedVariantStock();
    if (maxStock !== null && quantity > maxStock) {
      toast.error(`Stock insuficiente en origen. Disponible: ${maxStock}`);
      return;
    }

    this.submitting.set(true);
    try {
      const res = await firstValueFrom(
        this.inventoryApi.createTransfer({
          from_branch_id,
          to_branch_id,
          notes: notes || undefined,
          items: [{ variant_id, quantity: Number(quantity) }],
        })
      );

      toast.success(res.message || 'Traslado despachado en tránsito');
      this.closeCreateModal();
      await this.loadData();
    } catch (error) {
      toast.error(getErrorMessage(error, 'Error al despachar el traslado'));
    } finally {
      this.submitting.set(false);
    }
  }

  openReceiveModal(transfer: InventoryTransfer): void {
    this.selectedTransfer.set(transfer);
    this.receiveModalOpen.set(true);
  }

  closeReceiveModal(): void {
    this.selectedTransfer.set(null);
    this.receiveModalOpen.set(false);
  }

  async submitReceive(): Promise<void> {
    const transfer = this.selectedTransfer();
    if (!transfer) return;

    this.submitting.set(true);
    try {
      const res = await firstValueFrom(this.inventoryApi.receiveTransfer(transfer.id));
      toast.success(res.message || 'Mercadería recepcionada e inventario actualizado');
      this.closeReceiveModal();
      await this.loadData();
    } catch (error) {
      toast.error(getErrorMessage(error, 'Error al recibir el traslado'));
    } finally {
      this.submitting.set(false);
    }
  }

  openCancelModal(transfer: InventoryTransfer): void {
    this.selectedTransfer.set(transfer);
    this.cancelReason.set('Cancelación operativa por encargado');
    this.cancelModalOpen.set(true);
  }

  closeCancelModal(): void {
    this.selectedTransfer.set(null);
    this.cancelModalOpen.set(false);
  }

  async submitCancel(): Promise<void> {
    const transfer = this.selectedTransfer();
    if (!transfer) return;

    this.submitting.set(true);
    try {
      const res = await firstValueFrom(
        this.inventoryApi.cancelTransfer(transfer.id, this.cancelReason())
      );
      toast.success(res.message || 'Traslado cancelado y stock restituido a origen');
      this.closeCancelModal();
      await this.loadData();
    } catch (error) {
      toast.error(getErrorMessage(error, 'Error al cancelar el traslado'));
    } finally {
      this.submitting.set(false);
    }
  }

  canReceive(transfer: InventoryTransfer): boolean {
    if (transfer.status !== 'EN_TRANSITO') return false;
    if (this.isAdmin()) return true;
    return transfer.to_branch_id === this.userBranchId();
  }

  canCancel(transfer: InventoryTransfer): boolean {
    if (transfer.status !== 'EN_TRANSITO') return false;
    if (this.isAdmin()) return true;
    return transfer.from_branch_id === this.userBranchId();
  }

  statusClass(status: TransferStatus): string {
    switch (status) {
      case 'EN_TRANSITO':
        return 'bg-amber-100 text-amber-800 border-amber-300';
      case 'COMPLETADO':
        return 'bg-emerald-100 text-emerald-800 border-emerald-300';
      case 'CANCELADO':
        return 'bg-rose-100 text-rose-800 border-rose-300';
      default:
        return 'bg-slate-100 text-slate-800 border-slate-300';
    }
  }

  statusLabel(status: TransferStatus): string {
    switch (status) {
      case 'EN_TRANSITO':
        return 'En Tránsito';
      case 'COMPLETADO':
        return 'Completado';
      case 'CANCELADO':
        return 'Cancelado';
      case 'SOLICITADO':
        return 'Solicitado';
      default:
        return status;
    }
  }
}
