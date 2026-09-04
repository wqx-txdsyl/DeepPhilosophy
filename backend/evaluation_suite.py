# -*- coding: utf-8 -*-
"""Evaluation Suite（Phase 4）——回答质量五维评分（纯规则, 不调 LLM; 离线评估工具）

O4 Cognitive Layer Collapse 注: 原 interpretation_engine.py / answer_composer.py /
semantic_obligations.py 是 runtime 内的第二套认知裁决层（Shadow Agent）, 已从生产引擎
删除。本评估套件是纯离线评分器（只在测试/回归中调用, 不在 stream_agent 请求路径上）,
其解释质量与回答体验维度所需的检测启发式以自带副本形式保留在本文件中
（O4 任务书: "把这两个函数 MOVE 进 evaluation_suite（自带副本）"）——它们不再对
任何运行时行为产生注入/补正/改写效果。

五个评分器都是确定性规则:

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

用法（backend/tests/ 的 Evaluation Suite 用例与 regression_oldman_sea 回归集直接消费）:
  report = evaluate_answer(question, answer, tool_log=..., language="zh")
  每个维度返回 {score: 0..1, passed: bool, metrics: {...}, findings: [...]}
"""
import re

from epistemic_guard import PremiseVerifier, EpistemicClaimClassifier, _match_philosopher
from evidence_contract import build_evidence_contract

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
    # 未经证据支持的强化措辞（原 answer_composer 检测真源, O4 后为本文件自带副本）
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
      low_used_rate             检索很多但回答几乎没用（used/retrieved < 0.2 且 retrieved ≥ 5）
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


# ═══════════════════════════════════════════════════════════════════════
# 以下为评估专用检测启发式（自带副本; O4 后生产引擎不含这些逻辑——
# 原 answer_composer.py / interpretation_engine.py / semantic_obligations.py 已删除,
# 二者对 runtime 只剩 prompt 注入与 done 遥测, 按 O4 delete-first 整体移除;
# 本文件是纯离线评分器, 不在请求路径上, 不对回答产生任何注入/补正/改写效果。）
# ═══════════════════════════════════════════════════════════════════════

# ── 副本 A（原 answer_composer）: 强化措辞 / 回答结构 / 推理噪音检测 ──
FORBIDDEN_STRONG = [
    "完全正确", "绝对正确", "绝对肯定", "毫无疑问", "毫无疑义",
    "本质就是", "本质上就是", "本质上是", "本质即", "说到底就是",
    "绝不会", "绝无可能", "一定是", "必然就是", "必然是", "必定是", "绝对是",
    "唯一正确", "唯一解释", "唯一读法", "唯一可能",
    "definitely", "absolutely", "without a doubt", "completely correct", "essentially the same",
]
_NEGATION_BEFORE = re.compile(r"(并非|不是|未必|不一定|并不|也不|不见得|难说|称不上|算不上)$")

BANNED_DEFAULT_BLOCKS = [
    "材料说明", "先说明材料", "先交代材料", "先说材料", "材料如下", "材料整理如下",
    "工具说明", "检索过程", "检索结果如下", "检索情况",
    "五层报告", "五层分析", "五层结构",
    "再总结", "总结一下刚才", "让我先说明",
]

REASONING_NOISE = [
    "让我检索", "让我读取", "让我查", "让我搜", "让我调用", "让我看看", "让我读一读",
    "我来检索", "我来查", "我来搜", "我先检索", "我先查", "先让我", "让我先",
    "现在我已经有材料", "我已经有材料", "我已经有足够的材料", "我已经查到了",
    "我已经找到了", "我调用了", "我查阅了", "我搜索了", "我检索了", "我读取了",
    "工具返回", "工具结果显示", "检索结果显示", "刚才的工具", "我看了下",
]

_PROCESS_LEADIN = re.compile(
    r"^(让我|我先|好的,?让我|嗯,?让我|等我|我需要先|关于这个问题,?让我|先说明|先交代|"
    r"先看材料|先检索|我检索了|我查了|我调用|我查阅|我搜索|我读取|经过检索|在检索|"
    r"材料说明|工具说明|检索过程|再总结|五层|原典路径)")
_EMPTY_LEADIN = re.compile(r"^(这是一个好问题|这确实是个好问题|好问题|谢谢你的问题|你的问题很有深度|关于(这个|你问的))$")

_CONCLUSION_STACK = ["综上", "总之", "总而言之", "总结", "结论是", "说到底"]


