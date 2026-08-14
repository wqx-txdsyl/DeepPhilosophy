/**
 * 主题管理（浅色 / 深色 / 自动跟随系统）
 * 基于 index.css 的 .dark-mode 变量集 + localStorage 持久化
 */
const KEY = 'phiagent_theme';
const darkQuery = window.matchMedia('(prefers-color-scheme: dark)');

export function getTheme() {
  return localStorage.getItem(KEY) || 'light';
}

export function setTheme(theme) {
  localStorage.setItem(KEY, theme);
  applyTheme(theme);
}

export function applyTheme(theme) {
  const dark = theme === 'dark' || (theme === 'auto' && darkQuery.matches);
  document.body.classList.toggle('dark-mode', dark);
}

export function initTheme() {
  applyTheme(getTheme());
  darkQuery.addEventListener('change', () => {
    if (getTheme() === 'auto') applyTheme('auto');
  });
}
