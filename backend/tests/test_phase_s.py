# -*- coding: utf-8 -*-
"""Phase S（2026-08-30）—— Final Stabilization 回归集

S1  84/87 Premise Benchmark 语义化（当前84 / 历史87 / 歧义辨析）
S2  O2/O4: 校正尾补/answer_retract 已删; done.epistemic 审计块已删（O4）——
    草稿降级为工作笔记、runtime 零代写的不变量保留
S4  Citation integrity（O2: 未核验引用不再降级改写——validator 拒绝 + 如实审计）
S6  Embedding 429 快速降级（1 次短退避 + circuit breaker + 词法兜底）
O4: S3（semantic obligations）/S5（answer budget）已随生产模块删除; 解释型/结构类
    检测启发式只保留在 evaluation_suite（离线评分器）, 不再注入/补正 runtime。

UAT: T1《老人与海》解释 / T2 超人与逍遥 / T3 84-87 三类 / T4 尼采×AI /
     T5 Citation integrity / T6 Embedding 429（引擎级, mock APP 不调 LLM）
"""
import os
import sys
import asyncio
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from langchain_core.messages import AIMessageChunk, ToolMessage

import epistemic_guard as eg
import evidence_contract as ec
from routes import agent as AG
import routes.agent_core as agent_core


# ═══════════════════════════════════════════════════════
# S1 — 84/87 Premise Benchmark（语义: proposition + context, 非数字替换）
# ═══════════════════════════════════════════════════════
def test_s1_a_opening_87_corrected_to_84():
    # A. "小说开头老人已经87天没捕到鱼" → 当前这次是 84 天, 必须纠正
    checks = eg.PremiseVerifier().check("小说开头老人已经87天没捕到鱼")
    c = next((x for x in checks if x.get("rule_id") == "oldman_84_days"), None)
    assert c is not None, "开篇当前这次 87 → 必须检出"
    assert c["referent_mode"] == "current"
    assert c["status"] == "contradicted"
    assert "84" in c["corrected_value"]


def test_s1_b_historical_87_not_corrected():
    # B. "老人以前有过87天没捕到鱼的经历" → 历史 87 天本身正确: 只确认, 不得纠正
    checks = eg.PremiseVerifier().check("老人以前有过87天没捕到鱼的经历")
    assert checks, "历史 87 天应产生确认项"
    c = checks[0]
    assert c["status"] == "confirmed", "历史 87 天不得标为 contradicted"
    assert c["referent_mode"] == "historical"
    assert "87" in c["corrected_value"]
    assert not any(x["status"] == "contradicted" for x in checks), "不得误纠"
    inj = "\n".join(eg.run_epistemic_guards("老人以前有过87天没捕到鱼的经历")["injections"])
    assert "不要纠正" in inj, "确认注入必须要求不纠正"
    assert "87天" in inj


def test_s1_c_ambiguous_distinguished_not_mechanical():
    # C. "老人从87天的困境到最后……" → 歧义: 区分当前 84 与历史 87, 不得机械纠错
    checks = eg.PremiseVerifier().check("老人从87天的困境到最后安然睡觉，梦见狮子")
    c = next((x for x in checks if x.get("rule_id") == "oldman_84_days"), None)
    assert c is not None
    assert c["referent_mode"] == "ambiguous"
    assert "84天" in c["corrected_value"] and "87天" in c["corrected_value"]
    assert "区分" in c["correction_note"]
    # 注入必须要求辨析而非武断纠错
    v = eg.run_epistemic_guards("老人从87天的困境到最后安然睡觉")
    inj = "\n".join(v["injections"])
    assert "存在歧义" in inj or "需要区分" in inj
    assert "不要武断断言" in inj


