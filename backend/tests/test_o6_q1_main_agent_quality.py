# -*- coding: utf-8 -*-
"""O6-Q1 — Main-Agent Evidence Expression & Multi-Turn Quality（产品质量收尾测试）

对应任务: O6-Q1（BASE 4d7fbf9d）。焦点是 model-facing contracts（模型实际看到什么）,
不锁 prompt 措辞原文; validator 判定逻辑冻结（T15: 矩阵 TP=10/FN=0/TN=10/FP=0 不变）。

T1  引言 vs 转述 policy 可见（引号/引用块 = 断言"以下措辞是原文"）
T2  blockquote 语义（自己的分析/转述 ≠ 引用块）
T3  证据带 canonical 章节标签时模型可见（工具结果 citation_label）
T4  无章节标签时不发明（书级标签回退; 无悬空分隔符）
T5  NEAR 与 EXACT 可区分（修复反馈 match=NEAR vs match=NONE + 审计状态可区分）
T6  修复 issue 含 offending span（locator = 引文预览, 无需推断哪句失败）
T7  修复 issue 含证据元数据（best_evidence 标签 / evidence_id / 同书已检索章节）
T8  反馈保持中性（无命令式动作指令 + 中性结尾）
T9  会话历史 ≠ 证据（policy 声明 + 行为: 仅历史文本支撑的逐字引用被拒）
T10 合法已检索证据 follow-up 不丢（policy: 定点重读而非全量重查 + 证据池保留事实）
T11 agent 身份上下文（General↔Nietzsche 切换, 当前 responder 显式）
T12 单一认知策略 owner（注入站点不新增 = builder 1 处 + hard 预算机械 1 处）
T13 零工具可行（质量 policy 不机械强制工具）
T14 Evidence Appetite 保留（无"最少工具"替换）
T15 validator 矩阵不变（O6-RP1 20 例矩阵原样通过）
"""
import inspect
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import engine_langgraph as EG
import final_validator as FV
import quote_bound as QB
import routes.agent_tools_retrieval as RET


# ── 共享合成证据（与 test_o6_rp1_mechanical 同一构造风格）──────────
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
# T1 / T2 — 引言 vs 转述 policy（§3 引文表达纪律）
# ═══════════════════════════════════════════════════════
class TestT1T2QuoteVsParaphrasePolicy:
    def test_t1_quote_syntax_asserts_source_wording(self):
        ctx = _core_context()
        # 引号/引用块 = "以下措辞是原文"的声明, 需检索证据支撑该措辞
        assert "以下措辞是原文" in ctx
        assert "检索证据" in ctx
        # 逐字/近似/记忆的三种非原文形态都在纪律覆盖内
        assert "逐字" in ctx and "近似措辞" in ctx and "记忆" in ctx
        # 转述与译文变体走普通正文（Q3 失败形态的 policy 对策可见）
        assert "转述" in ctx and "译文变体" in ctx

    def test_t2_own_analysis_not_blockquote(self):
        ctx = _core_context()
        # 自己的解释/综合/诚实声明不排成引用块 → 普通正文
        assert "自己的解释" in ctx
        assert "普通正文" in ctx
        # 旧"引用块格式纪律"泛化后仍保留 blockquote 关键概念（O5 T10 契约不回退）
        assert "blockquote" in ctx and "引用块" in ctx


