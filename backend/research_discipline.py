# -*- coding: utf-8 -*-
"""Research Discipline（O10-R1, 2026-09-13）——检索纪律单一真源

修复 O10 Reviewer Holdout V1 判定的三个 P0（P0-01 OVER_RESEARCH /
P0-03 TOOL_SELECTION_DISCIPLINE / P0-02 CONVERGENCE 回归）:

  1. Research Need Decision: Main Agent 在调用任何检索类工具前必须经
     declare_research_need 登记 RESEARCH_NEED（NONE/PRIMARY/SCHOLARLY/WEB/MIXED）
     与 EVIDENCE_GAP; runtime 只做机械门（未声明/类别禁止/通道错配/软预算/
     缺口已闭合/无新信息循环 → 结构化拒绝, 不执行）。判断权在 Main Agent,
     执行纪律在 runtime——与 O1/O3 的"引擎不代行认知"契约一致:
     本模块不含任何语义判断, 全部是可审计的机械规则。

  2. Evidence-gap Stop Rule: 缺口闭合（gap_filled）后检索机械关闭;
     上一次检索无新信息（空命中/同结果 hash）后, 同通道高相似查询
     （字符 bigram Jaccard ≥ 0.75）被拒——除非换数据源通道或换明确不同的
     证据目标。同类改写碰运气被机械终止。

  3. Tool Budgets by research class（soft, 非截断）:
       NONE=0  PRIMARY=3  SCHOLARLY=4  WEB=3  MIXED=6
     超出 soft 预算必须以 declare_research_need 附 BUDGET_EXTENSION_REASON +
     UNRESOLVED_EVIDENCE_GAP 申请延展（机械留痕, 无理由不延展）。
     既有 hard 紧急上限（agent_runtime.ToolBudget）原样保留, 只是兜底而非常态预算。

  4. Token/Context Discipline: 工具原始结果只在新产生时全量注入一轮;
     已被模型消费过的结果在后续轮压缩为有界紧凑引用（compact evidence state）,
     完整结果永远保留在 raw_tool_log / tool_log 供确定性校验与证据契约使用
     ——压缩只作用于 LLM 上下文, 不触碰任何校验数据源（Safety Freeze）。

类别判定语义（提示词层, 唯一权威 = SYSTEM_PROMPT_LG 研究需求决策条款）:
  NONE      基本概念解释 / 普通哲学推理 / 用户已给前提的论证分析 /
            不依赖事实与出处的日常哲学（默认, TOOL_BUDGET=0）
  PRIMARY   需要精确引文 / 出处与语境核验 / 原典文本解读
  SCHOLARLY 用户明确要求学界/现代研究/论文/争议综述, 或回答确实依赖二手研究
  WEB       需要网络事实补充（超出原典库与可靠知识）
  MIXED     多通道证据需求
"""
import json
import os
import re
import time

# ═══════════════════════════════════════════════════════
# 配置（env 可覆盖; 引擎从本模块 import, 不允许就地写死）
# ═══════════════════════════════════════════════════════
def _env_int(name, default):
    try:
        return int(os.environ.get(name, "") or default)
    except (TypeError, ValueError):
        return default

def _env_float(name, default):
    try:
        return float(os.environ.get(name, "") or default)
    except (TypeError, ValueError):
        return default

# 研究类别 → soft 检索预算（执行口径; 被门拒绝的调用不计数）
TOOL_BUDGETS = {
    "NONE": _env_int("AGENT_BUDGET_NONE", 0),
    "PRIMARY": _env_int("AGENT_BUDGET_PRIMARY", 3),
    "SCHOLARLY": _env_int("AGENT_BUDGET_SCHOLARLY", 4),
    "WEB": _env_int("AGENT_BUDGET_WEB", 3),
    "MIXED": _env_int("AGENT_BUDGET_MIXED", 6),
}
RESEARCH_CLASSES = ("NONE", "PRIMARY", "SCHOLARLY", "WEB", "MIXED")

# 预算延展（机械审计; 两次机会, 每次 +2 次检索, 仍远低于 hard 紧急上限）
MAX_BUDGET_EXTENSIONS = _env_int("AGENT_BUDGET_MAX_EXTENSIONS", 2)
EXTENSION_STEP = _env_int("AGENT_BUDGET_EXTENSION_STEP", 2)

