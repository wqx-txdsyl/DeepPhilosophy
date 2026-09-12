/**
 * O9-R1 研究相位纯函数（docs/ui/O9_INTERACTION_SPEC §2）。
 *
 * 五态（用户可见文案）:
 *   UNDERSTANDING       正在理解问题 / Understanding the question
 *   PRIMARY_SEARCH      正在查找原典 / Searching primary texts
 *   SOURCE_VERIFY       正在核验出处 / Verifying sources
 *   SCHOLARLY_RESEARCH  正在查阅学术研究 / Consulting scholarship
 *   ARGUMENT_SYNTHESIS  正在整理论证 / Organizing the argument
 *
 * 确定性映射: 工具名 → 相位; 事件文本命中核验类词 → SOURCE_VERIFY（优先）。
 * 无 JSX 依赖——node 单测可直接 import。禁止在此暴露 raw args/CoT。
 */

export const RESEARCH_PHASES = {
  UNDERSTANDING: { zh: '正在理解问题', en: 'Understanding the question' },
  PRIMARY_SEARCH: { zh: '正在查找原典', en: 'Searching primary texts' },
  SOURCE_VERIFY: { zh: '正在核验出处', en: 'Verifying sources' },
  SCHOLARLY_RESEARCH: { zh: '正在查阅学术研究', en: 'Consulting scholarship' },
  ARGUMENT_SYNTHESIS: { zh: '正在整理论证', en: 'Organizing the argument' },
};

const TOOL_PHASE = {
  // UNDERSTANDING——结构化知识查询, 服务于问题理解
  query_graph: 'UNDERSTANDING',
  query_database: 'UNDERSTANDING',
  get_philosopher: 'UNDERSTANDING',
  get_school: 'UNDERSTANDING',
  profile: 'UNDERSTANDING',
  phti_test: 'UNDERSTANDING',
  // PRIMARY_SEARCH——原典检索与阅读
  search_books: 'PRIMARY_SEARCH',
  get_chapter: 'PRIMARY_SEARCH',
  get_book_detail: 'PRIMARY_SEARCH',
  list_books: 'PRIMARY_SEARCH',
  concept_trace: 'PRIMARY_SEARCH',
  // SCHOLARLY_RESEARCH——学术与外部资料
  search_scholarship: 'SCHOLARLY_RESEARCH',
  get_scholarly_source: 'SCHOLARLY_RESEARCH',
  websearch: 'SCHOLARLY_RESEARCH',
  // ARGUMENT_SYNTHESIS——生成/论证类
  write_essay: 'ARGUMENT_SYNTHESIS',
  dialectic: 'ARGUMENT_SYNTHESIS',
  compare_views: 'ARGUMENT_SYNTHESIS',
  essay_outline: 'ARGUMENT_SYNTHESIS',
  conceptual_map: 'ARGUMENT_SYNTHESIS',
  thought_experiment: 'ARGUMENT_SYNTHESIS',
  confrontation: 'ARGUMENT_SYNTHESIS',
  philosopher_debate: 'ARGUMENT_SYNTHESIS',
  school_arena: 'ARGUMENT_SYNTHESIS',
  agent_council: 'ARGUMENT_SYNTHESIS',
  socratic_tutor: 'ARGUMENT_SYNTHESIS',
  role_play: 'ARGUMENT_SYNTHESIS',
  advisor_council: 'ARGUMENT_SYNTHESIS',
  paper_review: 'ARGUMENT_SYNTHESIS',
  analyze_argument: 'ARGUMENT_SYNTHESIS',
  history_timeline: 'ARGUMENT_SYNTHESIS',
  generate_image: 'ARGUMENT_SYNTHESIS',
};

const VERIFY_TEXT_RE = /核验|验证出处|verify|verif|quote_check|引文核验|出处核验/i;

/**
 * researchPhaseKey(name, text) → 相位 key。
 * @param {string} name  工具名/事件名
 * @param {string} text  事件附带安全摘要（status/thought/result_summary; 可空）
 * 判定顺序: 核验类文本（优先, 使 SOURCE_VERIFY 恒可达）→ 工具名映射 → ARGUMENT_SYNTHESIS 兜底。
 */
export function researchPhaseKey(name, text) {
  if (VERIFY_TEXT_RE.test(String(text || ''))) return 'SOURCE_VERIFY';
  return TOOL_PHASE[name] || 'ARGUMENT_SYNTHESIS';
}

export function researchPhase(name, text, lang) {
  const k = researchPhaseKey(name, text);
  return RESEARCH_PHASES[k][lang === 'en' ? 'en' : 'zh'];
}

/* ── 来源分层（citation → primary|scholarly|web） ── */
export function layerOf(citation) {
  const c = citation || {};
  if (c.book) return 'primary';
  if (c.doi || c.source_record_id || /journal|press|proceedings/i.test(c.container_title || c.venue || '')) return 'scholarly';
  return 'web';
}

const LAYER_META = {
  primary: { zh: '原典', en: 'Primary' },
  scholarly: { zh: '学术', en: 'Scholarly' },
  web: { zh: '网络', en: 'Web' },
};
export function layerLabel(layer, lang) {
  return (LAYER_META[layer] || LAYER_META.web)[lang === 'en' ? 'en' : 'zh'];
}
