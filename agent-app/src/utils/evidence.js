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
