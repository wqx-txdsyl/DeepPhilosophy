# -*- coding: utf-8 -*-
"""V7-F2-R1 §3: 语义转移分类器——确定性的逐轮 issue 语义身份判定（零 LLM）。

Reviewer R1 要求（2026-09-11, chatgpt.com/c/6aa3e455）:
  - 七类封闭标签: RESOLVED / PERSISTED / GENUINELY_NEW_ISSUE /
    SAME_ISSUE_REKEYED / LOCATOR_SHIFT_ONLY / ISSUE_CODE_RELABEL / AMBIGUOUS
  - 弱/不完整语义身份不得猜成 GENUINELY_NEW; 无法可靠匹配 → AMBIGUOUS
  - AMBIGUOUS fail-closed（永不静默降级为其他标签）
  - fingerprint set-difference telemetry 原样保留——本分类器是新增第二层
  - 不允许 LLM judge transition identity

输入是 validation.history 的 issue 快照（新 8 字段 schema 或旧
code/locator/evidence_ref 字段名均可——_identity 双兼容）。全部规则为
确定性常数阈值; 无网络、无模型、无随机。
"""
import re

# ── 七类封闭标签 ──────────────────────────────────────────────
RESOLVED = "RESOLVED"
PERSISTED = "PERSISTED"
GENUINELY_NEW_ISSUE = "GENUINELY_NEW_ISSUE"
SAME_ISSUE_REKEYED = "SAME_ISSUE_REKEYED"
LOCATOR_SHIFT_ONLY = "LOCATOR_SHIFT_ONLY"
ISSUE_CODE_RELABEL = "ISSUE_CODE_RELABEL"
AMBIGUOUS = "AMBIGUOUS"

LABELS = (RESOLVED, PERSISTED, GENUINELY_NEW_ISSUE, SAME_ISSUE_REKEYED,
          LOCATOR_SHIFT_ONLY, ISSUE_CODE_RELABEL, AMBIGUOUS)

# validator 封闭 issue code 集合 → 语义家族（final_validator.py 的六码;
# 未知码确定性降级为首段——不抛异常, 不猜家族归属）
_SEMANTIC_FAMILY = {
    "UNVERIFIED_CITATION": "CITATION",
    "UNSUPPORTED_EXACT_QUOTE": "QUOTE",
    "NEAR_QUOTE_NOT_MARKED": "QUOTE",
    "STITCHED_QUOTE": "QUOTE",
    "EMPTY_FINAL": "EMPTY",
    "UNGROUNDED_BIBLIOGRAPHIC_DETAIL": "BIBLIOGRAPHIC",
}

# 确定性匹配阈值（V7-F2-R1 任务书: 规则可解释、无学习参数语义）
_LOCATOR_OVERLAP_MATCH = 0.5   # ≥: 同一语义目标（locator 词汇 Jaccard）
_LOCATOR_OVERLAP_GRAY = 0.3    # [GRAY, MATCH): 灰区 → AMBIGUOUS（fail-closed）


def semantic_family(issue_code):
    """issue code → 语义家族。未知码确定性降级（首段大写）, 缺失 → None。"""
    if not issue_code:
        return None
    c = str(issue_code).upper()
    if c in _SEMANTIC_FAMILY:
        return _SEMANTIC_FAMILY[c]
    return c.split("_")[0]


def normalize_locator(locator):
    """locator 归一化: 标点折叠为空格 + 空白压缩 + 小写 + 截断 200（有界）。"""
    s = re.sub(r"[^\w\s]+", " ", locator or "", flags=re.UNICODE)
    return re.sub(r"\s+", " ", s).strip().lower()[:200]


def _words(text):
    """语义比较用词集: ≥2 位拉丁数字词 + 单个 CJK 字（混合文本统一可比）。"""
    return set(re.findall(r"[a-z0-9]{2,}|[\u4e00-\u9fff]", text or ""))


