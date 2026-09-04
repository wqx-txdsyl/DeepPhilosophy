# -*- coding: utf-8 -*-
"""Agent Runtime Reliability（Phase A, 2026-08-30; O4 Cognitive Layer Collapse 后瘦身）——
tool loop 机械治理单一真源

O4 后本模块只保留两类东西（Shadow cognition 已删除——runtime 不再判断"证据是否充分/
该不该停/义务是否满足"; 这些判断全部归还 Main Agent）:

  1. 机械可靠性核心（O4 §13 Deterministic Core, 全部保留）:
     ToolLoopTrace       单轮 invocation 观测: conversation/message/agent/invocation id、
                         工具名、归一化参数+hash、call index、时长、成败、结果摘要/hash、
                         evidence 数、model retry、总时长 → JSONL
                         （禁止记录原始 chain-of-thought——只有运行轨迹字段与简短 rationale）
     DuplicateGuard      同 turn 内 same tool + effectively same args → 复用已有结果
                         （仅确定性只读检索工具; 生成类/交互类豁免; 失败后重试放行;
                           参数实质变化/范围变化自动放行）
     ToolBudget          有界 per-turn 硬资源预算（hard → 终止工具循环 → graceful
                         answer completion）; 区分 useful / retry / duplicate / no-gain
                         计数（纯遥测, snapshot 输出, 无任何控制分支）
     错误分类            模型 API 错误可恢复性判定 + agent_node 有限重试（引擎接线）;
                         重试耗尽 → ModelCallError（引擎 graceful completion）
     RECURSION_LIMIT     graph 步数兜底
  2. ExecutionFactLedger（ObligationLedger 瘦身后的纯事实登记器）:
     只登记已发生的检索/阅读事实（读了哪些章节 / 是否读到主文本 / 是否逐字命中 /
     search-read 执行计数）——不做任何准入拒绝、配额、义务满足判定。

已删除（O4, CONTROL_EFFECT=0 且无独立数据价值）:
  soft 预算提示 / no_gain warn+force / sufficiency 期望与收敛 / 检索准入（admission）/
  查询族判重 / 义务满足总闸 / RECOVERY_* 第二 writer 文案 / RetrievalState 语义增益统计。

────────────────────────────────────────────────────────────────────
预算取值依据（agent_stats.jsonl 665 条真实记录, 2026-08-06 ~ 08-30）:
  - 成功回合中位工具数 0-2; 复杂回合 8-12 次常见, 最高 26 次（成功完成）;
  - hard_total=24 / hard_retrieval=20: 高于观测成功区间, 只拦截真正失控的长尾。
    全部可用环境变量覆盖（AGENT_HARD_TOTAL 等）, 引擎内不散落 magic numbers。
"""
import hashlib
import json
import os
import re
import time
import uuid
from pathlib import Path

BASE = Path(__file__).resolve().parent          # backend/
TRACE_FILE = BASE / "data" / "agent_loop_trace.jsonl"

# ═══════════════════════════════════════════════════════
# 配置（env 可覆盖; 引擎从本模块 import, 不允许就地写死）
# ═══════════════════════════════════════════════════════
def _env_int(name, default):
    try:
        return int(os.environ.get(name, "") or default)
    except (TypeError, ValueError):
        return default

TOOL_BUDGET = {
    "hard_retrieval": _env_int("AGENT_HARD_RETRIEVAL", 20),
    "hard_total": _env_int("AGENT_HARD_TOTAL", 24),
}
MODEL_RETRY = {
    "attempts": _env_int("AGENT_MODEL_RETRY_ATTEMPTS", 2),   # 首次失败后的额外重试次数
    "backoff_seconds": [1.5, 4.0],                            # 指数间隔（末次失败后不再等待）
}
TOOL_RETRY = {"attempts": _env_int("AGENT_TOOL_RETRY_ATTEMPTS", 1)}   # 工具失败重试（原行为收编为配置）
TOOL_TIMEOUT = _env_int("AGENT_TOOL_TIMEOUT", 90)
RECURSION_LIMIT = _env_int("AGENT_RECURSION_LIMIT", 60)       # graph 步数兜底（≈29 轮工具）