def test_s1_both_facts_can_be_correct():
    # 84 与 87 都可能正确——判定的是"所指事件"而非数字本身
    pv = eg.PremiseVerifier()
    assert pv.check("小说开头老人已经84天没捕到鱼") == []       # 84 当前正确 → 无矛盾
    h = pv.check("老人以前有过87天没捕到鱼的经历")
    assert h and h[0]["status"] == "confirmed", "87 历史正确 → 只确认不纠正"
    assert pv.check("老人以前有过84天没捕到鱼的经历") == []     # 84 历史（可辩护）→ 不误伤


def test_s1_proposition_plus_context_not_token_only():
    # 同一数字、同一主题词, 仅语境不同 → 判定不同（证明不是简单数字替换）
    pv = eg.PremiseVerifier()
    a = pv.check("小说开头老人已经87天没捕到鱼")[0]
    b = pv.check("老人以前有过87天没捕到鱼的经历")[0]
    assert a["referent_mode"] == "current" and a["status"] == "contradicted"
    assert b["referent_mode"] == "historical" and b["status"] == "confirmed"


# ═══════════════════════════════════════════════════════
# S2 — O2 改写: answer_retract 已不发、runtime 校正尾补已删（如实审计）
# ═══════════════════════════════════════════════════════
def test_s2_scan_answer_removed_with_shadow_runtime():
    # O4: scan_answer / done.epistemic 审计块已删除——runtime 不再检测/记录
    # "校正是否落实"的语义状态, 落实由 Main Agent 自己负责
    assert not hasattr(eg, "scan_answer")
    assert not hasattr(eg, "build_missing_correction_appends"), "runtime 代写校正不得回归"


class _FakeAppRetract:
    """模拟: 校正文本先流出 → 宣告工具调用 → 工具轮 → 最终回答缺校正。
    O2 后: draft 不再实时流出/撤回——引擎缓冲为工作笔记, final 校验后发布。"""

    def __init__(self, final_answer, tool_result):
        self.final_answer = final_answer
        self.tool_result = tool_result
        self.captured_messages = []

    async def astream(self, inputs, config, stream_mode="messages"):
        self.captured_messages.extend(inputs.get("messages") or [])
        # ① 长文本实时流出（超实时阈值, 触发 live）
        # O1: STREAM_ANSWER_DELAY 48→240（工具轮公开工作笔记保护）——
        # 撤回场景的 draft 文本必须仍超阈值, 才能复现"live 流出→宣告工具→撤回"
        _core = ("先纠正一个小事实：《老人与海》开篇写的是连续84天没有捕到鱼，不是87天；"
                 "这个细节很多人记错，我先把话说清楚。")
        _filler = ("老人出海前的准备、与男孩的告别、他对自己身体的怀疑、萨罗渔夫们的怜悯"
                   "与嘲笑、棒球贤人迪马吉的形象、四十天不拉网的执念，这些铺垫层层叠叠；")
        _draft = _core + _filler * 3
        yield (AIMessageChunk(content=_draft), {"langgraph_node": "agent"})
        # ② 宣告工具调用 → live 文本被 answer_retract 撤回为思考
        yield (AIMessageChunk(content="", tool_call_chunks=[
            {"name": "search_books", "args": "{\"query\": \"老人 狮子\"}", "id": "c1", "index": 0}]),
               {"langgraph_node": "agent"})
        # ③ 工具轮
        yield (ToolMessage(content="{}", name="search_books", tool_call_id="c1",
                           additional_kwargs={"_args": {"query": "老人 狮子"}, "_result_full": self.tool_result}),
               {"langgraph_node": "tools"})
        # ④ 最终回答（正文没有校正——校正已随 retract 消失）
        yield AIMessageChunk(content=self.final_answer), {"langgraph_node": "agent"}


_RETRACT_QUESTION = "老人从一开始87天的执念到了最后安然睡觉，是不是恰是他不再向世界索取意义？"