# 无新信息停止: 同通道相似查询判定阈值（字符 bigram Jaccard; V1 机械审计同款口径）
SIMILAR_QUERY_THRESHOLD = _env_float("AGENT_SIMILAR_QUERY_THRESHOLD", 0.75)

# 声明工具名（引擎注入 general 工具集; 拦截于 tools_node, 不进内容工具注册表）
DECLARE_TOOL_NAME = "declare_research_need"

# ═══════════════════════════════════════════════════════
# 通道分类（机械集合, 与 agent_runtime.RETRIEVAL_TOOLS 的遥测口径分层）
# ═══════════════════════════════════════════════════════
CORPUS_RETRIEVAL_TOOLS = {
    "search_books", "get_chapter", "get_book_detail", "get_philosopher",
    "get_school", "query_graph", "list_books", "query_database", "concept_trace",
}
SCHOLARLY_CHANNEL_TOOLS = {"search_scholarship", "get_scholarly_source"}
WEB_CHANNEL_TOOLS = {"websearch"}
DISCIPLINE_RETRIEVAL_TOOLS = (CORPUS_RETRIEVAL_TOOLS | SCHOLARLY_CHANNEL_TOOLS
                              | WEB_CHANNEL_TOOLS)

def channel_of(tool_name):
    if tool_name in CORPUS_RETRIEVAL_TOOLS:
        return "CORPUS"
    if tool_name in SCHOLARLY_CHANNEL_TOOLS:
        return "SCHOLARLY"
    if tool_name in WEB_CHANNEL_TOOLS:
        return "WEB"
    return None

# 研究类别 → 允许的数据源通道（通道错配 = 机械拒绝, 可升级类别后重试）
CLASS_CHANNELS = {
    "NONE": frozenset(),
    "PRIMARY": frozenset({"CORPUS"}),
    "SCHOLARLY": frozenset({"CORPUS", "SCHOLARLY"}),
    "WEB": frozenset({"CORPUS", "WEB"}),
    "MIXED": frozenset({"CORPUS", "SCHOLARLY", "WEB"}),
}

# ═══════════════════════════════════════════════════════
# 查询相似度（字符 bigram Jaccard; 纯机械, 零 LLM）
# ═══════════════════════════════════════════════════════
_QUERY_KEYS = ("query", "q", "keyword", "concept", "topic", "question",
               "name", "philosopher")
_PUNCT_RE = re.compile(r"[\s\W\u3000-\u303F\uFF00-\uFFEF]+", re.UNICODE)

def extract_query_text(args):
    """从工具参数提取查询文本（取第一个非空文本参数）"""
    if not isinstance(args, dict):
        return ""
    for k in _QUERY_KEYS:
        v = args.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""

def _norm_text(s):
    return _PUNCT_RE.sub("", (s or "").lower())

def _bigrams(s):
    if len(s) < 2:
        return {s} if s else set()
    return {s[i:i + 2] for i in range(len(s) - 1)}

