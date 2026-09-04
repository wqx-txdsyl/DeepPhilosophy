# -*- coding: utf-8 -*-
"""Reasoning Plan（Backend Patch 1, B1/B3/B5/B6/B7）——问题结构规划（纯规则, 不调 LLM）

一个请求只规划一次; 产出的结构化计划驱动运行时各环节:

  B7 problem_type    问题类型分类（FACT_VERIFICATION / CONCEPT_EXPLANATION / ARGUMENT_ANALYSIS /
                     COMPARISON / HISTORICAL_GENEALOGY / TEXTUAL_INTERPRETATION / DEEP_SYNTHESIS /
                     SOCRATIC / PERSONA_RESPONSE）→ 自适应回答形态注入。
                     回答结构由 problem type + 论证结构决定; 质量要求（证据/限定/反方/结论完整）
                     保留为内部检查, 不再映射为固定可见标题。
  B1 complexity      复杂度档位（NARROW_FACTUAL / NORMAL_EXPLANATION / COMPARISON / DEEP_SYNTHESIS）
                     → 工具期望预算（agent_runtime.sufficiency_verdict 消费）。
  B6 relations       推理关系识别 + 依赖链要求（内部规划语义——关系名绝不写进用户可见回答）。
  B5 temporal        时期检测（年份 / 早期中期晚期 / 当时的你 / 为什么改变 / 时期比较）
                     → 哲学家智能体时期路由（philosopher_period 必须进入证据计划）。
  B3 verification    术语核验问题检测 + verify_term_presence（VERIFIED_EXACT / VERIFIED_SEMANTIC /
                     NOT_FOUND / AMBIGUOUS）+ 措辞约束注入 + 首句/含术语句无条件断言改写。

组件边界: 纯规则 + 数据驱动, 不联网、不调 LLM、不新增工具、不改 Persona/Memory/图/向量库。
"""
import re

# ═══════════════════════════════════════════════════════
# 0. 通用小工具
# ═══════════════════════════════════════════════════════
_QUOTED_RE = re.compile(r"[“\"「『‘]([^”\"」』’]{2,24})[”\"」』’]")


def _q(text):
    """引号内概念提取（首个）"""
    m = _QUOTED_RE.search(text or "")
    return m.group(1).strip() if m else ""


# ═══════════════════════════════════════════════════════
# B7. 问题类型分类（规则; 优先级从上到下, 首个命中即返回）
# ═══════════════════════════════════════════════════════
_SOCRATIC_CUES = ["苏格拉底", "不要直接告诉我答案", "不要直接告诉我", "带我自己", "带我想明白",
                  "引导我", "追问", "别告诉我答案"]
_ARGUMENT_CUES = ["分析这个论证", "分析一下这个论证", "分析该论证", "这个论证", "论证是否成立",
                  "推理是否成立", "推理成立", "论证结构", "反驳这个", "反驳该论证", "分析这段推理",
                  "论证分析", "是不是自相矛盾", "逻辑上", "前提", "论证有"]
_COMPARISON_CUES = ["比较", "对比", "区别", "异同", "分别评价", "分别怎么看", "分别如何",
                    "谁更", "差别", "不同之处", " vs ", "versus", "各自", "哪个更"]
_GENEALOGY_CUES = ["溯源", "来源", "起源", "历史演变", "历史发展", "演变", "系谱", "谱系",
                   "之前就存在", "之前就有", "发生了什么变化", "如何演变成", "发展脉络",
                   "时间线", "思想史", "从何而来", "怎么来的"]
_DEEP_CUES = ["深入分析", "深度分析", "深入解析", "深层", "根本问题", "既是.{0,10}也是",
              "为什么.{0,15}同时", "不只是一个", "系统论述", "彻底分析", "整体结构"]
_DEEP_CUES_EXPLICIT = ["深入分析", "深度分析", "深入解析", "深层", "根本问题", "系统论述",
                       "彻底分析", "整体结构", "既是.{0,10}也是", "为什么.{0,15}同时", "不只是一个"]
_INTERP_CUES = ["解读", "意味着", "象征着", "象征", "隐喻", "寓意", "怎么理解", "如何理解",
                "是什么意思", "读法", "理解.{0,4}(角度|方式|层面)", "解释.{0,4}(说法|含义|意思)",
                "会不会太", "是不是太", "怎么说", "如何评价", "怎么看"]

# 复杂问题关键词（DEEP_SYNTHESIS 判定; 长度阈值仅作次要信号）
_DEEP_KEYWORDS = ["体系", "根本", "深层", "整体", "为什么", "如何", "怎样", "到底", "本质"]


def classify_problem(message, agent="general"):
    """B7: 问题类型（agent 非 general → PERSONA_RESPONSE; 其余规则分类）"""
    msg = (message or "").strip()
    if agent != "general":
        return "PERSONA_RESPONSE"
    if any(c in msg for c in _SOCRATIC_CUES):
        return "SOCRATIC"
    if any(c in msg for c in _ARGUMENT_CUES):
        return "ARGUMENT_ANALYSIS"
    if detect_term_presence(msg):
        return "FACT_VERIFICATION"
    # 窄 yes/no 问题（短问句 + 是非问）→ 事实核验形态（先给核验结论再给证据与边界）
    if len(msg) <= 45 and (_YESNO_RE.search(msg) or "只回答一个问题" in msg):
        return "FACT_VERIFICATION"
    if any(c in msg for c in _COMPARISON_CUES):
        return "COMPARISON"
    if any(c in msg for c in _GENEALOGY_CUES):
        return "HISTORICAL_GENEALOGY"
    if any(re.search(c, msg) for c in _DEEP_CUES_EXPLICIT):
        return "DEEP_SYNTHESIS"
    if len(msg) >= 50 and sum(1 for k in _DEEP_KEYWORDS if k in msg) >= 2:
        return "DEEP_SYNTHESIS"
    # 体系/整体 类系统问题: 需与"为什么/如何/到底"等追问词共同出现且有一定长度, 才算深度综合
    if len(msg) >= 30 and any(k in msg for k in ("体系", "整体")) \
            and sum(1 for k in ("为什么", "如何", "怎样", "到底", "本质", "根本") if k in msg) >= 1:
        return "DEEP_SYNTHESIS"
    if any(c in msg for c in _INTERP_CUES):
        return "TEXTUAL_INTERPRETATION"
    return "CONCEPT_EXPLANATION"


# ═══════════════════════════════════════════════════════
# B1. 复杂度档位（工具期望预算; agent_runtime 消费）
# ═══════════════════════════════════════════════════════
_YESNO_RE = re.compile(r"是不是|是否是|是否|有没有|能不能|可不可以|真的吗|吗[？?]?$|只回答一个问题|简单回答")
_NARROW_RE = re.compile(r"只回答一个问题|简单(回答|说说)|一句话|是不是|有没有|对吗|对吗[？?]|能否|是否")