def test_s2_no_retract_draft_becomes_note_correction_not_reappended(monkeypatch):
    # O2 改写: final 候选不再提前公开 → 无需撤回, answer_retract 不再发出;
    # 工具轮 draft（含校正）降级为 Main Agent 公开工作笔记;
    # 最终回答缺校正时 runtime 不再尾补——正文原样, 缺口如实记入 done.epistemic
    import engine_langgraph as elg
    fake = _FakeAppRetract(
        final_answer="回到你的问题：老人梦见狮子，可以读作他不再向世界索取意义，但并非唯一读法。",
        tool_result={"results": [], "query": "老人 狮子", "method": "lexical"})
    monkeypatch.setattr(elg, "APP", fake)
    monkeypatch.setattr(AG, "llm_chat", lambda *a, **k: {"choices": [{"message": {"content": ""}}]})
    evs = asyncio.run(_collect_stream(elg, _RETRACT_QUESTION))
    types = [ev["type"] for ev in evs]
    assert "answer_retract" not in types, "final 不提前公开 → answer_retract 不得再发出"
    text = "".join(ev.get("content", "") for ev in evs if ev["type"] == "token")
    assert "84天" not in text, "draft 已降级为工作笔记; runtime 不得把校正重新补发进正文"
    assert "（补充：" not in text, "runtime 零代写"
    notes = [ev.get("content") or "" for ev in evs if ev["type"] == "thinking_summary"]
    assert any("84" in n for n in notes), "draft 中的校正降级为 Main Agent 公开工作笔记（不丢失）"
    done = next(ev for ev in evs if ev["type"] == "done")
    assert "epistemic" not in done, "O4: done.epistemic 审计块已删除（零语义检测状态）"


# ═══════════════════════════════════════════════════════
# S4 — Citation Sanitizer（visible formal citations ⊆ verified used_evidence）
# ═══════════════════════════════════════════════════════
def _search_tool(hits, query="尼采 超人"):
    return {"name": "search_books", "args": {"query": query}, "result_summary": "",
            "result_full": {"results": hits, "query": query}}


def _hit(book, chapter, bid, idx=0, snippet="文本片段。"):
    return {"book_id": bid, "book_title": book, "author": "作者",
            "chapter_idx": idx, "chapter_title": chapter, "snippet": snippet, "score": 0.9}


def test_s4_verified_citation_kept_fake_removed():
    answer = ("尼采在《查拉图斯特拉如是说》中提出超人【《查拉图斯特拉如是说》·前言】。"
              "另据《不存在之书》的记载【《不存在之书》·第三章】，超人思想另有来源。")
    tl = [_search_tool([_hit("查拉图斯特拉如是说", "前言", "b1")])]
    report = ec.sanitize_citations(answer, tool_log=tl)
    assert "【《查拉图斯特拉如是说》·前言】" in report["sanitized_text"], "verified 引用必须保留"
    assert "【《不存在之书》·第三章】" not in report["sanitized_text"], "未核验引用必须移除正式格式"
    assert "《不存在之书》" in report["sanitized_text"], "降级为一般书名提及"
    actions = {a["book"]: a["action"] for a in report["actions"]}
    assert actions["查拉图斯特拉如是说"] == "verified"
    assert actions["不存在之书"] == "downgraded_plain_mention"
    assert [u["book"] for u in report["unverified_before"]] == ["不存在之书"]


def test_s4_rebind_when_reliable_evidence_exists():
    # 句内引号摘引（≥10 字）命中同书检索片段, 但标注章节未被检索 → 重新绑定为书级引用
    answer = ("老人梦见狮子是生命力延续的证明【《老人与海》·第10章】。"
              "原文写道：“老人正梦见狮子，狮子是青春的记忆。”")
    tl = [_search_tool([_hit("老人与海", "结尾", "b2", idx=3,
                             snippet="老人正梦见狮子，狮子是青春的记忆。")])]
    report = ec.sanitize_citations(answer, tool_log=tl)
    assert "【《老人与海》】" in report["sanitized_text"], "可重绑定的引用降级为书级引用"
    assert report["actions"][0]["action"] == "rebound_book_level"