def query_similarity(a, b):
    """归一化后字符 bigram Jaccard ∈ [0,1]（V1 报告 NO_NEW_INFORMATION_LOOPS 同款阈值口径）"""
    na, nb = _norm_text(a), _norm_text(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    A, B = _bigrams(na), _bigrams(nb)
    union = A | B
    return len(A & B) / len(union) if union else 0.0

# ═══════════════════════════════════════════════════════
# Token/Context Discipline: 紧凑证据引用（compact evidence state）
# ═══════════════════════════════════════════════════════
# 长文本载体（章节原文/文献内容）压缩保留头尾窗口, 保住"就近引用"能力;
# 其余结果压缩为摘要引用。完整结果永远在 raw_tool_log（校验数据源, 不受影响）。
LONG_TEXT_TOOLS = {"get_chapter", "get_scholarly_source"}
COMPACT_HEAD_CHARS = _env_int("AGENT_COMPACT_HEAD_CHARS", 400)
COMPACT_TAIL_CHARS = _env_int("AGENT_COMPACT_TAIL_CHARS", 160)
COMPACT_SUMMARY_CHARS = _env_int("AGENT_COMPACT_SUMMARY_CHARS", 240)

def compact_reference(tool_name, args, full_content, result_hash=""):
    """生成已消费工具结果的有界紧凑引用（确定性, 零 LLM）"""
    full = full_content or ""
    a = args if isinstance(args, dict) else {}
    q = extract_query_text(a)
    q_part = f" query=「{q[:32]}」" if q else ""
    if tool_name in LONG_TEXT_TOOLS:
        head = full[:COMPACT_HEAD_CHARS]
        tail = full[-COMPACT_TAIL_CHARS:] if len(full) > COMPACT_HEAD_CHARS + COMPACT_TAIL_CHARS else ""
        kept = (head + ("\n…\n" + tail if tail else "")) if full else ""
        return (f"[证据已压缩·ev#{result_hash[:8] or 'NA'}] {tool_name}{q_part} "
                f"原文共{len(full)}字。此前轮已提供全文, 此处仅保留头尾窗口:{kept}")
    kept = full[:COMPACT_SUMMARY_CHARS]
    return (f"[证据已压缩·ev#{result_hash[:8] or 'NA'}] {tool_name}{q_part} "
            f"此前轮已提供完整结果, 摘要:{kept}")

# ═══════════════════════════════════════════════════════
# 词序不敏感查询指纹（bag-of-words 等价; O10-R1 RUN6 G07 实况修复）
# ═══════════════════════════════════════════════════════
# 「A B C」与「C B A」对检索 API 是同一查询（token 集合相同 → json.dumps 口径
# Jaccard=1.0, V1 审计同款）——换词序重复执行属 P0-02 形态。bag 指纹相同的调用
# 机械复用首次结果（缓存命中, 非新检索, 不占软预算）。
SEARCH_BAG_TOOLS = {"search_books", "websearch", "search_scholarship",
                    "query_database", "concept_trace"}
_TOKEN_RE = re.compile(r"\w+", re.UNICODE)

def query_bag_fingerprint(tool_name, args):
    """检索型工具的词序不敏感指纹（其余参数参与指纹; 查询文本取 token 集合排序）。
    非文本查询工具返回 None（走既有精确指纹路径）。"""
    if tool_name not in SEARCH_BAG_TOOLS or not isinstance(args, dict):
        return None
    q = None
    for k in _QUERY_KEYS:
        v = args.get(k)
        if isinstance(v, str) and v.strip():
            q = v
            break
    if q is None:
        return None
    toks = sorted(t for t in _TOKEN_RE.findall(q.lower()) if t)
    rest = {k: v for k, v in args.items()
            if k not in _QUERY_KEYS and v not in (None, "")}
    try:
        payload = json.dumps({"tool": tool_name, "tokens": toks,
                              "rest": rest}, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        payload = f"{tool_name}|{'|'.join(toks)}"
    import hashlib as _hl
    return _hl.sha1(payload.encode("utf-8")).hexdigest()[:16]

# ═══════════════════════════════════════════════════════
# 机械门拒绝码（机器可审计; 每条附 Main Agent 可执行的下一步）
# ═══════════════════════════════════════════════════════
def _blocked(code, message, extra=None):
    d = {"error": code, "message": message}
    if extra:
        d.update(extra)
    return d

# ═══════════════════════════════════════════════════════
# ResearchDiscipline 状态机（生命周期 = 单次 invocation, 与 DuplicateGuard 同层）
# ═══════════════════════════════════════════════════════
class ResearchDiscipline:
    """检索纪律机械状态机。

    判断权边界（与 O1/O3/O4 契约一致）: 研究需求类别、证据缺口、是否闭合、
    是否延展——全部由 Main Agent 经 declare_research_need 主动登记;
    本状态机只做登记与机械门, 绝不推断语义、绝不代行认知。"""

    def __init__(self, budgets=None):
        self.cfg = dict(TOOL_BUDGETS if budgets is None else budgets)
        self.declarations = []       # 声明审计链（含被拒的非法声明）
        self.active_class = None     # 当前生效类别
        self.evidence_gap = ""       # 当前登记的证据缺口
        self.gap_filled = False      # 缺口闭合标志（闭合后检索机械关闭）
        self.extension_units = 0     # 已获批延展检索次数
        self.extensions = []         # 延展审计链 [{reason, unresolved_gap, ts}]
        self.retrieval_executed = 0  # 本 invocation 已执行检索数（拒绝不计数）
        self.pending_slots = 0       # 本批已过门待执行的检索数（批内预算串行化; 批末清零）
        self.blocked = []            # 被门拒绝的调用 [{tool, code, ts}]
        self.executed_queries = {}   # channel -> [已执行查询文本]（相似判定用）
        self.executed_result_hashes = set()
        self.last_no_new_info = False  # 上一次执行的检索是否无新信息
        # Token/Context Discipline（事实计量）
        self.context_discipline = {
            "tool_messages_compacted": 0,
            "compacted_chars_saved": 0,
            "rounds": [],   # [{round, input_tokens, output_tokens, tool_chars_added}]
        }

    # ── 登记（Main Agent 主动动作; declare_research_need 工具的落点）──
    def declare(self, research_need=None, evidence_gap=None, gap_filled=False,
                budget_extension_reason=None, unresolved_evidence_gap=None,
                source_dependent=None):
        """登记研究需求 / 缺口闭合 / 预算延展。返回回执 dict（作为工具结果）。

        延展合同（机器可审计）: 当前软预算已耗尽时, 必须同时给出
        budget_extension_reason 与 unresolved_evidence_gap 才获延展;
        二者缺一 → 拒绝延展, 检索门继续关闭。
        升级合同（O10-R1 RUN4 后硬化）: 非 NONE 类别必须显式断言
        source_dependent=true（回答正确性确实依赖特定文献/出处）并给出具体化
        EVIDENCE_GAP——缺任一项则登记不被接受, 一次补正后生效。这是把
        "研究需求决策"从隐式判断变成显式、留痕的确认动作。"""
        need = (research_need or "").strip().upper() if isinstance(research_need, str) else ""
        if need and need not in RESEARCH_CLASSES:
            rec = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "accepted": False,
                   "reason": f"INVALID_RESEARCH_NEED:{need[:24]}"}
            self.declarations.append(rec)
            return _blocked("INVALID_RESEARCH_NEED",
                            f"未知研究需求类别「{need[:24]}」。有效值: {'/'.join(RESEARCH_CLASSES)}。")
        # 缺口闭合登记（Evidence-gap Stop Rule 的显式收口动作）
        if gap_filled:
            self.gap_filled = True
            rec = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "accepted": True,
                   "action": "EVIDENCE_GAP_FILLED", "research_need": self.active_class}
            self.declarations.append(rec)
            return {"ok": True, "status": "EVIDENCE_GAP_FILLED_RECORDED",
                    "message": "证据缺口已登记为闭合: 后续检索将被机械拒绝。请立即综合作答。",
                    "snapshot": self.snapshot()}
        if not need:
            rec = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "accepted": False,
                   "reason": "MISSING_RESEARCH_NEED"}
            self.declarations.append(rec)
            return _blocked("MISSING_RESEARCH_NEED",
                            "缺少 research_need 参数。有效值: " + "/".join(RESEARCH_CLASSES) + "。")
        # 非 NONE 升级合同: 类别发生变化（或缺口未具体化）时, 必须显式断言
        # source_dependent=true 并给出具体化 EVIDENCE_GAP——缺任一项则登记不被接受,
        # 一次补正后生效。同类别再登记（延展申请等）继承原声明的确认, 不重复索要。
        if need != "NONE" and (self.active_class != need or not self.evidence_gap):
            problems = []
            if source_dependent is not True:
                problems.append("source_dependent 未显式置 true（请确认: 这个问题的回答正确性"
                                "确实依赖特定文献/出处吗? 只是『查了更好看』就改用 NONE）")
            if not (evidence_gap and len(str(evidence_gap).strip()) >= 4):
                problems.append("evidence_gap 需具体化（至少4字: 哪句结论需要哪个出处/哪段原文）")
            if problems:
                rec = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "accepted": False,
                       "reason": "UPGRADE_CONTRACT_INCOMPLETE:" + ",".join(
                           p.split("（")[0] for p in problems)}
                self.declarations.append(rec)
                return {"ok": False, "status": "UPGRADE_CONTRACT_INCOMPLETE",
                        "message": "研究需求登记未生效（升级合同不完整）: " + "；".join(problems)
                        + "。补全后重新 declare, 或改用 NONE 直接作答。",
                        "valid_classes": list(RESEARCH_CLASSES)}
        # 类别升级/修正: 合法（全部留痕）; 软预算按新类别基准重算（延展次数累计不重置）
        prev = self.active_class
        self.active_class = need
        # 缺口文本: 再登记未给 gap 时继承已有缺口（防延展申请清空原缺口）
        self.evidence_gap = ((evidence_gap or "").strip() or self.evidence_gap)[:200]
        self.gap_filled = False   # 新研究需求 → 缺口重新打开（升级语义）
        rec = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "accepted": True,
               "action": "DECLARE", "research_need": need, "prev": prev,
               "evidence_gap": self.evidence_gap, "source_dependent": need == "NONE" or source_dependent is True}
        self.declarations.append(rec)
        msg = (f"已登记 RESEARCH_NEED={need}（EVIDENCE_GAP: {self.evidence_gap or '未具体化'}）。"
               f"soft 检索预算={self._soft_limit()} 次。")
        # 决策时刻的机械收口提示（读取闭环——检索命中后下一步是读取原文/实读文献）
        if need == "PRIMARY":
            msg += ("（PRIMARY 闭环: search 命中候选后, 下一步就是 get_chapter 读取对应篇章原文"
                    "核对措辞——正式引用与逐字引文必须落在已读证据上。）")
        elif need == "SCHOLARLY":
            msg += ("（SCHOLARLY 闭环: 对任何文献做内容性归因前必须 get_scholarly_source 实读;"
                    "只 search 到标题不能陈述其观点。）")
        # 预算延展申请（仅当当前预算已耗尽时才有意义; 但登记在任何时刻都合法留痕）
        if budget_extension_reason or unresolved_evidence_gap:
            if len(self.extensions) >= MAX_BUDGET_EXTENSIONS:
                rec["extension"] = "DENIED_MAX_EXTENSIONS"
                msg += ("延展申请被拒: 延展次数已达上限（"
                        f"{MAX_BUDGET_EXTENSIONS}）。请基于已取得的证据综合作答, "
                        "并如实说明未能核验的部分。")
            elif not (budget_extension_reason and str(budget_extension_reason).strip()
                      and unresolved_evidence_gap and str(unresolved_evidence_gap).strip()):
                rec["extension"] = "DENIED_MISSING_REASON"
                msg += ("延展申请被拒: 必须同时给出 budget_extension_reason（为什么现有证据"
                        "不足以收口）与 unresolved_evidence_gap（还缺哪个具体证据）。")
            else:
                self.extension_units += EXTENSION_STEP
                self.extensions.append({
                    "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "reason": str(budget_extension_reason).strip()[:300],
                    "unresolved_gap": str(unresolved_evidence_gap).strip()[:300]})
                rec["extension"] = f"GRANTED_+{EXTENSION_STEP}"
                msg += f"预算延展已获准（BUDGET_EXTENSION_REASON 已留痕）: soft 预算={self._soft_limit()} 次。"
        return {"ok": True, "status": "DECLARED", "message": msg,
                "snapshot": self.snapshot()}

    # ── 机械门（tools_node 在执行检索类工具前调用）──
    def gate(self, tool_name):
        """返回 None=放行, 或 dict(error=code, message=…) 拒绝。

        只表达机械纪律事实, 绝不暗含"证据已充分/库中无此书"——
        每条拒绝消息都给出 Main Agent 可执行的下一步。"""
        if tool_name not in DISCIPLINE_RETRIEVAL_TOOLS:
            return None
        if self.active_class is None:
            return _blocked(
                "RESEARCH_NEED_DECLARATION_REQUIRED",
                "检索被拒: 本轮尚未登记研究需求。请先调用 declare_research_need 登记 "
                "RESEARCH_NEED（NONE/PRIMARY/SCHOLARLY/WEB/MIXED）与 EVIDENCE_GAP, "
                "再决定是否检索; 若无需检索, 直接综合作答。",
                {"valid_classes": list(RESEARCH_CLASSES)})
        if self.gap_filled:
            return _blocked(
                "EVIDENCE_GAP_FILLED_STOP",
                "检索被拒: 你已登记证据缺口闭合（EVIDENCE_GAP_FILLED）。请立即停止研究、"
                "综合作答; 若确实出现了新的证据缺口, 先重新 declare_research_need 登记新缺口。")
        if self.active_class == "NONE":
            return _blocked(
                "RESEARCH_NEED_NONE_NO_RETRIEVAL",
                "检索被拒: 本轮研究需求为 NONE（TOOL_BUDGET=0）——基本概念/普通推理/"
                "日常哲学类问题不检索, 直接基于可靠知识综合作答（记忆性表述按证据分级降级标注）。"
                "若你判断确实存在证据依赖, 先重新 declare_research_need 升级类别。")
        ch = channel_of(tool_name)
        allowed = CLASS_CHANNELS.get(self.active_class, frozenset())
        if ch not in allowed:
            return _blocked(
                "CHANNEL_MISMATCH",
                f"检索被拒: 研究需求为 {self.active_class}（允许通道: {'/'.join(sorted(allowed)) or '无'}）,"
                f"而 {tool_name} 属于 {ch} 通道。若确需该通道证据, 先 declare_research_need 升级类别"
                "（如 MIXED）, 不要绕过。")
        if self.retrieval_executed + self.pending_slots >= self._soft_limit():
            return _blocked(
                "SOFT_BUDGET_REACHED",
                f"检索被拒: {self.active_class} 类 soft 检索预算（{self._soft_limit()} 次）已用完。"
                "二选一: ①基于已取得的证据综合作答; ②若确有未解决的证据缺口, 调用 "
                "declare_research_need 并附 budget_extension_reason 与 unresolved_evidence_gap "
                "申请预算延展——无理由不得继续检索。",
                {"soft_limit": self._soft_limit(), "executed": self.retrieval_executed})
        # 无新信息循环的查询粒度拦截（同通道相似查询）在 gate_query 完成——
        # tools_node 统一走 gate_query, 此处只做类别/通道/预算机械门。
        return None

    def gate_query(self, tool_name, args):
        """在 gate 之上的查询粒度判定（无新信息后同通道相似查询拦截）。"""
        base = self.gate(tool_name)
        if base is not None:
            return base
        if tool_name not in DISCIPLINE_RETRIEVAL_TOOLS or not self.last_no_new_info:
            return None
        ch = channel_of(tool_name)
        q = extract_query_text(args)
        if not q:
            return None
        for prev_q in self.executed_queries.get(ch, []):
            if query_similarity(prev_q, q) >= SIMILAR_QUERY_THRESHOLD:
                return _blocked(
                    "NO_NEW_INFORMATION_LOOP",
                    f"检索被拒: 上一次检索没有带来新信息, 且本次查询与已执行的查询高度相似"
                    f"（相似度口径: bigram-Jaccard ≥ {SIMILAR_QUERY_THRESHOLD}）。禁止同通道改写碰运气:"
                    "要么换明确不同的数据源/证据目标重新表述, 要么综合作答并如实标注证据边界。",
                    {"similar_to": prev_q[:60]})
        return None

    # ── 批内预算串行化（tools_node 在 asyncio.gather 之前同步逐调用过门:
    #     并行批的兄弟调用必须互相可见, 否则 5 连发能全部越过 4 次预算）──
    def reserve(self):
        """过门待执行的检索占位（tools_node 同步过门后调用; settle_batch 批末清零）"""
        self.pending_slots += 1

    def settle_batch(self):
        """工具批结束: 占位清零（已执行者已由 record 计入 retrieval_executed）"""
        self.pending_slots = 0

    # ── 执行事实登记（tools_node 执行成功后调用; 拒绝的调用不进这里）──
    def record(self, tool_name, args, result_hash, info_gain):
        if tool_name not in DISCIPLINE_RETRIEVAL_TOOLS:
            return
        self.retrieval_executed += 1
        self.executed_result_hashes.add(result_hash)
        ch = channel_of(tool_name)
        q = extract_query_text(args)
        if q:
            self.executed_queries.setdefault(ch, []).append(q[:120])
        # NEW_INFORMATION_GAIN 机械口径: empty（空命中）/ repeat（同 hash）= 无新信息
        self.last_no_new_info = info_gain in ("empty", "repeat")

    def record_blocked(self, tool_name, code):
        self.blocked.append({"tool": tool_name, "code": code,
                             "ts": time.strftime("%Y-%m-%d %H:%M:%S")})

    def record_round_usage(self, round_index, input_tokens=None, output_tokens=None,
                           tool_chars_added=0):
        self.context_discipline["rounds"].append({
            "round": round_index,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "tool_chars_added": int(tool_chars_added or 0)})
        if len(self.context_discipline["rounds"]) > 64:   # 有界（防长会话膨胀）
            self.context_discipline["rounds"] = self.context_discipline["rounds"][-64:]

    def record_compaction(self, chars_saved):
        self.context_discipline["tool_messages_compacted"] += 1
        self.context_discipline["compacted_chars_saved"] += int(chars_saved or 0)

    def _soft_limit(self):
        if self.active_class is None:
            return 0
        return self.cfg.get(self.active_class, 0) + self.extension_units

    def snapshot(self):
        total_input = sum(r.get("input_tokens") or 0 for r in self.context_discipline["rounds"])
        total_output = sum(r.get("output_tokens") or 0 for r in self.context_discipline["rounds"])
        return {
            "active_class": self.active_class,
            "evidence_gap": self.evidence_gap,
            "gap_filled": self.gap_filled,
            "declarations": list(self.declarations),
            "extensions": list(self.extensions),
            "extension_units": self.extension_units,
            "retrieval_executed": self.retrieval_executed,
            "soft_limit": self._soft_limit(),
            "soft_budget_base": self.cfg.get(self.active_class) if self.active_class else None,
            "blocked_calls": list(self.blocked),
            "blocked_total": len(self.blocked),
            "blocked_codes": sorted({b["code"] for b in self.blocked}),
            "no_new_information_pending": self.last_no_new_info,
            "budgets_cfg": dict(self.cfg),
            "similar_query_threshold": SIMILAR_QUERY_THRESHOLD,
            "context_discipline": dict(self.context_discipline),
            "token_usage": {"input_tokens": total_input, "output_tokens": total_output,
                            "total_tokens": total_input + total_output},
            "policy": "O10_R1_RESEARCH_DISCIPLINE",
        }