def classify_complexity(problem_type, message, agent="general"):
    """B1: 复杂度档位（窄事实 < 一般解释 < 对比 < 深度综合）"""
    msg = (message or "").strip()
    if problem_type == "FACT_VERIFICATION":
        return "NARROW_FACTUAL"
    if problem_type == "COMPARISON":
        return "COMPARISON"
    if problem_type == "DEEP_SYNTHESIS":
        return "DEEP_SYNTHESIS"
    if problem_type == "SOCRATIC":
        return "NORMAL_EXPLANATION"
    if _NARROW_RE.search(msg) and len(msg) <= 60:
        return "NARROW_FACTUAL"
    if problem_type == "HISTORICAL_GENEALOGY":
        return "COMPARISON" if len(msg) >= 40 else "NORMAL_EXPLANATION"
    if len(msg) >= 60:
        return "DEEP_SYNTHESIS"
    return "NORMAL_EXPLANATION"


COMPLEXITY_LABEL_ZH = {
    "NARROW_FACTUAL": "窄事实型", "NORMAL_EXPLANATION": "一般解释型",
    "COMPARISON": "对比型", "DEEP_SYNTHESIS": "深度综合型",
}
COMPLEXITY_LABEL_EN = {
    "NARROW_FACTUAL": "narrow-factual", "NORMAL_EXPLANATION": "normal-explanation",
    "COMPARISON": "comparison", "DEEP_SYNTHESIS": "deep-synthesis",
}


# ═══════════════════════════════════════════════════════
# B7. 自适应回答形态注入（替代固定"直接判断→理由一二三→反方→结论"骨架）
# ═══════════════════════════════════════════════════════
# 形态由 problem type + 论证结构决定; 不规定固定标题/固定顺序;
# 质量要求（证据/限定/反方/结论完整）保留为内部检查, 不进入可见骨架。
FORM_DIRECTIVES_ZH = {
    "FACT_VERIFICATION": (
        "【回答形态（系统）】这是一个需要核验事实/术语的问题。先直接给出核验结论（是/否/不能确认——"
        "必须区分“概念可确认”与“固定措辞逐字出现”两个层面），然后完整保留问题的核验义务："
        "1) 结论；2) 已核验到的原文/最接近原句（带【《书》·章节】，未能逐字命中时给出最接近的命题及其位置）；"
        "3) 版本/翻译区分（若相关：原著语言措辞 vs 中文译本措辞 vs 通俗概括，明确用户所给表述属于哪一层）；"
        "4) 确定性边界（哪些层面能确认、哪些不能）。简洁但不得让核验义务消失；"
        "不要用“理由一/理由二/理由三”平行罗列。"),
    "CONCEPT_EXPLANATION": (
        "【回答形态（系统）】按概念自身的层次展开：先直接界定概念，再用最有力的原文支撑，"
        "接着点出常见误读或边界，最后落到它在你这个问题中的意义。段落之间要有推进（为什么这一层"
        "引出下一层），不要写成并列的词条说明。"),
    "ARGUMENT_ANALYSIS": (
        "【回答形态（系统）】按论证自身的结构推进：先把论证重构出来（结论、显式前提、隐含前提），"
        "再逐一检验前提是否成立、有无偷换或歧义，然后给出修正后的论证或替代读法，最后给出你的判断。"
        "不要按“理由一/二/三”平行罗列，也不要只给结论不给检验过程。"),
    "COMPARISON": (
        "【回答形态（系统）】按“共同问题 → 分歧点 → 各自后果 → 对双方最强的质疑”推进：先指出双方"
        "共同面对的问题，再给出分歧发生在哪一环、各自付出了什么代价，最后分别给出对双方最有力的质疑。"
        "不要写成两段互不相干的分别介绍。"),
    "HISTORICAL_GENEALOGY": (
        "【回答形态（系统）】按时间与概念演变的链条推进：先看概念/问题在其起点处的形态，"
        "再说明转变发生的原因与机制（为什么从上一环节变到这一环节），最后落到当前形态。"
        "每个环节都要解释因果关系，不要只罗列时间点。"),
    "TEXTUAL_INTERPRETATION": (
        "【回答形态（系统）】先给出你对文本最直接的读法（一句话立场），再给出支持与反对的证据；"
        "若存在多种读法，说明各自依据与代价；最后说明你采信哪种及理由。论证要推进，不要并列罗列。"),
    "DEEP_SYNTHESIS": (
        "【回答形态（系统）】按问题自身的发展逻辑推进：问题如何产生 → 概念如何转换 → 张力在哪里 → "
        "尝试的解决 → 遗留问题 → 后来的批评。每一步都要解释前一环节为什么引出后一环节；"
        "若问题涉及多个领域（如认识论/美学/目的论），必须解释它们如何从同一个问题中派生出来——"
        "展示同一条线索如何贯穿它们，而不是罗列三个彼此并列的板块。"),
    "SOCRATIC": (
        "【回答形态（系统）】保持苏格拉底式追问：用问题引导对方自己推进，不要给出完整答案。"
        "追问要层层递进：先澄清概念，再暴露张力，再引导对方自己发现关键区分。"),
    "PERSONA_RESPONSE": (
        "【回答形态（系统）】保持你的人格表达方式（不要使用“直接判断/理由一二三/反方/结论”这类"
        "报告式结构），但论证仍要按问题自身的逻辑推进——每一段在思想上比前一段进一步，"
        "而不是重复同一立场。"),
}
FORM_DIRECTIVES_EN = {
    "FACT_VERIFICATION": (
        "[Answer form] This is a factual/terminology verification question. Lead with the verdict "
        "(yes / no / cannot confirm — distinguish 'the concept is confirmed' from 'the exact wording "
        "appears verbatim'), then give the textual evidence and the limits of certainty (edition, "
        "translation, segmentation differences; state plainly what could not be verified), and close "
        "in one sentence. Do not enumerate 'reason 1/2/3' in parallel."),
    "CONCEPT_EXPLANATION": (
        "[Answer form] Develop the concept by its own layers: define it directly, support it with the "
        "strongest passage, note common misreadings or boundaries, then land on its significance for "
        "the question. Paragraphs should advance (why one layer leads to the next), not read like "
        "parallel dictionary entries."),
    "ARGUMENT_ANALYSIS": (
        "[Answer form] Follow the argument's own structure: reconstruct it (conclusion, explicit "
        "premises, hidden premises), test each premise for validity and equivocation, then give the "
        "revised argument or alternative reading, then your judgment. Do not enumerate parallel "
        "reasons or jump straight to a verdict."),
    "COMPARISON": (
        "[Answer form] Proceed as shared problem → divergence point → consequences → strongest "
        "objection to each side. First state the common problem both face, then where they diverge "
        "and what each pays, then the strongest challenge to each. Do not write two disconnected "
        "introductions."),
    "HISTORICAL_GENEALOGY": (
        "[Answer form] Follow the chain of conceptual change over time: the concept/problem in its "
        "original form, then the causes and mechanism of the shift (why each stage leads to the next), "
        "then its current form. Explain causation at each step; do not just list dates."),
    "TEXTUAL_INTERPRETATION": (
        "[Answer form] Give your most direct reading first (one-sentence stance), then the evidence "
        "for and against; if several readings exist, state the basis and cost of each; then say which "
        "you adopt and why. The argument should advance, not sit in parallel."),
    "DEEP_SYNTHESIS": (
        "[Answer form] Follow the question's own developmental logic: how the problem arises → how "
        "concepts shift → where the tension lies → the attempted solution → the residual problem → "
        "later criticism. Explain at each step why the previous step leads to the next; if the "
        "question spans several domains (e.g. epistemology/aesthetics/teleology), explain how they "
        "derive from one and the same problem — one thread running through them, not three parallel "
        "blocks."),
    "SOCRATIC": (
        "[Answer form] Stay Socratic: lead with questions, do not hand over the full answer. Progress "
        "in layers: clarify concepts, expose the tension, then guide the other to discover the key "
        "distinction themselves."),
    "PERSONA_RESPONSE": (
        "[Answer form] Keep your persona's way of speaking (no report-style headers such as 'direct "
        "judgment / reason 1-2-3 / counterpoint / conclusion'), but the argument should still advance "
        "by the question's own logic — each paragraph goes one step further in thought rather than "
        "restating the same stance."),
}