def _overlap(a_words, b_words):
    """词集 Jaccard; 空集对按 0.0（不可比 ≠ 可比相等）。"""
    if not a_words or not b_words:
        return 0.0
    return len(a_words & b_words) / max(len(a_words | b_words), 1)


def _identity(issue):
    """从快照提取有界身份（双字段名兼容: 新 issue_code/normalized_locator
    与旧 code/locator）。fingerprint 缺失时保留 None——由调用方 fail-closed。"""
    i = issue or {}
    code = i.get("issue_code") or i.get("code")
    nloc = i.get("normalized_locator")
    if nloc is None:
        nloc = normalize_locator(i.get("locator") or "")
    return {
        "fp": i.get("fingerprint") or i.get("issue_fingerprint") or None,
        "code": code or None,
        "fam": semantic_family(code),
        "nloc": nloc or "",
        "ev": i.get("evidence_ref"),
        "words": _words(nloc),
    }


def _classify_pair(prev, cur):
    """单对（消失候选 prev, 新指纹 cur）→ (label, score)。

    label=None 表示「可确定不是同一目标」（供 GENUINELY_NEW 判定）;
    label=AMBIGUOUS 表示「无法可靠匹配」（fail-closed, 不得改猜）。
    score 仅用于多候选确定性择优与并列检测, 不是概率。
    """
    same_code = prev["code"] == cur["code"]
    ov = _overlap(prev["words"], cur["words"])
    if same_code:
        if prev["nloc"] == cur["nloc"]:
            # 同一目标文本, 指纹却变（如 evidence_ref 变）→ rekey
            return SAME_ISSUE_REKEYED, 1.0
        ev_both = prev["ev"] is not None and cur["ev"] is not None
        if ev_both and prev["ev"] == cur["ev"]:
            if ov >= _LOCATOR_OVERLAP_MATCH:
                return LOCATOR_SHIFT_ONLY, ov
            if ov >= _LOCATOR_OVERLAP_GRAY:
                return AMBIGUOUS, ov          # 灰区: 不猜
            return None, ov                    # 同证据但文本完全不同 → 新 span
        # locator 与 evidence_ref 双双改变 → 无法归因, fail-closed
        if ov >= _LOCATOR_OVERLAP_GRAY:
            return AMBIGUOUS, ov
        return None, ov
    # code 不同: 同家族 + 同目标文本 → 校验器改名（relabel）; 否则可判非同一
    if prev["fam"] is not None and prev["fam"] == cur["fam"] \
            and ov >= _LOCATOR_OVERLAP_MATCH:
        return ISSUE_CODE_RELABEL, ov + 0.25
    return None, ov


