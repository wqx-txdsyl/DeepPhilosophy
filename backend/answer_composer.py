# -*- coding: utf-8 -*-
"""Answer Composer（Phase 4）——把严谨内部状态转成好读的回答

解决第四个核心问题: 前三个 Phase 产出的认知层级/多候选/证据契约都正确, 但回答本身
可能仍是"材料说明 → 工具说明 → 检索过程 → 五层报告 → 原典路径 → 再总结"的流程腔,
或堆满"让我检索……/现在我已经有材料了"的过程叙述, 或滥用未经 epistemic state 支持的
强化措辞（"完全正确""毫无疑问""绝不会""本质就是"）。

组件（纯规则 + 数据驱动, 不联网、不调 LLM、不新增工具）:

  AnswerStructureComposer   默认回答结构定义（五段: 直接判断 → 2~4 核心理由 →
                             关键文本证据 → 必要的反方/限定 → 结论）; 生成前置注入:
                             - 禁止把材料/工具/检索/五层/原典路径/再总结当回答骨架
                             - 隐藏 raw reasoning（过程叙述不进正文; 用户只看推理摘要）
                             - 吸收 DeepSeek 优点（快给中心论点/概念压缩/比喻/自然段落/
                               有力结尾）, 但禁止未经证据支持的强化措辞
  CompositionScanner         应答后校验: 直接判断 / 结构信号 / 默认骨架残留 / 强化措辞 /
                             推理噪音 / 冗余; 需要时尾部补正（措辞级, 不编造内容）
  build_reasoning_summary    确定性推理摘要兜底（✦ 推理摘要）: LLM 摘要缺席时, 由
                             epistemic/interpretation/evidence 裁决生成 3~5 步摘要

Phase 4 边界（见任务书）:
  - 不改 Graph / Memory / Persona Snapshot / 矢量库 / 工具注册表 / 流式协议
  - 前置注入 + 应答后补正（token 事件）生效, 失败绝不影响主流程（与 Phase 1/2 同机制）
  - 生成类请求（写作文/生图/辩论等）不注入回答结构（成品形态由各自工具决定）

用法（engine_langgraph.stream_agent 内, 与 interpretation_engine 同机制）:
  verdict = run_answer_composer(req_message, agent, language)
  for inj in verdict["injections"]: messages.append(SystemMessage(content=inj))
  ... 应答完成后: scan_composition(verdict, full_answer, language, interpretation_scan)
  → appends 以 token 事件尾补; reasoning_summary 兜底由 build_reasoning_summary 生成
"""
import json
import re
import threading
import time
from pathlib import Path

from interpretation_engine import ConfidenceCalibrator   # 复用四档确定性语言（单一真源）

BASE = Path(__file__).resolve().parent          # backend/
LOG_FILE = BASE / "data" / "answer_composer.jsonl"   # 运行时记录（backend/data 已 gitignore）

# ═══════════════════════════════════════════════════════
# 1. 默认回答结构（五段; 结论先于过程）
# ═══════════════════════════════════════════════════════
ANSWER_STRUCTURE = [
    ("direct_judgment", "直接判断"),          # 第一句给出判断/立场, 不铺垫
    ("core_reasons", "2~4 个核心理由"),       # 每条一句话, 理由编号
    ("text_evidence", "关键文本证据"),        # 1~3 处原文, 【《书名》·章节】, 跟在所属理由后
    ("counter_qualification", "必要的反方/限定"),  # 另一种读法/局限/较弱一环
    ("conclusion", "结论"),                   # 收束判断, 一句有力的话
]

# 禁止默认的回答骨架（材料/工具/检索/五层/原典路径/再总结 只能作为补充, 不得当主体结构）
BANNED_DEFAULT_BLOCKS = [
    "材料说明", "先说明材料", "先交代材料", "先说材料", "材料如下", "材料整理如下",
    "工具说明", "检索过程", "检索结果如下", "检索情况",
    "五层报告", "五层分析", "五层结构",
    "再总结", "总结一下刚才", "让我先说明",
]