def get_form_directive(problem_type, language="zh"):
    """B7: 按问题类型取回答形态注入（无对应类型 → None）"""
    if not problem_type:
        return None
    return (FORM_DIRECTIVES_EN if language == "en" else FORM_DIRECTIVES_ZH).get(problem_type)


# ═══════════════════════════════════════════════════════
# Patch 1.1 (P2): 核验意图分类（verification intent classification）
# ═══════════════════════════════════════════════════════
# 语义线索（正则模式族）而非固定中文关键词 exact match——覆盖:
#   "是不是原话 / 是否写过 / 是否出自 / 具体出处 / 逐字 / 原文 /
#    这个说法真的是 X 说的吗 / 这句话在哪本书 / 哪一章哪一节 / 只用原典 / 不要二手来源"
# kind:     EXACT_WORDING（逐字/原话层面）| SOURCE_ATTRIBUTION（出处/归属层面）|
#           FACT_VERIFICATION（一般事实核验）
# constraint: PRIMARY_ONLY | AUTHOR_ONLY | BOOK_ONLY | EDITION_SPECIFIC | NONE
_VI_WORDING_RE = re.compile(
    r"逐字|一字不[差落地]|原话|原(文|句)(里|中|是|怎么|怎么写|怎么说的)?[？?]?"
    r"|(是不是|是否是?|算不算).{0,4}(他|她|它)?的?原(文|话|句)|字面(上|意思|表述)")
# T1.1-A: 出处/归属检测扩展——补齐裸「X出处」「X的出处」「在哪一篇」「是谁说的」
# 「是不是原话」「原文是什么」等口语词型（真实回归: "言必有中出处" 旧正则全不命中,
# vi=None → 核验路径整体缺席 → 模型凭记忆给 blockquote）。
_VI_ATTRIBUTION_RE = re.compile(
    r"(是否|是不是|真的|确实|究竟).{0,24}(说|写|提出|引用|讲)(过|了)"
    r"|真的是.{0,12}说的吗|(是不是|是否|算不算)(真的?)?出自"
    r"|(出自|来源于是|来源于|来自)(哪|什么|何)"
    r"|具体出处|出处(是|在哪|是什么)|在哪(一?本?书|部著作)|这句话?在哪"
    r"|(哪|第几)(一)?(章|节|卷|页|篇)|原文(是否|有没有|里)"
    r"|出处\s*[？?？]?\s*$|的出处|在哪(一)?[篇章节卷]|是谁(说|写|讲)的|谁(说|写|讲)(的|过)"
    r"|是不是原话|是原话[吗么]|原话(是什么|怎么说|怎么写)"
    r"|原文(是什么|怎么说|怎么写|出自哪里?)"
    r"|是不是《[^》]{1,24}》(里|中|内|上)(的|面|边)?")
_VI_PRIMARY_RE = re.compile(
    r"(只用|仅用|只以|仅以).{0,20}(原典|原文|原著|自己的文本|本人的著作|自己的话|本人文本)"
    r"|(不要|不用|不得|不能|别)(拿|用|看|引)?二手"
    r"|以原典为准|只用原典|原典回答|二手(书|来源|材料|研究).{0,8}(替代|代替|不要|排除|不)")
_VI_AUTHOR_ONLY_RE = re.compile(
    r"(本人|自己)(说|写|提出|的文本|的著作|的原话|的话)")
_VI_EDITION_RE = re.compile(
    r"(哪个|什么|哪一个)(译本|版本)|德文原(文|句)|英文译本|中译本|对照原文|逐字核对.{0,8}(德|英|希腊|拉丁)")
_VI_BOOK_RE = re.compile(r"具体(章节|出处|位置)|第几章|(哪|第几)(一)?(章|节|卷)|在哪(一?本?书|部著作)")

# T1.1-A: 裸出处句式的尾部词型（term 兜底提取用; 与 _VI_ATTRIBUTION_RE 同族）
_ATTR_CUE_TAIL_RE = re.compile(
    r"(?:的)?(?:具体)?(?:的)?出处(?:在哪(?:里|儿)?|是什么|是哪里)?\s*[？?？]?\s*$"
    r"|出自(?:哪里|哪儿|何处|哪本书|哪部著作|哪一篇?|哪一章?)?\s*[？?？]?\s*$"
    r"|来源(?:是什么|在哪(?:里)?)?\s*[？?？]?\s*$"
    r"|在哪(?:一)?[篇章节卷本](?:里|中)?\s*[？?？]?\s*$"
    r"|是(?:谁|哪位)(?:说|写|讲)(?:的|过)?\s*[？?？]?\s*$"
    r"|是谁(?:说|写|讲)(?:的|过)?\s*[？?？]?\s*$"
    r"|原文(?:是什么|怎么说|怎么写)?\s*[？?？]?\s*$"
    r"|是不是原话\s*[？?？]?\s*$"
    r"|原话(?:是什么)?\s*[？?？]?\s*$"
    r"|在哪一篇?\s*[？?？]?\s*$")


