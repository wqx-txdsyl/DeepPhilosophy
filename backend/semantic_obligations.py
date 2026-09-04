# -*- coding: utf-8 -*-
"""Semantic Obligation Registry（Phase S / S3）——同一认识论义务只履行一次

问题: 正文已经表达"超人与逍遥不等同"，Phase 2 仍追加同义补正。字符串/关键词去重
不足——"不是一回事""不能等同""二者有本质区别""只能类比""相似不意味着同一"是同一
analogy boundary 义务的不同措辞，应当视为已履行。

组件（纯规则 + 数据驱动, 不联网、不调 LLM、不新增工具）:

  OBLIGATION_TYPES       六类语义义务:
                           premise_correction          前提校正（用户事实前提有误）
                           analogy_boundary            类比≠等同边界（跨作者比较）
                           counterfactual_boundary     反事实边界（作者无直接史料）
                           uncertainty_disclosure      不确定性披露（结论非唯一）
                           alternative_interpretation  替代解读呈现（解释型问题）
                           source_limitation           来源局限披露（未核验出处）
  ObligationState        REQUIRED / SATISFIED / UNSATISFIED / UNKNOWN（Phase T/T13-C）
  derive_obligations()   由前置裁决（epistemic / interpretation）推导本请求的义务集
  assess_obligations()   用最终回答校验每项义务 → 逐项标注状态
  unsatisfied()          只返回 REQUIRED 且 UNSATISFIED 的义务（唯一允许追加补正的集合）

Phase T（T13-C）: 高层语义义务（alternative_interpretation / uncertainty_disclosure /
analogy_boundary）不再用"关键词未命中 → UNSATISFIED"的错判路径——关键词命中仍可靠地
判 SATISFIED（显式表达即履行）, 未命中时宁可标 UNKNOWN（无法可靠结构化判定）,
不得错误地报 UNSATISFIED（QG2: Q01 答案含"并非唯一"却记 UNSATISFIED、Q16 大纲含
完整反方节仍记 UNSATISFIED 的台账错位）。事实类义务（premise_correction /
counterfactual_boundary / source_limitation）的判定模式是结构性的, 保留两态。
本 Phase 不为此新增任何正文 Guard——UNSATISFIED 补正路径的消费方（interpretation_engine）
已同步改为只依赖结构性信号（overclaim / alternatives_offered）。

规则: 只有 REQUIRED + UNSATISFIED 才允许追加补正; 同一义务一旦 SATISFIED,
任何 Phase 不得因措辞不同重复追加。履行判定基于语义等价表达（见各义务的
fulfillment 词表）, 而非 token/字符串精确匹配。
"""
import re

# ═══════════════════════════════════════════════════════
# 1. 义务类型与状态
# ═══════════════════════════════════════════════════════
OBLIGATION_TYPES = [
    "premise_correction",
    "analogy_boundary",
    "counterfactual_boundary",
    "uncertainty_disclosure",
    "alternative_interpretation",
    "source_limitation",
]
OBLIGATION_STATES = ["REQUIRED", "SATISFIED", "UNSATISFIED", "UNKNOWN"]

# T13-C: 高层语义义务——关键词未命中时标 UNKNOWN 而非 UNSATISFIED
#（命中仍判 SATISFIED: 显式等价表达即履行, 无误判方向）
_HIGH_LEVEL_OBLIGATIONS = {"analogy_boundary", "uncertainty_disclosure", "alternative_interpretation"}