def classify_transition(prev_issues, cur_issues):
    """对一个 transition（prev 校验态 → cur 校验态）做语义分类。

    返回（全部 JSON 可序列化、有界——只含指纹/标签/计数, 无正文）:
      {
        "introduced_class": {fingerprint: label, ...},   # 逐个新指纹
        "successor_of": {new_fp: old_fp, ...},           # 确认的语义继承
        "summary": {七标签: 计数}
      }
    prev/cur 顺序按输入数组原样; 内部全部排序处理（确定性）。
    """
    prev = [_identity(i) for i in (prev_issues or [])]
    cur = [_identity(i) for i in (cur_issues or [])]
    prev_by_fp = {p["fp"]: p for p in prev if p["fp"]}
    cur_by_fp = {c["fp"]: c for c in cur if c["fp"]}

    persisted = sorted(set(prev_by_fp) & set(cur_by_fp))
    disappeared = [prev_by_fp[f] for f in sorted(set(prev_by_fp) - set(cur_by_fp))]
    introduced_fps = sorted(set(cur_by_fp) - set(prev_by_fp))

    introduced_class = {}
    successor_of = {}
    consumed = set()
    ambiguous_extra = 0
    for fp in introduced_fps:
        c = cur_by_fp[fp]
        # 身份不完整（无 code, 或 locator 无词且无 evidence_ref）→ 不得猜
        if not c["code"] or (not c["words"] and c["ev"] is None):
            introduced_class[fp] = AMBIGUOUS
            continue
        best = None          # (score, prev_fp, label)
        tie = False
        for p in disappeared:
            if p["fp"] in consumed or not p["code"]:
                continue
            label, score = _classify_pair(p, c)
            if label is None:
                continue
            if best is None or score > best[0]:
                best, tie = (score, p["fp"], label), False
            elif score == best[0]:
                tie = True   # 等强竞争候选 → fail-closed
        if best is None:
            introduced_class[fp] = GENUINELY_NEW_ISSUE
        elif tie:
            introduced_class[fp] = AMBIGUOUS
        else:
            introduced_class[fp] = best[2]
            if best[2] in (SAME_ISSUE_REKEYED, LOCATOR_SHIFT_ONLY, ISSUE_CODE_RELABEL):
                consumed.add(best[1])
                successor_of[fp] = best[1]
    # 指纹缺失的 issue（schema 允许显式 null）不可集合追踪 → fail-closed 计入 AMBIGUOUS
    null_fp_cur = sum(1 for c in cur if not c["fp"])
    null_fp_prev = sum(1 for p in prev if not p["fp"])
    ambiguous_extra = null_fp_cur + null_fp_prev

    resolved = [p["fp"] for p in disappeared if p["fp"] not in consumed]
    summary = {
        RESOLVED: len(resolved),
        PERSISTED: len(persisted),
        GENUINELY_NEW_ISSUE: sum(1 for v in introduced_class.values()
                                 if v == GENUINELY_NEW_ISSUE),
        SAME_ISSUE_REKEYED: sum(1 for v in introduced_class.values()
                                if v == SAME_ISSUE_REKEYED),
        LOCATOR_SHIFT_ONLY: sum(1 for v in introduced_class.values()
                                if v == LOCATOR_SHIFT_ONLY),
        ISSUE_CODE_RELABEL: sum(1 for v in introduced_class.values()
                                if v == ISSUE_CODE_RELABEL),
        AMBIGUOUS: sum(1 for v in introduced_class.values() if v == AMBIGUOUS)
                   + ambiguous_extra,
    }
    return {"introduced_class": introduced_class,
            "successor_of": successor_of,
            "summary": {k: summary[k] for k in LABELS}}


def introduced_count(summary):
    """新指纹总数（= 五个 introduced 标签之和; 与 legacy 集合差口径一致）。"""
    s = summary or {}
    return sum(s.get(k, 0) for k in (GENUINELY_NEW_ISSUE, SAME_ISSUE_REKEYED,
                                     LOCATOR_SHIFT_ONLY, ISSUE_CODE_RELABEL,
                                     AMBIGUOUS))


def transition_is_fail_closed(summary):
    """AMBIGUOUS>0 → 该 transition 不可裁决 → fail-closed（V2 硬门语义）。"""
    return bool((summary or {}).get(AMBIGUOUS))


def dev_probe_counts(summaries):
    """§4 DEV probe 六项计数（多轮 summary 聚合; 键名按 R1 任务书逐字）。"""
    ss = [s for s in (summaries or []) if s]
    rekey = sum(s.get(SAME_ISSUE_REKEYED, 0) for s in ss)
    shift = sum(s.get(LOCATOR_SHIFT_ONLY, 0) for s in ss)
    relabel = sum(s.get(ISSUE_CODE_RELABEL, 0) for s in ss)
    gen_new = sum(s.get(GENUINELY_NEW_ISSUE, 0) for s in ss)
    ambig = sum(s.get(AMBIGUOUS, 0) for s in ss)
    return {
        "NEW_FINGERPRINT_COUNT": gen_new + rekey + shift + relabel + ambig,
        "GENUINELY_NEW_ISSUE_COUNT": gen_new,
        "REKEY_COUNT": rekey,
        "LOCATOR_SHIFT_COUNT": shift,
        "RELABEL_COUNT": relabel,
        "AMBIGUOUS_COUNT": ambig,
    }