# A4: 可恢复错误判定（对异常文本匹配, 覆盖 openai SDK/httpx/langchain 各层措辞;
#     未命中的错误一律视为不可恢复——直接走 graceful completion, 不浪费重试）
_RETRYABLE_ERR_RE = re.compile(
    r"timeout|timed out|connection|peer closed|incomplete|reset by peer|broken pipe|"
    r"eof occurred|429|rate.?limit|overloaded|50[0234]|internal server|bad gateway|"
    r"service unavailable|server disconnected|temporarily", re.I)
_FATAL_MARKER_RE = re.compile(
    r"40[12]|authenticat|authorization|balance|invalid api key|"
    r"maximum context|context length|invalid request|bad request", re.I)

def classify_model_error(exc):
    """模型 API 异常 → 'retryable' | 'fatal'（A4; 不可恢复不重试）"""
    text = str(exc or "")
    if _FATAL_MARKER_RE.search(text):
        return "fatal"
    if _RETRYABLE_ERR_RE.search(text):
        return "retryable"
    return "fatal"

class ModelCallError(Exception):
    """agent_node LLM 调用在重试预算耗尽后仍失败（触发 graceful completion）"""

# ═══════════════════════════════════════════════════════
# A2 参数归一化与指纹
# ═══════════════════════════════════════════════════════
# 结果"数量/范围"参数: 只改取回条数, 不改变检索对象本身（scope 变体, 放行执行但标记）
SCOPE_PARAMS = {"limit", "top_k", "k", "count", "max_results", "num"}

# 只读检索工具白名单——同参数重复调用可安全复用结果。
# 生成类/交互类（write_essay/generate_image/philosopher_debate/thought_experiment/
# school_arena/agent_council/confrontation/role_play/socratic_tutor/life_coach/
# advisor_council/essay_outline/dialectic/paper_review/profile/conceptual_map 等）
# 同参数重调是合法交互（继续/下一轮/再来一张）, 一律豁免, 绝不拦截。
REUSE_SAFE_TOOLS = {
    "search_books", "get_chapter", "get_book_detail", "query_graph", "get_philosopher",
    "get_school", "list_books", "query_database", "concept_trace", "websearch",
    "philosopher_memory", "philosopher_quote", "philosopher_corpus", "philosopher_graph",
    "philosopher_concepts", "philosopher_user", "philosopher_style", "philosopher_period",
}

def normalize_args(args):
    """归一化工具参数: 去空白噪声/空值/浮点整型化/键排序（A2 语 义 等价判定基础）"""
    out = {}
    for k in sorted(args or {}):
        v = (args or {})[k]
        if v is None or v == "":
            continue
        if isinstance(v, str):
            v = re.sub(r"\s+", " ", v).strip()
            if not v:
                continue
        elif isinstance(v, float) and v.is_integer():
            v = int(v)
        out[k] = v
    return out

def _fp(payload):
    return hashlib.sha1(json.dumps(payload, ensure_ascii=False, sort_keys=True)
                        .encode("utf-8")).hexdigest()[:16]

def call_fingerprint(tool, args):
    """(tool, 归一化参数) → 稳定指纹; core_fingerprint 剥离 scope 参数（范围变体判定）"""
    norm = normalize_args(args)
    full = _fp({"tool": tool, "args": norm})
    core = _fp({"tool": tool, "args": {k: v for k, v in norm.items() if k not in SCOPE_PARAMS}})
    return full, core

def result_hash(result):
    """结果稳定 hash（information gain 判定: 同 hash = 无新增信息）"""
    try:
        return _fp({"r": result if isinstance(result, (dict, list)) else str(result)})
    except (TypeError, ValueError):
        return _fp({"r": str(result)})