def _strong_hits(answer):
    """强化措辞命中列表（否定词须紧邻命中前才豁免——"并非完全正确"不误伤, "这完全正确"照报）"""
    t = answer or ""
    out = []
    for w in FORBIDDEN_STRONG:
        start = 0
        while True:
            i = t.find(w, start)
            if i < 0:
                break
            if not _NEGATION_BEFORE.search(t[max(0, i - 3):i]):
                out.append(w)
            start = i + len(w)
    return out


def strong_wording_hits(answer):
    """回答中的强化措辞命中（评估套件用; O4 后真源移至本文件）"""
    return _strong_hits(answer)


def _noise_hits(answer):
    return [p for p in REASONING_NOISE if p in (answer or "")]


def _block_hits(answer):
    return [b for b in BANNED_DEFAULT_BLOCKS if b in (answer or "")]


def _first_sentence(text):
    for s in re.split(r"[。！？；!?;\n]+", (text or "").strip()):
        if s.strip():
            return s.strip()
    return ""


def _is_direct(first):
    if not first:
        return False
    if _PROCESS_LEADIN.match(first):
        return False
    if _EMPTY_LEADIN.match(first):
        return False
    return True


def _structure_signals(answer):
    ans = answer or ""
    return {
        "evidence_marker": bool(re.search(r"【《[^》]+》[^】]*】", ans)),
        "reasons_enumerated": bool(re.search(r"(首先|其次|再次|最后|第一|第二|第三|其一|其二|理由[一二三四1234])", ans)),
        "counter_qualification": bool(re.search(r"(但|不过|然而|需要(注意|指出|限定)|另一种|局限|反方|值得怀疑|并非唯一|不一定)", ans)),
        "conclusion_marker": bool(re.search(r"(综上|总之|结论|说到底|因此|可见)", ans)),
    }


def _redundancy_findings(answer):
    """冗余: 归一化后完全重复的句子 / 总结连接词堆叠"""
    out = []
    sents = [s.strip() for s in re.split(r"[。！？；!?;\n]+", answer or "") if s.strip()]
    normed = [re.sub(r"[\s，,、：:]+", "", s) for s in sents]
    seen = {}
    for i, n in enumerate(normed):
        if len(n) >= 12:
            seen.setdefault(n, []).append(i)
    for n, idxs in seen.items():
        if len(idxs) >= 2:
            out.append(f"duplicated_sentence:{sents[idxs[0]][:24]}")
            break
    stack = sum(1 for m in _CONCLUSION_STACK if m in (answer or ""))
    if stack >= 3:
        out.append("conclusion_connector_stack")
    return out


def scan_composition(verdict, answer, language="zh", interpretation_scan=None, budget_scan=None):
    """应答后结构检测（评估用; 无 appends——runtime 不再有任何补正通道）:
    结构信号 / 默认骨架残留 / 强化措辞 / 推理噪音 / 冗余"""
    res = {
        "activated": bool(verdict.get("activated")),
        "direct_judgment": None,
        "structure_signals": {},
        "banned_blocks": [],
        "strong_wording": [],
        "reasoning_noise": [],
        "redundancy": [],
        "appends": [],
    }
    if not res["activated"]:
        return res
    ans = answer or ""
    res["direct_judgment"] = _is_direct(_first_sentence(ans))
    res["structure_signals"] = _structure_signals(ans)
    res["banned_blocks"] = _block_hits(ans)
    res["strong_wording"] = _strong_hits(ans)
    res["reasoning_noise"] = _noise_hits(ans)
    res["redundancy"] = _redundancy_findings(ans)
    return res


# ── 副本 B（原 interpretation_engine）: 解释型问题识别 / 越级断言 / 多候选检测 ──
# 解释性动词/问法（触发"这是解释型问题"的强信号）
_INTERP_VERBS = [
    "意味着", "象征着", "象征", "隐喻", "寓意", "暗示", "解读", "读作", "代表", "体现出",
    "反映出", "反映", "潜台词", "言外之意", "深层含义", "背后的",
    "怎么理解", "如何理解", "作何理解", "怎么解读", "如何解读", "究竟象征", "到底象征",
]
_LITERARY_OBJ = [
    "梦", "梦见", "梦到", "狮子", "老虎", "老人", "小说", "故事", "人物", "主人公", "角色",
    "情节", "文学", "作品", "叙事", "意象", "结尾", "结局", "剧情", "寓言", "童话", "诗歌",
    "戏剧", "小说里", "象征物", "神话",
]
_PHIL_OBJ = [
    "哲学", "思想", "理论", "概念", "观点", "主义", "框架", "意义", "存在", "荒诞", "自由",
    "虚无", "本质", "生命", "精神", "超验", "道德", "灵魂", "世界", "索取", "转化", "态度",
    "目的", "价值", "幸福", "理式", "理性", "意志",
]
_COMPARISON_CUES = [
    "对比", "比较", "异同", "区别", "一样", "相同", "相通", "谁更", "类似", "类比",
    "是不是", "是否", "一不一样", "一回事", "相同点", "不同点", "共通", "契合", "对应", "联系起来",
]
_HISTORY_AMBIGUITY = [
    "众说纷纭", "存在争议", "有争议", "学界", "历来", "悬案", "谜团", "未解之谜",
    "史料不足", "史料缺乏", "无定论", "尚无定论", "解读不一", "分歧", "史家", "历史学家",
]
_HISTORY_OBJ = [
    "历史", "事件", "记载", "史料", "时代", "战争", "时期", "人物", "皇帝", "王朝",
    "起义", "变法", "革命", "辩论", "论战", "生平", "去世",
]
_FRAMED_RE = re.compile(r"从《([^》]{1,40})》[^。！？]{0,24}看")
_EITHER_OR_RE = re.compile(r"是[^。！？]{1,30}还是")

