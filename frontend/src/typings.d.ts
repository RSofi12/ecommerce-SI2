// Declare missing Firebase and Unovis modules with basic type placeholders
declare module 'firebase/app' {
  // Firebase App placeholder
  export const initializeApp: any;
  export const getApp: any;
  export const getApps: any;
}

declare module 'firebase/messaging' {
  // Messaging interface placeholder
  export interface Messaging {}
  export const getMessaging: any;
  export const getToken: any;
  export const isSupported: any;
  export const onMessage: any;
}

declare module '@unovis/ts' {
  // Interface for bullet legend items used in charts
  export interface BulletLegendItemInterface {
    name: string;
    color: string;
  }
  // Add any additional types as needed
}