def detect_verification_intent(message):
    """P2: 核验意图检测 → {kind, term, quoted, constraint, subject_author} | None

    语义分类（不是单一关键词表）:
      EXACT_WORDING      用户要核验的是"固定措辞是否逐字出现"（逐字/原话/原文怎么写）
      SOURCE_ATTRIBUTION 用户要核验的是"归属/出处"（是否写过/是否出自/哪本书哪一章）
      FACT_VERIFICATION  一般事实核验（明确要求确认/核实某个说法）
    constraint 附带来源约束（P3 消费: PRIMARY_ONLY 时二手不得进入 used_evidence）。
    """
    msg = (message or "").strip()
    if not msg:
        return None
    kind = None
    if _VI_WORDING_RE.search(msg):
        kind = "EXACT_WORDING"
    elif _VI_ATTRIBUTION_RE.search(msg):
        kind = "SOURCE_ATTRIBUTION"
    elif re.search(r"(确认|核实|考据|查证|考辨).{0,20}(是不是|是否|说法|表述|出处|原文)", msg):
        kind = "FACT_VERIFICATION"
    if not kind:
        return None
    # 来源约束
    if _VI_PRIMARY_RE.search(msg):
        constraint = "PRIMARY_ONLY"
    elif _VI_AUTHOR_ONLY_RE.search(msg):
        constraint = "AUTHOR_ONLY"
    elif _VI_EDITION_RE.search(msg):
        constraint = "EDITION_SPECIFIC"
    elif _VI_BOOK_RE.search(msg):
        constraint = "BOOK_ONLY"
    else:
        constraint = "NONE"
    # 核验对象: 优先引号内最长概念（用户给出的待核验表述）; 兜底《》书名
    term, quoted = "", False
    cands = [m.group(1).strip() for m in _QUOTED_RE.finditer(msg)]
    if cands:
        term = max(cands, key=len)
        quoted = True
    else:
        m = re.search(r"《([^》]{2,20})》", msg)
        term = m.group(1).strip() if m else ""
    # T1.1-A: 裸出处句式的 term 兜底——「言必有中出处」「过犹不及是谁说的」
    # 无引号也无《》时, 剥掉尾部出处/归属词型, 余下片段即待核验表述。
    # 没有它, 核验机制（verif_box/义务满足判定/逐字核验）全部空转。
    if not term and kind in ("SOURCE_ATTRIBUTION", "EXACT_WORDING"):
        t = _ATTR_CUE_TAIL_RE.sub("", msg).strip(" 　\t，。；、！？?！,.;：:~")
        for fill in ("请问", "请问一下", "请问下", "你知道", "告诉我", "帮我查", "帮我",
                     "查一下", "帮忙查", "想问", "想问问", "我想知道", "问一下"):
            if t.startswith(fill):
                t = t[len(fill):].strip(" 　，。")
        t = t.rstrip("的呢吗啊是了").strip(" 　“”\"'「」『』")
        if t in ("这句话", "这句诗", "这句词", "此话", "该句", "它", "这话"):
            t = ""
        if 2 <= len(t) <= 24 and re.search(r"[\u4e00-\u9fffA-Za-z]", t):
            term = t
    # 主体作者: "X 本人/自己" 句式 → X（P3 的二手排除基准）。
    # 遍历全部匹配 + 前缀收窄校验（贪婪匹配会吞修饰语, 且引号句可能含"自己"）。
    subject_author = ""
    try:
        from epistemic_guard import _match_philosopher as _mp
        for m in re.finditer(r"([\u4e00-\u9fff·A-Za-z]{2,14})(本人|自己)", msg):
            cand = m.group(1)
            hits = _mp(cand)
            if not hits:
                for k in range(1, len(cand) - 1):
                    hits = _mp(cand[k:])
                    if hits:
                        break
            if hits:
                subject_author = hits[0]
                break
    except Exception:
        subject_author = ""
    return {"kind": kind, "term": term, "quoted": quoted,
            "constraint": constraint, "subject_author": subject_author}


VERIFICATION_CONSTRAINT_ZH = {
    "PRIMARY_ONLY": (
        "【来源约束（系统）】用户要求只以原典为据（PRIMARY_ONLY）。二手研究/评注/导论即使被检索到，"
        "也不得作为最终主张的证据来源，不得以【《书》·章】正式引用二手书；"
        "最终断言只能建立在提问对象本人文本之上。若库内原典无法确认，直接明说不能确认，"
        "绝不拿二手书替代原典下结论。"),
    "AUTHOR_ONLY": (
        "【来源约束（系统）】用户只认可该哲学家本人的文字。他人（包括研究者）的转述、评注只能作背景，"
        "不得作为“他本人说过 X”的证据；无法从其本人文本确认时明确说明。"),
    "BOOK_ONLY": (
        "【来源约束（系统）】用户要求章节级定位：给出可核验的【《书》·章节】位置；"
        "库内无法定位到章节时，明确说明“未能定位具体章节”，不得编造章节号。"),
    "EDITION_SPECIFIC": (
        "【来源约束（系统）】用户关注版本/译本差异：回答需区分原著语言版本与中文译本措辞，"
        "不同译本措辞不同时如实指出，不得把某一译本的措辞当成逐字原文。"),
    "NONE": "",
}
VERIFICATION_CONSTRAINT_EN = {
    "PRIMARY_ONLY": (
        "[Source constraint] The user accepts only primary texts (PRIMARY_ONLY). Secondary "
        "scholarship/commentaries, even if retrieved, must not back the final claims and must not be "
        "formally cited as 【《Book》· chapter】; ground every final assertion in the philosopher's own "
        "text. If the primary corpus cannot confirm it, say plainly that it cannot be confirmed — "
        "never substitute a secondary source."),
    "AUTHOR_ONLY": (
        "[Source constraint] Only the philosopher's own writings count. Others' paraphrases or "
        "commentaries are background only and must not evidence 'he himself wrote X'; say plainly "
        "when his own text cannot confirm it."),
    "BOOK_ONLY": (
        "[Source constraint] Chapter-level location is requested: give a verifiable 【《Book》· "
        "chapter】; if the corpus cannot locate it, state so instead of inventing a chapter number."),
    "EDITION_SPECIFIC": (
        "[Source constraint] Edition/translation differences matter: distinguish the original-language "
        "wording from the Chinese translation; never present one translation's wording as the verbatim "
        "original."),
    "NONE": "",
}


def verification_constraint_directive(constraint, language="zh"):
    """P2/P3: 来源约束注入（NONE 返回 None）"""
    tpl = (VERIFICATION_CONSTRAINT_EN if language == "en" else VERIFICATION_CONSTRAINT_ZH).get(constraint)
    return tpl or None


