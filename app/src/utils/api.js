/**
 * Shared API base URL helper — single source of truth.
 * All modules should import getApiBase from here.
 */
export function getApiBase() {
  try {
    const config = JSON.parse(localStorage.getItem('dp_api_config') || '{}');
    if (config.apiUrl && config.apiUrl !== window.location.origin) return config.apiUrl;
  } catch {}
  // Same-origin deployment: use relative URL (no CORS issues)
  if (typeof import.meta !== 'undefined' && import.meta.env?.PROD) return '';
  return import.meta?.env?.VITE_API_URL || 'http://localhost:8000';
}
