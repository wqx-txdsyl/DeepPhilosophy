# -*- coding: utf-8 -*-
"""Tool Architecture（Phase T）——工具职责契约单一真源

QG2 结论: 专用工具的"成品化"设计与主 Agent 的 reasoning-first 纪律存在结构性张力
（Q08 compare_views 自述"结果即成品"被绕开 / Q10 dialectic 内部 prompt 强制正反合
无视用户约束 / Q13 conceptual_map 只会"概念→哲学家"图被整体架空 / Q14 socratic_tutor
一次齐发 4 轮与单问题合同冲突 / Q11 thought_experiment 退化迭代三连调）。

本模块是 Phase T 的单一真源（纯规则, 不联网, 不调 LLM, 异常只降级为跳过）:

  TOOL_TAXONOMY            38 项生产工具的分类与契约字段（T1 审计的机器可读形态;
                           30 项通用 TOOLS + 8 项哲学家专属 PHILO_EXTRA_TOOLS）
  REASONING_AUTHORITY      主 Agent 最终答案权原则（T2）
  scaffold_result()        统一 ToolResult 构建器——结构化中间产物, 非 ready-to-render 成品
  SkillReentryTracker      reasoning/generation skill 的 invocation 级重入策略（T7）
  infer_map_type()         用户请求 → MAP_TYPE 预判（T5 路由辅助）
  render_mermaid()         graph structure → Mermaid 确定性渲染器（T5:
                           quote/括号 escaping、节点 id、label、edge syntax 全部确定性处理）
  validate_mermaid()       Mermaid 文本解析回结构并与 graph 对账（Q13 回归的 parse 验证）
  strip_runtime_phrases() / RuntimePhraseScrubber  内部运行时措辞不得进入 Final（T13-B）
  tool_ownership_audit()   tool_value / final_use 审计（T12; REDUNDANT/BYPASSED → anomaly）
"""
import os
import re

# ═══════════════════════════════════════════════════════
# T2: Reasoning Authority Rule
# ═══════════════════════════════════════════════════════
# 单一原则: Main Agent owns final reasoning。除用户明确请求独立 artifact
# （USER_REQUESTED_ARTIFACT, 如 essay_outline/write_essay/generate_image）外,
# 任何 reasoning tool 不得拥有最终答案权——工具返回 structured intermediate result,
# 由主 Agent 结合 problem_model/evidence/claim roles/conversation context 生成 Final。
REASONING_AUTHORITY = "MAIN_AGENT"


def scaffold_result(kind, summary, confidence=0.6, presentation_hint="", **fields):
    """统一 ToolResult 构建器（T2/T3/T4/T6/T8）。

    工具返回结构化中间产物:
      kind              产物类型（comparison_scaffold / dialectical_movement /
                        socratic_turn / argument_structure / structured_review /
                        thought_experiment_scaffold / perspectives_scaffold / graph_map）
      summary           一句话说明（供主 Agent 快速判断可用性）
      confidence        工具对自身产物的置信度（0~1, 主 Agent 可参考可无视）
      presentation_hint 展示建议（非命令——展示深度由主 Agent 决定）
      reasoning_authority 恒为 MAIN_AGENT——标记最终综合权归属
      其余字段          该 kind 的结构化载荷（不要求所有字段存在）
    """
    out = {"kind": kind, "summary": summary,
           "confidence": round(max(0.0, min(1.0, float(confidence))), 2)}
    out.update(fields)
    out["reasoning_authority"] = REASONING_AUTHORITY
    if presentation_hint:
        out["presentation_hint"] = presentation_hint
    return out


# ═══════════════════════════════════════════════════════
# T1: TOOL TAXONOMY（38 项生产工具）
# ═══════════════════════════════════════════════════════
# TOOL_CLASS ∈ RETRIEVAL / READ / STRUCTURED_DATA / EXTERNAL_ACTION / GENERATION /
#              REASONING_SKILL / INTERACTION_MODE / PRESENTATION / PERSONA_DATA
# 字段: USES_INTERNAL_LLM / RETURNS_FINAL_PROSE / STATEFUL / EVIDENCE_PRODUCING /
#       USER_VISIBLE_ARTIFACT / SAFE_TO_REPEAT
_T = lambda cls, **kw: {"TOOL_CLASS": cls, **kw}

