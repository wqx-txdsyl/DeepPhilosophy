/**
 * Phase 3 Evidence Contract 前端配套（2026-08-30）
 *
 * 后端 done.citations 已是 used_evidence 投影（检索到但不被回答引用的候选不会出现）;
 * 前端再按 used 标记兜底过滤一次: "引用来源"面板永远只展示回答实际引用的证据。
 * 旧数据无 used 字段 → 视为已用（向后兼容）, 不因缺标记而误清空历史引用。
 */
import { DP_READER } from './api.js';

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
    WEB_PASSAGE_READ: ['已读取网页正文片段', 'Webpage passages read'],
    ABSTRACT_AVAILABLE: ['摘要片段', 'Abstract excerpts'],
    ABSTRACT_READ: ['摘要片段', 'Abstract excerpts'],
    FULL_TEXT_AVAILABLE: ['正文可获取，未记录读取', 'Full text available; reading not recorded'],
    FULL_TEXT_READ: ['已读取正文片段', 'Full-text passages read'],
  };
  return labels[level]?.[lang === 'en' ? 1 : 0] || '';
}

/** Only known chapter coordinates become direct reader links; never invent chapter zero. */
export function sourceHref(c = {}) {
  const primary = generalEvidenceLayer(c) === 'primary';
  const index = c.chapter_idx;
  if (primary && c.book_id && index !== null && index !== undefined && index !== '' && typeof index !== 'boolean'
      && Number.isInteger(Number(index)) && Number(index) >= 0) {
    return `${DP_READER}/${encodeURIComponent(c.book_id)}?ch=${Number(index)}`;
  }
  for (const value of [c.reader_url, c.url]) {
    try {
      const url = new URL(value);
      if (primary) {
        if (url.origin === 'https://deepphilosophy.top' && /^\/(reader|book)\/[^/]+$/.test(url.pathname)) return url.href;
      } else if (['https:', 'http:'].includes(url.protocol)) return url.href;
    } catch { /* unavailable */ }
  }
  const doi = String(c.doi || '').replace(/^https?:\/\/(?:dx\.)?doi\.org\//i, '');
  return /^10\.\d{4,9}\/\S+$/.test(doi) ? `https://doi.org/${encodeURI(doi)}` : null;
}

export function primaryResearch(message = {}) {
  const research = message.evidence?.primary_research;
  if (research && Array.isArray(research.sources)) return research;
  // Old saved answers retain known citations; unknown retrieval history is not reconstructed.
  const sources = pickUsedEvidence(message.citations).filter(c => generalEvidenceLayer(c) === 'primary');
  return { status: sources.length ? 'complete' : 'not_requested', sources, total: sources.length };
}