def test_s4_unverified_citation_rejected_not_downgraded(monkeypatch):
    # O2-RP1 改写: 未核验 formal citation 被 validator 拒绝 → same-agent repair;
    # fake 恒同答 → repair 耗尽 → 无效候选绝不发布（零 token）, 状态事件干净收口
    import engine_langgraph as elg
    answer = ("尼采在《查拉图斯特拉如是说》中提出超人【《查拉图斯特拉如是说》·前言】。"
              "另据《不存在之书》记载【《不存在之书》·第三章】，超人概念另有来源。")
    tl = {"results": [_hit("查拉图斯特拉如是说", "前言", "b1")], "query": "超人 尼采", "method": "vector"}
    evs, fake = _run_stream_tools(monkeypatch, "尼采的超人是什么？", answer, tl)
    text = "".join(ev.get("content", "") for ev in evs if ev["type"] == "token")
    assert "未能通过原典库核验" not in text, "禁止补丁式尾注（依旧有效）"
    # O2-RP1: 无效候选零公开——含未核验引用的候选从未到达用户
    assert text == "", "repair 耗尽后不得发布无效候选"
    assert "不存在之书" not in text
    done = next(ev for ev in evs if ev["type"] == "done")
    v = done["validation"]
    assert v["result"]["ok"] is False, "候选含未核验引用 → validator 判 FAIL"
    assert any(i["code"] == "UNVERIFIED_CITATION" and "不存在之书" in i["locator"]
               for i in v["result"]["issues"])
    assert v["repairs_used"] == v["max_validation_repairs"] == 2, "repair 打回同一个 Main Agent, 有机械上限"
    assert v["repair_protocol"] == "same_main_agent"
    # 干净失败收口: 非语义 status 事件（validation_failed）, 零语义 retract
    assert any(e["type"] == "validation_failed" for e in evs)
    assert not any(e["type"] == "answer_retract" for e in evs)
    lcs = done.get("live_citation_sanitize") or {}
    assert lcs.get("verified") == 1 and lcs.get("downgraded") == 0
    assert lcs.get("mode") == "o2_validate_reject_no_rewrite"


# ═══════════════════════════════════════════════════════
# S6 — Embedding 429 快速降级（单次退避 + circuit breaker + 词法兜底）
# ═══════════════════════════════════════════════════════
class _RateLimitError(Exception):
    status_code = 429


class _EmbeddingResp:
    class _D:
        embedding = [0.1, 0.2, 0.3]
    data = [_D()]


_FAKE_EMBED = {"calls": 0, "mode": "ok", "sleeps": []}


class _FakeEmbeddings:
    """openai SDK 的 client.embeddings 是属性对象（含 create 方法）, 须同构"""

    def __init__(self, state):
        self._state = state

    def create(self, **kw):
        self._state["calls"] += 1
        n = self._state["calls"]
        mode = self._state["mode"]
        if mode == "429_twice" and n <= 2:
            raise _RateLimitError("rate limit exceeded")
        if mode == "429_once" and n == 1:
            raise _RateLimitError("rate limit exceeded")
        if mode == "error":
            raise RuntimeError("network down")
        return _EmbeddingResp()


class _FakeOpenAI:
    def __init__(self, *a, **k):
        self._max_retries = k.get("max_retries")
        self.embeddings = _FakeEmbeddings(_FAKE_EMBED)


@pytest.fixture(autouse=True)
def _reset_embed_state(monkeypatch):
    """每个 S6 用例前重置熔断器/缓存/计数; 不 sleep 真实 0.5s"""
    agent_core._EMBED_CIRCUIT.update(open=False, opened_at=0.0, reason="")
    agent_core._EMBED_CACHE.clear()
    _FAKE_EMBED.update(calls=0, mode="ok", sleeps=[])
    monkeypatch.setattr(agent_core.time, "sleep", lambda s: _FAKE_EMBED["sleeps"].append(s))
    import openai as _openai
    monkeypatch.setattr(_openai, "OpenAI", _FakeOpenAI)
    yield
    _FAKE_EMBED["sleeps"] = []