_EMPTY_KEYS = ("results", "echoes", "hits", "quotes", "memories", "concepts",
               "entities", "items", "events")

def result_is_empty(res):
    """检索类结果是否为空命中（无新增信息的可靠信号之一）"""
    if not isinstance(res, dict):
        return False
    for k in _EMPTY_KEYS:
        v = res.get(k)
        if isinstance(v, list):
            return len(v) == 0
    return False

# ═══════════════════════════════════════════════════════
# A2 DuplicateGuard
# ═══════════════════════════════════════════════════════
class DuplicateGuard:
    """同 turn 内重复调用防护（生命周期 = 单次 invocation）

    决策规则（纯机械, 与证据充分性无关）:
      - 同 (tool, 完整指纹) 此前成功 且 工具只读 → reuse（复用已有结果, 不再执行）
      - 同 (tool, 完整指纹) 此前失败 → execute（retry_after_fail, 重试合理）
      - 剥离 scope 参数后核心指纹相同（如仅 limit 不同）且工具只读 → execute 但标记
        scope_variant（放行——"明确需要不同证据范围"合法）
      - 其余（参数实质变化/过滤器变化/period 变化 → 指纹必然不同）→ execute
    """

    def __init__(self):
        self._success = {}        # full_fp -> result（只读工具）
        self._failed = set()      # full_fp（失败后允许重试）
        self._core_seen = set()   # core_fp（成功执行过的核心指纹）

    def decide(self, tool, args):
        full, core = call_fingerprint(tool, args)
        if tool in REUSE_SAFE_TOOLS:
            if full in self._success:
                return {"action": "reuse", "cls": "duplicate",
                        "reason": "同工具同参数本轮已成功调用, 复用已有结果", "prev": self._success[full]}
            if full in self._failed:
                return {"action": "execute", "cls": "retry_after_fail",
                        "reason": "上次调用失败, 重试合理"}
            if core in self._core_seen:
                return {"action": "execute", "cls": "scope_variant",
                        "reason": "检索对象相同但范围参数不同（合法变体）"}
        return {"action": "execute", "cls": "unique", "reason": ""}

    def record(self, tool, args, ok, result):
        full, core = call_fingerprint(tool, args)
        if ok:
            if tool in REUSE_SAFE_TOOLS:
                self._success[full] = result
                self._core_seen.add(core)
            self._failed.discard(full)
        else:
            self._failed.add(full)
            self._success.pop(full, None)

# ═══════════════════════════════════════════════════════
# A3 ToolBudget（O4: 只剩硬资源上限 + 遥测计数）
# ═══════════════════════════════════════════════════════
class ToolBudget:
    """per-turn 工具预算（生命周期 = 单次 invocation; 数值来自 TOOL_BUDGET 配置）

    分类口径（纯遥测——这些计数不触发任何控制分支）:
      useful          新指纹且执行成功
      retry           失败后的重试（跨轮; 轮内重试计入工具自身 attempts, 不重复计数）
      duplicate       同参数重复调用（已被复用替代, 未执行, 不占执行预算）
      no_gain         执行成功但结果为空命中（无新增信息）
    hard 达标 → 引擎终止工具循环, 进入 graceful answer completion（唯一保留的停止机制）。
    """

    def __init__(self, retrieval_tools=frozenset(), cfg=None):
        self.cfg = dict(TOOL_BUDGET if cfg is None else cfg)
        self.retrieval_tools = set(retrieval_tools)
        self.useful = 0
        self.retry = 0
        self.inner_retries = 0   # 轮内自动重试次数（工具执行器自愈, 成功后不计入 retry 类）
        self.duplicate_reused = 0
        self.no_gain = 0
        self.total_executed = 0
        self.retrieval_executed = 0

    def count(self, tool, cls, executed, info_gain=""):
        if cls == "duplicate":
            self.duplicate_reused += 1          # 复用: 未执行, 不占执行预算
            return
        if not executed:
            return
        self.total_executed += 1
        if tool in self.retrieval_tools:
            self.retrieval_executed += 1
        if cls == "retry_after_fail":
            self.retry += 1
        elif info_gain in ("repeat", "empty"):
            self.no_gain += 1
        else:
            self.useful += 1

    def hard_reached(self):
        return (self.total_executed >= self.cfg["hard_total"]
                or self.retrieval_executed >= self.cfg["hard_retrieval"])

    def snapshot(self):
        return {"useful": self.useful, "retry": self.retry,
                "inner_retries": self.inner_retries,
                "duplicate_reused": self.duplicate_reused, "no_gain": self.no_gain,
                "total_executed": self.total_executed,
                "retrieval_executed": self.retrieval_executed,
                "hard": self.hard_reached(),
                "cfg": dict(self.cfg)}