# ═══════════════════════════════════════════════════════
# Phase T.1 (T1.1-B/E/H): 出处核验纪律——主文本读取义务 + MEMORY_HINT≠EVIDENCE
# + 禁止 verify-later 反模式（检测到核验意图时随 plan 注入, 每请求一次）
# ═══════════════════════════════════════════════════════
VERIFY_NOW_DIRECTIVE_ZH = (
    "【出处核验纪律（系统）】检测到出处/原文核验意图，以下三条是硬约束：\n"
    "1) 核验义务必须在本次回答内完成：检索定位到候选作品/篇章后，必须实际读取该篇章原文"
    "（get_chapter），在全文中核验措辞后才算完成；绝对禁止以“如果你需要我可以再读原文/再核实”"
    "“需要的话我可以进一步查证”等说法把核验推给后续轮次——那等于没有核验。\n"
    "2) 记忆与检索片段只是定位线索（MEMORY_HINT），不是证据：模型记忆可以提供候选书名/篇章"
    "用于检索与读取，但“原文是……/原文如下”式的逐字引用只能出自已读取的章节全文；"
    "检索片段命中只证明“可以定位”，不构成逐字核验。\n"
    "3) 出处核验的完成状态分层：定位（候选找到）≠ 已读（读取原文）≠ 逐字核验（原句在原文中）"
    "——只有“已读”之后才可声称出处已核验；用户要求原话/逐字时，必须逐字命中才能给原文引用，"
    "未命中时给出最接近原文并明确说明差异。")
VERIFY_NOW_DIRECTIVE_EN = (
    "[Source-verification discipline] A source/attribution intent was detected; three hard rules:\n"
    "1) The verification obligation must be completed within THIS answer: once a candidate work/"
    "chapter is located, actually read the chapter (get_chapter) and verify the wording in the full "
    "text. Never defer with 'if you want, I can read the original later' — that is non-verification.\n"
    "2) Memory and search snippets are location hints (MEMORY_HINT), not evidence: memory may supply "
    "candidate titles/chapters for retrieval, but verbatim quotation ('the original reads…') may only "
    "come from chapter text actually read.\n"
    "3) Verification states are layered: LOCATED ≠ READ ≠ QUOTE_VERIFIED. Only after READ may the "
    "attribution be called verified; if the user asks for exact wording, an exact hit is required "
    "before quoting — otherwise give the closest passage and state the difference.")


# ═══════════════════════════════════════════════════════
# Patch 1.1 (P6): 主张角色（claim role）语气校准（内部语义, 不是正文标题）
# ═══════════════════════════════════════════════════════
# 作用: 让回答知道每一步主张属于哪一层, 措辞强度与层级相称——
# 解释性重构不得伪装成无争议的文本事实。角色名本身绝不进入用户可见正文。
CLAIM_ROLES = ["TEXTUAL_CLAIM", "RECONSTRUCTION", "INTERPRETIVE_CLAIM",
               "LATER_CRITICISM", "AGENT_SYNTHESIS"]

CLAIM_ROLE_DIRECTIVE_ZH = (
    "【主张层级（内部规划）】组织回答时在内部区分每一步主张的级别，让措辞强度与层级相称：\n"
    "· 原文事实（有【《书》·章】支撑的直接文本主张）→ 可直陈：“康德明确主张……”；\n"
    "· 重构（你替作者补全的论证步骤）→ 用“可以把这一步理解为……”引出，不与原文事实混排；\n"
    "· 解释主张（文本允许多种读法中的一读）→ 用“一个有力的读法是……”；\n"
    "· 后来批评（后人的批评，如黑格尔/叔本华对康德）→ 注明“后来如X所提出的批评是……”，不写成作者自己的话；\n"
    "· 你自己的综合（跨线索判断）→ 直认归属：“如果把这些线索合在一起，我会把代价概括为……”。\n"
    "不要给每句话加免责声明，也不要退化成“有人认为……也有人认为……”的并列百科体——"
    "要求只有一个：解释性重构与你的综合判断不得伪装成无争议的文本事实，并知道自己的判断属于哪一层。"
    "以上角色名是内部分类，绝不写进回答。")
CLAIM_ROLE_DIRECTIVE_EN = (
    "[Claim-role calibration (internal)] While composing, keep track of each step's claim level and "
    "match wording strength to it: textual facts (backed by 【《Book》· chapter】) may be stated "
    "directly ('Kant explicitly holds…'); reconstructions you complete on the author's behalf are "
    "introduced as 'this step can be understood as…'; interpretive claims as 'one strong reading "
    "is…'; later criticism is attributed ('as Hegel later objected…'), never as the author's own "
    "words; your own synthesis is owned ('putting these threads together, I would summarize the cost "
    "as…'). Do not hedge every sentence and do not collapse into an encyclopedia 'some say… others "
    "say…' register — the only requirement is that reconstruction and your synthesis never pass "
    "themselves off as uncontested textual fact. These role names are internal and never appear in "
    "the answer.")


def get_claim_role_directive(problem_type, language="zh"):
    """P6: 深度/论证/比较类问题注入主张层级要求（其余类型 None——不扩大范围）"""
    if problem_type not in ("DEEP_SYNTHESIS", "ARGUMENT_ANALYSIS", "COMPARISON"):
        return None
    return CLAIM_ROLE_DIRECTIVE_EN if language == "en" else CLAIM_ROLE_DIRECTIVE_ZH


# ═══════════════════════════════════════════════════════
# Patch 1.1 (P7): 原典路径附录——仅当来源导航对用户有价值时出现（确定性, 非随机）
# ═══════════════════════════════════════════════════════
SOURCE_NAV_ALLOWED = {"DEEP_SYNTHESIS", "HISTORICAL_GENEALOGY", "TEXTUAL_INTERPRETATION"}
_NAV_ASK_RE = re.compile(
    r"(阅读|读书|学习)?(路径|顺序|路线|书单)|读(哪些|哪几)本|从哪本.{0,6}(读|开始)|先读哪|按.{0,8}(顺序|次序)读")


def source_navigation_allowed(problem_type, message):
    """P7: 原典路径附录是否允许——用户明确要阅读路径, 或问题类型本身是深度文本分析/
    谱系/文本解读（多原典之间存在明确递进）。普通概念解释/出处核验/论证分析 → 不默认附加。"""
    if _NAV_ASK_RE.search(message or ""):
        return True
    return problem_type in SOURCE_NAV_ALLOWED


