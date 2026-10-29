import { Injectable, inject } from '@angular/core';
import { CreateReservationRequest, Reservation } from '../../features/shared/models/reservation.model';
import { NetworkStatusService } from './network-status.service';

export interface PendingReservationItem {
  client_reservation_id: string;
  payload: CreateReservationRequest;
  branch_name?: string;
  items_summary: string;
  total_estimated: number;
  created_at: string;
  synced: boolean;
  sync_error?: string;
}

const STORAGE_KEY = 'fashionstore_pending_reservations';

@Injectable({ providedIn: 'root' })
export class IdbReservationsService {
  private readonly network = inject(NetworkStatusService);

  getPending(): PendingReservationItem[] {
    try {
      const data = localStorage.getItem(STORAGE_KEY);
      return data ? JSON.parse(data) : [];
    } catch {
      return [];
    }
  }

  savePending(item: PendingReservationItem): void {
    const list = this.getPending();
    const existingIndex = list.findIndex((p) => p.client_reservation_id === item.client_reservation_id);
    if (existingIndex >= 0) {
      list[existingIndex] = item;
    } else {
      list.unshift(item);
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
  }

  removePending(clientReservationId: string): void {
    const list = this.getPending().filter((p) => p.client_reservation_id !== clientReservationId);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
  }

  clearAll(): void {
    localStorage.removeItem(STORAGE_KEY);
  }
}
