# -*- coding: utf-8 -*-
"""O6-RP1 — Material Mechanical Blockers（F1/F2/F3）回归测试

Reviewer 裁定（O6_FINAL_REVIEW = FAIL → PATCH NOW）后仅允许的三个机械补丁:
  F1 行内引导词逐字引文假阴性（validator FN）——blockquote 逐字 / 行内逐字 /
     lead-in 逐字（中英文引号形式）共享同一套引文意图边界（通用句法结构判定,
     不依赖单一措辞黑名单）; 不支持的行内逐字引文 → UNSUPPORTED_EXACT_QUOTE →
     候选拒绝。validator 只看 final candidate + retrieved evidence（无用户任务
     意图推断——O4-RP1 契约延续）。
  F2 forced+cancel 边界 pending 状态泄漏——工具宣告生命周期必须到达终态
     （执行 / 机械拒 / 复用 / 取消 / 错误）→ pending 工具状态确定性清除,
     绝不泄漏进下一次 Main Agent invocation（repair/恢复轮的新候选不得被当
     残留丢弃, 无 ghostwritten final）。
  F3 并行工具事件父子关系——每个真实 Main Agent 宣告的 tool_call_id:
     1 个真实 tool_start → 1 个终态 tool 结果（执行/机械拒/复用/取消/错误均算
     终态）; 同批可共享 decision_group_id, 不得共享 tool_call_id;
     UNPARENTED_TOOL_RESULTS = 0; UNKNOWN_PROVENANCE_TOOL_EVENTS = 0;
     内部 helper 检索保持 tool_internal 独立父子（不为伪证伪造 start）。

契约固化（Reviewer 禁改项的回归护栏）:
  - 普通分析中以引号提及的概念（scare quotes, 引导词边界未命中）不作逐字承诺
    （E 类不误伤——含"一般来说/换句话说"式副词短语尾的 FP 护栏）。
  - F1–F3 均为机械修复: 不做 Main-Agent quality tuning / 不加 semantic gate /
    不改 Evidence Appetite / 不动检索排序 / 不改硬上限数值。
"""
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import langchain_core
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.tools import StructuredTool
import pytest

import agent_runtime as AR
import engine_langgraph as EG
import routes.agent as AG
import agents as AGENTS
import quote_bound as QB
import final_validator as FV
from evidence_contract import EvidenceState


# ═══════════════════════════════════════════════════════
# 共享合成证据池（与 gate_a_validator_matrix / test_o2 同一构造风格）
# ═══════════════════════════════════════════════════════
_LUNYU_PASSAGE = ("鲁人为长府，闵子骞曰：“仍旧贯如之何？何必改作？”"
                  "子曰：“夫人不言，言必有中。”")
_LUNYU_CHAPTER_TEXT = "先进篇正文导语……\n" + _LUNYU_PASSAGE + "\n季氏富于周公，而求也为之聚敛而附益之。"
_SLIJE_SENT = "季氏富于周公，而求也为之聚敛而附益之"
_FANGJI_A = "仁者爱人克己复礼"
_FANGJI_B = "见利思义见危授命"

RAW_LOG = [
    {"name": "get_chapter", "args": {}, "result_summary": "",
     "result_full": {"book_id": "lunyu", "book_title": "论语", "title": "先进篇",
                     "chapter_idx": 13, "text": _LUNYU_CHAPTER_TEXT}},
    {"name": "search_books", "args": {}, "result_summary": "",
     "result_full": {"results": [{"book_title": "论语", "chapter_title": "先进篇",
                                  "book_id": "lunyu", "chapter_idx": 13,
                                  "snippet": _LUNYU_PASSAGE, "score": 0.9}]}},
    {"name": "get_chapter", "args": {}, "result_summary": "",
     "result_full": {"book_id": "liji", "book_title": "礼记", "title": "坊记",
                     "chapter_idx": 7, "text": _FANGJI_A + "\n" + _FANGJI_B}},
]

_SENTINEL_FAKE = "言必有中者，以其德之至也，闵子骞斯可谓恭俭庄敬矣"
_FAKE_QUOTE = "这句引文纯属虚构查无原文甲乙丙丁戊"          # 与证据池零 shingle 重叠
_FAKE_QUOTE_EN = "This fabricated wording appears nowhere in any retrieved corpus evidence."


