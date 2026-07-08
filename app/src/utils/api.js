/**
 * Shared API base URL helper — single source of truth.
 * In production (GitHub Pages), API is always on Render.
 * In dev, uses localhost.
 */
const RENDER_URL = 'https://deepphilosophy-7g7m.onrender.com';

export function getApiBase() {
  try {
    const config = JSON.parse(localStorage.getItem('dp_api_config') || '{}');
    // User manually set a custom URL (settings page)
    if (config.apiUrl && config.apiUrl !== window.location.origin) return config.apiUrl;
  } catch {}
  // Dev mode: use env or localhost
  if (import.meta.env.DEV) {
    return import.meta.env.VITE_API_URL || 'http://localhost:8000';
  }
  // Production: always use Render (GitHub Pages != same origin)
  return RENDER_URL;
}