# ═══════════════════════════════════════════════════════
# A1 ToolLoopTrace
# ═══════════════════════════════════════════════════════
class ToolLoopTrace:
    """单轮 invocation 运行轨迹（JSONL: 每工具调用一行 + 每轮汇总一行）

    明确不记录: 原始 chain-of-thought / reasoning_content / 思考流文本。
    rationale 仅限引擎已有的简短工具标签（≤40 字）。写盘失败静默跳过, 绝不影响主流程。
    """

    def __init__(self, conversation_id, message_id, agent_id, question_chars=0):
        self.invocation_id = uuid.uuid4().hex[:12]
        self.conversation_id = conversation_id or ""
        self.message_id = message_id or ""
        self.agent_id = agent_id or "general"
        self.question_chars = int(question_chars or 0)
        self.calls = []
        self.phases = []   # O1: 机械 timing observability（llm/tool/validator 阶段时长）
        self.model_retries = 0
        self._started = time.time()

    def record_call(self, call_index, tool, args, duration_ms, success, error,
                    result_summary, rh, budget_cls, info_gain, evidence_items,
                    executed=True, thought="", initiated_by="main_agent",
                    decision_group=None, tool_call_id=None):
        rec = {
            "type": "call", "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
            "conversation_id": self.conversation_id, "message_id": self.message_id,
            "agent_id": self.agent_id, "invocation_id": self.invocation_id,
            "call_index": call_index, "tool": tool,
            "args_normalized": normalize_args(args), "args_hash": call_fingerprint(tool, args)[0],
            # O1 provenance: 谁发起? main_agent=模型宣告 / runtime_mechanical=引擎机械动作 /
            # tool_internal=工具内部实现细节（引擎层不再产生认知性代执行）
            "initiated_by": initiated_by, "decision_group": decision_group,
            "tool_call_id": tool_call_id,
            "executed": bool(executed), "duration_ms": round(duration_ms or 0, 1),
            "success": bool(success), "error": (str(error)[:160] if error else None),
            "result_hash": rh, "result_summary": (result_summary or "")[:200],
            "budget_class": budget_cls, "info_gain": info_gain,
            "evidence_items": int(evidence_items or 0),
            "rationale": (thought or "")[:40],
        }
        self.calls.append(rec)
        _trace_write(rec)

    def record_phase(self, phase, t_start, **extra):
        """O1: 机械阶段计时（llm_invocation / validator_* 等）。duration_ms 记录, 不展示思考。"""
        rec = {"type": "phase", "phase": phase,
               "duration_ms": round((time.time() - t_start) * 1000, 1), **extra}
        self.phases.append(rec)
        _trace_write(rec)
        return rec

    # ── O1: Main Agent decision group（因果归属: 每次模型 invocation = 一组工具决定）──
    def begin_group(self):
        """agent_node 在每次 Main Agent LLM invocation 前调用 → 组号 +1, 返回组标识"""
        self._groups = getattr(self, "_groups", 0) + 1
        self._current_group = f"inv-{self._groups}"
        return self._current_group

    @property
    def current_group(self):
        return getattr(self, "_current_group", "inv-1")

    def finalize(self, total_duration_s, error=None, answer_chars=0, evidence_ids=None,
                 budget_snapshot=None):
        rec = {
            "type": "turn", "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
            "conversation_id": self.conversation_id, "message_id": self.message_id,
            "agent_id": self.agent_id, "invocation_id": self.invocation_id,
            "question_chars": self.question_chars,
            "total_tool_calls": len(self.calls),
            "executed_tool_calls": sum(1 for c in self.calls if c["executed"]),
            "duplicates_reused": sum(1 for c in self.calls if c["budget_class"] == "duplicate"),
            "no_gain_calls": sum(1 for c in self.calls if c["info_gain"] in ("repeat", "empty")),
            "model_retry_count": self.model_retries,
            "total_turn_duration_s": round(total_duration_s or 0, 1),
            "error": (str(error)[:200] if error else None),
            "answer_chars": int(answer_chars or 0),
            "evidence_ids": list(evidence_ids or []),
            "budget": budget_snapshot or {},
        }
        _trace_write(rec)
        return rec