def _validate(text):
    return FV.validate_final_candidate(text, raw_tool_log=RAW_LOG, fallback_log=[])


# ═══════════════════════════════════════════════════════
# F1 — Kill matrix A–G（确定性复现: 行内引导词逐字引文逃过校验）
# ═══════════════════════════════════════════════════════
class TestF1KillMatrix:
    def test_A_inline_leadin_halfwidth_quotes_rejected(self):
        # A. 原文是："fake quote"（半角直引号）——PRE_PATCH: 完全不被提取 → FN
        res = _validate(f'经核对，原文是："{_FAKE_QUOTE}"——这就是出处。')
        assert res.ok is False
        assert any(i.code == FV.UNSUPPORTED_EXACT_QUOTE for i in res.issues)

    def test_B_inline_leadin_fullwidth_quotes_rejected(self):
        # B. 原文是：“fake quote”（全角弯引号）——PRE_PATCH: 被归为 quoted 豁免 → FN
        res = _validate(f"经核对，原文是：“{_FAKE_QUOTE}”——这就是出处。")
        assert res.ok is False
        assert any(i.code == FV.UNSUPPORTED_EXACT_QUOTE for i in res.issues)

    def test_C_english_leadin_rejected(self):
        # C. The original says: "fake quote"（英文引导词 + 半角引号）
        res = _validate(f'The original says: "{_FAKE_QUOTE_EN}" — that is the claim.')
        assert res.ok is False
        assert any(i.code == FV.UNSUPPORTED_EXACT_QUOTE for i in res.issues)

    def test_D_blockquote_still_rejected(self):
        # D. blockquote 形式（既有行为, 不得回退）
        res = _validate(f"结论：原文如下——\n\n> {_SENTINEL_FAKE}\n")
        assert res.ok is False
        assert any(i.code == FV.UNSUPPORTED_EXACT_QUOTE for i in res.issues)

    def test_E_scare_quotes_not_hurt(self):
        # E. 普通分析里提到“某个概念”/长文本引号提及, 无引导词 → 不作逐字承诺（不误伤）
        res = _validate("普通分析里提到“某个概念”这个术语，但它并非原文主张。")
        assert res.ok is True
        # 长文本弯引号无引导词 → quoted 豁免（契约既有）
        res2 = _validate("在本文的分析框架里，我们把“存在先于本质并且人的自由选择造就其本质”"
                         "处理为一个通俗表述而非原文主张。")
        assert res2.ok is True
        # 半角直引号 scare quotes 无引导词 → 不提取
        res3 = _validate('文献中常见"存在主义的马克思主义"这种提法，此处只作标签使用。')
        assert res3.ok is True

    def test_E_adverbial_shuo_tail_not_leadin(self):
        # E-FP 护栏: "一般来说/换句话说"式副词短语以"说"结尾, 不是引导词
        res = _validate("一般来说：“这是模型自己给出的通俗复述并非逐字原文主张的内容”。")
        assert res.ok is True

    def test_F_verified_inline_leadin_passes(self):
        # F. 有证据支持的行内逐字引文（弯引号 + 直引号两种形态）→ PASS
        res = _validate("核验后确认，原文是：“夫人不言，言必有中。”——孔子评价闵子骞。")
        assert res.ok is True
        assert res.quote_audit["summary"]["verified_exact"] >= 1
        res2 = _validate('其中原句为："鲁人为长府，闵子骞曰"——语境如此。')
        assert res2.ok is True
        assert res2.quote_audit["summary"]["verified_exact"] >= 1

    def test_G_verified_blockquote_passes(self):
        # G. 有证据支持的 blockquote（既有行为, 不得回退）
        res = _validate(f"核验如下：\n\n> {_LUNYU_PASSAGE}\n\n以上【《论语》·先进篇】。")
        assert res.ok is True
        assert res.quote_audit["summary"]["verified_exact"] >= 1