# ═══════════════════════════════════════════════════════
# 2. 履行词表（同一义务的语义等价表达; 命中其一即视为履行）
# ═══════════════════════════════════════════════════════
# 类比≠等同（跨作者比较的边界表达）
ANALOGY_BOUNDARY_ZH = [
    "不是一回事", "并非一回事", "不是一码事", "不能等同", "不可等同", "不能画等号",
    "不能划等号", "不能混为一谈", "不可混为一谈", "并非等同", "并非同一",
    "不是等同", "不是同一个", "不等于", "并不等于",
    "二者有本质区别", "有本质区别", "本质区别", "本质不同",
    "只能类比", "只是类比", "仅是一种类比", "更适合作为类比", "作为一种类比",
    "相似不意味着同一", "相似不等于相同", "相似并非相同",
    "存在可资借鉴的类比", "analogy, not equivalence",
]
ANALOGY_BOUNDARY_EN = [
    "not equivalent", "not the same as", "not one and the same", "not identical",
    "cannot be equated", "cannot be conflated", "are not the same",
    "a valuable analogy", "heuristic analogy", "rather than equivalence",
    "analogy, not equivalence", "not to be equated",
]
ANALOGY_BOUNDARY_PATTERNS = (
    [re.compile(p) for p in ANALOGY_BOUNDARY_ZH] + [re.compile(p, re.I) for p in ANALOGY_BOUNDARY_EN])

# 反事实边界（作者无直接史料的推演声明）
COUNTERFACTUAL_BOUNDARY_PATTERNS = [
    re.compile(r"没有证据表明"), re.compile(r"no evidence (that|the|this)", re.I),
]

# 不确定性披露（结论是众多读法之一）
UNCERTAINTY_DISCLOSURE_PATTERNS = [
    re.compile(r"并非唯一"), re.compile(r"不是唯一"), re.compile(r"非唯一"),
    re.compile(r"一种读法"), re.compile(r"一种理解"), re.compile(r"并非定论"),
    re.compile(r"not the only", re.I), re.compile(r"one reading", re.I),
    re.compile(r"a defensible but not the only", re.I),
]

# 替代解读呈现（解释型问题给出第二种候选; "一种读法/第二种"也视为披露了替代可能）
ALTERNATIVE_INTERPRETATION_PATTERNS = [
    re.compile(r"另一种读法"), re.compile(r"另一种理解"), re.compile(r"另一种可能"),
    re.compile(r"另一种解读"), re.compile(r"也可以读作"), re.compile(r"也可以理解"),
    re.compile(r"也可以被理解"), re.compile(r"也可能被"), re.compile(r"也可以看作"),
    re.compile(r"一种读法"), re.compile(r"两种读法"), re.compile(r"第二种"),
    re.compile(r"读法之一"), re.compile(r"alternative reading", re.I),
    re.compile(r"another reading", re.I), re.compile(r"could also be read", re.I),
    re.compile(r"equally plausible", re.I),
]

# 来源局限披露（引用未通过原典核验）
SOURCE_LIMITATION_PATTERNS = [
    re.compile(r"库中未检索到"), re.compile(r"未检索到"), re.compile(r"未经库中核验"),
    re.compile(r"未能在原典库中直接定位"), re.compile(r"未能定位"), re.compile(r"无法核验"),
    re.compile(r"凭记忆"), re.compile(r"记忆中"), re.compile(r"未能通过核验"),
    re.compile(r"not verified", re.I), re.compile(r"could not be located", re.I),
    re.compile(r"from memory", re.I),
]