# 推理噪音（raw reasoning 泄漏进正文）——检索/阅读/调用过程叙述
REASONING_NOISE = [
    "让我检索", "让我读取", "让我查", "让我搜", "让我调用", "让我看看", "让我读一读",
    "我来检索", "我来查", "我来搜", "我先检索", "我先查", "先让我", "让我先",
    "现在我已经有材料", "我已经有材料", "我已经有足够的材料", "我已经查到了",
    "我已经找到了", "我调用了", "我查阅了", "我搜索了", "我检索了", "我读取了",
    "工具返回", "工具结果显示", "检索结果显示", "刚才的工具", "我看了下",
]

# 未经 epistemic state 支持的强化措辞（否定式剥离后匹配, "并非完全正确"不误伤）
FORBIDDEN_STRONG = [
    "完全正确", "绝对正确", "绝对肯定", "毫无疑问", "毫无疑义",
    "本质就是", "本质上就是", "本质上是", "本质即", "说到底就是",
    "绝不会", "绝无可能", "一定是", "必然就是", "必然是", "必定是", "绝对是",
    "唯一正确", "唯一解释", "唯一读法", "唯一可能",
    "definitely", "absolutely", "without a doubt", "completely correct", "essentially the same",
]
_NEGATION_BEFORE = re.compile(r"(并非|不是|未必|不一定|并不|也不|不见得|难说|称不上|算不上)$")

# 结论先行判据: 首句以这些开头 → 直接判断缺失（过程叙述/空转开场）
_PROCESS_LEADIN = re.compile(
    r"^(让我|我先|好的,?让我|嗯,?让我|等我|我需要先|关于这个问题,?让我|先说明|先交代|"
    r"先看材料|先检索|我检索了|我查了|我调用|我查阅|我搜索|我读取|经过检索|在检索|"
    r"材料说明|工具说明|检索过程|再总结|五层|原典路径)")
_EMPTY_LEADIN = re.compile(r"^(这是一个好问题|这确实是个好问题|好问题|谢谢你的问题|你的问题很有深度|关于(这个|你问的))$")

# 生成类请求（成品形态由专门工具决定, 不注入通用回答结构）
GENERATIVE_SKIP = ["写一篇", "写作文", "帮我写", "作文：", "写首诗", "写一首诗", "作一首诗",
                   "生成图片", "生成一张", "生成图像", "画一幅", "画一张", "画个", "画一画",
                   "剧本", "写个剧本", "翻译", "辩论", "辩一辩", "对决", "让.{0,8}对质"]

# 冗余判据（评估套件用）
_CONCLUSION_STACK = ["综上", "总之", "总而言之", "总结", "结论是", "说到底"]
# ══ O2 §7: _STRONG_HEDGE / _DIRECTNESS_NUDGE（确定性措辞补正文本）已删除——
# runtime 不得向用户正文追加"（补充：……）"式句子。强化措辞 / 结构噪音的检测
# 信号仍随 scan_composition 结果进入 done payload 供审计（appends 恒空）。


# ═══════════════════════════════════════════════════════
# 6. Phase S (S5): Answer Budget —— 问题复杂度 → 软篇幅预算 + 段落职责冗余
# ═══════════════════════════════════════════════════════
# 复杂度档位与建议篇幅（中文字; 软预算——只引导, 禁止直接字符截断）
BUDGETS = {
    "factual": (150, 350),
    "simple_explanation": (250, 500),
    "interpretation": (350, 700),
    "comparison": (500, 900),
    "explicit_deep_analysis": (800, None),   # None = 用户明确要求深度, 上限放宽
}
BUDGET_LABEL_ZH = {
    "factual": "事实型", "simple_explanation": "简明解释", "interpretation": "解释型",
    "comparison": "对比型", "explicit_deep_analysis": "深度分析",
}
BUDGET_LABEL_EN = {
    "factual": "factual", "simple_explanation": "brief explanation", "interpretation": "interpretive",
    "comparison": "comparative", "explicit_deep_analysis": "in-depth analysis",
}
# 显式深度要求（用户明确要长文/深入 → 预算上限放宽）
_DEEP_ANALYSIS_CUES = [
    "深入分析", "深度分析", "深入解析", "详细分析", "详细说说", "详细回答", "展开论述",
    "展开说", "深入探讨", "深入讲解", "彻底分析", "长篇分析", "系统论述", "透彻分析",
    "deep analysis", "in detail", "thorough", "elaborate",
]
# 事实型问题线索（可核验的确定性事实）
_FACTUAL_CUES = [
    "哪一年", "几年", "几岁", "何时", "生于", "卒于", "出生", "去世", "年代", "年份",
    "多少天", "多少年", "哪个国家", "哪里人", "出版于", "写于", "第几章", "谁写",
    "谁提出", "谁是", "是什么时候",
]
# 对比型问题线索
_COMPARISON_CUES_EXT = [
    "对比", "比较", "异同", "区别", "差别", "谁更", "与…不同", "与...不同",
    "vs", "versus", "不同之处", "相同之处",
]
# 解释型问题线索（与 interpretation_engine 同源语义）
_INTERP_CUES_EXT = [
    "意味着", "象征着", "象征", "隐喻", "寓意", "解读", "怎么理解", "如何理解",
    "是不是", "是否", "一回事", "本质", "意义",
]