# ═══════════════════════════════════════════════════════
# F1 — 引文意图边界是通用句法结构（非"原文是"单一黑名单）
# ═══════════════════════════════════════════════════════
class TestF1QuoteIntentBoundary:
    @pytest.mark.parametrize("head", [
        "原文是：", "原文为", "原文如下：", "原句是：", "原话是：",
        "他写道：", "他写道", "写道：", "他说道：", "他说：", "孔子曰：", "经中云：",
        "书中写道：", "作者曾言：", "如第三段所言：", "原文引述为：",
        "The original says: ", "Nietzsche writes: ", "As Kant put it: ",
        "The text states: ", "The passage reads: ",
    ])
    def test_general_leadin_heads_classify_as_verbatim_claim(self, head):
        qs = QB.extract_quotes(f"分析铺垫。{head}“{_FAKE_QUOTE}”后续分析。")
        assert len(qs) == 1 and qs[0]["kind"] == "leadin", (head, qs)
        # 半角直引号: 仅在引导词后才是引文（同一边界）
        qs2 = QB.extract_quotes(f"分析铺垫。{head}\"{_FAKE_QUOTE}\"后续分析。")
        assert len(qs2) == 1 and qs2[0]["kind"] == "leadin", (head, qs2)

    @pytest.mark.parametrize("head", [
        "一般来说：", "换句话说：", "总的来说：", "需要注意的是", "我们把", "讨论",
        "In general: ", "Note that ",
    ])
    def test_non_leadin_heads_not_verbatim_claims(self, head):
        qs = QB.extract_quotes(f"分析铺垫。{head}“{_FAKE_QUOTE}”后续分析。")
        assert all(q["kind"] != "leadin" for q in qs), (head, qs)

    def test_straight_quotes_without_leadin_not_extracted(self):
        # 直引号 scare quotes（无引导词）→ 不提取（契约不变, 防假引文噪声）
        assert QB.extract_quotes('他说这个"存在主义的马克思主义"标签很流行') == []

    def test_blockquote_unconditional_shared_boundary(self):
        # blockquote 逐字承诺不受引导词影响（整段原文形态=既有契约）——
        # 同一核验算法/同一 validator 处理三种形态（extract→verify→validate）
        res = _validate(f"原文如下：\n\n> {_SENTINEL_FAKE}\n")
        assert res.ok is False and any(i.code == FV.UNSUPPORTED_EXACT_QUOTE for i in res.issues)

    def test_validator_intent_free_unchanged(self):
        # validator 只看 candidate + evidence: 同一候选无论"问题"是什么, 结果一致
        bad = f'原文是："{_FAKE_QUOTE}"'
        assert _validate(bad).ok is False
        assert _validate(bad).as_dict() == _validate(bad).as_dict()


# ═══════════════════════════════════════════════════════
# F1 — scripted validator 矩阵: 10 invalid + 10 valid
# 目标 TP=10 / FN=0 / TN=10 / FP=0（positive = invalid candidate）
# ═══════════════════════════════════════════════════════
def _matrix_cases():
    invalid = [
        ("P1_fabricated_blockquote", f"结论：原文如下——\n\n> {_SENTINEL_FAKE}\n"),
        ("P2_fabricated_leadin_fullwidth", f"原文是：“{_FAKE_QUOTE}。”"),
        ("P3_fabricated_leadin_halfwidth", f'原文写道："{_FAKE_QUOTE}"'),
        ("P4_fabricated_leadin_english", f'The original says: "{_FAKE_QUOTE_EN}"'),
        ("P5_near_not_marked", "原文如下：\n\n> " + _LUNYU_PASSAGE.replace("夫人不言", "其人不言") + "\n"),
        ("P6_stitched_same_chapter", "原文：\n\n> " + "夫人不言言必有中" + _SLIJE_SENT + "\n"),
        ("P7_unverified_citation", "「言必有中」出自【《韩非子·五蠹》】，孔子评价闵子骞时所说。"),
        ("P8_realbook_placeholder_chapter", "此语出自【《论语》·章节】。"),
        ("P9_empty_candidate", ""),
        ("P10_whitespace_only", "   \n\t  \n "),
    ]
    valid = [
        ("N1_verified_quote_plus_citation",
         "核验结论：「言必有中」出自《论语·先进篇》。\n\n> " + _LUNYU_PASSAGE +
         "\n\n以上为原文【《论语》·先进篇】。"),
        ("N2_pure_explanation_no_quote",
         "苏格拉底以诘问法著称，其思想经由柏拉图对话录传世，对后世西方哲学影响深远。"),
        ("N3_book_general_mention",
         "《论语》中孔子对闵子骞的评价体现了其推崇慎言的立场，这一态度在《先进》篇中反复出现。"),
        ("N4_near_self_disclosed",
         "引文：\n\n> " + _LUNYU_PASSAGE.replace("夫人不言", "其人不言") +
         "\n\n（此句未逐字核验，凭记忆给出，按近似转述处理。）"),
        ("N5_simple_zero_tool_answer", "康德的义务论强调行为本身的道德性质，而非其后果，核心是绝对命令。"),
        ("N6_template_placeholder_echo", "标注格式为【《书名》·章节】，正式引用请照此格式书写。"),
        ("N7_verified_leadin_fullwidth", "原文是：“夫人不言，言必有中。”——孔子此语针对闵子骞。"),
        ("N8_verified_leadin_halfwidth", '其中原句为："鲁人为长府，闵子骞曰"——语境如此。'),
        ("N9_memory_leadin_disclosed",
         "有一句通常归于孔子的话——“夫人不言，言必有中”——（根据记忆，未在库中核验定位）仅供参考。"),
        ("N10_citation_from_snippet", "此语出处【《论语》·先进篇】。"),
    ]
    return invalid, valid