# 跨体系计数: 系统名 → 别名
CROSS_SYSTEMS = {
    "加缪": ["加缪", "加缪主义", "荒诞哲学", "西西弗斯"],
    "尼采": ["尼采", "权力意志", "永恒轮回", "超人哲学", "超人"],
    "庄子": ["庄子", "庄周", "逍遥游", "逍遥", "齐物"],
    "老庄/道家": ["老庄", "道家", "老子", "道德经", "无为"],
    "佛教": ["佛教", "佛学", "佛陀", "释迦牟尼", "涅槃", "缘起", "空性"],
    "斯多葛": ["斯多葛", "斯多亚", "斯多噶", "塞涅卡", "爱比克泰德", "马可·奥勒留"],
    "基督教": ["基督教", "圣经", "奥古斯丁", "神学", "三位一体"],
    "儒家": ["儒家", "孔孟", "仁义", "论语"],
    "康德": ["康德", "义务论", "先验"],
    "黑格尔": ["黑格尔", "绝对精神", "辩证法"],
    "叔本华": ["叔本华", "意志主义", "表象世界"],
    "萨特": ["萨特", "自为存在"],
    "海德格尔": ["海德格尔", "此在", "存在之思"],
    "现象学": ["现象学", "胡塞尔"],
    "分析哲学": ["分析哲学", "语言分析", "维特根斯坦", "逻辑哲学论"],
    "实用主义": ["实用主义", "詹姆士", "杜威", "皮尔士"],
    "马克思主义": ["马克思", "马克思主义", "异化", "历史唯物主义"],
    "柏拉图": ["柏拉图", "理念论", "洞穴喻"],
    "亚里士多德": ["亚里士多德", "四因", "潜与现实"],
    "弗洛伊德/心理学": ["弗洛伊德", "精神分析", "潜意识", "心理学"],
    "伊壁鸠鲁": ["伊壁鸠鲁", "快乐主义", "享乐主义"],
    "犬儒主义": ["犬儒", "第欧根尼"],
    "斯宾诺莎": ["斯宾诺莎", "实体论"],
    "存在主义": ["存在主义", "荒谬主义"],
}

_NEGATED_OVERCLAIM = ("并非唯一", "不是唯一", "并非必然", "不是必然", "非唯一",
                      "不是一个", "未必是", "不一定", "不是一回事", "并非一回事",
                      "not the only", "not necessarily", "not the same",
                      "not equivalent", "not identical")
_OVERCLAIM_RE = re.compile(
    r"完全正确|绝对正确|毫无疑问|显然是|显然就是|本质上完全一样|本质完全一样|本质相同|完全相同|"
    r"一模一样|是一回事|完全等同|必然如此|一定就是|唯一正确|唯一的解释|唯一的解读|唯一读法|唯一可能|"
    r"definitely|obviously|exactly the same|essentially the same|completely correct|identical")
_DIRECT_QUOTE_RE = re.compile(r"[“\"]([^”\"]{4,120})[”\"]")
_TEXT_CITE_RE = re.compile(r"【《[^》]+》[^】]*】")
_BOOK_QUOTE_RE = re.compile(r"《[^》]{2,30}》[^。]{0,60}(原文|写道|引文|说过|写到)")
_SCHOLARLY_RE = re.compile(r"研究|学界|有学者|文献(指出|认为)|评注者|权威解读")

