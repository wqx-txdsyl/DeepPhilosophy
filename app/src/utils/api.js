/**
 * Shared API base URL helper — single source of truth.
 * Auth → Cloudflare Worker (no cold start)
 * Other → Render
 * In dev, uses localhost.
 */
const RENDER_URL = 'https://deepphilosophy-7g7m.onrender.com';
const AUTH_URL = 'https://deepphilosophy-auth.wqx090915.workers.dev';

export function getApiBase() {
  try {
    const config = JSON.parse(localStorage.getItem('dp_api_config') || '{}');
    if (config.apiUrl && config.apiUrl !== window.location.origin) return config.apiUrl;
  } catch {}
  if (import.meta.env.DEV) {
    return import.meta.env.VITE_API_URL || '';
  }
  return RENDER_URL;
}

export function getAuthBase() {
  if (import.meta.env.DEV) return '';
  return AUTH_URL;
}
