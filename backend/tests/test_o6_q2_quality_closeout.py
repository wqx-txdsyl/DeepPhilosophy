# -*- coding: utf-8 -*-
"""O6-Q2 — Repair Convergence + Multi-Turn Evidence Expression Final Closeout（产品质量收尾）

对应任务: O6-Q2（BASE 943516d2e）。焦点: 修复收敛（repair 只修失败处, 不整篇重写、
不把修复说明排成引用块/引号）+ 多轮证据边界 + 引用粒度纪律。validator 生产代码零改动
（T16: Q1 blob 内容冻结 + 确定性矩阵 TP=10/FN=0/TN=10/FP=0 不变）。

T1  修复反馈全定位（每个被拒 quote/citation issue 自带 exact offending span 且反馈含 span）
T2  修复元数据粒度（书级 vs 章级可机械区分; 标签形态 + policy 可见）
T3  NEAR 契约可见（NEAR ≠ EXACT; 反馈带 match=NEAR + 近似不得静默升格逐字）
T4  不发明章节元数据（无章节 → 书级回退; 无悬空分隔符; 模型层零发明）
T5  修复反馈中性（无指定工具/动作指令）
T6  修复合同存在（policy: repair = 收敛动作而非重写/重复）
T7  保留有效内容 policy（已成立部分保持不动, 局部修正优先）
T8  Final 前表达自检存在（落笔前自检: 引号/引用标注须有本会话证据支撑）
T9  证据持久化边界（会话文本 ≠ 证据; 仅历史文本支撑的标签/逐字被拒）
T10 已核验证据持久化（policy 定点重读; 无跨调用证据合并新子系统）
T11 Agent 切换隔离（当前 responder 身份显式; 人格/历史 ≠ 证据）
T12 简单问题不被机械强制研究（无必须调用工具; 校准条款可见）
T13 Evidence Appetite 保留（无"最少工具"替换）
T14 Public Thinking 非 Runtime 清单（工作笔记 = 自然句因果判断, 无运行时检查清单）
T15 单一认知策略 owner（SystemMessage 注入 = builder + hard 预算机械位）
T16 validator 冻结（final_validator.py/quote_bound.py 与 Q1 blob 内容一致 + 矩阵不变）
"""
import inspect
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import engine_langgraph as EG
import final_validator as FV
import routes.agent_tools_retrieval as RET

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(BACKEND)

# ── 共享合成证据（与 Q1/RP1 同一构造风格）──────────────
_PASSAGE = "鲁人为长府，闵子骞曰：“仍旧贯如之何？何必改作？”子曰：“夫人不言，言必有中。”"
_CHAPTER_TEXT = "先进篇正文导语……\n" + _PASSAGE + "\n季氏富于周公，而求也为之聚敛而附益之。"
_FAKE = "这句引文纯属虚构查无原文甲乙丙丁戊己庚辛"

RAW_LOG = [
    {"name": "get_chapter", "args": {}, "result_summary": "",
     "result_full": {"book_id": "lunyu", "book_title": "论语", "title": "先进篇",
                     "chapter_idx": 13, "text": _CHAPTER_TEXT}},
]


def _validate(text, log=None):
    return FV.validate_final_candidate(text, raw_tool_log=RAW_LOG if log is None else log,
                                       fallback_log=[])


def _core_context():
    """模型每请求实际看到的完整核心上下文（builder 单源产出）"""
    return EG._build_context_messages("general", "zh")[0].content


# ═══════════════════════════════════════════════════════
# T1 — 修复反馈全定位（§3: 每个 issue = 精确 span + 机械事实）
# ═══════════════════════════════════════════════════════
class TestT1RepairFeedbackFullLocalization:
    def test_t1_every_quote_citation_issue_has_exact_span(self):
        cases = [
            "原文如下：\n\n> " + _PASSAGE.replace("夫人不言", "其人不言") + "\n",      # NEAR 引用块
            "原文如下：\n\n> " + _FAKE + "\n",                                        # 无据引用块
            "如《孟子》所说：“" + _FAKE + "”",                                       # 无据行内
            "出自【《论语》·雍也篇】。",                                               # 章节不匹配
            "出自【《韩非子·五蠹》】。",                                               # 书未检索
        ]
        for c in cases:
            res = _validate(c)
            if res.ok:
                continue
            assert res.issues
            fb = FV.format_feedback(res)
            for i in res.issues:
                assert i.locator, "每个被拒 issue 都必须自带 offending span"
                assert i.locator in c or i.code == FV.UNVERIFIED_CITATION, \
                    "locator 必须是候选内的原文片段（引用标记类以标记本身为 span）"
                assert i.locator[:60] in fb, "修复反馈必须包含被打回 span, 模型无需反推"

    def test_t1_repair_feedback_identifies_what_failed(self):
        res = _validate("原文如下：\n\n> " + _FAKE + "\n")
        i = next(x for x in res.issues if x.code == FV.UNSUPPORTED_EXACT_QUOTE)
        # 机械状态直接可读: match=NONE + 引用块类型（blockquote/leadin 有各自 issue 形态）
        assert "match=NONE" in i.detail
        assert ("blockquote" in i.detail) != ("in-line" in i.detail), \
            "blockquote 与行内引号两类失败的 issue 形态必须可区分"