_ALT_MARKERS = [
    "并非唯一", "不是唯一", "另一种读法", "另一种理解", "另一种可能", "也可以读作", "也可以理解",
    "也可能被", "一种阅读", "一种读法", "其他读法", "不同读法", "alternative", "not the only",
    "another reading", "could also be read", "equally plausible",
]
_CHALLENGE_FOUND = ["削弱", "反证", "反驳", "质疑", "挑战证据", "challenging evidence", "counter-evidence"]
_CHALLENGE_EMPTY = [
    "未检索到足以削弱", "未找到反证", "没有发现反证", "没有找到削弱", "无削弱材料", "未检索到削弱",
    "no counter-evidence", "no evidence against", "nothing that weakens",
]
_INTERPRETIVE_ANSWER = [
    "意味着", "象征着", "隐喻", "寓意", "暗示", "解读", "读作", "代表", "体现", "反映",
    "本身", "本质", "精神", "意义", "可以说", "是一种", "可以理解", "相通", "象征",
]

# 四档置信度语言（评估分层用）
TIERS = [
    ("strong", 0.85, "有很强文本依据"),
    ("moderate", 0.65, "相当有力的解释"),
    ("tentative", 0.40, "可成立但并非唯一的解释"),
    ("analogical", 0.0, "更适合作为启发性类比"),
]
TIER_LANGUAGE_ZH = {
    "strong": "这是一种有很强文本依据的解释",
    "moderate": "这是一个相当有力的解释",
    "tentative": "这是一种可成立但并非唯一的解释",
    "analogical": "这种联系更适合作为启发性类比",
}
TIER_LANGUAGE_EN = {
    "strong": "This interpretation has very strong textual support",
    "moderate": "This is a fairly forceful interpretation",
    "tentative": "This is a defensible but not the only interpretation",
    "analogical": "This connection is better treated as a heuristic analogy",
}


class InterpretationChallenger:
    """解释型问题识别 + 多候选解读/双面证据/反证尝试的结构要求（评估用副本）

    check(message) → {"activated", "categories", "object", "hypothesis_min",
                      "evidence_requirement", "analogy_guard", "depth_guard"}
    """

    def check(self, message):
        msg = (message or "").strip()
        out = {
            "activated": False,
            "categories": [],
            "object": "",
            "hypothesis_min": 0,
            "evidence_requirement": {"supporting": False, "challenging": False},
            "analogy_guard": False,
            "depth_guard": False,
            "question": msg,
        }
        if not msg:
            return out
        philo = _match_philosopher(msg)
        interp_cue = any(v in msg for v in _INTERP_VERBS) or bool(_FRAMED_RE.search(msg))
        lit_obj = any(v in msg for v in _LITERARY_OBJ)
        phil_obj = any(v in msg for v in _PHIL_OBJ) or bool(philo)
        yn = ("是不是" in msg) or ("是否" in msg) or bool(_EITHER_OR_RE.search(msg))
        concept_hits = [sys_name for sys_name, aliases in CROSS_SYSTEMS.items()
                        if any(a in msg for a in aliases)]
        phil_obj = phil_obj or bool(concept_hits)

        cats = []
        if (len(set(philo)) >= 2 or len(concept_hits) >= 2) and any(c in msg for c in _COMPARISON_CUES):
            cats.append("cross_author_comparison")
        if any(c in msg for c in _HISTORY_AMBIGUITY) and any(c in msg for c in _HISTORY_OBJ):
            cats.append("ambiguous_historical_interpretation")
        if (interp_cue and lit_obj) or (yn and lit_obj):
            cats.append("literary_interpretation")
        if (interp_cue and phil_obj) or (yn and phil_obj):
            cats.append("philosophical_interpretation")

        if not cats:
            return out
        out["activated"] = True
        out["categories"] = cats
        out["hypothesis_min"] = 2
        out["evidence_requirement"] = {"supporting": True, "challenging": True}
        out["analogy_guard"] = "cross_author_comparison" in cats
        out["depth_guard"] = True
        out["object"] = self._extract_object(msg)
        return out

    @staticmethod
    def _extract_object(msg):
        """解释对象提取: 《作品》→ 知名意象短语（梦狮/蝴蝶梦/超人…）→ 空"""
        m = re.search(r"《([^》]{1,40})》", msg)
        if m:
            return m.group(1)
        for cue in ("老人梦狮", "梦狮", "蝴蝶梦", "超人", "逍遥", "梦中", "梦见的", "无何有之乡", "寓言"):
            if cue in msg:
                return cue
        return ""