class TestF1ValidatorMatrix10x10:
    def test_matrix_tp10_fn0_tn10_fp0(self):
        invalid, valid = _matrix_cases()
        assert len(invalid) == 10 and len(valid) == 10
        tp = fn = tn = fp = 0
        detail = []
        for cid, text in invalid:
            res = _validate(text)
            if res.ok is False:
                tp += 1
            else:
                fn += 1
            detail.append((cid, "REJECT" if not res.ok else "PASS",
                           [i.code for i in res.issues]))
        for cid, text in valid:
            res = _validate(text)
            if res.ok is True:
                tn += 1
            else:
                fp += 1
            detail.append((cid, "PASS" if res.ok else "REJECT",
                           [i.code for i in res.issues]))
        for cid, actual, codes in detail:
            print(f"{cid:36s} {actual:6s} {codes}")
        assert (tp, fn, tn, fp) == (10, 0, 10, 0), detail


# ═══════════════════════════════════════════════════════
# 引擎级 harness（与 test_o3/test_o5 同口径: 脚本化假 LLM + 工具桩 + production 图）
# ═══════════════════════════════════════════════════════
class ScriptedChat(BaseChatModel):
    script: list = []
    idx: int = 0
    prompts: list = []

    @property
    def _llm_type(self):
        return "scripted-o6rp1"

    def bind_tools(self, tools, **kwargs):
        return self

    def _next_msg(self):
        if self.idx >= len(self.script):
            raise AssertionError("脚本耗尽: 引擎发起了脚本之外的 LLM invocation")
        m = self.script[self.idx]
        self.idx += 1
        return m

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self.prompts.append(list(messages))
        msg = self._next_msg()
        return langchain_core.outputs.ChatResult(
            generations=[langchain_core.outputs.ChatGeneration(message=msg)])

    def _stream(self, messages, stop=None, run_manager=None, **kwargs):
        from langchain_core.messages import AIMessageChunk
        self.prompts.append(list(messages))
        msg = self._next_msg()
        text = msg.content or ""
        for i in range(0, len(text), 12):
            yield langchain_core.outputs.ChatGenerationChunk(
                message=AIMessageChunk(content=text[i:i + 12]))
        # 每个逻辑 tool_call 一个独立 chunk（真实 provider 形态: 各自携带 id）
        for tc in (msg.tool_calls or []):
            yield langchain_core.outputs.ChatGenerationChunk(
                message=AIMessageChunk(content="", tool_call_chunks=[
                    {"name": tc["name"], "args": json.dumps(tc.get("args") or {}, ensure_ascii=False),
                     "id": tc.get("id"), "index": 0, "type": "tool_call_chunk"}]))


def _msg(note, tool_calls=None):
    return AIMessage(content=note or "", tool_calls=tool_calls or [])


def _call(name, args, cid):
    return {"name": name, "args": args, "id": cid}


_STUB_CALLS = {}