def classify_complexity(message):
    """问题复杂度分类: explicit_deep_analysis > comparison > interpretation > factual > simple_explanation"""
    msg = message or ""
    if any(c in msg for c in _DEEP_ANALYSIS_CUES):
        return "explicit_deep_analysis"
    if any(c in msg for c in _COMPARISON_CUES_EXT):
        return "comparison"
    # 跨作者/跨概念比较 + 解释型问题（复用 interpretation_engine 单一真源:
    # "超人和逍遥是不是一回事" → comparison; "从《老人与海》看加缪的荒谬主义" → interpretation）
    try:
        from interpretation_engine import InterpretationChallenger
        cats = InterpretationChallenger().check(msg)["categories"]
        if "cross_author_comparison" in cats:
            return "comparison"
        if cats:
            return "interpretation"
    except Exception:
        pass
    if any(c in msg for c in _INTERP_CUES_EXT):
        return "interpretation"
    if any(c in msg for c in _FACTUAL_CUES) or re.search(r"\d{3,4}年", msg):
        return "factual"
    return "simple_explanation"


def build_budget_injection(verdict, language="zh"):
    """篇幅预算 + 段落职责注入（软预算: 引导压缩与去重, 不硬截断）"""
    complexity = classify_complexity(verdict.get("question") or "")
    lo, hi = BUDGETS[complexity]
    if language == "en":
        hi_txt = f"{hi}" if hi else "unbounded (the user explicitly asked for depth)"
        return (
            f"[System answer budget] This is a {BUDGET_LABEL_EN[complexity]} question. "
            f"Target length: {lo}–{hi_txt} Chinese characters (soft budget — never truncate). "
            "Keep the argument compact and non-redundant: each paragraph must carry a NEW reasoning "
            "duty (new evidence, new argument, new qualification, or a further step of the chain). "
            "If a paragraph adds no new information beyond an earlier one (no new evidence, no new "
            "point, no further step), merge it into the neighboring paragraph or drop the weaker "
            "one. Never restate the same point in different words just to fill space.")
    hi_txt = f"{hi}" if hi else "上限放宽（用户明确要求深度）"
    return (
        f"【篇幅预算（系统）】本题属于{BUDGET_LABEL_ZH[complexity]}类问题，建议篇幅 {lo}–{hi_txt} 中文字"
        f"（软预算，不是硬截断）。论证要紧凑且不冗余：每段必须承担一个新的论证职责"
        f"（新证据、新论点、新限定，或论证链上更进一步）；"
        f"若某段相对前面段落没有明显新增信息（新证据、新论点、新推进），把它合并进相邻段或删去"
        f"较弱的一段；同一论点不要换种说法重复陈述凑字数。若你预计成稿会明显超过上限，在动笔前先压缩"
        f"合并——宁可少一个理由，也不要堆叠同职责段落。")


# 段落职责识别（judgment / reason / evidence / counterpoint / qualification / conclusion / explanation）
def _paragraph_role(para, is_first=False):
    if _CITE_MARKER_RE.search(para) and _REASON_ENUM_RE.search(para):
        return "reason_evidence"
    if _CITE_MARKER_RE.search(para):
        return "evidence"
    if re.search(r"(综上|总之|总而言之|结论是|说到底|因此可见|最终结论)", para):
        return "conclusion"
    if re.search(r"(需要指出|需要限定|值得怀疑|并非唯一|局限|限定|需注意|有所保留)", para):
        return "qualification"
    if re.search(r"(但|不过|然而|可是|质疑|反方|另一种|反驳)", para):
        return "counterpoint"
    if re.search(r"(首先|其次|再次|最后|第一|第二|第三|理由[一二三四1234]|原因)", para):
        return "reason"
    if is_first:
        return "judgment"
    return "explanation"