def _trace_write(rec):
    try:
        TRACE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TRACE_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass

# ═══════════════════════════════════════════════════════
# A4 模型重试（引擎 agent_node 接线用）
# ═══════════════════════════════════════════════════════
def invoke_llm_with_retry(invoke_fn, msgs, on_retry=None):
    """LLM 调用 + 有限重试（可恢复错误才重试; 耗尽抛 ModelCallError）
    返回 (resp, retry_count)。on_retry(attempt, exc) 供观测回调。"""
    attempts = MODEL_RETRY["attempts"]
    last = None
    for attempt in range(attempts + 1):
        try:
            return invoke_fn(msgs), attempt
        except Exception as e:                      # noqa: BLE001 —— 分类后决定重试
            last = e
            if attempt >= attempts or classify_model_error(e) != "retryable":
                break
            if on_retry:
                try:
                    on_retry(attempt, e)
                except Exception:
                    pass
            time.sleep(MODEL_RETRY["backoff_seconds"][min(attempt, len(MODEL_RETRY["backoff_seconds"]) - 1)])
    raise ModelCallError(str(last or "model call failed"))

# ═══════════════════════════════════════════════════════
# 终止条件（显式枚举, 引擎 should_continue/agent_node 接线; O4 后无语义终止源）
# ═══════════════════════════════════════════════════════
# Agent turn 结束条件（任一满足即收敛; 停止权威 = Main Agent 自主宣告 + 机械兜底）:
#   T1 模型不再宣告工具调用（Main Agent 自主判定证据已足）        → end（既有）
#   T2 生成类成品工具已返回完整结果（系统提示铁律 5' 引导, 不在本层强制）
#   T3 hard 预算达标 → 终止工具循环 → graceful answer completion    → 强制（A3）
#   T4 强制回答后模型仍宣告工具调用 → 补跑一轮后截断（既有 forced 机制）
#   T5 graph recursion_limit 兜底                                  → 异常→graceful（引擎）
#   T6 模型/工具错误重试耗尽                                       → graceful（A4, 引擎）

# 硬预算指令（机械资源约束文案——只表达资源上限, 绝不暗含"证据已充分"）
HARD_BUDGET_DIRECTIVE = ("（工具预算已达上限。现在进入最终回答: 禁止调用任何工具, "
                         "禁止输出任何 XML/工具调用标记（如 <invoke>、{TOOL:}）。"
                         "请直接基于已取得的检索结果输出最终回答正文, 引用标注【《书名》· 章节】; "
                         "材料不足的部分明确说明尚未核验。只输出回答文本。）")


