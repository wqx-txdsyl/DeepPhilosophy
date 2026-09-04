# -*- coding: utf-8 -*-
"""Agent Runtime Reliability（Phase A, 2026-08-30）——tool loop 治理单一真源

覆盖 A1-A5 五个子项的配置与纯规则实现（不联网、不调 LLM、不改 Persona/Memory/Answer 风格）:

  A1 ToolLoopTrace       单轮 invocation 观测: conversation/message/agent/invocation id、
                         工具名、归一化参数+hash、call index、时长、成败、结果摘要/hash、
                         evidence 数、information gain、model retry、总时长 → JSONL
                         （禁止记录原始 chain-of-thought——只有运行轨迹字段与简短 rationale）
  A2 DuplicateGuard      同 turn 内 same tool + effectively same args → 复用已有结果
                         （仅确定性只读检索工具; 生成类/交互类豁免; 失败后重试放行;
                           参数实质变化/范围变化/过滤器变化自动放行）
  A3 ToolBudget          有界 per-turn 预算: soft（提醒优先用已有 evidence）/
                         hard（终止工具循环 → graceful answer completion）;
                         区分 useful / retry / duplicate / no-information-gain
  A4 错误分类            模型 API 错误可恢复性判定 + agent_node 有限重试（引擎接线）;
                         重试耗尽 → 用已取得 evidence graceful completion（引擎接线）
  A5 终止条件            显式枚举 Agent turn 结束条件; 连续无信息增益轮 → 提醒/强制收口

────────────────────────────────────────────────────────────────────
根因记录（ROOT_CAUSE_13_CALLS）——RAM audit 第 9 轮"约 13 次工具调用后以模型侧
error 结束":

  agent_stats.jsonl 2026-08-30 11:34:46（nietzsche, 72.8s）:
  "peer closed connection without sending complete message body (incomplete chunked read)"

  即 DeepSeek 流式响应在长回合（约 13 次工具调用、70s+ 的多轮 LLM 流式请求）中被上游
  中断。三个叠加因素:
  1. openai SDK / ChatDeepSeek 不重试"已开始输出的"流式请求（连接建立阶段的错误才重试）;
  2. 引擎 agent_node 的 LLM 调用无应用层重试;
  3. stream_agent 外层 except 直接以 error 事件终止整轮——已完成的 13 次工具调用所
     取得的 evidence 全部丢弃（done/citations 不再发出）。
  修复（引擎接线）: agent_node 有限重试（可恢复错误分类 + 退避）→ 耗尽后 graceful
  completion（用已取得 evidence 直接完成回答, 明确降低置信度）, 证据契约/引用面板照常。
  次要根因（同文件 stats）: ① except 路径把工具调用数硬编码记 0（观测盲区, 已修）;
  ② AIMessage.tool_call_chunks 未防御（2026-08-30 10:12 三连错误, 已加 getattr 防御）。
  不是"模型调了 13 次工具触发上限"——recursion_limit 60 / 检索硬上限均未触达, 不存在
  因调用次数本身导致的模型侧报错; 降 max calls 是掩盖, 不采用。
────────────────────────────────────────────────────────────────────
预算取值依据（agent_stats.jsonl 665 条真实记录, 2026-08-06 ~ 08-30）:
  - 成功回合中位工具数 0-2（简单事实/解释类几乎不检索）;
  - 复杂跨主题比较/哲学家人格回合 8-12 次常见, 最高 26 次（08-29 15:46, 成功完成）;
  - 无上限时期出现过 26/21/18 次的长尾——其中确有同参数重复检索（浪费 token/时延）。
  → soft_total=10 / soft_retrieval=8（覆盖绝大多数复杂回合, 之后开始提醒收敛）;
    hard_total=24 / hard_retrieval=20（高于观测到的成功复杂回合 21-26 区间下沿,
    只拦截真正失控的长尾; 连续无增益轮守卫会更早触发, 不依赖硬上限兜底）。
    全部可用环境变量覆盖（AGENT_SOFT_TOTAL 等）, 引擎内不散落 magic numbers。
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
# A3 配置（env 可覆盖; 引擎从本模块 import, 不允许就地写死）
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

TOOL_BUDGET = {
    "soft_retrieval": _env_int("AGENT_SOFT_RETRIEVAL", 8),
    "soft_total": _env_int("AGENT_SOFT_TOTAL", 10),
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

# A5: 连续"无信息增益"检索轮 → 提醒 / 强制收口（比总数预算更早拦截原地打转）
NO_GAIN_WARN_STREAK = _env_int("AGENT_NO_GAIN_WARN_STREAK", 2)
NO_GAIN_FORCE_STREAK = _env_int("AGENT_NO_GAIN_FORCE_STREAK", 3)

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

    决策规则:
      - 同 (tool, 完整指纹) 此前成功 且 工具只读 → reuse（复用已有结果, 不再执行）
      - 同 (tool, 完整指纹) 此前失败 → execute（retry_after_fail, 重试合理）
      - 剥离 scope 参数后核心指纹相同（如仅 limit 不同）且工具只读 → execute 但标记
        scope_variant（放行——"明确需要不同证据范围"合法; 预算统计上施加收敛压力）
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
# A3 ToolBudget
# ═══════════════════════════════════════════════════════
class ToolBudget:
    """per-turn 工具预算（生命周期 = 单次 invocation; 数值来自 TOOL_BUDGET 配置）

    分类口径:
      useful          新指纹且执行成功
      retry           失败后的重试（跨轮; 轮内重试计入工具自身 attempts, 不重复计数）
      duplicate       同参数重复调用（已被复用替代, 未执行, 不占执行预算）
      no_gain         执行成功但结果与此前完全相同或空命中（无新增信息）
    soft 达标 → 引擎注入"优先用已有 evidence 作答"提醒（不强制）;
    hard 达标 → 引擎终止工具循环, 进入 graceful answer completion。
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
        elif info_gain in ("repeat", "empty", "low_gain"):
            self.no_gain += 1   # low_gain: 语义重复（查询改写但结果高度重合, B1）
        else:
            self.useful += 1

    def soft_reached(self):
        return (self.total_executed >= self.cfg["soft_total"]
                or self.retrieval_executed >= self.cfg["soft_retrieval"])

    def hard_reached(self):
        return (self.total_executed >= self.cfg["hard_total"]
                or self.retrieval_executed >= self.cfg["hard_retrieval"])

    def snapshot(self):
        return {"useful": self.useful, "retry": self.retry,
                "inner_retries": self.inner_retries,
                "duplicate_reused": self.duplicate_reused, "no_gain": self.no_gain,
                "total_executed": self.total_executed,
                "retrieval_executed": self.retrieval_executed,
                "soft": self.soft_reached(), "hard": self.hard_reached(),
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
# A5 终止条件（显式枚举, 引擎 should_continue/agent_node 接线）
# ═══════════════════════════════════════════════════════
# Agent turn 结束条件（任一满足即收敛, 前 4 项为"正常收口", 后 4 项为"保护性收口"）:
#   T1 模型不再宣告工具调用（已有足够 evidence / 义务满足）        → end（既有）
#   T2 soft 预算达标 → 提醒模型优先用已有 evidence 作答（模型自主停）→ 提醒（A3）
#   T3 后续调用预计无新增信息 → 连续无增益轮守卫                    → 提醒/强制（本模块）
#   T4 生成类成品工具已返回完整结果（系统提示铁律 5' 引导, 不在本层强制）
#   T5 hard 预算达标 → 终止工具循环 → graceful answer completion    → 强制（A3）
#   T6 强制回答后模型仍宣告工具调用 → 补跑一轮后截断（既有 forced 机制）
#   T7 graph recursion_limit 兜底                                  → 异常→graceful（引擎）
#   T8 模型/工具错误重试耗尽                                       → graceful（A4, 引擎）

def no_gain_verdict(streak):
    """连续无增益轮数 → 'none' | 'warn' | 'force'"""
    if streak >= NO_GAIN_FORCE_STREAK:
        return "force"
    if streak >= NO_GAIN_WARN_STREAK:
        return "warn"
    return "none"

# 引擎提示文案（集中于此, 避免散落; 均为约束性提醒, 不改变回答风格要求）
SOFT_BUDGET_HINT = ("（工具调用预算提示: 本轮已进行多次检索。请评估现有材料是否足以回答: "
                    "充分则停止检索直接作答; 确有必要再用新关键词补充检索, 但避免无意义重复。）")
HARD_BUDGET_DIRECTIVE = ("（工具预算已达上限。现在进入最终回答: 禁止调用任何工具, "
                         "禁止输出任何 XML/工具调用标记（如 <invoke>、{TOOL:}）。"
                         "请直接基于已取得的检索结果输出最终回答正文, 引用标注【《书名》· 章节】; "
                         "材料不足的部分明确说明尚未核验。只输出回答文本。）")
NO_GAIN_WARN_HINT = ("（提示: 最近几轮检索未带来新信息。请基于已有材料回答, "
                     "或换用实质不同的检索词/工具; 不要重复已有查询。）")
NO_GAIN_FORCE_DIRECTIVE = ("（连续多轮检索均无新增信息。现在进入最终回答: 禁止调用任何工具, "
                           "禁止输出任何工具调用标记。请直接基于已取得的检索结果输出最终回答, "
                           "材料不足处明确说明。只输出回答文本。）")

# ═══════════════════════════════════════════════════════
# B1: 检索语义状态与证据充分性（Patch 1, 2026-08-31）
#  invocation 级检索状态: 归一化查询/来源 ID/新证据计数/重叠率/相关证据/义务与充分性。
#  语义重复（query 改写但结果高度重合）→ low_gain; 充分性按复杂度期望收敛。
# ═══════════════════════════════════════════════════════
def _result_sources(tool, result):
    """检索结果 → 来源 ID 集合（去重）; 无来源返回空集"""
    out = set()
    if not isinstance(result, dict):
        return out
    if tool == "search_books":
        for it in result.get("results") or []:
            if not isinstance(it, dict) or not it.get("book_title"):
                continue
            cidx = it.get("chapter_idx")
            out.add((str(it.get("book_id") or ""), cidx if isinstance(cidx, int) else -1))
    elif tool == "get_chapter":
        bid = result.get("book_id")
        if bid:
            cidx = result.get("chapter_idx")
            out.add((str(bid), cidx if isinstance(cidx, int) else -1))
    elif tool in ("philosopher_corpus", "philosopher_quote", "philosopher_graph"):
        for e in (result.get("echoes") or result.get("quotes") or result.get("entities") or []):
            if isinstance(e, dict) and e.get("book"):
                out.add(("corpus:" + str(e.get("book")), str(e.get("chapter") or "")))
    return out


def _result_texts(result):
    """检索结果 → 文本拼接（相关证据判定用; 有界）"""
    if not isinstance(result, dict):
        return ""
    parts = []
    for it in result.get("results") or []:
        if isinstance(it, dict) and it.get("snippet"):
            parts.append(it["snippet"])
    if result.get("text"):
        parts.append(result["text"])
    for e in (result.get("echoes") or result.get("quotes") or []):
        if isinstance(e, dict):
            if e.get("text"):
                parts.append(e["text"])
            if e.get("snippet"):
                parts.append(e["snippet"])
    return "\n".join(parts)[:8000]


def _result_items(tool, result):
    """检索结果 → [(来源ID, 文本)]（相关证据判定用; 仅检索类工具）"""
    out = []
    if not isinstance(result, dict):
        return out
    if tool == "search_books":
        for it in result.get("results") or []:
            if isinstance(it, dict) and it.get("book_title") and it.get("snippet"):
                cidx = it.get("chapter_idx")
                out.append(((str(it.get("book_id") or ""), cidx if isinstance(cidx, int) else -1),
                            it["snippet"]))
    elif tool in ("philosopher_corpus", "philosopher_quote", "philosopher_graph"):
        for e in (result.get("echoes") or result.get("quotes") or []):
            if isinstance(e, dict) and e.get("book"):
                txt = e.get("text") or e.get("snippet") or ""
                if txt:
                    out.append((("corpus:" + str(e.get("book")), str(e.get("chapter") or "")), txt))
    return out


# 语义重复判据（B1）:
#   - 检索类工具: 未带来任何"新的、含问题关键术语的来源" → 对本问题无信息增益（low_gain）
#   - 完全无新来源 → low_gain
#   - 来源较多且重叠率 ≥0.6 且新增 ≤1（query 改写但结果高度重合）→ low_gain
#   - get_chapter 等阅读类工具豁免（每章全文都是新证据——正是逐字核验的途径）
_RELEVANCE_TOOLS = {"search_books", "philosopher_corpus", "philosopher_quote", "philosopher_graph", "websearch"}


class RetrievalState:
    """B1: invocation 级检索状态——语义重复判定 + 证据充分性统计

    register(tool, args, result, key_terms) 每次检索调用后登记:
      - 来源 ID 集合（去重）; 新增来源数 / 重叠率 → low_gain（语义重复）
      - 相关证据计数（含问题关键术语的来源数）
    """

    def __init__(self):
        self.seen_sources = set()
        self.relevant_ids = set()
        self.calls = []          # [{tool, query, n, new, overlap, low_gain}]
        self.total_new = 0
        self.last_round = []     # 本轮调用索引

    def _is_low_gain(self, tool, n, newn, overlap, new_relevant, key_terms):
        if n == 0:
            return False
        if tool in _RELEVANCE_TOOLS and key_terms and new_relevant == 0:
            return True
        if newn == 0:
            return True
        if n >= 4 and newn <= 1 and overlap >= 0.6:
            return True
        return False

    def register(self, tool, args, result, key_terms=()):
        srcs = _result_sources(tool, result)
        new = srcs - self.seen_sources
        self.seen_sources |= srcs
        n, newn = len(srcs), len(new)
        overlap = (n - newn) / n if n else 1.0
        # 相关新证据: 本次结果中、含问题关键术语、且此前未见过的来源
        new_relevant = 0
        if key_terms:
            for sid, txt in _result_items(tool, result):
                if sid in new and any(t and t in txt for t in key_terms):
                    self.relevant_ids.add(sid)
                    new_relevant += 1
        low_gain = self._is_low_gain(tool, n, newn, overlap, new_relevant, key_terms)
        q = str((args or {}).get("query") or "")[:60]
        rec = {"tool": tool, "query": q, "n": n, "new": newn, "new_relevant": new_relevant,
               "overlap": round(overlap, 2), "low_gain": low_gain}
        self.calls.append(rec)
        if newn:
            self.total_new += newn
        return rec

    def mark_round(self, start_idx):
        self.last_round = list(range(start_idx, len(self.calls)))

    def round_low_gain(self):
        idxs = [i for i in self.last_round if i < len(self.calls)]
        if not idxs:
            return False
        return all(self.calls[i]["low_gain"] for i in idxs)

    def round_any_low_gain(self):
        return any(self.calls[i]["low_gain"] for i in self.last_round if i < len(self.calls))

    def snapshot(self):
        return {
            "calls": list(self.calls),
            "total_new": self.total_new,
            "seen_sources": len(self.seen_sources),
            "relevant_sources": len(self.relevant_ids),
        }


# B1: 复杂度 → 工具期望预算（软期望, 非硬值; 达到期望后额外调用必须满足信息增益/未满足义务）
#   窄事实 1–3 / 一般解释 2–4 / 对比 3–6 / 深度综合 5–10
SUFFICIENCY_EXPECTATION = {
    "NARROW_FACTUAL": (1, 3),
    "NORMAL_EXPLANATION": (2, 4),
    "COMPARISON": (3, 6),
    "DEEP_SYNTHESIS": (5, 10),
}


def sufficiency_verdict(complexity, executed, round_all_low, relevant_sources, key_terms_met,
                        round_any_low=False):
    """B1: 证据充分性 → 'none' | 'force'

    规则（复杂度期望为准, 不是硬上限）:
      - 未达期望下沿 → none
      - 期望上沿附近的收口点 max(lo, hi-2)（≈ 期望上沿前的最后一个工具轮）→ force:
        达到后每次额外调用必须满足 NEW_INFORMATION_GAIN / UNSATISFIED_EVIDENCE_OBLIGATION,
        引擎侧收口——强制轮仍允许模型补跑其已宣告的关键调用（按轮内位置封顶 2 个检索,
        get_chapter 等阅读调用在强制轮内优先执行, 逐字核验不受影响）, 总数 ≈ hi..hi+2
      - 低增益提前收口（深度综合类除外——深问题允许试探性低增益轮）
      - 硬上限（hard budget）仍作为兜底, 非主要机制
    """
    lo, hi = SUFFICIENCY_EXPECTATION.get(complexity, (2, 4))
    if executed < lo:
        return "none"
    if executed >= max(lo, hi - 2):
        return "force"
    if complexity != "DEEP_SYNTHESIS" and executed >= lo \
            and (round_all_low or round_any_low):
        return "force"
    return "none"


SUFFICIENCY_WARN_HINT_ZH = (
    "（检索收敛提示: 本题属于{label}类问题, 检索已达期望范围且最近一轮未带来实质新信息。"
    "请评估现有材料是否足以作答: 足以则立即停止检索直接回答; 确有未解决的关键缺口"
    "（如核心概念的原典定位/逐字核验）才换用实质不同的检索词或工具补充, 并说明缺口是什么。）")
SUFFICIENCY_WARN_HINT_EN = (
    "(Retrieval convergence note: this is a {label} question; retrieval has reached the expected "
    "range and the last round brought no substantive new information. Judge whether the material "
    "suffices: if yes, stop searching and answer now; only if a real gap remains (e.g. locating the "
    "primary passage or verifying exact wording) try a substantially different query or tool, and "
    "state what the gap is.)")
SUFFICIENCY_FORCE_DIRECTIVE_ZH = (
    "（检索已充分: 本题属于{label}类问题, 检索已达期望上限且无实质新信息。现在进入最终回答: "
    "禁止调用任何工具, 禁止输出任何工具调用标记。直接基于已取得的检索结果输出最终回答, "
    "引用标注【《书名》· 章节】; 材料不足以支撑的关键主张必须明确说明未能核验。只输出回答文本。）")
SUFFICIENCY_FORCE_DIRECTIVE_EN = (
    "(Retrieval is sufficient: this is a {label} question; retrieval has reached the expected limit "
    "with no substantive new information. Enter the final answer now: do not call any tool, do not "
    "output any tool-call markers. Answer directly from the evidence already retrieved, citing "
    "【《Book》· chapter】; key claims the material cannot support must be explicitly marked "
    "unverified. Output only the answer text.)")


def sufficiency_hint(verdict, complexity, language="zh"):
    """sufficiency_verdict 结果 → 注入文案（warn/force; none 返回 None）"""
    from reasoning_plan import COMPLEXITY_LABEL_EN, COMPLEXITY_LABEL_ZH
    label = (COMPLEXITY_LABEL_EN if language == "en" else COMPLEXITY_LABEL_ZH).get(complexity, complexity)
    if verdict == "force":
        return (SUFFICIENCY_FORCE_DIRECTIVE_EN if language == "en"
                else SUFFICIENCY_FORCE_DIRECTIVE_ZH).format(label=label)
    if verdict == "warn":
        return (SUFFICIENCY_WARN_HINT_EN if language == "en"
                else SUFFICIENCY_WARN_HINT_ZH).format(label=label)
    return None
# ═══════════════════════════════════════════════════════
# Patch 1.1 (P1): Evidence Obligation Tracking —— 检索准入（admission）
# ═══════════════════════════════════════════════════════
# 问题形态（Final Gate）: 模型一次宣告一批 retrieval 后, 即使前面的结果已满足
# evidence obligation, 同批/后续同义改写检索仍继续执行（F01/F07/F12 budget FAIL;
# low_gain 25/63）。修复: 在真正执行 tool 前判定——
#   1) obligation 是否已 SATISFIED（核验意图下: 原文已定位且措辞证据已在手）
#   2) query_family 是否已有充分证据（同族已执行 / 同族曾低增益）
#   3) 是否预计产生新的 evidence class（重复取章/书目漫游不产生）
#   4) 是否只是同义改写继续搜（shingle 相似度判族）
# 无新义务 → cancel before execution（准入拒绝, 非 hard max_tools; 非随机概率）。
# 每个 retrieval 绑定: obligation_id(=义务语义键) / query_family / source_constraint。
def _q_shingles(q):
    """查询 → 2-字 shingle 集（同义改写判族基础; 剥空白/标点）"""
    t = re.sub(r"[\s，,。；;：:、？！?？()（）\"“”'‘’·《》【】]", "", q or "")
    return frozenset(t[i:i + 2] for i in range(len(t) - 1)) if len(t) >= 2 else frozenset([t]) if t else frozenset()


def _QUOTE_NORM(s):
    """T1.1-A/F: 逐字比对的归一口径——只保留文字与数字, 剥全部标点/空白/括号引号。
    归一后必须『连续包含』才算逐字命中（拼接/跳字在此即失败）。"""
    return re.sub(r"[^\w\u4e00-\u9fff]+", "", s or "")


def _jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


# 同族判定阈值: shingle Jaccard ≥ 0.45 视为同一 query_family（改写/变体）
QUERY_FAMILY_THRESHOLD = _env_float("AGENT_QUERY_FAMILY_THRESHOLD", 0.45)
# 同族最多执行次数（超过后族内不再准入——除非核验义务要求阅读新章节）
FAMILY_EXEC_LIMIT = _env_int("AGENT_FAMILY_EXEC_LIMIT", 2)
# 复杂度 → search 执行期望上限（窄事实 2 / 一般解释 4 / 对比 3 / 深度综合 6）
# Phase T: COMPARISON 收紧——compare_views 内部自带双方检索, search 类配额 3 次
#（含 compare_views 本身）即可覆盖; 手工多路对比检索是 QG2/Q08 超限根因
#（QG2 Patch 候选明确背书"比较类任务检索上限"）。配合 forced 轮阅读补跑上限（2）,
# 比较 Case 执行工具数机械 ≤5。
SEARCH_EXEC_LIMIT = {
    "NARROW_FACTUAL": _env_int("AGENT_SEARCH_LIMIT_NARROW", 2),
    "NORMAL_EXPLANATION": _env_int("AGENT_SEARCH_LIMIT_NORMAL", 4),
    "COMPARISON": _env_int("AGENT_SEARCH_LIMIT_COMPARISON", 3),
    "DEEP_SYNTHESIS": _env_int("AGENT_SEARCH_LIMIT_DEEP", 6),
}
# 总量包络（单次 invocation 检索类调用总和, 含 search/阅读/书目/meta/websearch）——
# 外层保底（义务/族规则做细粒度判定, 包络防长尾）; websearch 占包络（不同来源但同属
# 检索成本, 不计入会被连用超 Gate——真实回归: F02/F12 各连发 2 次 websearch）。
TOTAL_RETRIEVAL_LIMIT = {
    "NARROW_FACTUAL": _env_int("AGENT_TOTAL_NARROW", 3),
    "NORMAL_EXPLANATION": _env_int("AGENT_TOTAL_NORMAL", 5),
    "COMPARISON": _env_int("AGENT_TOTAL_COMPARISON", 3),
    "DEEP_SYNTHESIS": _env_int("AGENT_TOTAL_DEEP", 10),
}
VERIFICATION_TOTAL_LIMIT = _env_int("AGENT_TOTAL_VERIFICATION", 4)
# 强制收口轮: 最多补跑的未读章节阅读数（get_chapter 优先, 保逐字核验）; search 一律不准入
FORCED_READ_CAP = _env_int("AGENT_FORCED_READ_CAP", 2)
# websearch 独立预算（不同证据来源类; 防刷屏上限）
WEBSEARCH_CAP = _env_int("AGENT_WEBSEARCH_CAP", 2)
# 准入拒绝累计达该值 → 引擎注入强制收口（防"宣告→被拒→再宣告"空转循环——思考流卡住的根因）
ADMISSION_REJECT_FORCE = _env_int("AGENT_ADMISSION_REJECT_FORCE", 3)
# ── 核验路径（verification_intent 存在）分项配额（不用总量包络——真实事故复盘:
# 总包络会把"读原文"这个义务核心动作挤掉, 模型读不到原文又回到"未能逐字命中"）──
# search ≤2（定位原典足够） / read ≤2（独立配额——定位→阅读是核验义务动作, 不与 search 抢额度） /
# websearch ≤1（原典出处核验中上网是次要来源, 从严）
VERIFICATION_SEARCH_CAP = _env_int("AGENT_VERIF_SEARCH_CAP", 2)
VERIFICATION_READ_CAP = _env_int("AGENT_VERIF_READ_CAP", 2)
VERIFICATION_WEBCAP = _env_int("AGENT_VERIF_WEBCAP", 1)
VERIFICATION_META_CAP = _env_int("AGENT_VERIF_META_CAP", 1)   # 核验路径书目/详情类上限
# 核验路径强制收口轮的阅读补跑上限（1 章——F12 类 gate ≤5 的硬约束内保逐字核验）
VERIFICATION_FORCED_READ_CAP = _env_int("AGENT_VERIF_FORCED_READ_CAP", 1)
# 作者不明/集体署名（无法判定二手性时保留为可admissible）
_UNKNOWN_AUTHOR_RE = re.compile(r"^\s*(佚名|无名氏|匿名|unknown|佚)\s*$", re.I)


class ObligationLedger:
    """P1: invocation 级 evidence obligation 台账（生命周期 = 单次请求）

    admit(tool, args, complexity, forced)
      → (True, "") | (False, reason) —— 在真正执行 tool 前调用（含同批内按宣告顺序判定）。
    record(tool, args, ok, result)
      → 执行后登记: query_family 统计 / 已读章节 / 核验义务满足状态。
    """

    def __init__(self, plan=None, verification_intent=None):
        self.plan = plan or {}
        self.vi = verification_intent or (plan or {}).get("verification_intent") or None
        self._families = {}       # fam_id -> {"execs": int, "low_gain": int, "relevant": int}
        self._queries = []        # [(shingles, fam_id)]  供改写判族
        self.read_chapters = set()   # (book_id, chapter_idx) 已成功读取
        self._pending_reads = set()  # 同批内已准入、尚无结果的读取（防同批重复取章）
        self.search_execs = 0
        self.read_execs = 0
        self.meta_execs = 0          # 书目/详情/meta 类（get_philosopher/query_database 等）
        self.websearch_execs = 0     # websearch 独立预算（不占检索包络）
        self.rejected = 0            # 准入拒绝累计（引擎消费: 超阈值强制收口, 防空转循环）
        self.forced_reads = 0        # 强制轮已补跑的阅读数
        self.obligations_satisfied = False   # 核验义务 O1(定位原文)+O2(措辞证据) 已满足
        # ── Phase T.1 (T1.1-A): 出处核验状态分层——LOCATED ≠ READ ≠ QUOTE_VERIFIED ──
        # SOURCE_CANDIDATE_FOUND: search/meta 命中非空结果（只是定位线索 MEMORY_HINT）
        # PRIMARY_TEXT_READ:      get_chapter 实际读到全文（出处核验的最低完成线）
        # EXACT_QUOTE_VERIFIED:   待核验表述逐字出现在已读原文（EXACT_WORDING 要求）
        # MEMORY_HINT 永远不能置位后两者（T1.1-E）——只有 get_chapter 的全文能。
        self.source_candidate_found = False
        self.primary_text_read = False
        self.exact_quote_verified = False
        self.require_exact = bool(
            self.vi and self.vi.get("kind") == "EXACT_WORDING")
        # O1: auto_primary_read 标志已随引擎 auto-read 一并删除——主文本读取只能由
        # Main Agent 宣告产生（primary_text_read 仅由模型自己的 get_chapter 置位）。
        self._term_norm = ""
        if self.vi and self.vi.get("term"):
            self._term_norm = re.sub(r"[的是之其所\s]", "", self.vi["term"])

    # ── family 解析 ──
    def family_key(self, tool, args):
        """检索调用 → query_family 标识（search 类按语义改写判族; 阅读类按书+章; meta 类按对象）"""
        a = args or {}
        if tool == "get_chapter":
            return f"read:{a.get('book_id')}:{a.get('chapter_idx')}"
        if tool in ("get_book_detail", "list_books", "get_philosopher", "get_school", "query_database"):
            obj = (a.get("name") or a.get("book") or a.get("author") or a.get("school")
                   or a.get("key") or a.get("table") or "")
            return f"meta:{tool}:{obj}"
        q = str(a.get("query") or a.get("concept") or a.get("question") or a.get("keyword") or "")
        sh = _q_shingles(q)
        for seen_sh, fam_id in self._queries:
            if _jaccard(sh, seen_sh) >= QUERY_FAMILY_THRESHOLD:
                return fam_id
        fam_id = f"q:{len(self._queries)}:{q[:24]}"
        self._queries.append((sh, fam_id))
        return fam_id

    def _total_used(self):
        """总量包络口径: search + 阅读 + 书目/meta + websearch（含同批 pending）"""
        return (self.search_execs + self.read_execs + len(self._pending_reads)
                + self.meta_execs + self.websearch_execs)

    def _total_cap(self, complexity):
        return (VERIFICATION_TOTAL_LIMIT if (self.vi and complexity == "NARROW_FACTUAL")
                else TOTAL_RETRIEVAL_LIMIT.get(complexity, 5))

    # ── 准入判定（执行前; admit 即预登记——同批内后续调用可见前面的宣告）──
    # 拒绝 reason 措辞约束: 必须让模型明白"这是系统检索收敛, 不是'库中无此书'"——
    # 否则模型会把准入取消误读为"库里没收录", 向用户输出错误结论（真实事故: 《论语》案例）。
    # 核验路径（vi 存在）用分项配额（search≤2 / read≤2 独立 / websearch≤1）, 不用总量包络——
    # 总包络会把"读原文"这个义务核心动作挤掉（真实事故: read 排第 5 被拒 → 模型又"未能逐字命中"）。
    def admit(self, tool, args, complexity="NORMAL_EXPLANATION", forced=False):
        """在真正执行 tool 前判定是否准入。返回 (admitted, reason)。"""
        # forced 收口轮: 只允许未读章节阅读（保逐字核验）; 其余一律拒绝
        if forced:
            if tool == "get_chapter":
                a = args or {}
                key = (str(a.get("book_id") or ""), a.get("chapter_idx") if isinstance(a.get("chapter_idx"), int) else -1)
                if key in self.read_chapters or key in self._pending_reads:
                    return self._reject("obligation_satisfied: 该章节已读取/已准入, 重复取章不产生新证据")
                read_cap = VERIFICATION_FORCED_READ_CAP if self.vi else FORCED_READ_CAP
                if self.forced_reads >= read_cap:
                    return self._reject("forced_cap: 收口轮阅读补跑已达上限")
                self.forced_reads += 1
                self._pending_reads.add(key)
                return True, ""
            # T1.1-C: 拒绝理由必须写明"未执行≠库中无此书"——防模型把收口误读为"库中未收录"
            return self._reject("forced: 收口轮禁止新检索, 请立即基于已有材料完成回答"
                                "（未执行≠库中无此书; 不得向用户声称库中未收录）")
        # websearch: 独立证据来源（原典库不足时的合法补充路径）; 核验路径从严（≤1）, 其余 ≤2
        if tool == "websearch":
            ws_cap = VERIFICATION_WEBCAP if self.vi else WEBSEARCH_CAP
            if self.websearch_execs >= ws_cap:
                return self._reject(f"websearch_cap: 上网补充已达上限（{ws_cap}次）, 请基于已有材料作答")
            if not self.vi and self._total_used() >= self._total_cap(complexity):
                return self._reject("total_cap: 检索总量包络已满, 请基于已有材料作答（此为系统收敛, 非库中无此书）")
            self.websearch_execs += 1
            return True, ""
        # get_chapter（非 forced）: 核验路径用独立 read 配额（义务动作, 不与 search 抢额度）;
        # 非核验路径占总量包络（防取章漫游）
        if tool == "get_chapter":
            a = args or {}
            key = (str(a.get("book_id") or ""), a.get("chapter_idx") if isinstance(a.get("chapter_idx"), int) else -1)
            if key in self.read_chapters or key in self._pending_reads:
                return self._reject("obligation_satisfied: 该章节已读取/已准入, 重复取章不产生新证据")
            if self.vi:
                if self.read_execs + len(self._pending_reads) >= VERIFICATION_READ_CAP:
                    return self._reject(f"read_cap: 原文阅读已达核验配额（≤{VERIFICATION_READ_CAP}）, 请基于已读原文作答")
            else:
                total_used, cap = self._total_used(), self._total_cap(complexity)
                if total_used >= cap:
                    return self._reject(f"total_cap: 检索总量包络已满（{total_used}≥{cap}）, 请基于已有材料作答（此为系统收敛, 非库中无此书）")
            self._pending_reads.add(key)
            return True, ""
        # 书目/meta 类（get_book_detail / list_books / query_database / get_philosopher / get_school）:
        # 是"确认书是否在库/对象信息"的合法动作——仅义务已满足后拒绝, 不因"已有检索"误伤（真实事故: 《论语》案例）;
        # 核验路径 meta 有独立上限（≤1, 防"查目录/查详情"连环占用 gate 额度）
        if tool in ("get_book_detail", "list_books", "get_philosopher", "get_school", "query_database"):
            if self.obligations_satisfied:
                return self._reject("obligation_satisfied: 核验义务已满足, 书目定位不再产生新证据")
            if self.vi and self.meta_execs >= VERIFICATION_META_CAP:
                return self._reject(f"meta_cap: 书目/详情查询已达核验配额（≤{VERIFICATION_META_CAP}）, "
                                    "请直接用 get_chapter 阅读已定位的章节（此为系统收敛, 非库中无此书）")
            famstat = self._families.setdefault(fam := self.family_key(tool, args),
                                                {"execs": 0, "low_gain": 0, "relevant": 0})
            if famstat["execs"] >= 1:
                return self._reject("query_family_exhausted: 同一对象的书目/信息查询已执行过, 不再重复（此为系统收敛, 非库中无此书）")
            if not self.vi:
                total_used, cap = self._total_used(), self._total_cap(complexity)
                if total_used >= cap:
                    return self._reject(f"total_cap: 检索总量包络已满（{total_used}≥{cap}）, 请基于已有材料作答（此为系统收敛, 非库中无此书）")
            famstat["execs"] += 1
            self.meta_execs += 1
            return True, ""
        # search 类（含 query_graph 等带 query 的检索）
        fam = self.family_key(tool, args)
        famstat = self._families.setdefault(fam, {"execs": 0, "low_gain": 0, "relevant": 0})
        # 义务满足后: 一切检索收敛（F12 要求的"确认对应句后禁止重复 search"）
        if self.obligations_satisfied:
            return self._reject("obligation_satisfied: 核验义务已满足, 请立即基于已有材料完成回答")
        if famstat["execs"] >= FAMILY_EXEC_LIMIT or famstat["low_gain"] > 0:
            return self._reject("query_family_exhausted: 此查询与已执行检索高度重合（同族已执行/曾低增益）, "
                                "同义改写不产生新证据（此为系统收敛, 非库中无此书）")
        # 核验路径: search 分项配额（定位原典 2 次足够, 之后应转入阅读原文）
        if self.vi:
            if self.search_execs >= VERIFICATION_SEARCH_CAP:
                return self._reject(f"search_cap: 原典定位检索已达核验配额（≤{VERIFICATION_SEARCH_CAP}）, "
                                    "请改用 get_chapter 阅读已定位的原文, 或基于已有材料作答（此为系统收敛, 非库中无此书）")
        else:
            total_used, cap = self._total_used(), self._total_cap(complexity)
            if total_used >= cap:
                return self._reject(f"total_cap: 检索总量包络已满（{total_used}≥{cap}）, 请基于已有材料作答（此为系统收敛, 非库中无此书）")
            limit = SEARCH_EXEC_LIMIT.get(complexity, 4)
            if self.search_execs >= limit:
                return self._reject(f"search_budget: {complexity} 期望内检索义务已覆盖（≤{limit}）, 请基于已有材料作答（此为系统收敛, 非库中无此书）")
        famstat["execs"] += 1
        self.search_execs += 1
        return True, ""

    def _reject(self, reason):
        self.rejected += 1
        return False, reason

    # ── 执行后登记（结果回填; 计数已在 admit 预登记）──
    def record(self, tool, args, ok, result, key_terms=()):
        if tool == "websearch":
            return   # websearch 计数已在 admit 预登记
        if tool == "get_chapter":
            a = args or {}
            key = (str(a.get("book_id") or ""), a.get("chapter_idx") if isinstance(a.get("chapter_idx"), int) else -1)
            self._pending_reads.discard(key)
            if not ok:
                return
            self.read_execs += 1
            self.read_chapters.add(key)
            # T1.1-A: PRIMARY_TEXT_READ 只有 get_chapter 全文能置位（T1.1-E:
            # MEMORY_HINT——检索片段/书目/记忆——永远不算）。
            self.primary_text_read = True
            # 核验义务 O2: 已读取的文本中存在措辞级证据（逐字/去虚词成分/语义成分）
            # → 满足收口条件。EXACT_QUOTE_VERIFIED 是独立的更严状态（归一后连续包含,
            # T1.1-F 拼接在此即失败）——它决定"能否声称逐字", 不决定"能否收口";
            # 未逐字命中时最终回答必须给最接近原文并说明差异（T1.1-G 措辞强度联动）。
            if self.vi:
                text = str((result or {}).get("text") or "")
                if not self.exact_quote_verified:
                    self.exact_quote_verified = self._exact_in(text)
                if not self.obligations_satisfied and self._wording_evidence_in(text):
                    self.obligations_satisfied = True
            return
        # search/meta 类: 命中非空结果 → SOURCE_CANDIDATE_FOUND（只是定位线索, T1.1-A）
        if self.vi and not self.source_candidate_found and isinstance(result, dict) \
                and not result.get("error"):
            for k in ("results", "books", "items", "hits", "records"):
                v = result.get(k)
                if isinstance(v, list) and v:
                    self.source_candidate_found = True
                    break
        # search/meta 类计数已在 admit 预登记（失败不回滚——同族重试仍有余量）

    def mark_result(self, tool, args, low_gain=False, relevant_new=0):
        """引擎在 RetrievalState.register 后回填族的增益统计（供 admit 的同族判定）"""
        fam = self.family_key(tool, args)
        famstat = self._families.setdefault(fam, {"execs": 0, "low_gain": 0, "relevant": 0})
        if low_gain:
            famstat["low_gain"] += 1
        if relevant_new:
            famstat["relevant"] += relevant_new

    def _wording_evidence_in(self, text):
        """措辞级证据判定: 术语逐字出现, 或去虚词归一后 4+ 字成分命中, 或语义成分全部出现"""
        t = text or ""
        if not t or not self._term_norm:
            return False
        tn = re.sub(r"[的是之其所\s]", "", self.vi.get("term") or "")
        tnorm = re.sub(r"[的是之其所\s]", "", t)
        if self.vi.get("term") in t or (len(tn) >= 2 and tn in tnorm):
            return True
        if len(tn) >= 4:
            grams = {tn[i:i + 4] for i in range(len(tn) - 3)}
            if any(g in tnorm for g in grams):
                return True
        parts = [p for p in re.split(r"[的之]", self.vi.get("term") or "") if len(p) >= 2]
        if len(parts) >= 2 and all(p in t for p in parts):
            return True
        return False

    def _exact_in(self, text):
        """T1.1-A: 逐字命中判定——待核验表述（剥标点空白归一）作为连续片段出现在文本中。
        连续性是硬条件: 拼接/跳字都不算（T1.1-F 相邻章句拼接在此即失败）。"""
        t = text or ""
        if not t or not self.vi:
            return False
        term = self.vi.get("term") or ""
        if not term:
            return False
        if term in t:
            return True
        tn = _QUOTE_NORM(term)
        return len(tn) >= 4 and tn in _QUOTE_NORM(t)

    def snapshot(self):
        return {
            "obligations_satisfied": self.obligations_satisfied,
            "read_chapters": sorted(f"{b}#{c}" for b, c in self.read_chapters),
            "search_execs": self.search_execs,
            "read_execs": self.read_execs,
            "meta_execs": self.meta_execs,
            "websearch_execs": self.websearch_execs,
            "admission_rejected": self.rejected,
            "families": {k: dict(v) for k, v in self._families.items()},
            # T1.1-A: 出处核验状态分层（审计/回归断言用）
            "verification_states": {
                "source_candidate_found": self.source_candidate_found,
                "primary_text_read": self.primary_text_read,
                "exact_quote_verified": self.exact_quote_verified,
                "require_exact": self.require_exact,
            },
        }


RECOVERY_SYSTEM_DIRECTIVE = ("模型服务在回答生成前中断。请严格基于下面给出的检索材料直接输出最终回答"
                             "（可省略开场白）; 材料不足以支撑的部分必须明确说明'未能核验'并降低确定性措辞, "
                             "严禁编造引文。禁止输出任何工具调用标记。")
RECOVERY_NOTE_ZH = "（说明: 服务连接在回答生成前中断，以下回答基于已检索到的材料整理；材料不足处已降低确定性。）"
RECOVERY_NOTE_EN = ("(Note: the service connection dropped before the answer was generated; "
                    "the following is organized from the material already retrieved. "
                    "Confidence is reduced where the material was insufficient.)")