TOOL_TAXONOMY = {
    # ── 通用检索域（agent_tools_retrieval.py, 10）──
    "search_books":     _T("RETRIEVAL", USES_INTERNAL_LLM=False, RETURNS_FINAL_PROSE=False, STATEFUL=False, EVIDENCE_PRODUCING=True,  USER_VISIBLE_ARTIFACT=False, SAFE_TO_REPEAT=True),
    "get_book_detail":  _T("READ",       USES_INTERNAL_LLM=False, RETURNS_FINAL_PROSE=False, STATEFUL=False, EVIDENCE_PRODUCING=False, USER_VISIBLE_ARTIFACT=False, SAFE_TO_REPEAT=True),
    "get_chapter":      _T("READ",       USES_INTERNAL_LLM=False, RETURNS_FINAL_PROSE=False, STATEFUL=False, EVIDENCE_PRODUCING=True,  USER_VISIBLE_ARTIFACT=False, SAFE_TO_REPEAT=True),
    "query_graph":      _T("STRUCTURED_DATA", USES_INTERNAL_LLM=False, RETURNS_FINAL_PROSE=False, STATEFUL=False, EVIDENCE_PRODUCING=False, USER_VISIBLE_ARTIFACT=False, SAFE_TO_REPEAT=True),
    "get_philosopher":  _T("READ",       USES_INTERNAL_LLM=False, RETURNS_FINAL_PROSE=False, STATEFUL=False, EVIDENCE_PRODUCING=False, USER_VISIBLE_ARTIFACT=False, SAFE_TO_REPEAT=True),
    "list_books":       _T("READ",       USES_INTERNAL_LLM=False, RETURNS_FINAL_PROSE=False, STATEFUL=False, EVIDENCE_PRODUCING=False, USER_VISIBLE_ARTIFACT=False, SAFE_TO_REPEAT=True),
    "get_school":       _T("READ",       USES_INTERNAL_LLM=False, RETURNS_FINAL_PROSE=False, STATEFUL=False, EVIDENCE_PRODUCING=False, USER_VISIBLE_ARTIFACT=False, SAFE_TO_REPEAT=True),
    "concept_trace":    _T("STRUCTURED_DATA", USES_INTERNAL_LLM=False, RETURNS_FINAL_PROSE=False, STATEFUL=False, EVIDENCE_PRODUCING=True, USER_VISIBLE_ARTIFACT=False, SAFE_TO_REPEAT=True),
    "websearch":        _T("RETRIEVAL",  USES_INTERNAL_LLM=False, RETURNS_FINAL_PROSE=False, STATEFUL=False, EVIDENCE_PRODUCING=False, USER_VISIBLE_ARTIFACT=False, SAFE_TO_REPEAT=True),
    "query_database":   _T("STRUCTURED_DATA", USES_INTERNAL_LLM=False, RETURNS_FINAL_PROSE=False, STATEFUL=False, EVIDENCE_PRODUCING=False, USER_VISIBLE_ARTIFACT=False, SAFE_TO_REPEAT=True),
    # ── 记忆/创作域（agent_tools_memory.py, 5）──
    "write_essay":        _T("GENERATION", USES_INTERNAL_LLM=True, RETURNS_FINAL_PROSE=True,  STATEFUL=True,  EVIDENCE_PRODUCING=True,  USER_VISIBLE_ARTIFACT=True,  SAFE_TO_REPEAT=False, NOTE="USER_REQUESTED_ARTIFACT——用户请求的对象即作文本身"),
    "generate_image":     _T("EXTERNAL_ACTION", USES_INTERNAL_LLM=False, RETURNS_FINAL_PROSE=False, STATEFUL=True, EVIDENCE_PRODUCING=False, USER_VISIBLE_ARTIFACT=True, SAFE_TO_REPEAT=False, NOTE="外部生图 API; 迭代=图生图修改, 合法重入"),
    "philosopher_debate": _T("INTERACTION_MODE", USES_INTERNAL_LLM=True, RETURNS_FINAL_PROSE=True, STATEFUL=True, EVIDENCE_PRODUCING=False, USER_VISIBLE_ARTIFACT=True, SAFE_TO_REPEAT=True, NOTE="交互产物（逐轮/用户参与）, 重入=继续交互"),
    "thought_experiment": _T("REASONING_SKILL", USES_INTERNAL_LLM=True, RETURNS_FINAL_PROSE=False, STATEFUL=True, EVIDENCE_PRODUCING=False, USER_VISIBLE_ARTIFACT=False, SAFE_TO_REPEAT=False, NOTE="Phase T: 结构化脚手架 + 重入策略"),
    "role_play":          _T("PERSONA_DATA", USES_INTERNAL_LLM=False, RETURNS_FINAL_PROSE=False, STATEFUL=False, EVIDENCE_PRODUCING=False, USER_VISIBLE_ARTIFACT=False, SAFE_TO_REPEAT=True, NOTE="返回人格包数据, 不生成 prose"),
    # ── 评估/分析域（agent_tools_eval.py, 15）──
    "phti_test":         _T("INTERACTION_MODE", USES_INTERNAL_LLM=False, RETURNS_FINAL_PROSE=False, STATEFUL=False, EVIDENCE_PRODUCING=False, USER_VISIBLE_ARTIFACT=True, SAFE_TO_REPEAT=True),
    "compare_views":     _T("REASONING_SKILL", USES_INTERNAL_LLM=True, RETURNS_FINAL_PROSE=False, STATEFUL=False, EVIDENCE_PRODUCING=True,  USER_VISIBLE_ARTIFACT=False, SAFE_TO_REPEAT=False, NOTE="Phase T: comparison scaffold（T3）"),
    "socratic_tutor":    _T("INTERACTION_MODE", USES_INTERNAL_LLM=True, RETURNS_FINAL_PROSE=False, STATEFUL=True,  EVIDENCE_PRODUCING=False, USER_VISIBLE_ARTIFACT=False, SAFE_TO_REPEAT=True, NOTE="Phase T: stateful one-turn——ONE CALL = ONE QUESTION（T6）"),
    "advisor_council":   _T("REASONING_SKILL", USES_INTERNAL_LLM=True, RETURNS_FINAL_PROSE=False, STATEFUL=False, EVIDENCE_PRODUCING=False, USER_VISIBLE_ARTIFACT=False, SAFE_TO_REPEAT=False, NOTE="Phase T: perspectives scaffold"),
    "paper_review":      _T("REASONING_SKILL", USES_INTERNAL_LLM=True, RETURNS_FINAL_PROSE=False, STATEFUL=False, EVIDENCE_PRODUCING=False, USER_VISIBLE_ARTIFACT=False, SAFE_TO_REPEAT=False, NOTE="Phase T: structured review（T8）"),
    "analyze_argument":  _T("REASONING_SKILL", USES_INTERNAL_LLM=True, RETURNS_FINAL_PROSE=False, STATEFUL=False, EVIDENCE_PRODUCING=False, USER_VISIBLE_ARTIFACT=False, SAFE_TO_REPEAT=False, NOTE="Phase T: 论证结构脚手架（T8 仲裁: 短论证合法胜出）"),
    "profile":           _T("REASONING_SKILL", USES_INTERNAL_LLM=True, RETURNS_FINAL_PROSE=True,  STATEFUL=False, EVIDENCE_PRODUCING=False, USER_VISIBLE_ARTIFACT=False, SAFE_TO_REPEAT=False),
    "conceptual_map":    _T("PRESENTATION", USES_INTERNAL_LLM=True, RETURNS_FINAL_PROSE=False, STATEFUL=False, EVIDENCE_PRODUCING=False, USER_VISIBLE_ARTIFACT=True,  SAFE_TO_REPEAT=False, NOTE="Phase T: 通用关系图 + 确定性 Mermaid renderer（T5）"),
    "essay_outline":     _T("GENERATION", USES_INTERNAL_LLM=True, RETURNS_FINAL_PROSE=True,  STATEFUL=False, EVIDENCE_PRODUCING=True,  USER_VISIBLE_ARTIFACT=True,  SAFE_TO_REPEAT=False, NOTE="USER_REQUESTED_ARTIFACT——大纲即用户请求的对象（T10 保留）"),
    "life_coach":        _T("INTERACTION_MODE", USES_INTERNAL_LLM=True, RETURNS_FINAL_PROSE=True,  STATEFUL=False, EVIDENCE_PRODUCING=False, USER_VISIBLE_ARTIFACT=False, SAFE_TO_REPEAT=False, NOTE="疏导交互产物（支持体裁例外）"),
    "dialectic":         _T("REASONING_SKILL", USES_INTERNAL_LLM=True, RETURNS_FINAL_PROSE=False, STATEFUL=False, EVIDENCE_PRODUCING=False, USER_VISIBLE_ARTIFACT=False, SAFE_TO_REPEAT=False, NOTE="Phase T: 去固定正反合, 动态辩证运动字段（T4）"),
    "history_timeline":  _T("PRESENTATION", USES_INTERNAL_LLM=True, RETURNS_FINAL_PROSE=True,  STATEFUL=False, EVIDENCE_PRODUCING=True,  USER_VISIBLE_ARTIFACT=True,  SAFE_TO_REPEAT=False),
    "confrontation":     _T("INTERACTION_MODE", USES_INTERNAL_LLM=True, RETURNS_FINAL_PROSE=True,  STATEFUL=False, EVIDENCE_PRODUCING=True,  USER_VISIBLE_ARTIFACT=True,  SAFE_TO_REPEAT=True, NOTE="T9 最低限度统一: textual claim 与 simulated reply 分离; 主 Agent 保留裁决权"),
    "school_arena":      _T("INTERACTION_MODE", USES_INTERNAL_LLM=True, RETURNS_FINAL_PROSE=True,  STATEFUL=False, EVIDENCE_PRODUCING=False, USER_VISIBLE_ARTIFACT=True,  SAFE_TO_REPEAT=True),
    "agent_council":     _T("INTERACTION_MODE", USES_INTERNAL_LLM=True, RETURNS_FINAL_PROSE=True,  STATEFUL=False, EVIDENCE_PRODUCING=False, USER_VISIBLE_ARTIFACT=True,  SAFE_TO_REPEAT=True),
    # ── 哲学家智能体专属（PHILO_EXTRA_TOOLS, 8）──
    "philosopher_memory":   _T("READ",            USES_INTERNAL_LLM=False, RETURNS_FINAL_PROSE=False, STATEFUL=False, EVIDENCE_PRODUCING=False, USER_VISIBLE_ARTIFACT=False, SAFE_TO_REPEAT=True),
    "philosopher_period":   _T("READ",            USES_INTERNAL_LLM=False, RETURNS_FINAL_PROSE=False, STATEFUL=False, EVIDENCE_PRODUCING=False, USER_VISIBLE_ARTIFACT=False, SAFE_TO_REPEAT=True),
    "philosopher_style":    _T("READ",            USES_INTERNAL_LLM=False, RETURNS_FINAL_PROSE=False, STATEFUL=False, EVIDENCE_PRODUCING=False, USER_VISIBLE_ARTIFACT=False, SAFE_TO_REPEAT=True),
    "philosopher_quote":    _T("RETRIEVAL",       USES_INTERNAL_LLM=False, RETURNS_FINAL_PROSE=False, STATEFUL=False, EVIDENCE_PRODUCING=True,  USER_VISIBLE_ARTIFACT=False, SAFE_TO_REPEAT=True),
    "philosopher_graph":    _T("STRUCTURED_DATA", USES_INTERNAL_LLM=False, RETURNS_FINAL_PROSE=False, STATEFUL=False, EVIDENCE_PRODUCING=False, USER_VISIBLE_ARTIFACT=False, SAFE_TO_REPEAT=True),
    "philosopher_corpus":   _T("RETRIEVAL",       USES_INTERNAL_LLM=False, RETURNS_FINAL_PROSE=False, STATEFUL=False, EVIDENCE_PRODUCING=True,  USER_VISIBLE_ARTIFACT=False, SAFE_TO_REPEAT=True),
    "philosopher_concepts": _T("READ",            USES_INTERNAL_LLM=False, RETURNS_FINAL_PROSE=False, STATEFUL=False, EVIDENCE_PRODUCING=False, USER_VISIBLE_ARTIFACT=False, SAFE_TO_REPEAT=True),
    "philosopher_user":     _T("READ",            USES_INTERNAL_LLM=False, RETURNS_FINAL_PROSE=False, STATEFUL=False, EVIDENCE_PRODUCING=False, USER_VISIBLE_ARTIFACT=False, SAFE_TO_REPEAT=True),
}