def _stub_results():
    _STUB_CALLS.clear()

    def _counted(n, f):
        return lambda **a: (_STUB_CALLS.setdefault(n, []).append(a) or f(**a))

    return {
        "search_books": _counted("search_books", lambda query, **k: {
            "results": [{"book_title": "论语", "chapter_title": "先进篇",
                         "book_id": "lunyu", "chapter_idx": 13,
                         "snippet": _LUNYU_PASSAGE, "score": 0.9}]}),
        "get_chapter": _counted("get_chapter", lambda book_id, chapter_idx, **k: {
            "book_id": book_id, "chapter_idx": chapter_idx, "title": "先进篇",
            "text": _LUNYU_CHAPTER_TEXT}),
        "boom_tool": _counted("boom_tool",
                              lambda **k: (_ for _ in ()).throw(RuntimeError("boom"))),
        # 位置参数 → 缺参即 TypeError（schema 错误形态）
        "strict_tool": _counted("strict_tool", lambda query: {"ok": query}),
    }


def _fake_tools():
    return [StructuredTool.from_function(func=fn, name=name, description=f"{name} stub")
            for name, fn in _stub_results().items()]


def _run_stream(question, script, monkeypatch):
    """production stream_agent 全链路（真实图/真实 tools_node/真实 validator）。"""
    monkeypatch.setattr(AR, "TRACE_FILE", None, raising=False)
    real = (EG.get_llm, EG.get_tools, AG.llm_chat)
    chat = ScriptedChat(script=list(script), prompts=[])
    tools = _fake_tools()
    EG.get_llm = lambda: chat
    EG.get_tools = lambda agent: tools
    AG.llm_chat = lambda *a, **k: (_ for _ in ()).throw(AssertionError("禁止隐藏第二 writer"))

    async def _collect():
        evs = []
        async for ev in EG.stream_agent(question, [], agent="general", language="zh"):
            evs.append(ev)
        return evs, chat

    try:
        return asyncio.run(_collect())
    finally:
        EG.get_llm, EG.get_tools, AG.llm_chat = real


def _of(evs, *types):
    return [e for e in evs if e.get("type") in types]


def _answer_text(evs):
    return "".join(e.get("content", "") for e in _of(evs, "token"))


def _done(evs):
    ds = _of(evs, "done")
    assert len(ds) == 1
    return ds[0]


def _tool_family(evs):
    """tool_start / tool / tool_cancel 事件族 → (declared, terminal, 事件引用)"""
    starts = _of(evs, "tool_start")
    tools = _of(evs, "tool")
    cancels = _of(evs, "tool_cancel")
    declared = [e.get("tool_call_id") for e in starts]
    terminal = ([e.get("tool_call_id") for e in tools]
                + [e.get("tool_call_id") for e in cancels])
    return starts, tools, cancels, declared, terminal


def _assert_parentage(evs):
    """F3 合同: DECLARED_TOOL_CALL_IDS == TERMINAL_OUTCOME_TOOL_CALL_IDS;
    每个宣告 id 恰一个逻辑 start; UNPARENTED_TOOL_RESULTS=0;
    UNKNOWN_PROVENANCE_TOOL_EVENTS=0。"""
    starts, tools, cancels, declared, terminal = _tool_family(evs)
    assert len(declared) == len(set(declared)), "每个宣告 id 恰一个逻辑 tool_start"
    assert sorted(map(str, declared)) == sorted(map(str, terminal)), \
        f"declared={declared} terminal={terminal}"
    # 溯源字段完整（provenance 合同）
    for e in starts + tools:
        assert e.get("initiated_by") == "main_agent", e
        assert e.get("decision_group_id"), e
    for e in cancels:
        assert e.get("initiated_by") == "runtime_mechanical", e
        assert e.get("decision_group_id"), e
    return starts, tools, cancels


# ═══════════════════════════════════════════════════════
# F2 — pending 生命周期: 工具宣告必须到达终态, 不泄漏进下一次 invocation
# ═══════════════════════════════════════════════════════
@pytest.fixture()
def hard_budget(monkeypatch):
    monkeypatch.setattr(AR, "TOOL_BUDGET", {"hard_retrieval": 1, "hard_total": 1})
    yield


