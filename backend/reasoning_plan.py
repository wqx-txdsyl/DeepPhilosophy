# -*- coding: utf-8 -*-
"""Reasoning Plan（Patch 1; O4 Cognitive Layer Collapse 后瘦身）——机械/上下文元数据（纯规则, 不调 LLM）

O4 后 reasoning_plan 不再是"独立 reasoning planner"（REASONING_PLAN_RUNTIME_AUTHORITY = 0）:
问题类型分类（problem_type）、复杂度档位（complexity）、回答形态指令（form/chain/claim-role）、
推理关系识别（relations）、关键术语提取（key_terms）、原典路径开关（source_navigation）——
这些认知治理维度已全部删除。Main Agent 不需要 Python 先告诉它"这是 comparison/深度综合"
再决定怎么思考; 是否检索、检索多少、如何组织回答, 全部由 Main Agent 自主决定。

保留的只有两类机械/上下文元数据（无认知控制效果, 只服务核验机制与时期上下文）:

  verification_intent  出处/措辞核验意图检测（P2）——驱动 verif_box 术语核验与
                       final_validator 的来源约束（PRIMARY_ONLY/AUTHOR_ONLY）; 附带
                       VERIFY_NOW 纪律注入与来源约束注入（prompt 层上下文, 非控制门）
  verification_question  术语核验型问题检测（B3）+ verify_term_presence（VERIFIED_EXACT /
                       VERIFIED_SEMANTIC / NOT_FOUND / AMBIGUOUS）+ 措辞约束注入
  temporal             时期检测（B5: 年份 / 早期中期晚期 / 当时的你）→ 哲学家智能体
                       时期上下文注入 + year_to_period 映射（done.temporal 审计用）

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
    # 没有它, 核验机制（verif_box/逐字核验）全部空转。
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


# ══ O2/O4: 原 B3 无条件断言改写（_UNCONDITIONAL_CONFIRM / constrain_unconditional_claim /
# TermClaimGate 句界改写门）已删除——runtime 不得改写模型的句子、不得代为追加
# "该固定措辞未核验"式披露。术语核验状态（verify_term_presence）仍保留并经 prompt
# 层注入, 由 Main Agent 自己在正文中如实表述核验边界。


# ═══════════════════════════════════════════════════════
# 编排: build_plan —— 一次请求一个计划（O4 瘦身版: 只剩机械/上下文元数据）
# ═══════════════════════════════════════════════════════
def build_plan(message, agent="general", language="zh"):
    """构建请求计划（纯规则, 一次调用）

    返回 dict:
      temporal               时期检测（哲学家智能体时期上下文）
      verification_question  术语核验型问题检测（B3）
      verification_intent    出处/措辞核验意图（P2; final_validator 来源约束消费）
      injections             追加进 system 的消息列表（VERIFY_NOW 纪律 + 来源约束 + 时期要求;
                             无问题类型/形态/路由类认知指令——那是 Main Agent 的职权）
    """
    msg = message or ""
    # ── Patch 1.1 (P2): 核验意图 → verification-aware path ──
    v_intent = None if agent != "general" else detect_verification_intent(msg)
    plan = {
        "temporal": detect_temporal(msg),
        "verification_question": detect_term_presence(msg),
        "verification_intent": v_intent,
        "injections": [],
    }
    if v_intent:
        vcd = verification_constraint_directive(v_intent.get("constraint"), language)
        if vcd:
            plan["injections"].append(vcd)
        # Phase T.1 (T1.1-B/E/H): 出处核验纪律（主文本读取义务 / MEMORY_HINT≠EVIDENCE /
        # 禁止 verify-later）——检测到核验意图即注入
        plan["injections"].append(
            VERIFY_NOW_DIRECTIVE_EN if language == "en" else VERIFY_NOW_DIRECTIVE_ZH)
    if agent != "general" and plan["temporal"]["detected"]:
        td = temporal_directive(agent, plan["temporal"], language)
        if td:
            plan["injections"].append(td)
    return plan