# 专用工具集（tool_value/final_use 审计与重入策略的作用域）
SPECIALIZED_TOOL_CLASSES = {"GENERATION", "REASONING_SKILL", "INTERACTION_MODE",
                            "PRESENTATION", "EXTERNAL_ACTION", "PERSONA_DATA"}
SPECIALIZED_TOOLS = {n for n, t in TOOL_TAXONOMY.items()
                     if t["TOOL_CLASS"] in SPECIALIZED_TOOL_CLASSES}


# ═══════════════════════════════════════════════════════
# T7: Skill Reentry Policy（invocation 级）
# ═══════════════════════════════════════════════════════
def _env_int(name, default):
    try:
        return int(os.environ.get(name, "") or default)
    except (TypeError, ValueError):
        return default


# 同一 purpose 默认最多重入 1 次（即同 purpose 至多 2 次调用）
MAX_SAME_SKILL_REENTRY = _env_int("AGENT_SKILL_REENTRY", 1)

# 受重入策略约束的 reasoning/generation skill（交互类 philosopher_debate/
# generate_image/confrontation/socratic_tutor 的继续语义是合法重入, 不在内;
# phti_test 无内部 LLM）
SKILL_REENTRY_TOOLS = {
    "thought_experiment", "dialectic", "compare_views", "paper_review",
    "analyze_argument", "advisor_council", "essay_outline", "life_coach",
    "history_timeline", "school_arena", "agent_council", "conceptual_map", "profile",
}