# ═══════════════════════════════════════════════════════
# T3 / T4 — canonical 引用标签的模型可见性（§5 元数据）
# ═══════════════════════════════════════════════════════
class TestT3T4CitationMetadataVisibility:
    def test_t3_search_result_exposes_canonical_label(self):
        res = RET._exec_search_books({"query": "言必有中", "limit": 3})
        hits = res.get("results") or []
        assert hits, "真实书库应命中候选"
        for item in hits:
            assert "citation_label" in item
            # 标签由本条结果的 书名/章节 字段机械派生（模型可见 = validator 可认账的形态）
            assert item["citation_label"] == RET._cite_label(
                item.get("book_title"), item.get("chapter_title"))
            assert item["book_title"] in item["citation_label"]
            assert item["citation_label"].startswith("【《")

    def test_t3_chapter_read_exposes_canonical_label(self):
        res = RET._exec_search_books({"query": "言必有中", "limit": 1})
        hit = (res.get("results") or [None])[0]
        assert hit, "需要真实命中以取得 book_id/chapter_idx"
        ch = RET.TOOLS["get_chapter"]["execute"](
            {"book_id": hit["book_id"], "chapter_idx": hit["chapter_idx"]})
        assert not ch.get("error")
        # 元数据置于 text 之前（ToolMessage 4000 字符截断不丢标签）
        keys = list(ch.keys())
        assert keys.index("citation_label") < keys.index("text")
        assert ch["book_title"] and ch["book_title"] in ch["citation_label"]
        assert ch["title"] and ch["title"] in ch["citation_label"]

    def test_t3_label_form_matches_validator_accepted_citation(self):
        # 模型照抄工具结果给出的 citation_label → validator 认账（引用面板契约闭环）
        log = [{"name": "get_chapter", "args": {}, "result_summary": "",
                "result_full": {"book_id": "lunyu", "book_title": "论语", "title": "先进篇",
                                "chapter_idx": 13, "text": _CHAPTER_TEXT}}]
        label = RET._cite_label("论语", "先进篇")
        assert label == "【《论语》·先进篇】"
        res = _validate(f"此语出处{label}。", log=log)
        assert res.ok is True and res.verified_citations == 1

    def test_t4_no_chapter_label_no_invention(self):
        # 章节缺失 → 书级标签（无悬空分隔符, 不发明位置）
        assert RET._cite_label("论语", "") == "【《论语》】"
        assert RET._cite_label("论语", None) == "【《论语》】"
        assert "·】" not in RET._cite_label("论语", "")
        assert RET._cite_label("", "先进篇") == ""
        # 书级正式引用（只核验到书级时）本身可被 validator 接受
        res = _validate("此语出自《论语》。")
        assert res.ok is True

    def test_t4_policy_work_level_fallback_visible(self):
        ctx = _core_context()
        # 引用标签纪律: 标签取自检索证据; 只核验到书级 → 只标书级或不引用
        assert "引用标签纪律" in ctx
        assert "凭记忆补造" in ctx
        assert "只标书级" in ctx


# ═══════════════════════════════════════════════════════
# T5 / T6 / T7 / T8 — 修复反馈的机械事实质量（§7）
# ═══════════════════════════════════════════════════════
class TestT5T8RepairFeedbackQuality:
    def test_t5_near_distinguishable_from_exact(self):
        near = _PASSAGE.replace("夫人不言", "其人不言")
        res = _validate("原文如下：\n\n> " + near + "\n")
        codes = [i.code for i in res.issues]
        assert FV.NEAR_QUOTE_NOT_MARKED in codes
        issue = next(i for i in res.issues if i.code == FV.NEAR_QUOTE_NOT_MARKED)
        assert "match=NEAR" in issue.detail and "coverage=" in issue.detail
        # 无证据支撑的逐字块 → match=NONE（与 NEAR 机械可区分）
        res2 = _validate("原文如下：\n\n> " + _FAKE + "\n")
        issue2 = next(i for i in res2.issues if i.code == FV.UNSUPPORTED_EXACT_QUOTE)
        assert "match=NONE" in issue2.detail
        # 审计状态本身也可区分（done.quote_bound 契约不变）
        audit = QB.audit_quotes("原文如下：\n\n> " + near + "\n", RAW_LOG)
        assert audit["entries"][0]["verification_state"] == "VERIFIED_NEAR"

    def test_t6_issue_carries_offending_span(self):
        near = _PASSAGE.replace("夫人不言", "其人不言")
        cand = "原文如下：\n\n> " + near + "\n"
        res = _validate(cand)
        assert res.issues
        for i in res.issues:
            assert i.locator, "issue 必须自带命中位置（offending span 预览）"
            assert i.locator in cand, "locator 就是候选中的原文片段, 无需推断"
        # 候选的 blockquote 主张本身有一条直接指向它的 issue
        assert any(near[:30] in i.locator for i in res.issues)
        cand2 = "原文如下：\n\n> " + _FAKE + "\n"
        res2 = _validate(cand2)
        for i in res2.issues:
            assert i.locator in cand2
        assert any(_FAKE in i.locator for i in res2.issues)
        # UNVERIFIED_CITATION 的 locator = 引用标记本身
        res3 = _validate("出自【《韩非子·五蠹》】。")
        i3 = next(i for i in res3.issues if i.code == FV.UNVERIFIED_CITATION)
        assert "韩非子" in i3.locator

    def test_t7_issue_carries_evidence_metadata(self):
        near = _PASSAGE.replace("夫人不言", "其人不言")
        res = _validate("原文如下：\n\n> " + near + "\n")
        issue = next(i for i in res.issues if i.code == FV.NEAR_QUOTE_NOT_MARKED)
        # 机械已知的证据出处进 detail: evidence id + 最佳证据 canonical 标签
        assert issue.evidence_ref and issue.evidence_ref.startswith("qb_")
        assert "evidence=" in issue.detail
        assert "best_evidence=【《论语》·先进篇】" in issue.detail
        # 书名命中但章节不命中 → 列出该书已检索到的章节（只给事实, 不给指令）
        res2 = _validate("出自【《论语》·雍也篇】。")
        i2 = next(i for i in res2.issues if i.code == FV.UNVERIFIED_CITATION)
        assert i2.evidence_ref, "书名命中时 issue 应携带同书证据 id"
        assert "先进篇" in i2.detail and "retrieved chapters" in i2.detail
        # 书名完全未检索 → 如实说明
        res3 = _validate("出自【《韩非子·五蠹》】。")
        i3 = next(i for i in res3.issues if i.code == FV.UNVERIFIED_CITATION)
        assert i3.evidence_ref is None
        assert "book not found in retrieved evidence" in i3.detail

    def test_t8_feedback_neutral_no_prescribed_action(self):
        candidates = [
            "原文如下：\n\n> " + _PASSAGE.replace("夫人不言", "其人不言") + "\n",
            "原文如下：\n\n> " + _FAKE + "\n",
            "出自【《韩非子·五蠹》】。",
            "「X」",
        ]
        for c in candidates:
            res = _validate(c)
            if res.ok:
                continue
            fb = FV.format_feedback(res)
            for banned in ("Call get_chapter", "call get_chapter", "调用 get_chapter",
                           "Delete this sentence", "删除这句", "立即调用", "现在调用",
                           "必须调用", "Call search_books", "重新检索"):
                assert banned not in fb, (banned, fb)
            assert fb.endswith("Revise the candidate or gather more evidence as appropriate.")
            for i in res.issues:
                assert i.code in fb