def _paragraph_info_gain(para, previous_paras):
    """信息增益: 本段相对此前段落新增的 2-gram 数量（低增益 = 与前面职责重复且无新信息）"""
    def grams(t):
        t = re.sub(r"[\s，,。；;：:、？！!?（）()【】《》\"“”'‘’·—-]", "", t or "")
        return {t[i:i + 2] for i in range(len(t) - 1)} if len(t) >= 2 else set()
    cur = grams(para)
    prev = set().union(*(grams(p) for p in previous_paras)) if previous_paras else set()
    return len(cur - prev)


_CITE_MARKER_RE = re.compile(r"【《[^》]+》[^】]*】")
_REASON_ENUM_RE = re.compile(r"首先|其次|再次|第一|第二|第三|理由[一二三四1234]")


def scan_budget(verdict, answer):
    """应答后预算校验: 篇幅合规 + 段落职责去重 + 信息增益

    返回: {complexity, budget: [lo, hi], length, within_budget, over_budget, under_budget,
           paragraphs: [{role, gain}], argument_role_duplication: [...], findings: [...]}
    只把 over_budget / argument_role_duplication / low_information_gain 记为 findings;
    under_budget 仅作指标（软预算, 不惩罚短而精的回答）。
    """
    res = {
        "activated": bool(verdict.get("activated")),
        "complexity": None, "budget": None, "length": 0,
        "within_budget": True, "over_budget": False, "under_budget": False,
        "paragraphs": [], "argument_role_duplication": [], "findings": [],
    }
    if not res["activated"]:
        return res
    complexity = classify_complexity(verdict.get("question") or "")
    lo, hi = BUDGETS[complexity]
    length = len(answer or "")
    res.update({"complexity": complexity, "budget": [lo, hi], "length": length})
    if hi is not None:
        if length > hi:
            res["over_budget"] = True
            res["within_budget"] = False
            res["findings"].append(f"over_budget:{length}>{hi}")
        elif length < lo:
            res["under_budget"] = True
    paras = [p.strip() for p in re.split(r"\n\s*\n", answer or "") if p.strip()]
    if not paras:
        paras = [answer or ""] if (answer or "").strip() else []
    roles, dup = [], []
    for i, p in enumerate(paras):
        role = _paragraph_role(p, is_first=(i == 0))
        gain = _paragraph_info_gain(p, paras[:i])
        roles.append({"role": role, "gain": gain, "len": len(p)})
    # 职责重复 + 低信息增益 → 弱段（应合并/删除; 注入已要求 LLM 如此, 此处审计）
    seen = {}
    for i, r in enumerate(roles):
        if r["role"] in seen:
            prev_i = seen[r["role"]]
            if r["gain"] < 8:   # 新增 2-gram < 8 → 无明显新增信息
                dup.append({"role": r["role"], "para": i + 1, "gain": r["gain"],
                            "prev_para": prev_i + 1})
        else:
            seen[r["role"]] = i
    for d in dup:
        res["argument_role_duplication"].append(d)
        res["findings"].append(f"argument_role_duplication:{d['role']}:para{d['para']}")
    res["paragraphs"] = roles
    _log_record({"phase": "budget", "complexity": complexity, "length": length,
                 "budget": [lo, hi], "over": res["over_budget"], "under": res["under_budget"],
                 "dup_roles": [d["role"] for d in dup]})
    return res