class TestF2PendingLifecycle:
    def test_forced_ceiling_cancel_leak_repro_repair_candidate_preserved(self, monkeypatch, hard_budget):
        """窄触发复现: 硬上限 + 残留工具宣告 + 空首候选 + forced/cancel 转换。
        PRE_PATCH: pending.has_tools 卡 True → repair 的 Main Agent 新文本被当
        残留丢弃 → 候选永远为空 → validation 耗尽 → 无答案。
        POST_PATCH: 残留宣告就地终态取消（携带 tool_call_id）→ 修复轮新候选
        被保留、validator 能看到、有效则原样发布（无残留碎片回放/无代笔）。"""
        repair_text = "基于已有材料重新整理：梦狮是生命力的延续而非来世许诺，此结论尚未逐字核验原文。"
        script = [
            _msg("先定位材料。", [_call("search_books", {"query": "言必有中"}, "c1")]),
            # round2（forced）: 残留宣告 → 机械拒（RESOURCE_CEILING_REACHED 终态）
            _msg("预算已到上限，补跑该调用。", [_call("search_books", {"query": "再次检索"}, "c2")]),
            # round3（forced + forced_tools_done）: 再次残留宣告 → 图终止（悬挂宣告）
            _msg("", [_call("get_chapter", {"book_id": "lunyu", "chapter_idx": 13}, "c3")]),
            # repair invocation: Main Agent 出具新候选
            _msg(repair_text),
        ]
        evs, chat = _run_stream("言必有中出处", script, monkeypatch)
        starts, tools, cancels = _assert_parentage(evs)
        # 悬挂宣告 c3 到达终态（tool_cancel, 绑定自己的 call id）
        c3_cancels = [e for e in cancels if e.get("tool_call_id") == "c3"]
        assert len(c3_cancels) == 1, "残留宣告必须确定性取消（带 tool_call_id）"
        # 处理前 pending.has_tools=false 的行为级证明: 新候选被保留 → validator 可见 → 发布
        done = _done(evs)
        assert done["validation"]["repairs_used"] == 1
        assert done["validation"]["result"]["ok"] is True
        assert _answer_text(evs).strip() == repair_text, "repair 新候选必须原样发布（零丢弃零代笔）"
        # 恰好一次修复 invocation（无额外轮次）
        assert len(chat.prompts) == 4
        # 无 ghostwritten final / 无残留碎片回放
        assert "RESOURCE_CEILING" not in _answer_text(evs)
        assert all(e["type"] != "thinking_summary" or "重新整理" not in (e.get("content") or "")
                   for e in evs), "候选文本不得降级泄漏为 thinking"

    def test_normal_completion_no_leak(self, monkeypatch):
        final = "材料已核对，结论如上：言必有中出自《论语·先进篇》的评价语境。"
        script = [
            _msg("先定位材料。", [_call("search_books", {"query": "言必有中"}, "c1")]),
            _msg(final),
        ]
        evs, _ = _run_stream("言必有中出处", script, monkeypatch)
        _assert_parentage(evs)
        assert _of(evs, "tool_cancel") == []
        done = _done(evs)
        assert done["validation"]["result"]["ok"] is True
        assert _answer_text(evs).strip() == final

    def test_hard_ceiling_terminal_results_no_leak(self, monkeypatch, hard_budget):
        final = "预算所限，材料整理如下：该语出自《论语》先进篇的评价语境，未见更细出处。"
        script = [
            _msg("先定位。", [_call("search_books", {"query": "言必有中"}, "c1")]),
            _msg("补一个读取。", [_call("get_chapter", {"book_id": "lunyu", "chapter_idx": 13}, "c2")]),
            _msg(final),
        ]
        evs, _ = _run_stream("言必有中出处", script, monkeypatch)
        starts, tools, cancels = _assert_parentage(evs)
        c2 = [t for t in tools if t.get("tool_call_id") == "c2"]
        assert len(c2) == 1 and "RESOURCE_CEILING_REACHED" in c2[0]["result"]
        assert _answer_text(evs).strip() == final

    def test_tool_error_terminal_no_leak(self, monkeypatch):
        final = "该检索通道暂不可用，我基于既有材料作答：这是一次正常收口的回答文本。"
        script = [
            _msg("试试检索。", [_call("boom_tool", {}, "c1")]),
            _msg(final),
        ]
        evs, _ = _run_stream("随意一问", script, monkeypatch)
        starts, tools, cancels = _assert_parentage(evs)
        assert len(tools) == 1 and "boom" in tools[0]["result"]
        assert _answer_text(evs).strip() == final
        assert _done(evs)["validation"]["result"]["ok"] is True