SOURCE_NAV_SUPPRESS_ZH = (
    "【附录约束（系统）】本题不需要「原典路径」推荐阅读附录（普通概念解释/出处核验不默认附加"
    "阅读顺序清单）——回答完成后直接收束。仅当来源导航本身对回答必要（用户明确索要阅读路径）才可附。")
SOURCE_NAV_SUPPRESS_EN = (
    "[Appendix constraint] No 'original-text path' reading appendix for this question (plain concept "
    "explanations / source checks do not get a default reading-order list) — close the answer "
    "directly. Attach one only if source navigation is itself necessary for the answer.")


# ═══════════════════════════════════════════════════════
# B6. 推理关系识别 + 依赖链要求（内部规划语义; 关系名不进入用户可见回答）
# ═══════════════════════════════════════════════════════
RELATIONS = [
    "definition", "distinction", "dependency", "internal_tension", "contradiction",
    "conceptual_transition", "genealogy", "competing_interpretation", "counterexample",
    "internal_critique", "external_critique", "implication", "limitation",
]
_RELATION_CUES = {
    "definition": [r"什么是", r"指什么", r"定义", r"概念", r"术语", r"什么意思"],
    "distinction": [r"区别", r"区分", r"不同", r"不是.*而是", r"vs", r"分别", r"差异", r"差别"],
    "dependency": [r"为什么", r"因此", r"所以", r"因为", r"导致", r"使得", r"由此", r"必然"],
    "internal_tension": [r"矛盾", r"张力", r"悖论", r"二律背反", r"冲突", r"自相矛盾", r"疑难"],
    "contradiction": [r"矛盾", r"自相矛盾", r"对立", r"不一致"],
    "conceptual_transition": [r"转变", r"转向", r"过渡", r"转换", r"从.{0,8}到", r"变成", r"演变成", r"发展"],
    "genealogy": [r"溯源", r"来源", r"起源", r"系谱", r"谱系", r"历史", r"之前", r"演变"],
    "competing_interpretation": [r"另一种", r"别的读法", r"不同解读", r"争议", r"学界", r"批评者", r"也有人", r"读法"],
    "counterexample": [r"反例", r"例外", r"反证", r"驳倒"],
    "internal_critique": [r"内部", r"自身", r"自洽", r"自己"],
    "external_critique": [r"批判", r"批评", r"不满意", r"质疑", r"反驳", r"反对", r"指责", r"诟病"],
    "implication": [r"意味着", r"蕴含", r"引申", r"推论", r"影响", r"后果", r"代价"],
    "limitation": [r"局限", r"限制", r"不足", r"边界", r"不能", r"限度"],
}


def derive_relations(message, problem_type=None):
    """B6: 由问题动态识别需要的推理关系（不要求全部存在; 返回关系名列表）"""
    msg = message or ""
    rels = []
    for rel, cues in _RELATION_CUES.items():
        if any(re.search(c, msg) for c in cues):
            rels.append(rel)
    if problem_type in ("DEEP_SYNTHESIS", "COMPARISON", "ARGUMENT_ANALYSIS") and "dependency" not in rels:
        rels.insert(0, "dependency")
    if problem_type == "COMPARISON" and "distinction" not in rels:
        rels.insert(0, "distinction")
    if problem_type == "ARGUMENT_ANALYSIS" and "definition" not in rels:
        rels.insert(0, "definition")
    return rels


# 依赖链要求注入（B6 核心: 论证必须形成 dependency chain, 而非平行 bullet list）
CHAIN_DIRECTIVE_ZH = (
    "【论证推进要求（内部规划）】本题需要的是推进式的论证链，而不是并列的理由清单。"
    "按问题自身的逻辑顺序推进，每一步都要让读者看到“前一步为什么引出这一步”："
    "先界定或区分核心概念；再建立概念之间的依赖与转换（某环节为何必然出现、为何需要某个原则）；"
    "点出内部的张力或矛盾点；呈现为解决张力而出现的概念转换；"
    "若问题涉及批评者或对手，说明批评从哪个内部节点发起，以及该替代方案付出什么代价。"
    "禁止把不同领域或不同作者写成彼此并列的独立板块——必须建立它们之间的因果/派生/回应关系。"
    "这些要求本身不要写进回答。")
CHAIN_DIRECTIVE_EN = (
    "[Argument progression (internal plan)] This question needs a progressive chain of reasoning, "
    "not a parallel list of reasons. Advance by the question's own logic; at each step the reader "
    "should see why the previous step leads to this one: define or distinguish the core concepts; "
    "establish dependencies and transitions between them (why a step must appear, why a principle is "
    "needed); locate the internal tension or contradiction; show the conceptual shift that answers "
    "the tension; if critics or opponents are involved, say which internal node they attack and what "
    "their alternative costs. Do not present separate domains or authors as parallel standalone "
    "blocks — build causal/derivative/response relations between them. Do not write these "
    "requirements into the answer.")


def get_chain_directive(problem_type, language="zh"):
    """B6: 深度/对比/论证类问题注入依赖链要求（其余类型返回 None）"""
    if problem_type not in ("DEEP_SYNTHESIS", "COMPARISON", "ARGUMENT_ANALYSIS", "HISTORICAL_GENEALOGY"):
        return None
    return CHAIN_DIRECTIVE_EN if language == "en" else CHAIN_DIRECTIVE_ZH


# ═══════════════════════════════════════════════════════
# B5. 时期检测与路由（哲学家智能体）
# ═══════════════════════════════════════════════════════
_YEAR_RE = re.compile(r"(1[6-9]\d{2}|20\d{2})")
_PERIOD_WORDS = ["早期", "中期", "晚期", "早年的", "晚年的", "当时的你", "后来的你", "年轻时",
                 "晚年", "为什么改变", "转变", "时期", "两个时期", "不同时期", "几年后的你",
                 "青年", "壮年", "暮年", "后来为什么"]

# 已知哲学家的年份→时期映射（运行时路由用; 不重构 Persona Evolution, 只接入已有 period 能力）
_AGENT_PERIOD_YEARS = {
    "nietzsche": {"early": (1844, 1876), "middle": (1877, 1882), "late": (1883, 1900)},
}


def detect_temporal(message):
    """B5: 时期维度检测 → {detected, years, words}"""
    msg = message or ""
    years = [int(y) for y in _YEAR_RE.findall(msg)]
    words = [w for w in _PERIOD_WORDS if w in msg]
    return {"detected": bool(years) or bool(words), "years": years, "words": words}


def year_to_period(agent, year):
    """年份 → 时期（该智能体已知则映射, 未知返回 None）"""
    table = _AGENT_PERIOD_YEARS.get(agent)
    if not table or not year:
        return None
    for period, (lo, hi) in table.items():
        if lo <= year <= hi:
            return period
    return None