class ConfidenceCalibrator:
    """解释置信度校准（评估用副本; 数字仅内部评分, 不进入任何用户可见流）"""

    @staticmethod
    def count_cross_systems(text):
        if not text:
            return 0
        found = []
        for name, aliases in CROSS_SYSTEMS.items():
            if any(a in (text or "") for a in aliases):
                found.append(name)
        return len(found)

    @staticmethod
    def interpretation_order(text_or_signals):
        return text_or_signals.get("interpretation_order", 0) if isinstance(text_or_signals, dict) \
            else ConfidenceCalibrator.count_cross_systems(text_or_signals)

    @staticmethod
    def depth_penalty(order):
        return 0.05 * max(0, order - 1)

    def detect_signals(self, text):
        t = text or ""
        t_clean = t
        for neg in _NEGATED_OVERCLAIM:
            t_clean = t_clean.replace(neg, "")
        order = self.count_cross_systems(t)
        return {
            "primary_text_support": bool(_TEXT_CITE_RE.search(t) or _BOOK_QUOTE_RE.search(t)),
            "direct_quote": bool(_DIRECT_QUOTE_RE.search(t)) and ("《" in t),
            "scholarly": bool(_SCHOLARLY_RE.search(t)),
            "overclaim": bool(_OVERCLAIM_RE.search(t_clean)),
            "interpretation_order": order,
        }

    def calibrate(self, text=None, signals=None):
        sig = signals if signals is not None else self.detect_signals(text or "")
        conf = 0.50
        if sig.get("primary_text_support"):
            conf += 0.15
        if sig.get("direct_quote"):
            conf += 0.10
        if sig.get("scholarly"):
            conf += 0.05
        if sig.get("overclaim"):
            conf -= 0.10
        conf -= self.depth_penalty(sig.get("interpretation_order", 0))
        conf = round(max(0.05, min(0.95, conf)), 2)
        basis = []
        if sig.get("primary_text_support"):
            basis.append("primary_text_support")
        if sig.get("direct_quote"):
            basis.append("direct_quote")
        if sig.get("scholarly"):
            basis.append("scholarly_consensus")
        if not sig.get("primary_text_support") and not sig.get("direct_quote"):
            basis.append("cross_text_inference")
        if sig.get("interpretation_order", 0) >= 2:
            basis.append("framework_chain")
        if sig.get("overclaim"):
            basis.append("overclaim_detected")
        return {"confidence": conf, "basis": basis, "tier": self.tier_of(conf), "signals": sig}

    @staticmethod
    def tier_of(confidence):
        for key, threshold, _ in TIERS:
            if confidence >= threshold:
                return key
        return "analogical"

    @staticmethod
    def tier_language(tier, language="zh"):
        return TIER_LANGUAGE_ZH.get(tier, TIER_LANGUAGE_ZH["tentative"]) if language == "zh" \
            else TIER_LANGUAGE_EN.get(tier, TIER_LANGUAGE_EN["tentative"])


def _challenge_trace(ans, tool_log):
    """挑战证据痕迹: found=答案/检索中见反证; empty=明确宣称无削弱材料（允许）; absent=未提及"""
    if any(m in (ans or "") for m in _CHALLENGE_FOUND):
        return "found"
    if any(m in (ans or "") for m in _CHALLENGE_EMPTY):
        return "empty"
    quest = [str(tc.get("args", {}).get("query", "")) for tc in (tool_log or [])
             if isinstance(tc, dict) and tc.get("name") in ("search_books", "websearch", "concept_trace")]
    if any(any(k in q for k in ("反例", "异议", "批评", "质疑", "不同读法", "削弱")) for q in quest):
        return "found"
    return "absent"


def scan_interpretation(verdict, answer, language="zh", tool_log=None):
    """解释型回答检测（评估用; 无 appends——runtime 不再有任何补正通道）:
    候选读法 / 越级断言 / 反证痕迹 / 置信度档位"""
    res = {
        "activated": bool(verdict.get("activated")),
        "categories": verdict.get("categories", []),
        "answer_signals": {},
        "confidence": None, "basis": [], "tier": None,
        "supporting_evidence_present": False,
        "challenging_evidence_trace": "absent",
        "alternatives_offered": False,
        "overclaim": False,
        "appends": [],
    }
    if not res["activated"]:
        return res
    ans = answer or ""
    cal = ConfidenceCalibrator()
    sig = cal.detect_signals(ans)
    calib = cal.calibrate(signals=sig)
    res.update({
        "answer_signals": sig,
        "confidence": calib["confidence"],
        "basis": calib["basis"],
        "tier": calib["tier"],
        "supporting_evidence_present": sig["primary_text_support"] or sig["direct_quote"],
        "challenging_evidence_trace": _challenge_trace(ans, tool_log),
        "alternatives_offered": any(m in ans for m in _ALT_MARKERS),
        "overclaim": sig["overclaim"],
    })
    return res
