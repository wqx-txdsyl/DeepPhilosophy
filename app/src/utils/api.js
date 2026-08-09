/**
 * Shared API base URL helper — single source of truth.
 * Auth + 业务 API 全部走 Cloudflare Worker（同域 deepphilosophy.top，无冷启动）
 * In dev, uses localhost (Vite proxy → 本地后端)。
 * 注意：不再读 dp_api_config.apiUrl —— 那是 AI 直连配置（QA/Reader 各自读取），
 * 曾因覆盖全站 API 基址导致 5173 请求被拐到旧 Render（2026-08-09 简介被吞事故）。
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
