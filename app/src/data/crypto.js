/**
 * API Key 本地加密存储
 * 使用 Web Crypto API (AES-GCM)，密钥基于设备指纹
 */
const STORAGE_KEY = 'dp_api_config';

function getRawKey() {
  if (!crypto?.subtle) {
    throw new Error('Web Crypto API not available (requires HTTPS or localhost)');
  }
  // Use stable device fingerprint: hardware + language (not screen dimensions which change)
  const seed = [
    navigator.hardwareConcurrency || 4,
    navigator.language || 'zh-CN',
    'DeepPhilosophy-salt-v2',
  ].join('|');
  return crypto.subtle.digest('SHA-256', new TextEncoder().encode(seed));
}

async function getCryptoKey() {
  const raw = await getRawKey();
  return crypto.subtle.importKey('raw', raw, { name: 'AES-GCM' }, false, ['encrypt', 'decrypt']);
}

function bufferToHex(buf) { return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, '0')).join(''); }
function hexToBuffer(hex) { return new Uint8Array(hex.match(/.{1,2}/g).map(b => parseInt(b, 16))); }

export async function encryptApiKey(plaintext) {
  if (!plaintext) return '';
  try {
    const key = await getCryptoKey();
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const encoded = new TextEncoder().encode(plaintext);
    const encrypted = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, key, encoded);
    // store as iv:data hex
    return bufferToHex(iv) + ':' + bufferToHex(new Uint8Array(encrypted));
  } catch { return ''; }
}

export async function decryptApiKey(encrypted) {
  if (!encrypted || !encrypted.includes(':')) return encrypted; // unencrypted fallback
  try {
    const key = await getCryptoKey();
    const [ivHex, dataHex] = encrypted.split(':');
    const iv = hexToBuffer(ivHex);
    const data = hexToBuffer(dataHex);
    const decrypted = await crypto.subtle.decrypt({ name: 'AES-GCM', iv }, key, data);
    return new TextDecoder().decode(decrypted);
  } catch { return ''; }
}

/** Save config with encrypted API key */
export async function saveConfig(apiKey, model, apiUrl) {
  const encrypted = await encryptApiKey(apiKey);
  const config = { apiKey: encrypted, model, apiUrl, _encrypted: true };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
}

/** Load config with decrypted API key */
export async function loadConfig() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return {};
    const config = JSON.parse(raw);
    if (config._encrypted && config.apiKey) {
      config.apiKey = await decryptApiKey(config.apiKey);
    }
    return config;
  } catch { return {}; }
}
