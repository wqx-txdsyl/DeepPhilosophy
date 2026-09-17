/**
 * Phase 3 Evidence Contract 前端配套（2026-08-30）
 *
 * 后端 done.citations 已是 used_evidence 投影（检索到但不被回答引用的候选不会出现）;
 * 前端再按 used 标记兜底过滤一次: "引用来源"面板永远只展示回答实际引用的证据。
 * 旧数据无 used 字段 → 视为已用（向后兼容）, 不因缺标记而误清空历史引用。
 */
export const pickUsedEvidence = (citations) =>
  (Array.isArray(citations) ? citations : []).filter((c) => c && c.used !== false);

/** 面板可用条目数（used）; retrieved 计数由 message.evidence.retrieved_count 提供 */
export const usedEvidenceCount = (citations) => pickUsedEvidence(citations).length;

/** General citations carry explicit provenance; a scholarly work can also have a book title. */
export function generalEvidenceLayer(citation = {}) {
  if (citation.source_type === 'scholarly' || citation.doi || citation.source_record_id) return 'scholarly';
  if (['web', 'secondary'].includes(citation.source_type)) return 'web';
  return citation.book || citation.book_id ? 'primary' : 'web';
}

export function generalAccessLabel(level, lang = 'zh') {
  const labels = {
    PASSAGE_READ: ['已读取原文片段', 'Source passages read'],
    SEARCH_EXCERPT: ['仅检索片段', 'Search excerpts only'],
    METADATA_ONLY: ['仅书目信息', 'Bibliographic metadata only'],
    WEB_DISCOVERY_ONLY: ['仅定位网页，未读取正文', 'Page located; content not read'],
    ABSTRACT_AVAILABLE: ['摘要片段', 'Abstract excerpts'],
    ABSTRACT_READ: ['摘要片段', 'Abstract excerpts'],
    FULL_TEXT_AVAILABLE: ['正文可获取，未记录读取', 'Full text available; reading not recorded'],
    FULL_TEXT_READ: ['已读取正文片段', 'Full-text passages read'],
  };
  return labels[level]?.[lang === 'en' ? 1 : 0] || '';
}
