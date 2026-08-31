/**
 * localPrefs — 设置偏好持久化（spec §25 Settings IA 的真实能力项）
 * 组件禁止直接散布 localStorage 读写; 统一走本模块（未来可换后端同步）。
 */

const KEY = 'phiagent_prefs_v1';

const DEFAULTS = {
  theme: null,                       // 主题槽（由 theme.js 管理, 本模块仅读）
  showCitations: true,               // 证据：显示"引用来源"chip 行
  toolTraceOpen: false,              // 工具披露：tool detail 默认折叠（§18 Progressive Disclosure）
  defaultResponder: 'general',       // 回答者：新对话默认 responder
  sidebarCollapsed: false,           // 桌面侧栏收起
};

function _read() {
  try {
    const raw = JSON.parse(localStorage.getItem(KEY) || '{}');
    return { ...DEFAULTS, ...(raw && typeof raw === 'object' ? raw : {}) };
  } catch (e) {
    return { ...DEFAULTS };
  }
}

function _write(prefs) {
  try {
    localStorage.setItem(KEY, JSON.stringify(prefs));
  } catch (e) { /* 配额等: 忽略 */ }
}

export function getPref(key) {
  return _read()[key] ?? DEFAULTS[key];
}

export function setPref(key, value) {
  const prefs = _read();
  prefs[key] = value;
  _write(prefs);
}