# 用户要求迭代/变体的标志词（出现在工具参数或用户消息中 → USER_REQUESTED_ITERATION）
_ITERATION_MARKS = ("改", "换成", "变体", "如果", "假设", "变化", "再来", "重推",
                    "调整", "重新", "另一个版本", "换一个", "更深", "更强")

_REENTRY_SHINGLE = 2


def _purpose_shingles(text):
    t = re.sub(r"[\s，,。；;：:、？！?？()（）\"“”'‘’·《》【】]", "", text or "")
    if len(t) < _REENTRY_SHINGLE:
        return frozenset([t]) if t else frozenset()
    return frozenset(t[i:i + _REENTRY_SHINGLE] for i in range(len(t) - _REENTRY_SHINGLE + 1))


def _jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


class SkillReentryTracker:
    """invocation 级 skill 重入治理（生命周期 = 单次请求, engine 持有）。

    规则（T7）:
      - 首次调用一律放行;
      - 同 purpose 重入默认 MAX_SAME_SKILL_REENTRY=1 次, 且必须满足 justification:
        USER_REQUESTED_ITERATION（参数/用户消息含迭代标志词）
        或 FIRST_RESULT_INVALID（上次调用失败）
        或 NEW_OBLIGATION（purpose 实质变化: jaccard < 0.45 且非退化包含）;
      - 退化迭代（新 purpose 文本极短且其 shingle 几乎全部被先前 purpose 包含,
        如 Q11 第三次仅传 base="全知之镜"）→ 视为同一 purpose, 不算 NEW_OBLIGATION;
      - 同工具调用总量硬上限 = 2 + MAX_SAME_SKILL_REENTRY（防换purpose刷调用）。
    """

    def __init__(self):
        self.calls = {}          # tool -> [{"purpose": str, "sh": frozenset, "ok": bool}]

    @staticmethod
    def purpose_text(args):
        """参数 → purpose 文本（字符串值拼接; 列表/字典序列化）"""
        parts = []
        for k in sorted(args or {}):
            v = (args or {})[k]
            if isinstance(v, str) and v.strip():
                parts.append(v)
            elif isinstance(v, (list, tuple)):
                parts.append(" ".join(str(x) for x in v))
            elif isinstance(v, dict):
                parts.append(json_s(v))
        return " ".join(parts)[:400]

    def admit(self, tool, args, user_message=""):
        """执行前判定。返回 (admitted, reason)。
        user_message: 原始用户消息——含迭代标志词时视为 USER_REQUESTED_ITERATION。
        ok_history: 可选 bool 列表（该工具此前调用的成败; 缺省取内部记录）"""
        if tool not in SKILL_REENTRY_TOOLS:
            return True, ""
        args = args or {}
        purpose = self.purpose_text(args)
        hist = self.calls.get(tool, [])
        if not hist:
            return True, ""
        total_cap = 2 + MAX_SAME_SKILL_REENTRY
        if len(hist) >= total_cap:
            # 绝对上限（防御深度）: 同工具调用总数超限一律拒绝——
            # 用户迭代意图已由下方 same_chain ≤ MAX_SAME_SKILL_REENTRY 管控, 不在此二次解锁
            return self._reject(tool, "skill_total_cap: 同一技能本请求调用总数已达上限, 请基于已有结果综合")
        # FIRST_RESULT_INVALID: 上次失败 → 重试合理
        prev_ok = hist[-1]["ok"]
        if not prev_ok:
            return True, ""
        sh = _purpose_shingles(purpose)
        # NEW_OBLIGATION: 与所有先前 purpose 实质不同（且非退化包含）
        degenerate_or_same = False
        new_purpose = True
        for h in hist:
            j = _jaccard(sh, h["sh"])
            if j >= 0.45:
                degenerate_or_same, new_purpose = True, False
                break
            # 退化包含: 新 purpose 极短且 shingle 几乎全被先前包含（Q11 形态）
            if sh and len(sh) <= 6 and len(sh & h["sh"]) / len(sh) >= 0.8:
                degenerate_or_same, new_purpose = True, False
                break
        user_iter = bool(user_message and any(m in user_message for m in _ITERATION_MARKS)) \
            or any(m in purpose for m in _ITERATION_MARKS)
        if new_purpose and not degenerate_or_same:
            return True, ""
        # 同 purpose: 需 justification 且重入未超限
        same_chain = sum(1 for h in hist if _jaccard(sh, h["sh"]) >= 0.45
                         or (sh and len(sh) <= 6 and len(sh & h["sh"]) / len(sh) >= 0.8))
        if user_iter:
            if same_chain <= MAX_SAME_SKILL_REENTRY:
                return True, ""
            return self._reject(tool, f"skill_reentry_cap: 同一 purpose 的用户要求迭代已达上限（≤{MAX_SAME_SKILL_REENTRY}）, 请基于已有结果综合")
        # 无 justification 的同 purpose 重入 = 退化迭代（Q11 形态）→ 拒绝
        return self._reject(tool, "skill_reentry_undeclared: 同 purpose 重入缺少依据（无用户迭代要求/前次无效/实质新义务）, "
                                 "请基于已有结果综合; 如用户确要求变体请在参数中体现迭代意图")

    def _reject(self, tool, reason):
        return False, reason

    def record(self, tool, args, ok):
        if tool not in SKILL_REENTRY_TOOLS:
            return
        self.calls.setdefault(tool, []).append(
            {"purpose": self.purpose_text(args), "sh": _purpose_shingles(self.purpose_text(args)),
             "ok": bool(ok)})