# ═══════════════════════════════════════════════════════
# T2 / T3 / T4 — 修复元数据粒度 + NEAR 契约 + 零发明
# ═══════════════════════════════════════════════════════
class TestT2T4GranularityAndNearContract:
    def test_t2_work_level_vs_chapter_level_mechanically_distinct(self):
        # 标签形态: 章级【《书》·章】vs 书级【《书》】——模型所见即机械派生
        assert RET._cite_label("论语", "先进篇") == "【《论语》·先进篇】"
        assert RET._cite_label("论语", "") == "【《论语》】"
        ctx = _core_context()
        assert "只标书级" in ctx and "书级" in ctx      # 只核验到书级 → 只标书级

    def test_t2_work_level_only_citation_accepted(self):
        # 证据只到书级时, 书级正式引用可被认账; 章级标签需该章确实在证据中
        assert _validate("此语出自【《论语》】。").ok is True

    def test_t3_near_visible_and_not_exact(self):
        near = _PASSAGE.replace("夫人不言", "其人不言")
        res = _validate("原文如下：\n\n> " + near + "\n")
        issue = next(i for i in res.issues if i.code == FV.NEAR_QUOTE_NOT_MARKED)
        assert "match=NEAR" in issue.detail
        assert "approximation" in issue.detail.lower() or "近似" in issue.detail
        ctx = _core_context()
        # 近似措辞不得静默升格为逐字原文
        assert "近似措辞不得当作逐字原文呈现" in ctx

    def test_t4_no_invented_chapter_metadata(self):
        assert "·】" not in RET._cite_label("论语", None)
        assert "·】" not in RET._cite_label("论语", "")
        assert RET._cite_label("", "先进篇") == ""
        ctx = _core_context()
        assert "凭记忆补造" in ctx and "不得" in ctx


# ═══════════════════════════════════════════════════════
# T5 — 修复反馈中性（无指定工具/动作）
# ═══════════════════════════════════════════════════════
def test_t5_repair_feedback_neutral():
    for c in ["原文如下：\n\n> " + _FAKE + "\n", "出自【《韩非子·五蠹》】。"]:
        res = _validate(c)
        assert not res.ok
        fb = FV.format_feedback(res)
        for banned in ("Call get_chapter", "call get_chapter", "调用 get_chapter",
                       "立即调用", "现在调用", "必须调用", "Call search_books", "删除这句"):
            assert banned not in fb
        assert fb.endswith("Revise the candidate or gather more evidence as appropriate.")


# ═══════════════════════════════════════════════════════
# T6 / T7 / T8 — 修复合同 + 保留有效内容 + Final 前自检（§4/§5/§6）
# ═══════════════════════════════════════════════════════
class TestT6T8RepairContractPolicy:
    def test_t6_repair_contract_present(self):
        ctx = _core_context()
        assert "修复合同" in ctx
        assert "原样重复" in ctx and "不是重写" in ctx      # 不重复措辞, 也不整篇重写
        assert "收敛动作" in ctx                            # repair = 收敛
        assert "修复说明写成普通正文" in ctx                 # 修复元评论不进引用块/引号

    def test_t7_preserve_valid_content_policy(self):
        ctx = _core_context()
        assert "已成立的部分保持不动" in ctx                 # 局部修正优先
        assert "只修被打回" in ctx

    def test_t8_prefinal_expression_selfcheck(self):
        ctx = _core_context()
        assert "落笔前自检" in ctx
        assert "本会话" in ctx or "本次会话" in ctx          # 支撑 = 本次会话检索证据
        assert "补造引证精度" in ctx                          # 不必要精确引文 → 准确散文


# ═══════════════════════════════════════════════════════
# T9 / T10 — 多轮证据边界与持久化（§10/§11: 无跨调用证据合并）
# ═══════════════════════════════════════════════════════
class TestT9T10EvidencePersistenceBoundary:
    def test_t9_history_labels_not_evidence(self):
        # 标签只出现在上一轮 assistant 文本中（历史）→ 本轮不被当作已核验证据
        res = _validate("如我此前引用的【《论语》·先进篇】：\n\n> " + _PASSAGE + "\n",
                        log=[])
        assert res.ok is False
        codes = [i.code for i in res.issues]
        assert any(c in codes for c in (FV.UNVERIFIED_CITATION, FV.UNSUPPORTED_EXACT_QUOTE))
        ctx = _core_context()
        assert "会话历史" in ctx and "不是证据" in ctx

    def test_t10_rehydrate_policy_and_no_cross_call_merge(self):
        ctx = _core_context()
        assert "定点重读" in ctx                 # 需要精确措辞 → 定点重读已知出处（rehydrate）
        assert "重跑" in ctx                     # 无需全量重查
        # 架构冻结: stream 入口不接受跨调用证据合并（无新证据子系统）
        sig = inspect.signature(EG.stream_agent)
        params = set(sig.parameters)
        assert not (params & {"evidence_pool", "carried_evidence", "prior_evidence"})