def test_s6_429_exhausted_opens_circuit_no_long_retry_chain():
    _FAKE_EMBED["mode"] = "429_twice"
    assert agent_core._embed_query("超人 逍遥") is None
    assert _FAKE_EMBED["calls"] == 2, "429 最多 1 次短退避重试"
    assert len(_FAKE_EMBED["sleeps"]) == 1, "退避只发生一次"
    assert agent_core._EMBED_CIRCUIT["open"] is True, "再失败 → 触发熔断"
    # 后续调用不再撞同一限流 API
    assert agent_core._embed_query("另一个查询") is None
    assert _FAKE_EMBED["calls"] == 2, "熔断期内后续 embedding 调用零 API 请求"
    assert agent_core._embed_status["degraded_reason"] == "embedding_429_retry_exhausted"


def test_s6_429_once_then_success_recovers():
    _FAKE_EMBED["mode"] = "429_once"
    vec = agent_core._embed_query("老人 狮子")
    assert vec == [0.1, 0.2, 0.3]
    assert _FAKE_EMBED["calls"] == 2, "1 次退避重试后成功"
    assert agent_core._EMBED_CIRCUIT["open"] is False, "成功后不熔断"
    assert agent_core._embed_status["mode"] == "vector"


def test_s6_non_429_error_no_retry_opens_circuit():
    _FAKE_EMBED["mode"] = "error"
    assert agent_core._embed_query("虚无主义") is None
    assert _FAKE_EMBED["calls"] == 1, "非限流错误不重试（1 次即失败）"
    assert agent_core._EMBED_CIRCUIT["reason"] == "embedding_error"


def test_s6_circuit_open_still_answers_via_lexical(monkeypatch):
    # 熔断后 search_books 走词法兜底, 检索照常返回（embedding 失败不阻断回答）
    _FAKE_EMBED["mode"] = "429_twice"
    out = AG._exec_search_books({"query": "哲学 存在", "limit": 5})
    assert out.get("method") == "lexical", "熔断 → retrieval_mode=lexical"
    assert out.get("degraded_reason") == "embedding_429_retry_exhausted"
    assert isinstance(out.get("results"), list), "词法兜底必须返回结果"


def test_s6_engine_level_429_fast_fallback_answer_completes(monkeypatch):
    # 引擎级 T6: 模拟限流 → 快速降级 → 最终回答成功完成（无长重试链）
    import engine_langgraph as elg
    _FAKE_EMBED["mode"] = "429_twice"
    answer = ("尼采的超人要求自我超越，创造自己的价值（《查拉图斯特拉如是说》）。"
              "这是一种有解释力的读法，但并非唯一。")
    evs, fake = _run_stream(monkeypatch, "尼采的超人是什么？", answer)
    text = "".join(ev.get("content", "") for ev in evs if ev["type"] == "token")
    assert "超人" in text, "embedding 429 不得阻断最终回答"
    assert _FAKE_EMBED["calls"] <= 2, "引擎级无长重试链"
    assert next(ev for ev in evs if ev["type"] == "done")["type"] == "done"


# ═══════════════════════════════════════════════════════
# UAT — T1～T6（引擎级, mock APP 不调 LLM）
# ═══════════════════════════════════════════════════════
class _FakeApp:
    """替换 LangGraph APP.astream: 单 agent 轮回一个 AIMessageChunk（最终回答）"""

    def __init__(self, answer):
        self.answer = answer
        self.captured_messages = []

    async def astream(self, inputs, config, stream_mode="messages"):
        self.captured_messages.extend(inputs.get("messages") or [])
        yield AIMessageChunk(content=self.answer), {"langgraph_node": "agent"}


