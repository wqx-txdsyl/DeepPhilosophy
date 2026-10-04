/**
 * Shared API base URL helper — single source of truth.
 * Auth + 业务 API 全部走 Cloudflare Worker（同域 deepphilosophy.top，无冷启动）
 * In dev, uses localhost (Vite proxy → 本地后端)。
 */
const API_URL = 'https://deepphilosophy.top';

export function getApiBase() {
  if (import.meta.env.DEV) {
    return import.meta.env.VITE_API_URL || '';
  }
  return API_URL;
}

export function getAuthBase() {
  if (import.meta.env.DEV) return '';
  return API_URL;
}