def temporal_directive(agent, detected, language="zh"):
    """B5: 时期路由注入（仅哲学家智能体 + 检测到时期维度时使用）"""
    years = (detected or {}).get("years") or []
    mapped = {y: year_to_period(agent, y) for y in years}
    period_hint = ""
    if any(mapped.values()):
        period_hint = "（年份→时期: " + "；".join(f"{y}年→{mapped[y]}" for y in years if mapped.get(y)) + "）"
    time_desc = "、".join(f"{y}年" for y in years) if years else "早期/中期/晚期"
    if language == "en":
        return (
            f"[Period requirement] This question has an explicit temporal dimension ({time_desc}). "
            "Your answer must rest on the actual state of your thought in each period, not on one "
            "uniform late-period voice: 1) first resolve each period with philosopher_period"
            f"{period_hint}, and gather evidence per period (use the period as context when "
            "retrieving corpus/quotes); 2) distinguish clearly what was actually written/held in "
            "that period (needs corpus or primary-text support) from inferences you draw from that "
            "period's thought (mark those explicitly, e.g. 'were I then'); 3) do not attribute later "
            "positions to the earlier period as things actually said, and do not simulate period "
            "difference by style alone; 4) do not dodge with 'an assistant has no personal historical "
            "perspective' — resolve the periods and answer.")
    return (
        f"【时期要求】这个问题包含明确的时间维度（{time_desc}）。"
        "你的回答必须建立在该时期的真实思想状态上，不得用统一的后期视角回答所有时期：\n"
        "1) 先调用 philosopher_period 分别解析问题涉及的各个时期" + period_hint + "，"
        "并据各时期语料分别取证（philosopher_corpus/philosopher_quote 检索时把时期作为背景）；\n"
        "2) 明确区分：哪些是该时期历史上真实写下的文本/立场（需有语料或原典依据），"
        "哪些是你依据该时期思想所做的推演（推演必须显式标注，如“若当时的我”）；\n"
        "3) 不得把后期立场写成前期实际说过的话，也不得只靠改变文风来模拟时期差异；\n"
        "4) 不要用“作为助手没有个人历史视角”这类说法回避问题——按上述时期解析直接作答。")


# ═══════════════════════════════════════════════════════
# B3. 术语核验（term-presence 问题 → 核验状态 → 措辞约束）
# ═══════════════════════════════════════════════════════
# 术语核验型问题线索: 完整术语/逐字/明确提出/原文是否写/有没有这个说法…
_TERM_PRESENCE_RE = re.compile(
    r"完整术语|逐字(出现|表述|核对|定位|核验|验证)|明确提出|明确提出了|明确地提出|"
    r"原文(是否|有没有|是不是|里|中).{0,12}(说|写|提|出现)|"
    r"有没有.{0,8}(术语|说法|词|表述)|"
    r"是不是.{0,10}(提出|说过|写过|用过)|真的(说过|提出|用过|写过)|"
    r"这个(完整)?(术语|说法|表述).{0,6}(是不是|是否|有没有|出现)")


def detect_term_presence(message):
    """B3: 检测术语核验型问题 → {term, quoted} | None"""
    msg = message or ""
    if not _TERM_PRESENCE_RE.search(msg):
        return None
    term = _q(msg)
    if not term:
        # 兜底: "这个完整术语" 前的最长名词片段
        m = re.search(r"([\u4e00-\u9fff]{2,12})这个(完整)?术语", msg)
        if m:
            term = m.group(1)
    return {"term": term, "quoted": bool(term and _q(msg))} if term else None


def _tool_texts(tool_log):
    """tool_log → 已取回的全部原文文本（search_books snippet / get_chapter 全文 / 语料回响）"""
    texts = []
    for tc in tool_log or []:
        rf = tc.get("result_full")
        if not isinstance(rf, dict):
            continue
        name = tc.get("name")
        if name == "search_books":
            for item in rf.get("results") or []:
                if isinstance(item, dict) and item.get("snippet"):
                    texts.append(item["snippet"])
        elif name == "get_chapter":
            if rf.get("text"):
                texts.append(rf["text"])
        elif name in ("philosopher_corpus", "philosopher_quote"):
            for e in (rf.get("echoes") or rf.get("quotes") or []):
                if isinstance(e, dict):
                    if e.get("text"):
                        texts.append(e["text"])
                    if e.get("snippet"):
                        texts.append(e["snippet"])
    return texts


def verify_term_presence(term, tool_log):
    """B3: 术语核验状态
      VERIFIED_EXACT    term 完整逐字出现在已取回原文
      VERIFIED_SEMANTIC term 未逐字出现, 但按"的/之"拆出的成分全部出现于同一文本（思想可确认）
      NOT_FOUND         两者皆无
      AMBIGUOUS         保留状态位（当前按 SEMANTIC 口径处理变体差异）
    返回 {state, exact_hits, semantic_parts, texts_searched}
    """
    texts = _tool_texts(tool_log)
    t = (term or "").strip()
    res = {"state": "NOT_FOUND", "exact_hits": 0, "semantic_parts": [], "texts_searched": len(texts)}
    if not t or not texts:
        return res
    if any(t in x for x in texts):
        res["state"] = "VERIFIED_EXACT"
        res["exact_hits"] = sum(1 for x in texts if t in x)
        return res
    parts = [p for p in re.split(r"[的之]", t) if len(p) >= 2]
    if len(parts) >= 2:
        for x in texts:
            if all(p in x for p in parts):
                res["state"] = "VERIFIED_SEMANTIC"
                res["semantic_parts"] = parts
                return res
    return res


VERIFICATION_WORDING = {
    "VERIFIED_EXACT": "【术语核验·EXACT】原文检索已逐字命中「{term}」。你可以明确说“原文明确写道该术语”，并直接引用原文。",
    "VERIFIED_SEMANTIC": (
        "【术语核验·SEMANTIC】原文检索未逐字命中「{term}」，但该思想（成分: {parts}）在原文中可确认。"
        "回答必须区分“思想可确认”与“固定措辞逐字出现”：不得说“已完整提出该术语”“原文明确写道{term}”；"
        "应表述为“这一思想有明确的原文依据，但『{term}』这一固定表述是否逐字出现，我未能在库中核验”。"),
    "NOT_FOUND": (
        "【术语核验·NOT_FOUND】原文检索未找到「{term}」的逐字出现。首句不得无条件肯定“是”；"
        "应表述为“我不能确认这个完整术语逐字出现在原文中”，并基于概念层面给出判断。"),
    "AMBIGUOUS": (
        "【术语核验·AMBIGUOUS】不同译本/分词可能不同，目前证据不足以作逐字判断。"
        "回答须明确说明这一点，不得断言“原文明确写道该术语”。"),
}


