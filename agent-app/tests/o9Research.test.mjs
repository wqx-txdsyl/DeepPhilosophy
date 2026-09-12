/**
 * O9-R1 研究相位映射 + DepthControls 双语 prompt 纯函数测试。
 * 运行: node tests/o9Research.test.mjs
 */
import assert from 'node:assert/strict';
import { researchPhaseKey, researchPhase, RESEARCH_PHASES, layerOf, layerLabel } from '../src/utils/o9Research.js';
import { readFileSync } from 'node:fs';

const PHASES = Object.keys(RESEARCH_PHASES);
assert.deepEqual(PHASES.sort(), ['ARGUMENT_SYNTHESIS', 'PRIMARY_SEARCH', 'SCHOLARLY_RESEARCH', 'SOURCE_VERIFY', 'UNDERSTANDING'], '5 phases exactly');

// ── RESEARCH_PHASE_MAPPING_TEST（任务书 7 例）──
assert.equal(researchPhaseKey('search_books'), 'PRIMARY_SEARCH');
assert.equal(researchPhaseKey('get_chapter'), 'PRIMARY_SEARCH');
assert.equal(researchPhaseKey('search_scholarship'), 'SCHOLARLY_RESEARCH');
assert.equal(researchPhaseKey('get_scholarly_source'), 'SCHOLARLY_RESEARCH');
assert.equal(researchPhaseKey('query_graph'), 'UNDERSTANDING');
// verification-class: 工具名未知但事件文本为核验类 → SOURCE_VERIFY
assert.equal(researchPhaseKey('unknown_tool', '正在核验引用与出处'), 'SOURCE_VERIFY');
assert.equal(researchPhaseKey('quote_bound', 'verify citations'), 'SOURCE_VERIFY');
// non-retrieval synthesis（生成/论证类 + 兜底）
assert.equal(researchPhaseKey('write_essay'), 'ARGUMENT_SYNTHESIS');
assert.equal(researchPhaseKey('dialectic'), 'ARGUMENT_SYNTHESIS');
assert.equal(researchPhaseKey('totally_new_tool'), 'ARGUMENT_SYNTHESIS');
// 文本优先于工具名（核验类文本不被工具映射覆盖）
assert.equal(researchPhaseKey('search_books', '出处核验完成'), 'SOURCE_VERIFY');
// 双语文案
assert.equal(researchPhase('search_books', '', 'zh'), '正在查找原典');
assert.equal(researchPhase('search_books', '', 'en'), 'Searching primary texts');
assert.equal(researchPhase('query_graph', '', 'zh'), '正在理解问题');
console.log('RESEARCH_PHASE_MAPPING_TEST=PASS');

// ── 来源分层（O9 既有合同回归）──
assert.equal(layerOf({ book: '论语' }), 'primary');
assert.equal(layerOf({ doi: '10.1111/x' }), 'scholarly');
assert.equal(layerOf({ title: 'web page' }), 'web');
assert.equal(layerLabel('primary', 'zh'), '原典');
console.log('LAYER_OF_TEST=PASS');

// ── DEPTH_CONTROLS_ZH/EN_TEST: DEPTHS prompt 双语化（源码级断言）──
const src = readFileSync(new URL('../src/components/conversation/O9.jsx', import.meta.url), 'utf8');
for (const key of ['simpler', 'deeper', 'primary', 'scholarly']) {
  const block = src.slice(src.indexOf(`key: '${key}'`), src.indexOf(`key: '${key}'`) + 600);
  assert.ok(/promptZh: '/.test(block), `${key} has promptZh`);
  assert.ok(/promptEn: '/.test(block), `${key} has promptEn`);
  assert.ok(!/prompt: '/.test(block), `${key} legacy single-language prompt removed`);
}
// 语言选择逻辑: en → promptEn
assert.ok(/onPick\(en \? d\.promptEn : d\.promptZh\)/.test(src), 'DepthControls picks prompt by lang');
// MessageBubble 传递真实 lang（不再 lang={undefined}）
const ml = readFileSync(new URL('../src/components/conversation/MessageList.jsx', import.meta.url), 'utf8');
assert.ok(/<DepthControls lang=\{lang\}/.test(ml), 'MessageBubble passes lang to DepthControls');
assert.ok(!/lang=\{undefined\}/.test(ml), 'no lang=undefined left');
// MessageList 已接线 researchPhase（PhasePill）
assert.ok(/researchPhase\(name, text, lang\)/.test(ml), 'PhasePill uses researchPhase');
console.log('DEPTH_CONTROLS_ZH_TEST=PASS');
console.log('DEPTH_CONTROLS_EN_TEST=PASS');

console.log('O9 RESEARCH/DEPTH TESTS ALL GREEN');