def json_s(obj):
    import json
    return json.dumps(obj, ensure_ascii=False)


def extract_json(text):
    """从 LLM 回复中稳健提取 JSON 对象（剥 ``` 围栏 / 前后杂文字; 截断 JSON 括号配平修复;
    失败返回 None）"""
    import json as _json
    t = (text or "").strip()
    t = re.sub(r"^```(?:json)?\s*", "", t)
    t = re.sub(r"\s*```$", "", t)
    lo, hi = t.find("{"), t.rfind("}")
    if lo < 0:
        return None
    frag = t[lo:hi + 1] if hi > lo else t[lo:]
    for cand in (frag, frag.replace("，", ",").replace("：", ":")):
        try:
            v = _json.loads(cand)
            if isinstance(v, dict):
                return v
        except Exception:
            continue
    # 截断修复: 扫描括号配平, 补齐缺失的闭合符（max_tokens 截断 JSON 的常见形态）
    opens = {'{': '}', '[': ']'}
    stack, in_str, esc = [], False, False
    for ch in frag:
        if esc:
            esc = False
            continue
        if ch == '\\':
            esc = True
            continue
        if ch == '"':
            in_str = not in_str
            continue
        if not in_str:
            if ch in opens:
                stack.append(opens[ch])
            elif ch in '}]':
                if stack and stack[-1] == ch:
                    stack.pop()
    if stack:
        cand = frag + ('"' if in_str else "") + "".join(reversed(stack))
        try:
            v = _json.loads(cand)
            if isinstance(v, dict):
                return v
        except Exception:
            pass
    return None


# ═══════════════════════════════════════════════════════
# T5: 通用关系图 + 确定性 Mermaid
# ═══════════════════════════════════════════════════════
MAP_TYPES = ("CONCEPT_NETWORK", "PROCESS_FLOW", "ARGUMENT_GRAPH",
             "HISTORICAL_GENEALOGY", "PERSON_RELATION", "SYSTEM_ARCHITECTURE")

_MAP_HINTS = [
    (("论证", "依赖", "前提", "支撑", "推出", "得出", "辩护", "反驳", "驳倒"), "ARGUMENT_GRAPH"),
    (("流程", "过程", "步骤", "环节", "阶段", "推导链", "链条"), "PROCESS_FLOW"),
    (("历史", "演变", "脉络", "发展", "谱系", "时间线", "起源", "沿革"), "HISTORICAL_GENEALOGY"),
    (("人物", "师承", "交往", "论敌", "关系网", "星图", "影响谁"), "PERSON_RELATION"),
    (("体系", "架构", "组成", "结构", "系统"), "SYSTEM_ARCHITECTURE"),
]


def infer_map_type(text):
    """用户请求 → MAP_TYPE 预判（引擎 MAP_HINTS 注入用; 允许模型覆盖）。
    计分式: 每类命中标记数取最大（平分按列表序优先）——单字标记会造成
    "先验演绎"误判 PROCESS_FLOW 的真实回归, 故标记全部 ≥2 字。"""
    t = text or ""
    best, best_score = None, 0
    for marks, mt in _MAP_HINTS:
        s = sum(1 for m in marks if m in t)
        if s > best_score:
            best, best_score = mt, s
    return best or "CONCEPT_NETWORK"


_MAX_LABEL = 48


def _mm_label(text):
    """节点/边 label 确定性净化: 换行→空格; 内嵌双引号→全角引号（Q13 语法风险根除）;
    控制字符剥离; 超长截断。返回值永远可以安全包在 "..." 中。"""
    s = str(text or "").replace("\r", " ").replace("\n", " ").strip()
    s = s.replace('"', "”").replace("`", "'").replace("\\", "／")
    s = re.sub(r"[\x00-\x1f]", "", s)
    if len(s) > _MAX_LABEL:
        s = s[:_MAX_LABEL - 1] + "…"
    return s or "（未命名）"