def verification_injection(verification, language="zh"):
    """B3: 核验状态 → 措辞约束注入（无状态或 EXACT 也返回约束——EXACT 允许明确措辞）"""
    state = (verification or {}).get("state")
    if not state:
        return None
    tpl = VERIFICATION_WORDING.get(state)
    if not tpl:
        return None
    return tpl.format(term=(verification.get("term") or "该术语"),
                      parts="、".join(verification.get("semantic_parts") or []))


# B3 后置: 无条件断言改写（仅在 state != VERIFIED_EXACT 时启用）
# 目标短语 → 受约束替换（吸收宾语到句内边界, 避免"…这一命题"悬空）; 不改变句子其余部分
_UNCONDITIONAL_CONFIRM = [
    (re.compile(r"(?:已经|已)(?:完整|明确)地?提出了[^，。；;]{0,24}"),
     "已经完整阐述了这一思想（该固定措辞是否逐字出现，未能核验）"),
    (re.compile(r"(?:完整|明确)地?提出了[^，。；;]{0,24}"),
     "完整阐述了这一思想（该固定措辞是否逐字出现，未能核验）"),
    (re.compile(r"原文明确写道"), "原文明确阐述了这一思想（该固定措辞是否逐字出现，未能核验）"),
]


def constrain_unconditional_claim(sentence, verification_state):
    """B3: 若核验状态非 EXACT, 将句中无条件“已提出该术语”类断言改写为受约束表述。
    不命中任何模式时原句不变。"""
    if not sentence or verification_state in (None, "VERIFIED_EXACT"):
        return sentence
    out = sentence
    for rx, repl in _UNCONDITIONAL_CONFIRM:
        out = rx.sub(repl, out)
    return out


class TermClaimGate:
    """B3: 最终回答流中的术语断言约束门。

    仅当目标术语出现时缓冲（含术语的句子在句界处做无条件断言改写）;
    不含术语的文本立即放行（不增加逐句延迟）。约束一次后自动放行后续文本。
    """

    def __init__(self, term, constrain):
        self._term = term or ""
        self._constrain = constrain
        self._buf = ""
        self._active = bool(term)

    def push(self, text):
        if not self._active or not text:
            return text
        self._buf += text
        if self._term not in self._buf:
            out, self._buf = self._buf, ""
            return out
        m = re.search(r"[。！？!?;\n]", self._buf)
        if not m:
            return ""
        head, self._buf = self._buf[:m.end()], self._buf[m.end():]
        self._active = False
        return self._constrain(head) if self._constrain else head

    def flush(self):
        out, self._buf = self._buf, ""
        if self._active and out and self._constrain:
            self._active = False
            return self._constrain(out)
        return out


# ═══════════════════════════════════════════════════════
# 编排: build_plan —— 一次请求一个计划
# ═══════════════════════════════════════════════════════
def extract_key_terms(message):
    """B1: 问题关键术语（引号内概念 + 《》书名 + 各分句最长片段; 供 evidence relevance 统计）"""
    terms = []
    msg = (message or "").strip()
    for m in _QUOTED_RE.finditer(msg):
        t = m.group(1).strip()
        if 2 <= len(t) <= 16 and t not in terms:
            terms.append(t)
    for m in re.finditer(r"《([^》]{2,20})》", msg):
        t = m.group(1).strip()
        if 2 <= len(t) <= 16 and t not in terms:
            terms.append(t)
    if len(terms) >= 3:
        return terms
    for clause in re.split(r"[，。；、！？!?;:：\n]", msg):
        chunk = re.sub(r"[^一-鿿A-Za-z0-9]", "", clause)
        # 取最长 2~6 字片段（去掉常见虚词起止）
        for cand in sorted({chunk[i:i + 2] for i in range(len(chunk) - 1)}, key=len, reverse=True)[:2]:
            if 2 <= len(cand) <= 6 and cand not in terms:
                terms.append(cand)
        if len(terms) >= 3:
            break
    return terms[:4]


def build_plan(message, agent="general", language="zh"):
    """构建请求计划（纯规则, 一次调用）

    返回 dict:
      problem_type / complexity / key_terms / form_directive / chain_directive /
      temporal / verification_question / verification_intent / source_navigation /
      injections（追加进 system 的消息列表）
    """
    msg = message or ""
    problem_type = classify_problem(msg, agent)
    complexity = classify_complexity(problem_type, msg, agent)
    # ── Patch 1.1 (P2): 核验意图 → verification-aware path ──
    # 检测到核验意图（含语义变体）时, 问题类型与复杂度一律归入核验族:
    # FACT_VERIFICATION / NARROW_FACTUAL——出处核验不该因句长被抬成 DEEP_SYNTHESIS。
    v_intent = None if agent != "general" else detect_verification_intent(msg)
    if v_intent:
        problem_type = "FACT_VERIFICATION"
        complexity = "NARROW_FACTUAL"
    plan = {
        "problem_type": problem_type,
        "complexity": complexity,
        "key_terms": extract_key_terms(msg),
        "relations": derive_relations(msg, problem_type),
        "form_directive": get_form_directive(problem_type, language),
        "chain_directive": get_chain_directive(problem_type, language),
        "claim_role_directive": get_claim_role_directive(problem_type, language),
        "temporal": detect_temporal(msg),
        "verification_question": detect_term_presence(msg),
        "verification_intent": v_intent,
        # ── Patch 1.1 (P7): 原典路径附录按价值条件出现（确定性规则）──
        "source_navigation": source_navigation_allowed(problem_type, msg),
        "injections": [],
    }
    if plan["form_directive"]:
        plan["injections"].append(plan["form_directive"])
    if plan["chain_directive"]:
        plan["injections"].append(plan["chain_directive"])
    if plan["claim_role_directive"]:
        plan["injections"].append(plan["claim_role_directive"])
    if v_intent:
        vcd = verification_constraint_directive(v_intent.get("constraint"), language)
        if vcd:
            plan["injections"].append(vcd)
        # Phase T.1 (T1.1-B/E/H): 出处核验纪律（主文本读取义务 / MEMORY_HINT≠EVIDENCE /
        # 禁止 verify-later）——检测到核验意图即注入
        plan["injections"].append(
            VERIFY_NOW_DIRECTIVE_EN if language == "en" else VERIFY_NOW_DIRECTIVE_ZH)
    if not plan["source_navigation"]:
        nav = SOURCE_NAV_SUPPRESS_EN if language == "en" else SOURCE_NAV_SUPPRESS_ZH
        plan["injections"].append(nav)
    if agent != "general" and plan["temporal"]["detected"]:
        td = temporal_directive(agent, plan["temporal"], language)
        if td:
            plan["injections"].append(td)
    return plan