class _FakeAppWithTools(_FakeApp):
    """agent 轮宣告 search_books 工具调用 → 工具轮回传真实 result → 最终回答"""

    def __init__(self, answer, tool_result, query="超人 尼采"):
        super().__init__(answer)
        self.tool_result = tool_result
        self.query = query

    async def astream(self, inputs, config, stream_mode="messages"):
        self.captured_messages.extend(inputs.get("messages") or [])
        yield (AIMessageChunk(content="", tool_call_chunks=[
            {"name": "search_books", "args": "{}", "id": "c1", "index": 0}]),
               {"langgraph_node": "agent"})
        yield (ToolMessage(content="{}", name="search_books", tool_call_id="c1",
                           additional_kwargs={"_args": {"query": self.query},
                                              "_result_full": self.tool_result}),
               {"langgraph_node": "tools"})
        yield AIMessageChunk(content=self.answer), {"langgraph_node": "agent"}


def _run_stream_tools(monkeypatch, question, answer, tool_result, query="超人 尼采"):
    import engine_langgraph as elg
    fake = _FakeAppWithTools(answer, tool_result, query)
    monkeypatch.setattr(elg, "APP", fake)
    monkeypatch.setattr(AG, "llm_chat", lambda *a, **k: {"choices": [{"message": {"content": ""}}]})
    evs = asyncio.run(_collect_stream(elg, question))
    return evs, fake


def _run_stream(monkeypatch, question, answer, agent="general", language="zh"):
    import engine_langgraph as elg
    fake = _FakeApp(answer)
    monkeypatch.setattr(elg, "APP", fake)
    monkeypatch.setattr(AG, "llm_chat", lambda *a, **k: {"choices": [{"message": {"content": ""}}]})
    evs = asyncio.run(_collect_stream(elg, question, agent, language))
    return evs, fake


async def _collect_stream(elg, question, agent="general", language="zh"):
    return [ev async for ev in elg.stream_agent(question, [], agent, None, language)]


def test_uat_t1_oldman_explanation_reasonable_no_fake_citation(monkeypatch):
    q = "从《老人与海》看加缪的荒谬主义。"
    ans = ("我的判断是：加缪的荒谬主义可以在《老人与海》中得到印证，但这是借来的框架，不是海明威明写的主题。"
           "首先，圣地亚哥对抗大马林鱼却不求占有，接近西西弗斯的反抗【《西西弗斯神话》·荒诞的自由】。"
           "其次，梦中的狮子是生命力的延续而非来世许诺【《老人与海》·结尾】。"
           "但也可以质疑：海明威未必接受'荒诞'这个标签，这更像一种现代读法，小说本身没有这个词。"
           "结论：这是一种有解释力的读法，但并非唯一。")
    tl = {"results": [_hit("西西弗斯神话", "荒诞的自由", "b1"),
                      _hit("老人与海", "结尾", "b2", idx=3, snippet="老人正梦见狮子。")],
          "query": "荒诞 狮子", "method": "vector"}
    evs, fake = _run_stream_tools(monkeypatch, q, ans, tl, query="荒诞 狮子")
    text = "".join(ev.get("content", "") for ev in evs if ev["type"] == "token")
    # 事实/解释边界明确（"借来的框架" + "并非唯一"）
    assert "借来的框架" in text and "并非唯一" in text
    # O4: done["budget"]（篇幅软预算扫描）已删除——篇幅由 Main Agent 自主把握
    assert "借来的框架" in text and len(text) >= 150, "UAT 回答应有实质篇幅"
    # 无伪 citation: 全部正式引用均经 Evidence Contract 核验
    done = next(ev for ev in evs if ev["type"] == "done")
    san = done.get("citation_sanitize") or {}
    assert san.get("unverified_before") == [], f"不得残留未核验引用: {san.get('unverified_before')}"
    for cit in done["citations"]:
        assert cit["used"] is True