def render_mermaid(graph, map_type="CONCEPT_NETWORK", direction=None):
    """graph structure → Mermaid 文本（确定性 renderer——Mermaid 只是 renderer,
    不是 reasoning result; 不让内部 LLM 自由手写未经验证的 Mermaid）。

    graph: {"nodes": [{"id": "感性", "label": "感性（接受性）", "group": "认识论"}...],
            "edges": [{"from": "感性", "to": "知性", "label": "提供杂多"}...]}
    节点 id = 稳定序号 n1..nN; label 引号包裹; 边语法 n1 -->|"label"| n2。
    PROCESS_FLOW/ARGUMENT_GRAPH 默认 TD, 其余 LR（direction 可覆盖: TD/LR）。
    """
    nodes = [n for n in (graph or {}).get("nodes", []) if isinstance(n, dict) and (n.get("label") or n.get("id"))]
    edges = [e for e in (graph or {}).get("edges", []) if isinstance(e, dict)]
    if not nodes:
        return ""
    ident = {n.get("id") or n.get("label"): f"n{i + 1}" for i, n in enumerate(nodes)}
    if direction not in ("TD", "LR"):
        direction = "TD" if map_type in ("PROCESS_FLOW", "ARGUMENT_GRAPH") else "LR"
    lines = [f"flowchart {direction}"]
    # 分组（subgraph）: 组名同样确定性净化
    groups = {}
    for n in nodes:
        g = _mm_label(n.get("group") or "") if n.get("group") else ""
        if g:
            groups.setdefault(g, []).append(n)
    if groups and len(groups) >= 2:
        for gi, (gname, gnodes) in enumerate(groups.items(), 1):
            lines.append(f"  subgraph G{gi}[\"{gname}\"]")
            for n in gnodes:
                lines.append(f"    {ident[n.get('id') or n.get('label')]}[\"{_mm_label(n.get('label') or n.get('id'))}\"]")
            lines.append("  end")
        for n in nodes:
            g = _mm_label(n.get("group") or "") if n.get("group") else ""
            if not g:
                lines.append(f"  {ident[n.get('id') or n.get('label')]}[\"{_mm_label(n.get('label') or n.get('id'))}\"]")
    else:
        for n in nodes:
            lines.append(f"  {ident[n.get('id') or n.get('label')]}[\"{_mm_label(n.get('label') or n.get('id'))}\"]")
    for e in edges:
        a = ident.get(e.get("from"))
        b = ident.get(e.get("to"))
        if not a or not b or a == b:
            continue
        lbl = (e.get("label") or "").strip()
        if lbl:
            lines.append(f"  {a} -->|\"{_mm_label(lbl)}\"| {b}")
        else:
            lines.append(f"  {a} --> {b}")
    return "\n".join(lines)


# validate: 逐行语法 + 与 graph 对账（parse PASS 的确定性口径）
_NODE_LINE_RE = re.compile(r'^\s*(?:subgraph\s+\S+\["[^"]*"\]|end|(\w+)\["([^"]+)"\])\s*$')
_EDGE_LINE_RE = re.compile(r'^\s*(\w+)\s*-->\s*(?:\|"([^"]+)"\s*\|\s*)?(\w+)\s*$')


def validate_mermaid(text, graph=None):
    """Mermaid 文本 parse 验证（确定性）:
    ① 围栏与 flowchart 指令 ② 逐行语法（节点/边/subgraph）③ 每行引号配平
    ④ 节点/边数量与 graph structure 对账 ⑤ label 无裸括号风险（全部引号包裹）。
    返回 {"ok": bool, "errors": [...], "parsed": {"nodes": n, "edges": m}}"""
    errors = []
    t = (text or "").strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:mermaid)?\s*", "", t)
        t = re.sub(r"\s*```$", "", t).strip()
    if not t:
        return {"ok": False, "errors": ["empty mermaid"], "parsed": {"nodes": 0, "edges": 0}}
    first = t.splitlines()[0].strip()
    if not re.match(r"^(flowchart|graph)\s+(TD|TB|LR|RL|BT)$", first):
        errors.append(f"bad directive line: {first[:40]!r}")
    n_nodes, n_edges, seen_ids = 0, 0, set()
    depth = 0
    for raw in t.splitlines()[1:]:
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.strip().count('"') % 2 == 1:
            errors.append(f"unbalanced quotes: {line.strip()[:40]!r}")
            continue
        s = line.strip()
        if s == "end":
            depth = max(0, depth - 1)
            continue
        m = re.match(r'^subgraph\s+(\w+)\["([^"]+)"\]$', s)
        if m:
            depth += 1
            continue
        m = _EDGE_LINE_RE.match(line)
        if m and depth >= 0 and not s.startswith("subgraph"):
            a, b = m.group(1), m.group(3)
            seen_ids.update((a, b))
            n_edges += 1
            continue
        m = re.match(r'^(\w+)\["([^"]+)"\]$', s)
        if m:
            seen_ids.add(m.group(1))
            n_nodes += 1
            continue
        errors.append(f"unparseable line: {s[:48]!r}")
    # 对账
    g_nodes = [n for n in (graph or {}).get("nodes", []) if isinstance(n, dict)]
    g_edges = [e for e in (graph or {}).get("edges", []) if isinstance(e, dict)]
    if graph is not None:
        if n_nodes != len(g_nodes):
            errors.append(f"node count mismatch: mermaid={n_nodes} graph={len(g_nodes)}")
        if n_edges != len(g_edges):
            errors.append(f"edge count mismatch: mermaid={n_edges} graph={len(g_edges)}")
    if len(seen_ids) > 0 and n_nodes == 0:
        errors.append("edges present but no node definitions")
    return {"ok": not errors, "errors": errors[:8],
            "parsed": {"nodes": n_nodes, "edges": n_edges}}


