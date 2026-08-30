# -*- coding: utf-8 -*-
"""Evaluation Suite（Phase 4）——回答质量五维评分（纯规则, 不调 LLM）

把前四个 Phase 的裁决汇总成可断言的回答质量评估。每个评分器都是确定性规则:

  evaluate_premise_accuracy    前提准确性: 错误数字 / 错误作者 / 错误书名 / 错误年代 /
                               错误概念归属 的检出、校正落实、校正是否破坏主体分析
  evaluate_epistemic_accuracy  知识论准确性: fact/quote/inference/interpretation/
                               counterfactual/speculation 的区分与措辞一致性
  evaluate_interpretation_quality  解释质量: confirmation bias / alternative explanation /
                               cross-framework overreach（类比≠等同）
  evaluate_evidence            证据: citation validity / citation used rate /
                               unsupported claim rate
  evaluate_answer_ux           回答体验: answer directness / redundancy / reasoning noise
  evaluate_answer              五维汇总（供运行时审计日志与测试断言）

用法（backend/tests/ 的 Evaluation Suite 用例与 regression_oldman_sea 回归集直接消费;
运行时可在 done 后调用 evaluate_answer 把评分写入审计日志）:
  report = evaluate_answer(question, answer, tool_log=..., language="zh")
  每个维度返回 {score: 0..1, passed: bool, metrics: {...}, findings: [...]}
"""
import re

from epistemic_guard import PremiseVerifier, EpistemicClaimClassifier, _match_philosopher
from interpretation_engine import InterpretationChallenger, scan_interpretation
from evidence_contract import build_evidence_contract
from answer_composer import scan_composition, strong_wording_hits

# ═══════════════════════════════════════════════════════
# 1. Premise Accuracy —— 错误数字/作者/书名/年代/概念归属
# ═══════════════════════════════════════════════════════
def _premise_category(rule_id):
    """rule_id → 错误类别（评估维度要求的五类）"""
    if rule_id.startswith("title:"):
        return "wrong_book_title"
    if rule_id.startswith("concept:"):
        return "wrong_concept_attribution"
    if rule_id.startswith("attribution:"):
        return "wrong_author"
    if rule_id == "oldman_84_days":
        return "wrong_number"
    if rule_id in ("antichrist_1888", "rebel_1951"):
        return "wrong_era"
    return "other"


def _correction_present(check, answer):
    """校正落实: 回答包含 corrected_value 中任一数字或前缀（多数字值逐个匹配, 防"19511942"拼接误判）"""
    fixed = check.get("corrected_value") or ""
    ans = answer or ""
    nums = re.findall(r"\d+", fixed)
    if nums and any(n in ans for n in nums):
        return True
    return bool(fixed and fixed[:6] in ans)


def _analysis_intact(check, answer):
    """校正是否破坏主体分析: 校正之后仍有实质内容（≥40 字）+ 无拒绝/敷衍"""
    ans = answer or ""
    if len(ans) < 80:
        return False
    if any(r in ans for r in ("无法回答", "不能回答", "拒绝回答", "我回答不了")):
        return False
    fixed = check.get("corrected_value") or ""
    digits = next((d for d in re.findall(r"\d+", fixed) if d in ans), "")
    rest = ans
    if digits:
        i = ans.find(digits)
        if i >= 0:
            rest = ans[i + len(digits):]
    return len(rest) >= 40


def evaluate_premise_accuracy(question, answer, checks=None, language="zh"):
    """前提准确性: 每个已检出矛盾 → 校正落实? 破坏主体分析?

    metrics: {detected, corrected, disruptive, categories: {类别: [rule_id]}}
    """
    checks = checks if checks is not None else PremiseVerifier().check(question)
    contrad = [c for c in checks if c.get("status") == "contradicted"]
    cases, categories = [], {}
    for c in contrad:
        cat = _premise_category(c.get("rule_id") or "")
        categories.setdefault(cat, []).append(c.get("rule_id"))
        corrected = _correction_present(c, answer or "")
        intact = _analysis_intact(c, answer or "")
        cases.append({
            "rule_id": c.get("rule_id"), "category": cat,
            "corrected": corrected, "analysis_intact": intact,
            "disruptive": corrected and not intact,
        })
    n = len(cases)
    passed = all(not x["disruptive"] and x["corrected"] for x in cases) if n else True
    score = 1.0 if n == 0 else sum(
        1.0 if x["corrected"] and x["analysis_intact"] else
        0.5 if x["corrected"] else 0.0 for x in cases) / n
    findings = []
    for x in cases:
        if not x["corrected"]:
            findings.append(f"correction_missing:{x['rule_id']}")
        elif x["disruptive"]:
            findings.append(f"correction_disrupted_analysis:{x['rule_id']}")
    return {
        "score": round(score, 2), "passed": passed,
        "metrics": {"detected": n, "corrected": sum(1 for x in cases if x["corrected"]),
                    "disruptive": sum(1 for x in cases if x["disruptive"]),
                    "categories": categories},
        "findings": findings,
    }