# ═══════════════════════════════════════════════════════
# T11 — Agent 切换隔离
# ═══════════════════════════════════════════════════════
class TestT11AgentSwitchIsolation:
    def test_t11_current_responder_explicit_on_switch(self):
        for agent, token in (("general", "通用"), ("nietzsche", "尼采")):
            msgs = EG._build_context_messages(agent, "zh", user_message="继续")
            ctx = msgs[0].content
            assert "本轮回答者身份" in ctx
            assert token in ctx
            assert "不自动成为证据" in ctx      # 人格/历史角色 ≠ 证据

    def test_t11_single_builder_message_kept(self):
        msgs = EG._build_context_messages("general", "zh")
        assert len(msgs) == 1
        assert msgs[0].content.startswith(EG.SYSTEM_PROMPT_LG[:24])


# ═══════════════════════════════════════════════════════
# T12 / T13 — 简单问题不强制研究 vs Evidence Appetite（§13/§14）
# ═══════════════════════════════════════════════════════
class TestT12T13ResearchCalibration:
    def test_t12_simple_case_not_mechanically_forced(self):
        ctx = _core_context()
        for banned in ("必须调用工具", "每次都必须检索", "最少也要检索"):
            assert banned not in ctx
        # Q2 校准条款可见: 不依赖逐字核验 → 额外检索非必需
        assert "不依赖逐字核验" in ctx
        assert "持续加检" in ctx
        # 零工具纯解释性候选照常通过
        assert _validate("康德的义务论强调行为本身的道德性质，而非其后果，核心是绝对命令。").ok is True

    def test_t13_evidence_appetite_preserved(self):
        ctx = _core_context()
        assert "主动使用" in ctx and "配额管制" in ctx
        assert "优先直接证据" in ctx and "最强相关解读" in ctx
        assert "检索次数不受限制" in ctx
        for banned in ("最少工具", "最小化工具"):
            assert banned not in ctx


# ═══════════════════════════════════════════════════════
# T14 — Public Thinking 不是运行时清单（§17）
# ═══════════════════════════════════════════════════════
def test_t14_thinking_not_runtime_checklist():
    ctx = _core_context()
    # 工作笔记 = 自然句的因果判断（知道什么/不确定什么/为何下步/证据是否改变）
    assert "自然句" in ctx
    for banned in ("检查 1", "检查 2", "Checklist", "合规清单"):
        assert banned not in ctx
    # runtime 不注入逐项检查模板（engine 源内无此类事件文案）
    code_only = "\n".join(ln for ln in inspect.getsource(EG).splitlines()
                          if not ln.strip().startswith("#"))
    assert "检查 1" not in code_only


# ═══════════════════════════════════════════════════════
# T15 — 单一认知策略 owner（无新增注入点）
# ═══════════════════════════════════════════════════════
def test_t15_single_cognitive_policy_owner():
    code_only = "\n".join(ln for ln in inspect.getsource(EG).splitlines()
                          if not ln.strip().startswith("#"))
    builder_src = "\n".join(ln for ln in
                            inspect.getsource(EG._build_context_messages).splitlines()
                            if not ln.strip().startswith("#"))
    sites = [ln.strip() for ln in code_only.splitlines() if "SystemMessage(" in ln]
    sites_in_builder = [ln.strip() for ln in builder_src.splitlines() if "SystemMessage(" in ln]
    outside = [ln for ln in sites if ln not in sites_in_builder]
    assert len(outside) == 1, outside
    assert "HARD_BUDGET_DIRECTIVE" in outside[0]


# ═══════════════════════════════════════════════════════
# T16 — validator/quote_bound 冻结（§18: 零生产改动）
# ═══════════════════════════════════════════════════════
def test_t16_verification_stack_unchanged_from_q1():
    for rel in ("final_validator.py", "quote_bound.py"):
        r = subprocess.run(["git", "diff", "--quiet", "943516d2e", "--",
                            os.path.join("backend", rel)],
                           cwd=REPO, capture_output=True)
        assert r.returncode == 0, f"{rel} 相对 Q1 blob 内容有改动（validator 冻结）"

def test_t16_validator_matrix_unchanged():
    from tests.test_o6_rp1_mechanical import _matrix_cases
    invalid, valid = _matrix_cases()
    assert len(invalid) == 10 and len(valid) == 10
    tp = fn = tn = fp = 0
    for cid, text in invalid:
        if not _validate(text).ok:
            tp += 1
        else:
            fn += 1
    for cid, text in valid:
        if _validate(text).ok:
            tn += 1
        else:
            fp += 1
    assert (tp, fn, tn, fp) == (10, 0, 10, 0)