# ═══════════════════════════════════════════════════════
# T9 / T10 — 多轮证据边界（§9）
# ═══════════════════════════════════════════════════════
class TestT9T10MultiTurnEvidenceBoundary:
    def test_t9_policy_history_is_not_evidence(self):
        ctx = _core_context()
        assert "会话历史" in ctx and "不是证据" in ctx
        assert "本次" in ctx  # 逐字引用/正式引用落在本次检索证据上

    def test_t9_history_quote_alone_rejected(self):
        # 上一轮 assistant 回答里的逐字引文, 若本轮未检索 → 不进入证据, 逐字引用被拒
        history_assistant = f"尼采曾说：“{_FAKE}”"
        res = FV.validate_final_candidate(
            f"如我此前所说，原文是：“{_FAKE}”",
            raw_tool_log=[], fallback_log=[])   # 历史不在任何工具日志里
        assert res.ok is False
        assert any(i.code in (FV.UNSUPPORTED_EXACT_QUOTE, FV.NEAR_QUOTE_NOT_MARKED)
                   for i in res.issues)
        assert history_assistant  # 历史文本本身不改变判定输入

    def test_t10_policy_keeps_retrieved_evidence_reusable(self):
        ctx = _core_context()
        # follow-up 不必全部重查: 定点重读即可; 合法已检索证据不丢
        assert "定点重读" in ctx
        assert "重跑" in ctx

    def test_t10_evidence_pool_keeps_legitimate_facts(self):
        # 同一 invocation 内先读后检索, 证据池保留两者——follow-up 逐字核验仍可用
        log = RAW_LOG + [{"name": "search_books", "args": {}, "result_summary": "",
                          "result_full": {"results": [{"book_title": "论语", "chapter_title": "先进篇",
                                                       "book_id": "lunyu", "chapter_idx": 13,
                                                       "snippet": _PASSAGE, "score": 0.9}]}}]
        spans = QB.evidence_spans(log)
        assert len(spans) == 2   # chapter 全文 + 检索片段同池
        res = _validate("原文如下：\n\n> " + _PASSAGE + "\n", log=log)
        assert res.ok is True