# ═══════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════
# 2. 前置注入（build_composer_injections）
# ═══════════════════════════════════════════════════════
# Patch 1 (B7): 回答结构由 problem type + 论证结构决定（reasoning_plan 自适应形态注入）——
# 不再注入固定"直接判断→理由一二三→反方→结论"五段骨架。
# 此处保留的通用约束均为质量要求（隐藏推理过程/禁止过程叙述/强化措辞与证据匹配/
# 禁止材料-工具-检索-五层-原典路径-再总结骨架/原典路径可选附录）, 不规定可见标题与顺序。
def build_composer_injections(verdict, language="zh"):
    """自适应回答形态 + 通用质量约束注入（生成类请求返回 []）"""
    if not verdict.get("activated"):
        return []
    en = language == "en"
    # Patch 1 (B7): 按问题类型取形态注入（形态由 problem type + 论证结构决定）
    form = None
    try:
        from reasoning_plan import get_form_directive
        form = get_form_directive(verdict.get("problem_type"), language)
    except Exception:
        form = None
    if en:
        parts = [
            ("[Answer composition] Do not narrate retrieval/reading in the answer body "
             "('let me search…', 'now I have the material…' are forbidden); tool cards are shown "
             "by the UI and the user only sees a reasoning summary, so do not restate your "
             "thinking in the answer. Absorb these strengths: reach the central thesis faster, "
             "compress concepts forcefully, use apt metaphors, natural paragraph rhythm, a strong "
             "ending. But determinacy of wording must match the evidence: emphatic claims "
             "unsupported by evidence ('completely correct', 'without a doubt', 'essentially is') "
             "are forbidden."),
            ("[Answer composition] Never build the answer around this skeleton: material overview "
             "→ tool explanation → retrieval process → five-layer report → original-text path → "
             "re-summary. The original-text path may appear only as a brief optional appendix when "
             "the question has a clear textual lineage and the passages were actually retrieved."),
        ]
        if form:
            parts.insert(0, form)
        return parts
    parts = [
        ("【回答结构（系统）】检索/阅读的过程一律不写进回答正文（“让我检索……”“现在我已经有材料了”"
         "这类过程叙述禁止出现）；工具调用卡片由界面展示，用户只看到推理摘要，思考过程不需要你在正文里复述。\n"
         "风格上吸收：更快给出中心论点、有力的概念压缩、恰当的比喻、自然的段落节奏、有力量的结尾；"
         "但确定性措辞必须与证据强度匹配，禁止未经证据支持的强化措辞（如“完全正确”“毫无疑问”“绝不会”“本质就是”）。"),
        ("【回答结构（系统）】禁止把以下内容当作回答骨架：材料说明 → 工具说明 → 检索过程 → 五层报告 → "
         "原典路径 → 再总结。原典路径仅在问题确有文本脉络且检索到位时，作为简短附录附在结论之后，不作为默认结构。"),
    ]
    if form:
        parts.insert(0, form)
    return parts


# ═══════════════════════════════════════════════════════
# 3. CompositionScanner —— 应答后校验 + 措辞级补正
# ═══════════════════════════════════════════════════════
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
    """回答中的强化措辞命中（公共 API, 供 Evaluation Suite 复用——单一真源）"""
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
    """应答后校验: 结构信号 / 默认骨架残留 / 强化措辞 / 推理噪音 / 冗余

    返回: {activated, direct_judgment, structure_signals, banned_blocks, strong_wording,
           reasoning_noise, redundancy, appends}
    原则: ①补正只做措辞级, 不编造内容; ②解释型问题的强化措辞由 interpretation_engine 负责
          补正, 本扫描不重复补（传 interpretation_scan.appends 非空则跳过）;
          ③生成类请求不扫描; ④Phase S (S5): 已超篇幅预算的回答不再追加非必要结构提示
          （不硬截断, 只是不加长）。
    """
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
    first = _first_sentence(ans)
    res["direct_judgment"] = _is_direct(first)
    res["structure_signals"] = _structure_signals(ans)
    res["banned_blocks"] = _block_hits(ans)
    res["strong_wording"] = _strong_hits(ans)
    res["reasoning_noise"] = _noise_hits(ans)
    res["redundancy"] = _redundancy_findings(ans)
    # O2 §7: 措辞/结构补正文本生成已删除——appends 恒空（engine 不再尾补任何句子）,
    # strong_wording / direct_judgment / noise 检测信号保留在结果中供 done 审计。
    _log_record({"phase": "post", "language": language,
                 "activated": res["activated"],
                 "direct_judgment": res["direct_judgment"],
                 "structure": res["structure_signals"],
                 "banned_blocks": len(res["banned_blocks"]),
                 "strong_wording": len(res["strong_wording"]),
                 "reasoning_noise": len(res["reasoning_noise"]),
                 "redundancy": len(res["redundancy"]),
                 "appends": len(res["appends"]),
                 "answer_len": len(ans)})
    return res


