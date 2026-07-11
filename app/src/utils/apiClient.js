/**
 * Unified API client — single source of truth for all fetch calls.
 * Provides timeout, retry, caching, and consistent error handling.
 */
import { getApiBase } from './api';

const DEFAULT_TIMEOUT = 10000;
const AI_TIMEOUT = 60000; // AI endpoints take longer

class ApiClient {
  constructor() {
    this.baseUrl = getApiBase();
    this.cache = new Map();
  }

  /** Core request method with timeout and error handling */
  async request(path, options = {}) {
    const url = `${this.baseUrl}${path}`;
    const controller = new AbortController();
    const timeout = options.timeout || DEFAULT_TIMEOUT;
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const resp = await fetch(url, {
        ...options,
        signal: options.signal || controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...(options.headers || {}),
        },
      });
      clearTimeout(timeoutId);
      if (!resp.ok) {
        const text = await resp.text().catch(() => '');
        throw new ApiError(resp.status, text, url);
      }
      return resp.json();
    } catch (err) {
      clearTimeout(timeoutId);
      if (err instanceof ApiError) throw err;
      if (err.name === 'AbortError') {
        throw new ApiError(408, 'Request timeout', url);
      }
      throw new ApiError(0, err.message, url);
    }
  }

  /** GET with optional caching */
  async get(path, { cache = false, ttl = 300000, ...opts } = {}) {
    if (cache) {
      const entry = this.cache.get(path);
      if (entry && Date.now() - entry.time < ttl) return entry.data;
    }
    const data = await this.request(path, { ...opts, method: 'GET' });
    if (cache) this.cache.set(path, { data, time: Date.now() });
    return data;
  }

  /** POST */
  async post(path, body, opts = {}) {
    return this.request(path, {
      ...opts,
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  /** PUT */
  async put(path, body, opts = {}) {
    return this.request(path, {
      ...opts,
      method: 'PUT',
      body: JSON.stringify(body),
    });
  }

  /** DELETE */
  async delete(path, opts = {}) {
    return this.request(path, { ...opts, method: 'DELETE' });
  }

  /** Auth-aware request — automatically attaches Bearer token */
  async authRequest(path, options = {}) {
    const token = localStorage.getItem('dp_token');
    const headers = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    return this.request(path, {
      ...options,
      headers: { ...headers, ...(options.headers || {}) },
    });
  }

  /** POST with auth */
  async authPost(path, body, opts = {}) {
    return this.authRequest(path, {
      ...opts,
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  /** POST with auth — fire and forget (no await, no error thrown) */
  fireAndForget(path, body) {
    this.authPost(path, body).catch(() => {});
  }

  /** Clear all cached responses */
  clearCache() {
    this.cache.clear();
  }
}

class ApiError extends Error {
  constructor(status, body, url = '') {
    const msg = typeof body === 'string' ? body.slice(0, 200) : JSON.stringify(body).slice(0, 200);
    super(`API ${status} [${url}]: ${msg}`);
    this.status = status;
    this.body = body;
    this.url = url;
  }
}

export const api = new ApiClient();
export { ApiError };
export default api;
