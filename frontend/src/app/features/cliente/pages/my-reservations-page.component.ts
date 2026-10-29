import { CommonModule } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { NgIcon, provideIcons } from '@ng-icons/core';
import {
  lucideAlertCircle,
  lucideArrowRight,
  lucideCalendar,
  lucideCheck,
  lucideCheckCircle2,
  lucideClock,
  lucideCopy,
  lucideExternalLink,
  lucideMapPin,
  lucidePlus,
  lucideRefreshCw,
  lucideShoppingCart,
  lucideTicket,
  lucideTrash2,
  lucideWifi,
  lucideWifiOff,
  lucideX,
} from '@ng-icons/lucide';

import { toast } from '@spartan-ng/brain/sonner';

import { HlmBadgeImports } from '../../../components/badge/src';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { requestWithToast } from '../../../core/utils/request-toast.util';
import { Reservation } from '../../shared/models/reservation.model';
import { ReservationApiService } from '../../shared/services/reservation-api.service';
import { NetworkStatusService } from '../../../core/offline/network-status.service';
import { IdbReservationsService, PendingReservationItem } from '../../../core/offline/idb-reservations.service';

@Component({
  selector: 'app-my-reservations-page',
  standalone: true,
  imports: [CommonModule, RouterLink, NgIcon, HlmButton, ...HlmBadgeImports, ...HlmCardImports],
  providers: [
    provideIcons({
      lucideAlertCircle,
      lucideArrowRight,
      lucideCalendar,
      lucideCheck,
      lucideCheckCircle2,
      lucideClock,
      lucideCopy,
      lucideExternalLink,
      lucideMapPin,
      lucidePlus,
      lucideRefreshCw,
      lucideShoppingCart,
      lucideTicket,
      lucideTrash2,
      lucideWifi,
      lucideWifiOff,
      lucideX,
    }),
  ],
  templateUrl: './my-reservations-page.component.html',
})
export class MyReservationsPageComponent {
  private readonly reservationApi = inject(ReservationApiService);
  protected readonly networkStatus = inject(NetworkStatusService);
  private readonly idbReservations = inject(IdbReservationsService);

  protected readonly reservations = signal<Reservation[]>([]);
  protected readonly pendingOffline = signal<PendingReservationItem[]>([]);
  protected readonly syncing = signal(false);
  protected readonly activeQrModal = signal<Reservation | null>(null);

  protected readonly isOffline = computed(() => !this.networkStatus.effectiveOnline());

  constructor() {
    void this.loadReservations();
    this.loadPending();
  }

  protected reservationStatusLabel(status: Reservation['status']): string {
    switch (status) {
      case 'pending': return 'Pendiente';
      case 'confirmed': return 'Confirmada';
      case 'attended': return 'Atendida en Tienda';
      case 'purchase_pending': return 'Compra Pendiente';
      case 'sold': return 'Vendida / Despachada';
      case 'not_sold': return 'Cerrada sin Compra';
      case 'cancelled': return 'Cancelada';
      case 'expired': return 'Vencida (Stock Liberado)';
      default: return status;
    }
  }

  protected reservationStatusClass(status: Reservation['status']): string {
    switch (status) {
      case 'pending': return 'bg-amber-100 text-amber-800 border-amber-300';
      case 'confirmed': return 'bg-sky-100 text-sky-800 border-sky-300';
      case 'attended': return 'bg-emerald-100 text-emerald-800 border-emerald-300';
      case 'purchase_pending': return 'bg-violet-100 text-violet-800 border-violet-300';
      case 'sold': return 'bg-emerald-100 text-emerald-800 border-emerald-300';
      case 'not_sold': return 'bg-slate-100 text-slate-700 border-slate-300';
      case 'cancelled': return 'bg-rose-100 text-rose-800 border-rose-300';
      case 'expired': return 'bg-slate-200 text-slate-600 border-slate-300';
      default: return 'bg-slate-100 text-slate-700 border-slate-300';
    }
  }

  protected loadPending(): void {
    this.pendingOffline.set(this.idbReservations.getPending());
  }

  protected async syncAllPending(): Promise<void> {
    const list = this.pendingOffline();
    if (!list.length) return;

    this.syncing.set(true);
    let successCount = 0;
    try {
      for (const item of list) {
        try {
          await firstValueFrom(this.reservationApi.createReservation(item.payload));
          this.idbReservations.removePending(item.client_reservation_id);
          successCount++;
        } catch (err) {
          console.error('Error sincronizando reserva offline:', err);
        }
      }
      this.loadPending();
      await this.loadReservations();
      if (successCount > 0) {
        toast.success(`Se sincronizaron ${successCount} reservas offline exitosamente.`);
      } else {
        toast.error('No se pudieron sincronizar las reservas pendientes. Revisa el stock o tu conexión.');
      }
    } finally {
      this.syncing.set(false);
    }
  }

  protected removePendingOffline(id: string): void {
    this.idbReservations.removePending(id);
    this.loadPending();
    toast.info('Reserva offline descartada localmente.');
  }

  protected copyCode(code: string | undefined): void {
    if (!code) return;
    navigator.clipboard.writeText(code);
    toast.success('Código copiado al portapapeles');
  }

  protected openQrModal(res: Reservation): void {
    this.activeQrModal.set(res);
  }

  protected closeQrModal(): void {
    this.activeQrModal.set(null);
  }

  protected async cancelReservation(reservationId: string): Promise<void> {
    try {
      const response = await requestWithToast(
        this.reservationApi.cancelReservation(reservationId),
        {
          loading: 'Liberando existencias y cancelando reserva...',
          success: 'Reserva cancelada. Las existencias han sido liberadas.',
          error: 'No se pudo cancelar la reserva.',
        },
      );
      const updated = response.data;
      if (updated) {
        this.reservations.update((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      }
    } catch {
      // Toast handled by requestWithToast.
    }
  }

  protected async decideReservation(reservationId: string, purchase: boolean): Promise<void> {
    try {
      const response = await requestWithToast(
        this.reservationApi.decideReservation(reservationId, purchase),
        {
          loading: purchase ? 'Confirmando decisión de compra...' : 'Cerrando reserva y liberando prendas...',
          success: purchase ? 'Prendas marcadas para compra.' : 'Reserva cerrada sin compra. Prendas liberadas.',
          error: 'No se pudo actualizar la reserva.',
        },
      );
      const updated = response.data;
      if (updated) {
        this.reservations.update((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      }
    } catch {
      // Toast handled by requestWithToast.
    }
  }

  protected async transferToCart(reservationId: string): Promise<void> {
    try {
      await requestWithToast(
        this.reservationApi.transferToCart(reservationId),
        {
          loading: 'Pasando prendas reservadas al carrito de compras...',
          success: '¡Prendas agregadas al carrito exitosamente!',
          error: 'No se pudo transferir la reserva al carrito.',
        },
      );
      await this.loadReservations();
    } catch {
      // Toast handled by requestWithToast.
    }
  }

  private async loadReservations(): Promise<void> {
    try {
      const response = await firstValueFrom(this.reservationApi.listMyReservations());
      this.reservations.set(response.data ?? []);
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudieron cargar tus reservas.'));
    }
  }
}
