// Run via Vite: /tests/browser/genealogySearch.html. Exercises the real page and router.
import React from 'react';
import { createRoot } from 'react-dom/client';
import { MemoryRouter, useLocation, useNavigate } from 'react-router-dom';
import GenealogyPage from '../../src/pages/GenealogyPage.jsx';

const originalFetch = window.fetch.bind(window);
window.fetch = (url, options) => String(url).includes('/gene/atlas.json')
  ? originalFetch('/gene/atlas.json', options) : originalFetch(url, options);
let root, location, navigate;
function Probe() {
  location = useLocation();
  navigate = useNavigate();
  return <output id="router-location">{location.search}</output>;
}
const assert = (condition, message) => { if (!condition) throw new Error(message); };
const query = () => new URLSearchParams(location.search).get('q') || '';
const flush = () => new Promise(resolve => setTimeout(resolve, 40));
async function until(check) {
  for (let i = 0; i < 100; i++) { if (check()) return; await flush(); }
  throw new Error('Timed out waiting for page update');
}
const input = () => document.querySelector('.atlas-search input');
const setNativeValue = (value) => Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(input(), value);
function change(value, isComposing = false) {
  setNativeValue(value);
  input().dispatchEvent(new InputEvent('input', { bubbles: true, data: value, inputType: isComposing ? 'insertCompositionText' : 'insertText', isComposing }));
}
function start() { input().dispatchEvent(new CompositionEvent('compositionstart', { bubbles: true })); }
function end(value) {
  setNativeValue(value);
  input().dispatchEvent(new CompositionEvent('compositionend', { bubbles: true, data: value }));
}

document.getElementById('run-tests').onclick = async () => {
  const output = document.getElementById('test-results');
  output.textContent = 'RUNNING';
  const results = [];
  async function check(name, run) { await run(); results.push('PASS ' + name); output.textContent = results.join('\n'); }
  try {
    root?.unmount();
    root = createRoot(document.getElementById('root'));
    root.render(<MemoryRouter initialEntries={['/genealogy?region=china&q=道家', '/genealogy?region=europe&view=relation&q=存在']} initialIndex={1}><Probe /><GenealogyPage /></MemoryRouter>);
    await until(() => input() && document.querySelector('.atlas-node'));
    await check('拼音组合期间不改URL、不筛掉当前结果、不重复输入', async () => {
      input().focus();
      const originalInput = input(), count = document.querySelectorAll('.atlas-node').length;
      start();
      for (const value of ['c', 'cu', 'cun', "cun'zai"]) {
        change(value, true); await flush();
        assert(input().value === value, 'Native draft was overwritten');
        assert(query() === '存在', 'Uncommitted pinyin reached the URL');
        assert(document.querySelectorAll('.atlas-node').length === count, 'Composition changed results');
        assert(input() === originalInput && document.activeElement === originalInput, 'Input focus or identity changed');
      }
    });
    await check('选词后只提交中文，并保留地区和视图', async () => {
      end('存在'); change('存在'); await flush();
      assert(input().value === '存在' && query() === '存在', 'Chinese commit failed');
      const params = new URLSearchParams(location.search);
      assert(params.get('region') === 'europe' && params.get('view') === 'relation', 'Other filters lost');
    });
    await check('兼容最后一次input早于compositionend的事件顺序', async () => {
      start(); change('存在主', true); change('存在主义', true); await flush();
      assert(query() === '存在', 'Final composing input committed early');
      end('存在主义'); await until(() => query() === '存在主义');
      const committedKey = location.key;
      change('存在主义'); await flush();
      assert(input().value === '存在主义' && location.key === committedKey, 'Trailing input duplicated navigation');
    });
    await check('连续英文按键不会被异步URL回写，焦点保持', async () => {
      change(''); input().focus();
      let expected = '';
      for (const char of 'phenomenology') {
        expected += char; change(input().value + char);
        assert(input().value === expected, 'Fast typing lost or duplicated characters');
      }
      await until(() => query() === expected);
      assert(document.activeElement === input(), 'Typing lost focus');
    });
    await check('中间插入文字后光标位置保持', async () => {
      change('存在主义'); await until(() => query() === '存在主义');
      setNativeValue('存在与主义'); input().setSelectionRange(3, 3);
      input().dispatchEvent(new InputEvent('input', { bubbles: true, data: '与', inputType: 'insertText' }));
      await until(() => query() === '存在与主义');
      assert(input().value === '存在与主义' && input().selectionStart === 3, 'Caret moved during URL sync');
    });
    await check('清空及清除筛选同步输入框和URL', async () => {
      change(''); await until(() => query() === '');
      assert(!new URLSearchParams(location.search).has('q'), 'Empty q left in URL');
      change('不存在的搜索词'); await until(() => document.querySelector('.atlas-empty button'));
      document.querySelector('.atlas-empty button').click(); await until(() => query() === '' && input().value === '');
      assert(!new URLSearchParams(location.search).has('region'), 'Reset did not clear region');
    });
    await check('前进后退恢复历史搜索词', async () => {
      navigate(-1); await until(() => query() === '道家' && input().value === '道家');
      navigate(1); await until(() => query() === '' && input().value === '');
    });
    await check('输入法Escape不关闭预览，取消组合后普通Escape仍可关闭', async () => {
      change('存在主义'); await until(() => query() === '存在主义');
      document.querySelector('[data-school-id="存在主义"]').click();
      await until(() => new URLSearchParams(location.search).has('focus'));
      input().focus(); start(); change('cun', true);
      input().dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true, isComposing: true }));
      await flush(); assert(new URLSearchParams(location.search).has('focus'), 'IME Escape closed preview');
      end('存在主义'); await flush();
      assert(query() === '存在主义' && input().value === '存在主义', 'Cancelled composition corrupted query');
      input().dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
      await until(() => !new URLSearchParams(location.search).has('focus'));
    });
    output.textContent = `PASS ${results.length}/8\n` + results.join('\n');
  } catch (error) { output.textContent = 'FAIL\n' + results.join('\n') + '\n' + error.message; }
};