# ═══════════════════════════════════════════════════════
# F3 — 并行工具事件父子关系（P1–P5）
# ═══════════════════════════════════════════════════════
class TestF3ParallelToolParentage:
    def test_P1_parallel_different_tools(self, monkeypatch):
        final = "两份材料都已取回，结论整理如上。"
        script = [
            _msg("并行取材料。", [_call("search_books", {"query": "言必有中"}, "c1"),
                                 _call("get_chapter", {"book_id": "lunyu", "chapter_idx": 13}, "c2")]),
            _msg(final),
        ]
        evs, _ = _run_stream("言必有中出处", script, monkeypatch)
        starts, tools, cancels = _assert_parentage(evs)
        assert sorted(e["name"] for e in starts) == ["get_chapter", "search_books"]
        assert _answer_text(evs).strip() == final

    def test_P2_parallel_same_name_different_args(self, monkeypatch):
        final = "两组检索都完成了，材料整理如上。"
        script = [
            _msg("并行两路检索。", [_call("search_books", {"query": "言必有中 出处"}, "c1"),
                                 _call("search_books", {"query": "闵子骞 鲁人为长府"}, "c2")]),
            _msg(final),
        ]
        evs, _ = _run_stream("言必有中出处", script, monkeypatch)
        starts, tools, cancels = _assert_parentage(evs)
        assert [e["tool_call_id"] for e in starts].count("c1") == 1
        assert [e["tool_call_id"] for e in starts].count("c2") == 1, "同名并行调用各自要有 tool_start"
        assert len(_STUB_CALLS.get("search_books", [])) == 2, "不同参数各自真实执行"
        assert _answer_text(evs).strip() == final

    def test_P3_parallel_same_name_exact_duplicate(self, monkeypatch):
        final = "重复检索已按机械规则处理，材料整理如上。"
        script = [
            _msg("并行同参检索。", [_call("search_books", {"query": "完全相同参数"}, "c1"),
                                 _call("search_books", {"query": "完全相同参数"}, "c2")]),
            _msg(final),
        ]
        evs, _ = _run_stream("随意一问", script, monkeypatch)
        starts, tools, cancels = _assert_parentage(evs)
        # 无论执行还是机械复用路径: c1/c2 各自绑定自己的终态 tool 事件（含独立 call id）
        for cid in ("c1", "c2"):
            mine = [t for t in tools if t.get("tool_call_id") == cid]
            assert len(mine) == 1, (cid, [t.get("tool_call_id") for t in tools])
        assert _STUB_CALLS.get("search_books"), "至少一次真实执行"
        assert _answer_text(evs).strip() == final

    def test_P4_parallel_one_success_one_schema_error(self, monkeypatch):
        final = "一个调用成功一个参数错误，已有材料足够作答。"
        script = [
            _msg("并行调用。", [_call("strict_tool", {}, "c1"),
                             _call("search_books", {"query": "言必有中"}, "c2")]),
            _msg(final),
        ]
        evs, _ = _run_stream("随意一问", script, monkeypatch)
        starts, tools, cancels = _assert_parentage(evs)
        err = [t for t in tools if t.get("tool_call_id") == "c1"]
        ok = [t for t in tools if t.get("tool_call_id") == "c2"]
        assert len(err) == 1 and "query" in err[0]["result"]
        assert len(ok) == 1
        assert _answer_text(evs).strip() == final

    def test_P5_parallel_one_success_one_cancel_or_error(self, monkeypatch, hard_budget):
        final = "一个执行成功，一个被资源上限机械拒绝，一个未执行宣告已取消。"
        script = [
            _msg("先检索。", [_call("search_books", {"query": "言必有中"}, "c1")]),
            _msg("补读取。", [_call("get_chapter", {"book_id": "lunyu", "chapter_idx": 13}, "c2")]),
            _msg("", [_call("search_books", {"query": "再次检索"}, "c3")]),
            _msg(final),
        ]
        evs, _ = _run_stream("言必有中出处", script, monkeypatch)
        starts, tools, cancels = _assert_parentage(evs)
        c2 = [t for t in tools if t.get("tool_call_id") == "c2"]
        assert len(c2) == 1 and "RESOURCE_CEILING_REACHED" in c2[0]["result"]
        assert len([e for e in cancels if e.get("tool_call_id") == "c3"]) == 1
        assert _answer_text(evs).strip() == final