# ═══════════════════════════════════════════════════════
# 3. 义务推导（前置裁决 → 本请求必须履行的义务集）
# ═══════════════════════════════════════════════════════
def derive_obligations(epistemic_verdict=None, interpretation_verdict=None):
    """由前置裁决推导 REQUIRED 义务列表

    epistemic_verdict:    run_epistemic_guards 的返回值
    interpretation_verdict: run_interpretation_engine 的返回值
    返回: [{type, status: "REQUIRED", source, ...payload}]
    """
    out = []
    epi = epistemic_verdict or {}
    for c in (epi.get("premise_checks") or []):
        if c.get("status") != "contradicted":
            continue
        out.append({
            "type": "premise_correction",
            "status": "REQUIRED",
            "source": c.get("rule_id") or "premise",
            "rule_id": c.get("rule_id"),
            "corrected_value": c.get("corrected_value") or "",
            "correction_note": c.get("correction_note") or "",
            "referent_mode": c.get("referent_mode") or "current",
        })
    cv = epi.get("counterfactual") or {}
    if cv.get("requires_guard"):
        out.append({
            "type": "counterfactual_boundary", "status": "REQUIRED",
            "source": "counterfactual_guard", "author": cv.get("author") or "",
        })
    iv = interpretation_verdict or {}
    if iv.get("activated"):
        if "cross_author_comparison" in (iv.get("categories") or []):
            out.append({"type": "analogy_boundary", "status": "REQUIRED",
                        "source": "cross_author_comparison"})
        out.append({"type": "alternative_interpretation", "status": "REQUIRED",
                    "source": "interpretation_challenger"})
        out.append({"type": "uncertainty_disclosure", "status": "REQUIRED",
                    "source": "confidence_calibrator"})
    return out


# ═══════════════════════════════════════════════════════
# 4. 履行判定
# ═══════════════════════════════════════════════════════
def _satisfied(ob, answer):
    t = ob.get("type")
    if t == "premise_correction":
        fixed = ob.get("corrected_value") or ""
        nums = re.findall(r"\d+", fixed)
        if nums and any(n in answer for n in nums):
            return True
        return bool(fixed and fixed[:6] in answer)
    if t == "analogy_boundary":
        return any(p.search(answer) for p in ANALOGY_BOUNDARY_PATTERNS)
    if t == "counterfactual_boundary":
        return any(p.search(answer) for p in COUNTERFACTUAL_BOUNDARY_PATTERNS)
    if t == "uncertainty_disclosure":
        return any(p.search(answer) for p in UNCERTAINTY_DISCLOSURE_PATTERNS)
    if t == "alternative_interpretation":
        return any(p.search(answer) for p in ALTERNATIVE_INTERPRETATION_PATTERNS)
    if t == "source_limitation":
        return any(p.search(answer) for p in SOURCE_LIMITATION_PATTERNS)
    return False


def _hits(ob, answer):
    t = ob.get("type")
    if t == "premise_correction":
        fixed = ob.get("corrected_value") or ""
        return [n for n in re.findall(r"\d+", fixed) if n in (answer or "")]
    tables = {
        "analogy_boundary": ANALOGY_BOUNDARY_PATTERNS,
        "counterfactual_boundary": COUNTERFACTUAL_BOUNDARY_PATTERNS,
        "uncertainty_disclosure": UNCERTAINTY_DISCLOSURE_PATTERNS,
        "alternative_interpretation": ALTERNATIVE_INTERPRETATION_PATTERNS,
        "source_limitation": SOURCE_LIMITATION_PATTERNS,
    }
    return [p.pattern[:30] for p in tables.get(t, []) if p.search(answer or "")]


def assess_obligations(obligations, answer):
    """逐项判定: REQUIRED → SATISFIED / UNSATISFIED / UNKNOWN（附命中片段, 审计用）
    T13-C: 高层语义义务未命中关键词 → UNKNOWN（不可靠判 UNSATISFIED）"""
    ans = answer or ""
    out = []
    for ob in obligations or []:
        satisfied = _satisfied(ob, ans)
        if satisfied:
            status = "SATISFIED"
        elif ob.get("type") in _HIGH_LEVEL_OBLIGATIONS:
            status = "UNKNOWN"
        else:
            status = "UNSATISFIED"
        out.append({
            **ob,
            "status": status,
            "hits": _hits(ob, ans),
        })
    return out


def unsatisfied(obligations, answer):
    """只有 REQUIRED 且未履行的义务才允许追加补正（补正去重的唯一判据）"""
    return [o for o in assess_obligations(obligations, answer)
            if o["status"] == "UNSATISFIED"]


def status_map(obligations, answer):
    """type → status（快速查询用）"""
    return {o["type"]: o["status"] for o in assess_obligations(obligations, answer)}