# ═══════════════════════════════════════════════════════
# T11 — Agent 身份上下文（§10/§11）
# ═══════════════════════════════════════════════════════
class TestT11AgentIdentityContext:
    def test_t11_general_identity_explicit(self):
        ctx = _core_context()
        assert "本轮回答者身份" in ctx
        assert "深哲" in ctx and "通用哲学智能体" in ctx
        # 历史消息可能出自其他 responder —— 机械事实随上下文可见
        assert "哲学家人格" in ctx and "不自动成为证据" in ctx

    def test_t11_persona_switch_keeps_current_responder(self):
        ctx = EG._build_context_messages("nietzsche", "zh", user_message="你好")[0].content
        assert "本轮回答者身份" in ctx
        assert "尼采" in ctx and "哲学家人格" in ctx
        assert "不改变你当前的人格" in ctx
        # 人格保持提醒与时期层不受影响（既有契约不回退）
        assert "你就是你" in ctx
        ctx2 = EG._build_context_messages("nietzsche", "zh",
                                          user_message="以1888年的你谈谈永恒轮回。")[0].content
        assert "【时期要求】" in ctx2

    def test_t11_identity_inside_single_builder_message(self):
        # 身份上下文并入 builder 的同一条 SystemMessage（不新增注入源）
        msgs = EG._build_context_messages("general", "zh")
        assert len(msgs) == 1
        assert msgs[0].content.startswith(EG.SYSTEM_PROMPT_LG[:24])


# ═══════════════════════════════════════════════════════
# T12 — 单一认知策略 owner（§16 无架构回归）
# ═══════════════════════════════════════════════════════
def test_t12_single_cognitive_policy_owner():
    code_only = "\n".join(ln for ln in inspect.getsource(EG).splitlines()
                          if not ln.strip().startswith("#"))
    builder_src = "\n".join(ln for ln in
                            inspect.getsource(EG._build_context_messages).splitlines()
                            if not ln.strip().startswith("#"))
    sites = [ln.strip() for ln in code_only.splitlines() if "SystemMessage(" in ln]
    sites_in_builder = [ln.strip() for ln in builder_src.splitlines() if "SystemMessage(" in ln]
    outside = [ln for ln in sites if ln not in sites_in_builder]
    assert len(outside) == 1, outside          # 仅 hard 预算一个机械注入点
    assert "HARD_BUDGET_DIRECTIVE" in outside[0]


# ═══════════════════════════════════════════════════════
# T13 / T14 — 研究校准不推翻 Evidence Appetite（§12/§14）
# ═══════════════════════════════════════════════════════
class TestT13T14ResearchCalibration:
    def test_t13_zero_tool_still_possible(self):
        ctx = _core_context()
        # 质量补丁不得引入无条件强制工具的 policy
        assert "必须调用工具" not in ctx
        assert "每次都必须检索" not in ctx
        # 无工具的纯解释性候选照常通过 validator（零工具路径无机械阻碍）
        res = _validate("康德的义务论强调行为本身的道德性质，而非其后果，核心是绝对命令。")
        assert res.ok is True

    def test_t14_evidence_appetite_preserved(self):
        ctx = _core_context()
        # 主动研究纪律原样保留（test_o4 T6 关键词契约）
        assert "主动使用" in ctx and "配额管制" in ctx
        assert "优先直接证据" in ctx and "最强相关解读" in ctx and "继续研究" in ctx
        # 未被"最少工具"策略替换
        for banned in ("最少工具", "最小化工具", "minimum tools", "Use the minimum tools"):
            assert banned not in ctx
        # 研究校准新增可见: 更新研究问题 / 不发同义词变体 / 收敛综合作答
        assert "研究校准" in ctx
        assert "同义词变体" in ctx
        assert "综合作答" in ctx

    def test_t14_repair_strategy_policy_visible(self):
        ctx = _core_context()
        # §8: 被拒后不原样重复措辞——按反馈区分"修表达"与"补研究/降级"
        assert "修复策略" in ctx
        assert "原样重复" in ctx
        assert "修改表达" in ctx


# ═══════════════════════════════════════════════════════
# T15 — validator 矩阵冻结（§15: 任何回归 = STOP）
# ═══════════════════════════════════════════════════════
def test_t15_validator_matrix_unchanged():
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