# ═══════════════════════════════════════════════════════
# 2. Epistemic Accuracy —— fact/quote/inference/interpretation/counterfactual/speculation
# ═══════════════════════════════════════════════════════
_SPECULATION_MARKERS = ["或许", "可能", "也许", "推测", "猜测", "一种可能", "不妨设想"]
_COUNTERFACTUAL_ASSERT = re.compile(
    r"(一定会|肯定会|必定会|绝不会|必然认为|肯定认为|一定认为|无疑会)")
_QUOTE_CUE = re.compile(r"(原文写道|原文说|原话是|书上原话|直接引用)")
_CITE_MARKER = re.compile(r"【《[^》]+》[^】]*】")


def evaluate_epistemic_accuracy(answer, language="zh"):
    """知识论准确性: 回答的措辞与知识论层级一致

    findings:
      unhedged_assertion:{词}   未经证据支持的强化措辞（完全正确/毫无疑问/本质就是…）
      overclaim_unhedged        强模态 + 解释性判断（"一定完成了转变"≠ 原文所说）
      counterfactual_unbounded  作者反事实断言无边界（"加缪一定会认为…"无"没有证据表明"）
      quote_unlocatable         宣称原文引语但既无引号也无引用标注（无法定位）
      hedge_contradiction       同一句既用推测词又用强模态
    metrics: claim_types 计数（六类区分）; overclaim / unbounded / unlocatable
    """
    cl = EpistemicClaimClassifier()
    sents = cl.split_sentences(answer or "")
    claims = [cl.classify(s, extra=True) for s in sents if len(s.strip()) >= 8]
    findings = []
    # 未经 epistemic state 支持的强化措辞（与 answer_composer 同一真源）
    for w in strong_wording_hits(answer or ""):
        findings.append(f"unhedged_assertion:{w}")
    for c in claims:
        t = c["claim"]
        if any(m in t for m in _SPECULATION_MARKERS) and _STRONG_MODAL.search(t):
            findings.append(f"hedge_contradiction:{t[:24]}")
            break
        if c.get("strong_modal") and c["epistemic_type"] in (
                "TEXTUAL_INFERENCE", "CROSS_TEXT_INTERPRETATION", "SPECULATION"):
            findings.append(f"overclaim_unhedged:{t[:24]}")
            break
        if _QUOTE_CUE.search(t) and not re.search(r"[“\"『]", t) and not _CITE_MARKER.search(t):
            findings.append(f"quote_unlocatable:{t[:24]}")
    # 反事实断言无边界: 作者名 + 断言词, 但回答通篇没有"没有证据表明"
    authors = _match_philosopher(answer or "")
    unbounded = False
    if authors and "没有证据表明" not in (answer or ""):
        for a in authors[:1]:
            if re.search(rf"{a}[^。！？\n]{{0,20}}(一定会|绝不会|肯定认为|一定认为|必定会)", answer or ""):
                unbounded = True
                findings.append(f"counterfactual_unbounded:{a}")
                break
    types = {}
    for c in claims:
        types[c["epistemic_type"]] = types.get(c["epistemic_type"], 0) + 1
    score = 1.0
    score -= 0.3 * len([f for f in findings if f.startswith("unhedged_assertion")])
    if any(f.startswith("overclaim_unhedged") for f in findings):
        score -= 0.4
    if unbounded:
        score -= 0.3
    if any(f.startswith("quote_unlocatable") for f in findings):
        score -= 0.2
    if any(f.startswith("hedge_contradiction") for f in findings):
        score -= 0.2
    score = max(0.0, round(score, 2))
    return {
        "score": score, "passed": not findings,
        "metrics": {"claim_types": types, "claim_count": len(claims)},
        "findings": findings,
    }


# ═══════════════════════════════════════════════════════
# 3. Interpretation Quality —— confirmation bias / alternative / overreach
# ═══════════════════════════════════════════════════════
def evaluate_interpretation_quality(question, answer, tool_log=None, language="zh"):
    """解释质量: 单候选（confirmation bias）/ 无替代解释 / 跨框架越级

    findings:
      confirmation_bias          解释型问题只给单候选（无替代读法/无反证痕迹）
      no_challenge_attempt       未主动设想削弱材料（absent 记为软性发现）
      cross_framework_overreach  越级断言（本质完全一样/毫无疑问/唯一解释 等）
    """
    verdict = InterpretationChallenger().check(question)
    scan = scan_interpretation(verdict, answer, language, tool_log)
    findings = []
    if not scan["activated"]:
        return {
            "score": 1.0, "passed": True,
            "metrics": {"activated": False, "categories": []},
            "findings": [],
        }
    if scan["overclaim"]:
        findings.append("cross_framework_overreach")
    if not scan["alternatives_offered"]:
        findings.append("confirmation_bias")
    if scan["challenging_evidence_trace"] == "absent":
        findings.append("no_challenge_attempt")
    score = 1.0 - 0.4 * findings.count("cross_framework_overreach") \
        - 0.4 * findings.count("confirmation_bias") - 0.2 * findings.count("no_challenge_attempt")
    return {
        "score": max(0.0, round(score, 2)), "passed": not findings,
        "metrics": {"activated": True, "categories": scan["categories"],
                    "alternatives_offered": scan["alternatives_offered"],
                    "challenging_trace": scan["challenging_evidence_trace"],
                    "overclaim": scan["overclaim"]},
        "findings": findings,
    }


