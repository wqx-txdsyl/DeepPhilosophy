/**
 * Shared API base URL helper — single source of truth.
 * All modules should import getApiBase from here.
 */
export function getApiBase() {
  try {
    const config = JSON.parse(localStorage.getItem('dp_api_config') || '{}');
    if (config.apiUrl && config.apiUrl !== window.location.origin) return config.apiUrl;
  } catch {}
  // GitHub Pages: API is on Render (different origin, cannot use relative path)
  if (typeof import.meta !== 'undefined' && import.meta.env?.PROD) {
    return 'https://deepphilosophy-7g7m.onrender.com';
  }
  return import.meta?.env?.VITE_API_URL || 'http://localhost:8000';
}
