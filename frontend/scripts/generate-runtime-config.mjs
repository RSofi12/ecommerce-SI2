import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Determinación del entorno de ejecución
const isRender = process.env.RENDER === 'true' || process.env.RENDER === '1';
const isProd = process.env.NODE_ENV === 'production' || isRender;

// URL de la API: prioriza variable de entorno explícita, luego Render backend por defecto, o localhost para dev local
const apiBaseUrl = (
  process.env.API_BASE_URL ||
  (isProd ? 'https://ecommerce-si2.onrender.com/api' : 'http://localhost:8000/api')
).trim();

const decartApiKey = (
  process.env.DECART_PUBLIC_KEY ||
  process.env.DECART_API_KEY ||
  ''
).trim();

const stripePublishableKey = (
  process.env.STRIPE_PUBLISHABLE_KEY ||
  ''
).trim();

const firebaseVapidKey = (
  process.env.FIREBASE_VAPID_KEY ||
  ''
).trim();

const runtimeConfigContent = `// Configuración inyectada para despliegue en Render / Cloud
window.__runtimeConfig = {
  apiBaseUrl: ${JSON.stringify(apiBaseUrl)},
  decartApiKey: ${JSON.stringify(decartApiKey)},
  stripePublishableKey: ${JSON.stringify(stripePublishableKey)},
  firebaseVapidKey: ${JSON.stringify(firebaseVapidKey)}
};
`;

const publicPath = resolve(__dirname, '../public/runtime-config.js');
mkdirSync(dirname(publicPath), { recursive: true });
writeFileSync(publicPath, runtimeConfigContent, 'utf-8');

console.log(`[runtime-config] Generado exitosamente en: ${publicPath}`);
console.log(`[runtime-config] API_BASE_URL configurada: ${apiBaseUrl}`);
