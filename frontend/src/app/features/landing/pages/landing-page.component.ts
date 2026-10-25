import { CommonModule } from '@angular/common';
import { Component, HostListener, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

interface FaqItem {
  question: string;
  answer: string;
  open?: boolean;
}

interface StepItem {
  number: string;
  title: string;
  description: string;
}

interface FeatureItem {
  title: string;
  description: string;
  icon: string;
  badge?: string;
}

@Component({
  selector: 'app-landing-page',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './landing-page.component.html',
  styleUrl: './landing-page.component.css',
})
export class LandingPageComponent {
  // Configuración de imágenes del sitio
  readonly images = {
    logoIcon: '/assets/logo-fashionstore.png',
    logoName: '/assets/logo-name.png',
    heroStore: '/assets/clothes-perch-cream.jpg',
    tryOnStore: '/assets/women-store.jpg',
  };

  // Estado de desplazamiento para fluidez de la navbar y botón flotante
  readonly isScrolled = signal(false);

  @HostListener('window:scroll', [])
  onWindowScroll(): void {
    if (typeof window !== 'undefined') {
      this.isScrolled.set(window.scrollY > 30);
    }
  }

  // Desplazamiento suave y preciso hacia cualquier sección
  scrollToSection(event: Event, sectionId: string): void {
    event.preventDefault();
    if (typeof document === 'undefined') return;

    const element = document.getElementById(sectionId);
    if (element) {
      const navOffset = 85;
      const elementPosition = element.getBoundingClientRect().top + window.scrollY;
      const offsetPosition = elementPosition - navOffset;

      window.scrollTo({
        top: offsetPosition,
        behavior: 'smooth',
      });

      // Actualiza la URL de forma limpia
      window.history.pushState(null, '', `#${sectionId}`);
    }
  }

  // Desplazamiento fluido al inicio (Top)
  scrollToTop(event?: Event): void {
    if (event) event.preventDefault();
    if (typeof window === 'undefined') return;

    window.scrollTo({
      top: 0,
      behavior: 'smooth',
    });

    window.history.pushState(null, '', '/');
  }

  // FAQ reactivo con estado abierto/cerrado
  readonly faqs = signal<FaqItem[]>([
    {
      question: '¿Necesito ingresar tarjeta de crédito para iniciar mi prueba?',
      answer:
        'No, absolutamente nada de tarjetas ni cobros ocultos. Tu primer mes es 100% gratuito para que pruebes todas las herramientas de FashionStore con total tranquilidad.',
      open: true,
    },
    {
      question: '¿Puedo importar mi inventario actual si uso Excel?',
      answer:
        'Sí. Dispones de un asistente de importación para cargar tus prendas, códigos SKU, tallas, colores y precios en lote en solo unos segundos.',
      open: false,
    },
    {
      question: '¿Cómo funciona el Probador Virtual con IA?',
      answer:
        'Nuestro probador virtual utiliza modelos de visión artificial para superponer tus prendas sobre fotos de clientes o maniquíes digitales. Esto reduce las devoluciones por error de talle hasta en un 94%.',
      open: false,
    },
    {
      question: '¿Sirve si tengo tienda física, tienda online o ambas?',
      answer:
        'FashionStore está diseñado para negocios omnicanal. Puedes gestionar ventas en el mostrador de tu boutique física con el punto de venta (POS) y sincronizar el stock con tu catálogo web en tiempo real.',
      open: false,
    },
    {
      question: '¿Puedo manejar múltiples sucursales y empleados?',
      answer:
        'Sí. Puedes crear múltiples locales o depósitos y asignar roles seguros para cajeros, encargados de stock y administradores.',
      open: false,
    },
  ]);

  readonly steps: StepItem[] = [
    {
      number: '01',
      title: 'Registra tu tienda',
      description:
        'Crea tu cuenta en menos de 2 minutos. Solo necesitas tu correo y el nombre de tu marca de moda para comenzar.',
    },
    {
      number: '02',
      title: 'Configura tus productos',
      description:
        'Añade tus prendas con sus respectivas variantes: curvas de talle (XS a XXL), colores, fotos y precios de venta.',
    },
    {
      number: '03',
      title: 'Comienza a vender',
      description:
        'Usa el punto de venta (POS) en mostrador para registrar cobros rápidos o habilita tu catálogo interactivo online.',
    },
    {
      number: '04',
      title: 'Analiza y haz crecer tu marca',
      description:
        'Revisa reportes automáticos de rotación de prendas, márgenes de ganancia y fideliza a tus mejores clientes.',
    },
  ];

  readonly features: FeatureItem[] = [
    {
      title: 'Gestión de Inventario Textil',
      description:
        'Control total por prenda, matriz de tallas, colores y SKUs individuales. Alertas automáticas de bajo stock.',
      icon: 'inventory',
      badge: 'Esencial',
    },
    {
      title: 'Sistema POS de Mostrador',
      description:
        'Punto de venta ultra ágil para tu local físico. Emisión de comprobantes, apertura/cierre de caja y lector de barras.',
      icon: 'pos',
      badge: 'Rápido',
    },
    {
      title: 'Probador Virtual con IA',
      description:
        'Permite a tus clientes verse con tus prendas antes de comprar. La tecnología del futuro para reducir devoluciones.',
      icon: 'ai',
      badge: 'Exclusivo',
    },
    {
      title: 'Gestión de Clientes & Tallas',
      description:
        'Fichas personalizadas con historial de compras, tallas habituales y promociones exclusivas para fidelizar.',
      icon: 'customers',
    },
    {
      title: 'Catálogo & Reservas Online',
      description:
        'Tus clientes exploran prendas desde su móvil, reservan para retirar en tu boutique o solicitan envío directo.',
      icon: 'catalog',
    },
    {
      title: 'Métricas y Reportes de Ganancia',
      description:
        'Descubre qué prendas rotan más rápido, márgenes reales por colección y balance diario de tus ventas.',
      icon: 'analytics',
    },
  ];

  toggleFaq(index: number): void {
    this.faqs.update((items) =>
      items.map((item, i) =>
        i === index ? { ...item, open: !item.open } : item,
      ),
    );
  }
}