# ═══════════════════════════════════════════════════════
# 4. Evidence —— citation validity / used rate / unsupported claim rate
# ═══════════════════════════════════════════════════════
def evaluate_evidence(answer, contract=None, tool_log=None, language="zh"):
    """证据: 未核验引用 / 引用使用率 / 无支撑 Claim 率

    findings:
      unverified_citation:{书}  回答引用了检索池无法定位的原典
      low_used_rate              检索很多但回答几乎没用（used/retrieved < 0.2 且 retrieved ≥ 5）
      unsupported_claims         无 DIRECT evidence 支撑的断言占比 > 0.5
                                  （SPECULATION/UNKNOWN 除外——它们本就无需直接证据）
    """
    if contract is None:
        contract = build_evidence_contract(tool_log or [], answer, language=language)
    findings = []
    for u in contract["unverified_citations"]:
        findings.append(f"unverified_citation:{u.get('book')}")
    retrieved = contract["retrieved_count"]
    used = contract["used_count"]
    used_rate = round(used / retrieved, 2) if retrieved else None
    if retrieved >= 5 and used_rate is not None and used_rate < 0.2:
        findings.append("low_used_rate")
    claims = contract["claims"]
    assessable = [c for c in claims
                  if c["epistemic_type"] not in ("SPECULATION", "UNKNOWN")]
    unsupported = [c for c in assessable if not c["direct_evidence"]]
    unsupported_rate = round(len(unsupported) / len(assessable), 2) if assessable else 0.0
    if assessable and unsupported_rate > 0.5:
        findings.append("unsupported_claims")
    score = 1.0
    score -= 0.3 * len(contract["unverified_citations"])
    if "unsupported_claims" in findings:
        score -= 0.3
    score = max(0.0, round(score, 2))
    return {
        "score": score, "passed": not findings,
        "metrics": {"retrieved_count": retrieved, "used_count": used,
                    "used_rate": used_rate,
                    "unverified_count": len(contract["unverified_citations"]),
                    "unsupported_rate": unsupported_rate,
                    "claim_count": len(claims)},
        "findings": findings,
    }


# ═══════════════════════════════════════════════════════
# 5. Answer UX —— directness / redundancy / reasoning noise
# ═══════════════════════════════════════════════════════
def evaluate_answer_ux(answer, composer_scan=None, language="zh"):
    """回答体验: 直接判断 / 冗余 / 推理噪音 / 默认骨架残留

    findings:
      process_leadin            首句是过程叙述而非直接判断
      reasoning_noise:{词}      过程叙述泄漏进正文（"让我检索…"）
      default_block:{词}        材料说明/检索过程/原典路径/再总结 等默认骨架残留
      redundancy:{详情}         重复句 / 总结连接词堆叠
    """
    scan = composer_scan if composer_scan is not None \
        else scan_composition({"activated": True}, answer, language)
    findings = []
    if scan["direct_judgment"] is False:
        findings.append("process_leadin")
    for p in scan["reasoning_noise"]:
        findings.append(f"reasoning_noise:{p}")
    for b in scan["banned_blocks"]:
        findings.append(f"default_block:{b}")
    for r in scan["redundancy"]:
        findings.append(f"redundancy:{r}")
    score = 1.0
    if scan["direct_judgment"] is False:
        score -= 0.3
    score -= 0.2 * len(scan["reasoning_noise"])
    score -= 0.2 * len(scan["banned_blocks"])
    score -= 0.2 * len(scan["redundancy"])
    return {
        "score": max(0.0, round(score, 2)), "passed": not findings,
        "metrics": {"direct_judgment": scan["direct_judgment"],
                    "structure": scan["structure_signals"]},
        "findings": findings,
    }


# ═══════════════════════════════════════════════════════
# 6. 汇总: evaluate_answer
# ═══════════════════════════════════════════════════════
def evaluate_answer(question, answer, tool_log=None, language="zh"):
    """五维汇总评估（供运行时审计与测试断言）

    返回: {premise, epistemic, interpretation, evidence, ux, overall, passed_all}
    """
    report = {
        "premise": evaluate_premise_accuracy(question, answer, language=language),
        "epistemic": evaluate_epistemic_accuracy(answer, language=language),
        "interpretation": evaluate_interpretation_quality(question, answer, tool_log, language),
        "evidence": evaluate_evidence(answer, contract=None, tool_log=tool_log, language=language),
        "ux": evaluate_answer_ux(answer, language=language),
    }
    dims = ("premise", "epistemic", "interpretation", "evidence", "ux")
    scores = [report[k]["score"] for k in dims]
    report["overall"] = round(sum(scores) / len(scores), 2)
    report["passed_all"] = all(report[k]["passed"] for k in dims)
    return report


# 供 epistemic 评分复用的强模态（与 epistemic_guard 保持单一真源, 局部兜底）
_STRONG_MODAL = re.compile(r"一定|必然|肯定|必定|毫无疑问|绝对")