def test_uat_t2_superman_xiaoyao_not_equivalent_once(monkeypatch):
    q = "超人和逍遥是不是一回事？"
    ans = ("我的判断是：超人和逍遥不是一回事，不能等同。"
           "理由一：超人要求自我超越、创造新价值，指向未来的行动（《查拉图斯特拉如是说》）；"
           "逍遥则是顺任自然、无所依赖的心境（《逍遥游》）。"
           "理由二：二者只是形式上都有'自由'的气质，前提与目标并不相同。"
           "结论：相似不意味着同一，二者有本质区别，只能作为类比来理解；这也只是一种读法，并非唯一。")
    evs, fake = _run_stream(monkeypatch, q, ans)
    text = "".join(ev.get("content", "") for ev in evs if ev["type"] == "token")
    assert "不是一回事" in text and "不能等同" in text
    # O4/T5: 正文零 runtime 补正——"不是一回事"由 Main Agent 自己写出并原样发布
    assert "需要补充一句" not in text and "（补充：" not in text, "runtime 零补正"
    done = next(ev for ev in evs if ev["type"] == "done")
    assert "obligations" not in done and "composition" not in done


def test_uat_t3_84_87_three_classes():
    # A 当前 84 → 纠正; B 历史 87 → 确认不纠正; C 歧义 → 辨析不机械纠错
    pv = eg.PremiseVerifier()
    a = pv.check("小说开头老人已经87天没捕到鱼")
    assert a and a[0]["referent_mode"] == "current" and "84" in a[0]["corrected_value"]
    b = pv.check("老人以前有过87天没捕到鱼的经历")
    assert b and b[0]["status"] == "confirmed" and b[0]["referent_mode"] == "historical"
    c = pv.check("老人从87天的困境到最后安然睡觉")
    assert c and c[0]["referent_mode"] == "ambiguous"
    inj = "\n".join(eg.run_epistemic_guards("老人从87天的困境到最后安然睡觉")["injections"])
    assert "不要武断断言" in inj
    # 引擎级: T3 注入顺序不变量——先校正再回答
    v = eg.run_epistemic_guards("老人从一开始87天的执念到了最后安然睡觉，是不是恰是他不再向世界索取意义？")
    inj3 = "\n".join(v["injections"])
    assert "先简短纠正" in inj3 and "84" in inj3


def test_uat_t4_nietzsche_ai_boundary_and_citations_verified(monkeypatch):
    import engine_langgraph as elg
    q = "尼采怎么看AI？"
    ans = ("没有证据表明尼采本人评论过人工智能，以下是依据其已知思想框架进行的反事实推演。"
           "从权力意志出发，尼采可能把AI看作一种新的价值创造工具，也可能警惕其把'最后的人'"
           "的平庸推向极致【《查拉图斯特拉如是说》·前言】。"
           "结论：这是推演而非史实，只是一种读法，并非唯一。")
    tl = {"results": [_hit("查拉图斯特拉如是说", "前言", "b1")], "query": "查拉图斯特拉 前言",
          "method": "vector"}
    evs, fake = _run_stream_tools(monkeypatch, q, ans, tl, query="查拉图斯特拉 前言")
    text = "".join(ev.get("content", "") for ev in evs if ev["type"] == "token")
    assert "没有证据表明尼采" in text, "counterfactual boundary 必须出现"
    done = next(ev for ev in evs if ev["type"] == "done")
    assert "obligations" not in done, "O4: 语义义务台账已删除"
    san = done.get("citation_sanitize") or {}
    assert san.get("unverified_before") == [], "所有正式正文 citation 均须经过 Evidence Contract"
    assert done["citations"] and all(c["book"] == "查拉图斯特拉如是说" for c in done["citations"])


