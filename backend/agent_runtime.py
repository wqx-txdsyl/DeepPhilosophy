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
        elif info_gain in ("repeat", "empty"):
            self.no_gain += 1
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
        self.model_retries = 0
        self._started = time.time()

    def record_call(self, call_index, tool, args, duration_ms, success, error,
                    result_summary, rh, budget_cls, info_gain, evidence_items,
                    executed=True, thought=""):
        rec = {
            "type": "call", "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
            "conversation_id": self.conversation_id, "message_id": self.message_id,
            "agent_id": self.agent_id, "invocation_id": self.invocation_id,
            "call_index": call_index, "tool": tool,
            "args_normalized": normalize_args(args), "args_hash": call_fingerprint(tool, args)[0],
            "executed": bool(executed), "duration_ms": round(duration_ms or 0, 1),
            "success": bool(success), "error": (str(error)[:160] if error else None),
            "result_hash": rh, "result_summary": (result_summary or "")[:200],
            "budget_class": budget_cls, "info_gain": info_gain,
            "evidence_items": int(evidence_items or 0),
            "rationale": (thought or "")[:40],
        }
        self.calls.append(rec)
        _trace_write(rec)

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
RECOVERY_SYSTEM_DIRECTIVE = ("模型服务在回答生成前中断。请严格基于下面给出的检索材料直接输出最终回答"
                             "（可省略开场白）; 材料不足以支撑的部分必须明确说明'未能核验'并降低确定性措辞, "
                             "严禁编造引文。禁止输出任何工具调用标记。")
RECOVERY_NOTE_ZH = "（说明: 服务连接在回答生成前中断，以下回答基于已检索到的材料整理；材料不足处已降低确定性。）"
RECOVERY_NOTE_EN = ("(Note: the service connection dropped before the answer was generated; "
                    "the following is organized from the material already retrieved. "
                    "Confidence is reduced where the material was insufficient.)")
