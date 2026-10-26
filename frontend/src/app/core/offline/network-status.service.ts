import { Injectable, computed, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class NetworkStatusService {
  /**
   * Estado de conectividad real del navegador.
   */
  readonly isOnline = signal<boolean>(typeof navigator !== 'undefined' ? navigator.onLine : true);

  /**
   * Conmutador para simular modo desconectado en laboratorio / desarrollo.
   */
  readonly simulatedOffline = signal<boolean>(false);

  /**
   * Conectividad efectiva considerando simulación.
   */
  readonly effectiveOnline = computed(() => this.isOnline() && !this.simulatedOffline());

  constructor() {
    if (typeof window !== 'undefined') {
      window.addEventListener('online', () => this.isOnline.set(true));
      window.addEventListener('offline', () => this.isOnline.set(false));
    }
  }

  toggleSimulatedOffline(): void {
    this.simulatedOffline.update((prev) => !prev);
  }

  setSimulatedOffline(value: boolean): void {
    this.simulatedOffline.set(value);
  }
}
