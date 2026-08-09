// 用真实章节数据验证渲染层段落重建: 会饮篇
import fs from 'fs';

const BASE = 'F:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters';
// 找柏拉图对话集 meta
const dirs = fs.readdirSync(BASE);
let bid = null;
for (const d of dirs) {
  try {
    const meta = JSON.parse(fs.readFileSync(`${BASE}/${d}/meta.json`, 'utf-8'));
    if (meta.title && meta.title.includes('柏拉图对话集')) { bid = d; break; }
  } catch {}
}
console.log('BID:', bid);
const meta = JSON.parse(fs.readFileSync(`${BASE}/${bid}/meta.json`, 'utf-8'));
const ti = meta.chapterTitles.findIndex(t => t.includes('会饮篇'));
console.log('会饮篇 toc 序号:', ti, '共', meta.chapterTitles.length, '章');

// 复刻 ChapterReader 渲染逻辑
const END_SENT = /[。！？…"”』」）〉\.!?]$/;
const splitPageParas = (text) => {
  const paras = [];
  let cur = '';
  let curLen = 0;
  for (const ln of (text || '').split('\n')) {
    const s = ln.trim();
    if (!s) continue;
    cur += s; curLen += s.length;
    if (END_SENT.test(s)) { paras.push(cur); cur = ''; curLen = 0; }
    else if (curLen >= 300) {
      const m = cur.match(/.*[。！？…"”』」）〉\.!?]/);
      if (m && m[0].length > 50) {
        paras.push(m[0]); cur = cur.slice(m[0].length); curLen = cur.length;
      } else { paras.push(cur); cur = ''; curLen = 0; }
    }
  }
  if (cur) paras.push(cur);
  return paras;
};

const renderParas = (ch) => {
  const paras = [];
  let tail = null;
  for (const blk of ch.content) {
    if (blk.type !== 'text') {
      if (tail) { paras.push(tail); tail = null; }
      paras.push(blk);
      continue;
    }
    const parts = (blk.value || '').split('[IMG]');
    const imgs = blk.imgs || [];
    parts.forEach((p, j) => {
      const segs = splitPageParas(p);
      segs.forEach((seg, k) => {
        if (!seg.trim()) return;
        const isBlockFirst = (j === 0 && k === 0);
        if (isBlockFirst && tail && !END_SENT.test(tail.text.trim().slice(-1))) {
          tail.text += seg;
        } else {
          if (tail) paras.push(tail);
          tail = { text: seg };
        }
      });
    });
  }
  if (tail) paras.push(tail);
  return paras;
};

const ch = JSON.parse(fs.readFileSync(`${BASE}/${bid}/${ti}.json`, 'utf-8'));
console.log('原始块数:', ch.content.length);
const paras = renderParas(ch);
console.log('重建段数:', paras.length);
const lens = paras.map(p => p.text.length).sort((a, b) => a - b);
const stats = {
  min: lens[0], max: lens[lens.length - 1],
  median: lens[Math.floor(lens.length / 2)],
  p90: lens[Math.floor(lens.length * 0.9)],
};
console.log('段长(字) min/median/p90/max:', stats);
console.log('段长分布: <100:%d <200:%d <300:%d <500:%d >=500:%d',
  lens.filter(l => l < 100).length, lens.filter(l => l < 200).length,
  lens.filter(l => l < 300).length, lens.filter(l => l < 500).length,
  lens.filter(l => l >= 500).length);
// 抽查: 前 3 段 + 用户案例段
console.log('\n-- 前 3 段 --');
paras.slice(0, 3).forEach((p, i) => console.log(`[段${i} %d字] %s`, p.text.length, p.text.slice(0, 80) + '…'));
// 案例: 借用一条谚语
const hit = paras.findIndex(p => p.text.includes('借用一条谚语'));
if (hit >= 0) {
  console.log(`\n-- 案例段(第${hit}段 %d字) --`, paras[hit].text.length);
  console.log(paras[hit].text.slice(0, 200) + '\n……\n' + paras[hit].text.slice(-150));
}
// 全部拼接段(含 \n 的已不再有, 拼接是直接 +=): 检查所有段尾是否句末标点
const badEnd = paras.filter(p => p.text && !END_SENT.test(p.text.trim().slice(-1)));
console.log('\n段尾非句末标点的段数:', badEnd.length, '(应≈0, 这些是强切兜底段)');