# ═══════════════════════════════════════════════════════
# O4: ExecutionFactLedger（原 ObligationLedger 瘦身）——纯事实登记器
# ═══════════════════════════════════════════════════════
# 只登记已发生的执行事实（Evidence Store 观测元数据）:
#   read_chapters           get_chapter 成功读取过的 (book_id, chapter_idx)
#   primary_text_read       本次是否实际读到过章节全文（出处核验的最低完成线;
#                           只能由 get_chapter 的全文置位——检索片段/书目永远不算）
#   exact_quote_verified    待核验表述（term）在已读原文中逐字命中（简单精确匹配/归一包含）
#   source_candidate_found  search/meta 类命中过非空结果（只是定位线索 MEMORY_HINT）
#   search_execs/read_execs 执行计数（遥测）
# 无 admit / 无配额 / 无义务满足判定 / 无查询族判重——是否继续检索、何时收口,
# 全部由 Main Agent 自主决定。
def _QUOTE_NORM(s):
    """逐字比对的归一口径——只保留文字与数字, 剥全部标点/空白/括号引号。
    归一后必须『连续包含』才算逐字命中（拼接/跳字在此即失败）。"""
    return re.sub(r"[^\w\u4e00-\u9fff]+", "", s or "")


class ObligationLedger:
    """O4 瘦身: invocation 级执行事实台账（生命周期 = 单次请求; 纯登记, 零控制效果）

    record(tool, args, ok, result)
      → 执行后登记事实: 已读章节 / 主文本已读 / 逐字命中 / 定位线索命中 / 执行计数。
    snapshot()
      → 这些事实字段 + search/read 计数（随 done 输出供审计; validator 只消费
        primary_text_read——VERIFY_LATER_MISSTATEMENT 的唯一触发依据）。
    """

    def __init__(self, plan=None, term=None):
        self.term = term or ""       # 待核验表述（verif_box 术语核验共用; 无则为空）
        self.read_chapters = set()   # (book_id, chapter_idx) 已成功读取
        self.search_execs = 0
        self.read_execs = 0
        # 出处核验事实分层: LOCATED（定位线索）≠ READ（读到全文）≠ QUOTE_VERIFIED（逐字命中）
        self.source_candidate_found = False
        self.primary_text_read = False
        self.exact_quote_verified = False

    def record(self, tool, args, ok, result):
        """执行后登记事实（成败都登记——失败是事实; 但只有成功读取才置位 READ 状态）"""
        if tool == "get_chapter":
            if not ok:
                return
            a = args or {}
            key = (str(a.get("book_id") or ""), a.get("chapter_idx") if isinstance(a.get("chapter_idx"), int) else -1)
            self.read_execs += 1
            self.read_chapters.add(key)
            # PRIMARY_TEXT_READ 只有 get_chapter 全文能置位——MEMORY_HINT
            # （检索片段/书目/记忆）永远不算。
            self.primary_text_read = True
            if not self.exact_quote_verified and self.term:
                text = str((result or {}).get("text") or "")
                if text:
                    if self.term in text:
                        self.exact_quote_verified = True
                    else:
                        tn = _QUOTE_NORM(self.term)
                        if len(tn) >= 4 and tn in _QUOTE_NORM(text):
                            self.exact_quote_verified = True
            return
        # search/meta 类: 命中非空结果 → SOURCE_CANDIDATE_FOUND（只是定位线索）
        self.search_execs += 1
        if not self.source_candidate_found and isinstance(result, dict) \
                and not result.get("error"):
            for k in ("results", "books", "items", "hits", "records"):
                v = result.get(k)
                if isinstance(v, list) and v:
                    self.source_candidate_found = True
                    break

    def snapshot(self):
        return {
            "read_chapters": sorted(f"{b}#{c}" for b, c in self.read_chapters),
            "search_execs": self.search_execs,
            "read_execs": self.read_execs,
            # 出处核验事实分层（审计/回归断言用; primary_text_read 为 validator 唯一消费项）
            "verification_states": {
                "source_candidate_found": self.source_candidate_found,
                "primary_text_read": self.primary_text_read,
                "exact_quote_verified": self.exact_quote_verified,
            },
        }