# ═══════════════════════════════════════════════════════
# declare_research_need 工具 schema（引擎注入 general 工具集;
# 实际登记在 tools_node 拦截完成——此 executor 只是占位, 不会被走到）
# ═══════════════════════════════════════════════════════
DECLARE_TOOL_DESCRIPTION = (
    "研究需求登记（每次检索前必用）: 登记本次请求的 RESEARCH_NEED 类别与 EVIDENCE_GAP。"
    "NONE=概念解释/普通推理/日常哲学（不检索, 预算0）; PRIMARY=需精确引文/出处核验/原典解读（预算3）; "
    "SCHOLARLY=用户明确要求学界研究/论文/争议综述（预算4）; WEB=需网络事实补充（预算3）; "
    "MIXED=多通道证据（预算6）。可与本轮检索工具同批宣告（先 declare 后检索）。"
    "证据缺口已补齐时传 gap_filled=true 立即收口检索。"
    "超出 soft 预算需同时传 budget_extension_reason 与 unresolved_evidence_gap 申请延展。")

DECLARE_TOOL_PARAMETERS = {
    "type": "object",
    "properties": {
        "research_need": {"type": "string",
                          "description": "NONE/PRIMARY/SCHOLARLY/WEB/MIXED"},
        "evidence_gap": {"type": "string",
                         "description": "一句话: 本次要补的具体证据缺口（如'《理想国》洞穴喻原文措辞'）; 非 NONE 时必填且需具体化"},
        "source_dependent": {"type": "boolean",
                             "description": "非 NONE 类别必须 true: 回答的正确性确实依赖特定文献/出处（只为了'更扎实'则应改用 NONE）"},
        "gap_filled": {"type": "boolean",
                       "description": "证据缺口已补齐 → true（立即机械收口检索, 之后综合作答）"},
        "budget_extension_reason": {"type": "string",
                                    "description": "预算延展申请: 为什么已取得的证据不足以收口"},
        "unresolved_evidence_gap": {"type": "string",
                                    "description": "预算延展申请: 还缺哪个具体证据（二者齐备才延展）"},
    },
    "required": ["research_need"],
}

def declare_tool_stub(_args=None):
    """占位 executor（真实登记在 tools_node 拦截层; 若意外走到, 返回中性确认）"""
    return {"ok": True, "status": "DECLARED_BY_RUNTIME_INTERCEPT"}