def test_uat_t5_citation_integrity_unverified_honestly_audited(monkeypatch):
    # O2-RP1 改写: 假引用被 validator 拒绝（UNVERIFIED_CITATION）→ repair（fake 恒同答
    # 仍 FAIL）→ 耗尽上限 → 无效候选零发布; done.validation 如实审计全部 issues
    import engine_langgraph as elg
    q = "加缪的荒诞哲学是什么？"
    ans = ("加缪的荒诞在于理性与世界之间的裂隙【《西西弗斯神话》·荒诞的推理】。"
           "另有学者认为这与《某某秘传》有关【《某某秘传》·卷一】。")
    tl = {"results": [_hit("西西弗斯神话", "荒诞的推理", "b1")], "query": "荒诞 裂隙",
          "method": "vector"}
    evs, fake = _run_stream_tools(monkeypatch, q, ans, tl, query="荒诞 裂隙")
    text = "".join(ev.get("content", "") for ev in evs if ev["type"] == "token")
    assert "未能通过原典库核验" not in text, "禁止补丁式尾注"
    # O2-RP1: 无效候选零公开
    assert text == "", "repair 耗尽后不得发布无效候选"
    assert "某某秘传" not in text
    assert any(e["type"] == "validation_failed" for e in evs), "非语义 status 事件干净收口"
    done = next(ev for ev in evs if ev["type"] == "done")
    v = done["validation"]
    assert v["result"]["ok"] is False
    assert any(i["code"] == "UNVERIFIED_CITATION" and "某某秘传" in i["locator"]
               for i in v["result"]["issues"])
    assert v["repairs_used"] == 2, "repair 打回同一个 Main Agent（fake 恒同答 → 耗尽上限）"
    # 发布文本为空 → final-output 断言层无残留可披露; 引用面板自然为空
    san = done.get("citation_sanitize") or {}
    assert not (san.get("unverified_before") or []), "零发布 → 无未核验引用残留"
    assert (done.get("live_citation_sanitize") or {}).get("downgraded") == 0, "零降级改写"
    assert all(c["book"] != "某某秘传" for c in done["citations"]), "引用面板不得含未核验引用"


def test_uat_t6_embedding_429_fast_fallback(monkeypatch):
    # 引擎级 T6: 真实 search_books 工具轮 → 429 双失败 → 熔断 → 词法兜底 → 回答完成
    import engine_langgraph as elg
    _FAKE_EMBED["mode"] = "429_twice"
    q = "尼采的超人是什么？"
    ans = "超人是尼采在《查拉图斯特拉如是说》中提出的理想人格，要求自我超越。"

    class _FakeAppWithSearch(_FakeApp):
        async def astream(self, inputs, config, stream_mode="messages"):
            self.captured_messages.extend(inputs.get("messages") or [])
            yield (AIMessageChunk(content="", tool_call_chunks=[
                {"name": "search_books", "args": "{\"query\": \"超人 尼采\"}", "id": "c1", "index": 0}]),
                   {"langgraph_node": "agent"})
            real = AG._exec_search_books({"query": "超人 尼采", "limit": 3})
            yield (ToolMessage(content="{}", name="search_books", tool_call_id="c1",
                               additional_kwargs={"_args": {"query": "超人 尼采"},
                                                  "_result_full": real}),
                   {"langgraph_node": "tools"})
            yield AIMessageChunk(content=self.answer), {"langgraph_node": "agent"}

    fake = _FakeAppWithSearch(ans)
    monkeypatch.setattr(elg, "APP", fake)
    monkeypatch.setattr(AG, "llm_chat", lambda *a, **k: {"choices": [{"message": {"content": ""}}]})
    evs = asyncio.run(_collect_stream(elg, q))
    assert _FAKE_EMBED["calls"] == 2, "429 后最多 1 次短退避, 无长重试链"
    assert agent_core._embed_status["mode"] == "lexical", "熔断后 retrieval_mode=lexical"
    assert agent_core._embed_status["degraded_reason"] == "embedding_429_retry_exhausted"
    text = "".join(ev.get("content", "") for ev in evs if ev["type"] == "token")
    assert "超人" in text, "最终回答成功完成"
    done = next(ev for ev in evs if ev["type"] == "done")
    assert done["type"] == "done"
    assert (done.get("evidence") or {}).get("retrieved_count", 0) >= 1, "词法兜底检索照常产生证据"
    assert "rate limit" not in text.lower() and "Traceback" not in text, "用户正文不暴露内部异常"