# ═══════════════════════════════════════════════════════
# T13-B: 内部运行时措辞不得进入 Final
# ═══════════════════════════════════════════════════════
# 这些措辞属于引擎内部治理语言（thinking/tool event 可用）, 模型转述进正文即泄漏。
RUNTIME_PHRASES = (
    "检索已被收口", "工具预算已达上限", "系统收敛", "系统检索收敛", "准入未通过",
    "检索收敛", "检索准入", "收口轮", "检索总量包络", "核验配额", "强制收口",
    "工具调用预算", "预算提示", "收敛机制取消", "执行前取消",
)
_MAX_PHRASE = max(len(p) for p in RUNTIME_PHRASES)


def strip_runtime_phrases(text, cleanup=True):
    """确定性去除正文中的内部运行时措辞。
    cleanup=True 时同时清理去除后的悬挂标点/空括号——只应在确有短语被移除时启用
    （流式逐 chunk 处理时, chunk 常以"，"开头, 无条件清理会把正常标点吃掉）。"""
    out = text or ""
    removed = False
    for ph in RUNTIME_PHRASES:
        if ph in out:
            out = out.replace(ph, "")
            removed = True
    if removed and cleanup:
        # 悬挂清理: 空括号 / 行首标点 / 重复标点
        out = re.sub(r"[（(]\s*[）)]", "", out)
        out = re.sub(r"(?m)^[ \t]*[，、；：,;][ \t]*", "", out)
        out = re.sub(r"([，、；])\1+", r"\1", out)
        out = re.sub(r"。\s*。", "。", out)
    return out


class RuntimePhraseScrubber:
    """流式安全版 strip_runtime_phrases（跨 chunk: 缓冲可能被切碎的短语尾巴）。
    仅当 chunk 内确实出现运行时短语时才做标点清理（防误吃正常标点, 真实回归:
    无条件清理会把每个以"，"开头的流式 chunk 的逗号剥掉）。"""

    def __init__(self):
        self._buf = ""

    def push(self, text):
        self._buf += text or ""
        cleaned = strip_runtime_phrases(self._buf, cleanup=False)
        removed = cleaned != self._buf
        if removed:
            cleaned = strip_runtime_phrases(cleaned, cleanup=True)
        # 尾部可能是短语前缀 → 扣下（最长短语长度-1）
        hold = 0
        tail = cleaned[-(_MAX_PHRASE - 1):] if len(cleaned) >= _MAX_PHRASE - 1 else cleaned
        for k in range(len(tail), 0, -1):
            suf = tail[-k:]
            if any(ph[:k] == suf and len(ph) > k for ph in RUNTIME_PHRASES):
                hold = k
                break
        emit = cleaned[:len(cleaned) - hold] if hold else cleaned
        self._buf = cleaned[len(cleaned) - hold:] if hold else ""
        return emit

    def flush(self):
        out, self._buf = strip_runtime_phrases(self._buf, cleanup=True), ""
        return out


# ═══════════════════════════════════════════════════════
# T12: Tool Result Ownership 审计
# ═══════════════════════════════════════════════════════
# tool_value: 该调用给主 Agent 带来了什么（NEW_EVIDENCE/NEW_STATE/NEW_STRUCTURE/
#             NEW_ARTIFACT/PRESENTATION/REDUNDANT）
# final_use : 主 Agent 最终怎么用了它（USED/PARTIALLY_USED/BYPASSED）
# tool_value=REDUNDANT 或 final_use=BYPASSED → observability anomaly
#（目标不是禁止, 而是自动识别 Q13 式"合规性调用"）
_VALUE_BY_TOOL = {
    "search_books": "NEW_EVIDENCE", "get_chapter": "NEW_EVIDENCE", "concept_trace": "NEW_EVIDENCE",
    "websearch": "NEW_EVIDENCE", "philosopher_corpus": "NEW_EVIDENCE", "philosopher_quote": "NEW_EVIDENCE",
    "get_book_detail": "NEW_EVIDENCE", "get_philosopher": "NEW_EVIDENCE", "get_school": "NEW_EVIDENCE",
    "list_books": "NEW_EVIDENCE", "query_graph": "NEW_EVIDENCE", "query_database": "NEW_EVIDENCE",
    "philosopher_memory": "NEW_STATE", "philosopher_period": "NEW_STATE", "philosopher_style": "NEW_STATE",
    "philosopher_concepts": "NEW_EVIDENCE", "philosopher_user": "NEW_STATE", "philosopher_graph": "NEW_EVIDENCE",
    "role_play": "NEW_STATE", "phti_test": "NEW_STATE",
    "socratic_tutor": "NEW_STATE",
    "compare_views": "NEW_STRUCTURE", "dialectic": "NEW_STRUCTURE", "analyze_argument": "NEW_STRUCTURE",
    "paper_review": "NEW_STRUCTURE", "advisor_council": "NEW_STRUCTURE", "thought_experiment": "NEW_STRUCTURE",
    "profile": "NEW_STRUCTURE", "life_coach": "NEW_STRUCTURE",
    "conceptual_map": "PRESENTATION", "history_timeline": "PRESENTATION",
    "school_arena": "PRESENTATION", "agent_council": "PRESENTATION", "philosopher_debate": "PRESENTATION",
    "confrontation": "NEW_STRUCTURE",
    "essay_outline": "NEW_ARTIFACT", "write_essay": "NEW_ARTIFACT", "generate_image": "NEW_ARTIFACT",
}

# 结果文本中抽取指纹的最短长度与采样上限（final_use 判定的确定性口径）
_FINGER_LEN = 8
_FINGER_SAMPLES = 24
_FINGER_GRAM = 6          # 采样 n-gram 长度（paraphrase 感知: 模型转述时逐字长串不再,
_FINGER_STEP = 10         # 但关键 6 字片段大概率保留）
# 指纹提取排除的元字段（summary/hint 常被提示词复述, 计入会高估 usage）
_AUDIT_EXCLUDE_KEYS = {"summary", "presentation_hint", "reasoning_authority", "confidence", "kind"}
_AUDIT_ANS_NORM_RE = re.compile(r"[\s，,。；;：:、？！?？()（）\"“”'‘’·《》【】\*\#\-—_>]")


def _distinctive_grams(result_full):
    """工具结果 → 指纹 n-gram 集合（CJK 长串的滑窗采样; 排除元字段）"""
    import json as _json
    payload = result_full
    if isinstance(result_full, dict):
        payload = {k: v for k, v in result_full.items() if k not in _AUDIT_EXCLUDE_KEYS}
    try:
        blob = _json.dumps(payload, ensure_ascii=False) if not isinstance(payload, str) else payload
    except Exception:
        blob = str(payload or "")
    frags = []
    for m in re.finditer(r"[\u4e00-\u9fff\u3000-\u303f]{%d,}" % _FINGER_LEN, blob):
        frags.append(m.group(0))
        if len(frags) >= _FINGER_SAMPLES:
            break
    grams = set()
    for f in frags:
        if len(f) <= _FINGER_GRAM:
            grams.add(f)
            continue
        for i in range(0, min(len(f) - _FINGER_GRAM + 1, 60), _FINGER_STEP):
            grams.add(f[i:i + _FINGER_GRAM])
    return grams


def _norm_answer(text):
    return _AUDIT_ANS_NORM_RE.sub("", text or "")


def _payload_cjk_len(result_full):
    """排除元字段后的载荷 CJK 字符数（实质产物判定）"""
    import json as _json
    payload = result_full
    if isinstance(result_full, dict):
        payload = {k: v for k, v in result_full.items() if k not in _AUDIT_EXCLUDE_KEYS}
    try:
        blob = _json.dumps(payload, ensure_ascii=False) if not isinstance(payload, str) else payload
    except Exception:
        blob = str(payload or "")
    return sum(1 for ch in blob if '\u4e00' <= ch <= '\u9fff')


def tool_ownership_audit(tool_log, answer, language="zh"):
    """tool_log（含 result_full,须在 pop 前调用）→ T12 审计:
    {"entries": [{tool, executed, tool_value, final_use, reason}],
     "bypassed_specialized_tools": n, "redundant_specialized_tools": n}
    final_use 判定为 paraphrase 感知: 6 字片段采样与归一化正文重叠。
    hits=0 时区分两种形态——实质产物（载荷 ≥60 CJK 字）被模型转述式综合 →
    PARTIALLY_USED(no_literal_overlap_but_substantive); 空薄产物被无视 → BYPASSED
    （Q13 式合规性调用的可检测形态: 产物不含用户所需结构/为空/模型完全未采纳其节点词）。"""
    ans = _norm_answer(answer)
    entries = []
    for tc in tool_log or []:
        name = tc.get("name") or ""
        rf = tc.get("result_full")
        thought = tc.get("thought") or ""
        not_admitted = "准入未通过" in thought or "执行前取消" in thought or "重入" in thought
        is_spec = name in SPECIALIZED_TOOLS
        failed = isinstance(rf, dict) and bool(rf.get("error"))
        reused = "复用本轮早前结果" in thought
        if not_admitted or reused:
            entries.append({"tool": name, "executed": False,
                            "tool_value": "REDUNDANT",
                            "final_use": "BYPASSED" if is_spec else "—",
                            "reason": thought[:60] or "not_executed"})
            continue
        if failed:
            entries.append({"tool": name, "executed": True,
                            "tool_value": "REDUNDANT", "final_use": "—",
                            "reason": "tool_error"})
            continue
        value = _VALUE_BY_TOOL.get(name, "NEW_EVIDENCE")
        if not is_spec:
            entries.append({"tool": name, "executed": True,
                            "tool_value": value, "final_use": "—",
                            "reason": "retrieval_read_data"})
            continue
        # 专用工具: 指纹重叠 → USED / PARTIALLY_USED / BYPASSED
        grams = _distinctive_grams(rf)
        hits = sum(1 for g in grams if g and g in ans)
        if not grams:
            final_use, reason = "PARTIALLY_USED", "no_fingerprint_extractable"
        elif hits == 0 and _payload_cjk_len(rf) >= 60:
            final_use, reason = "PARTIALLY_USED", "no_literal_overlap_but_substantive"
        elif hits == 0:
            final_use, reason = "BYPASSED", "thin_result_unused"
        elif hits >= 3 and hits >= len(grams) * 0.2:
            final_use, reason = "USED", f"grams={hits}/{len(grams)}"
        else:
            final_use, reason = "PARTIALLY_USED", f"grams={hits}/{len(grams)}"
        entries.append({"tool": name, "executed": True, "tool_value": value,
                        "final_use": final_use, "reason": reason})
    bypassed = sum(1 for e in entries if e["tool_value"] != "REDUNDANT"
                   and e["final_use"] == "BYPASSED")
    redundant = sum(1 for e in entries if e["tool_value"] == "REDUNDANT"
                    and e.get("tool") in SPECIALIZED_TOOLS)
    return {"entries": entries,
            "bypassed_specialized_tools": bypassed,
            "redundant_specialized_tools": redundant}