# ═══════════════════════════════════════════════════════
# 4. 确定性推理摘要（✦ 推理摘要兜底; LLM 摘要缺席时使用）
# ═══════════════════════════════════════════════════════
def build_reasoning_summary(epistemic_verdict=None, interpretation_verdict=None,
                            interpretation_scan=None, evidence_payload=None,
                            tool_log=None, language="zh"):
    """由各 Phase 裁决生成 3~5 步摘要（纯规则, 不调 LLM）; 无信息返回 None

    示例（zh）: 1. 核验文本事实（校正 1 处前提）
                2. 检索原典与引文
                3. 提出候选解读并检验反证
                4. 核验引用与证据（3/20 条已用）
                5. 结论置信度：可成立但并非唯一
    """
    en = language == "en"
    steps = []
    pv = epistemic_verdict or {}
    iv = interpretation_verdict or {}
    isc = interpretation_scan or {}
    ev = evidence_payload or {}
    checks = pv.get("premise_checks") or []
    contrad = [c for c in checks if c.get("status") == "contradicted"]
    if contrad:
        steps.append(f"核验文本事实（校正 {len(contrad)} 处前提）" if not en
                     else f"Verified textual facts (corrected {len(contrad)} premise)")
    names = {t.get("name") for t in (tool_log or []) if isinstance(t, dict)}
    if names & {"search_books", "get_chapter", "philosopher_corpus", "philosopher_quote"}:
        steps.append("检索原典与引文" if not en else "Searched primary texts")
    if iv.get("activated"):
        cats = iv.get("categories", [])
        if "cross_author_comparison" in cats:
            steps.append("比较两种解释（跨作者）" if not en else "Compared readings across authors")
        else:
            steps.append("提出候选解读并检验反证" if not en else "Offered candidate readings and tested counter-evidence")
    cv = pv.get("counterfactual") or {}
    if cv.get("requires_guard"):
        steps.append("标注反事实边界" if not en else "Marked counterfactual boundary")
    if ev.get("retrieved_count"):
        steps.append(f"核验引用与证据（{ev.get('used_count', 0)}/{ev.get('retrieved_count', 0)} 条已用）"
                     if not en else
                     f"Checked citations and evidence ({ev.get('used_count', 0)}/{ev.get('retrieved_count', 0)} used)")
    tier = isc.get("tier")
    if tier:
        steps.append(f"结论置信度：{ConfidenceCalibrator.tier_language(tier, language)}"
                     if not en else
                     f"Conclusion confidence: {ConfidenceCalibrator.tier_language(tier, 'en')}")
    if not steps:
        return None
    return "\n".join(f"{i + 1}. {s}" for i, s in enumerate(steps))


# ═══════════════════════════════════════════════════════
# 5. 编排: run_answer_composer / 日志
# ═══════════════════════════════════════════════════════
def run_answer_composer(message, agent="general", language="zh"):
    """前置: 自适应回答形态注入（Patch 1/B7: 结构由 problem type 决定; 生成类请求跳过;
    纯计算, 不调 LLM）

    返回: {activated, structure, problem_type, injections}
    """
    msg = message or ""
    activated = bool(msg.strip()) and not any(re.search(k, msg) for k in GENERATIVE_SKIP)
    # Patch 1 (B7): 问题类型（reasoning_plan 单一真源; 形态注入按类型自适应）
    problem_type = None
    try:
        from reasoning_plan import classify_problem
        problem_type = classify_problem(msg, agent)
    except Exception:
        problem_type = None
    verdict = {
        "activated": activated,
        "structure": ANSWER_STRUCTURE,
        "problem_type": problem_type,
        "question": msg,     # Phase S (S5): 预算注入/扫描按问题复杂度分类
        "injections": [],
    }
    if activated:
        verdict["injections"] = build_composer_injections(verdict, language)
        # Phase S (S5): 篇幅预算 + 段落职责注入（软预算, 追加一条系统消息）
        try:
            verdict["injections"].append(build_budget_injection(verdict, language))
        except Exception:
            pass
    _log_record({"phase": "pre", "agent": agent, "language": language,
                 "message": msg[:300],
                 "activated": activated,
                 "problem_type": problem_type,
                 "injections": len(verdict["injections"])})
    return verdict


# ── 运行时记录（backend/data/ 已 gitignore, 纯观察/审计用; 失败静默）──
_log_lock = threading.Lock()


def _log_record(rec):
    try:
        rec = dict(rec)
        rec["ts"] = time.strftime("%Y-%m-%d %H:%M:%S")
        with _log_lock:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass
