# -*- coding: utf-8 -*-
"""Tool Architecture（Phase T; O4 Cognitive Layer Collapse 后瘦身）——工具能力契约单一真源

QG2 结论: 专用工具的"成品化"设计与主 Agent 的 reasoning-first 纪律存在结构性张力
（Q08 compare_views 自述"结果即成品"被绕开 / Q10 dialectic 内部 prompt 强制正反合
无视用户约束 / Q13 conceptual_map 只会"概念→哲学家"图被整体架空 / Q14 socratic_tutor
一次齐发 4 轮与单问题合同冲突 / Q11 thought_experiment 退化迭代三连调）。

本模块是工具的 CAPABILITY CONTRACT（纯规则, 不联网, 不调 LLM, 异常只降级为跳过）,
不是 cognitive policy engine（O4: 重入治理 SkillReentryTracker 与所有权审计
tool_ownership_audit 已删除——工具选择与重入判断归 Main Agent）:

  TOOL_TAXONOMY            38 项生产工具的分类与契约字段（T1 审计的机器可读形态;
                           30 项通用 TOOLS + 8 项哲学家专属 PHILO_EXTRA_TOOLS）
  REASONING_AUTHORITY      主 Agent 最终答案权原则（T2）
  scaffold_result()        统一 ToolResult 构建器——结构化中间产物, 非 ready-to-render 成品
  infer_map_type()         用户请求 → MAP_TYPE 预判（T5 路由辅助）
  render_mermaid()         graph structure → Mermaid 确定性渲染器（T5:
                           quote/括号 escaping、节点 id、label、edge syntax 全部确定性处理）
  validate_mermaid()       Mermaid 文本解析回结构并与 graph 对账（Q13 回归的 parse 验证）
  strip_runtime_phrases() / RuntimePhraseScrubber  内部运行时措辞不得进入 Final（T13-B）
"""
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
    # ── 二手学术文献检索域（agent_tools_scholarly.py, O7-C 2）──
    "search_scholarship":     _T("RETRIEVAL", USES_INTERNAL_LLM=False, RETURNS_FINAL_PROSE=False, STATEFUL=False, EVIDENCE_PRODUCING=False, USER_VISIBLE_ARTIFACT=False, SAFE_TO_REPEAT=True, NOTE="O7-C: Crossref+OpenAlex 双源; 返回真实书目+access_level"),
    "get_scholarly_source":   _T("READ",       USES_INTERNAL_LLM=False, RETURNS_FINAL_PROSE=False, STATEFUL=True,  EVIDENCE_PRODUCING=True,  USER_VISIBLE_ARTIFACT=False, SAFE_TO_REPEAT=True, NOTE="O7-C: 只接受 source_record_id; 访问状态机 PAPER_EXISTS!=PAPER_READ"),
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


# ═══════════════════════════════════════════════════════
# T5: 通用关系图 + 确定性 Mermaid
# ═══════════════════════════════════════════════════════
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

