"""Offline production-graph checks for general-only incremental delivery.

Thread gates establish causal streaming order without timing thresholds. Every
model/tool is a local stub; the real LangGraph and evidence validators still run.
"""
import asyncio
from collections import Counter
import json
from pathlib import Path
import sys
import threading

import pytest
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessageChunk
from langchain_core.outputs import ChatGenerationChunk
from langchain_core.tools import StructuredTool
from pydantic import Field

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import deep_streaming as DS
import engine_langgraph as EG
import mcp_client


FIRST = "一个选择会改变处境，但它是否值得，仍取决于我们愿意承担怎样的后果。\n\n"
LAST = "自由不保证选对，它使我们能够重新审视自己的理由。"
PRIVATE = "PRIVATE_PROVIDER_REASONING_ONLY_83A16"
FAKE_QUOTE = "人生只需成功就能免除所有责任这是完全伪造的原典引文"


class DeliveryScriptedChat(BaseChatModel):
    script: list = Field(default_factory=list)
    audit: list = Field(default_factory=list)
    idx: int = 0

    @property
    def _llm_type(self):
        return "offline-delivery-contract"

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        raise AssertionError("This test requires the production streaming callback path")

    def _stream(self, messages, stop=None, run_manager=None, **kwargs):
        assert self.idx < len(self.script), "Unexpected extra main-model invocation"
        round_index = self.idx
        round_ = self.script[self.idx]
        self.idx += 1
        self.audit.append(("model_started", round_index))
        reasoning = round_.get("reasoning", "")
        for offset in range(0, len(reasoning), 7):
            yield ChatGenerationChunk(message=AIMessageChunk(
                content="", additional_kwargs={"reasoning_content": reasoning[offset:offset + 7]}))
        for part in round_.get("parts", []):
            if isinstance(part, dict):
                if "gate" in part:
                    assert part["gate"].wait(3), "A published event did not unblock model/tool generation"
                if "mark" in part:
                    self.audit.append((part["mark"], round_index))
                if "raise" in part:
                    raise RuntimeError(part["raise"])
                continue
            yield ChatGenerationChunk(message=AIMessageChunk(content=part))
        for index, call in enumerate(round_.get("tool_calls", [])):
            yield ChatGenerationChunk(message=AIMessageChunk(content="", tool_call_chunks=[{
                "name": call["name"], "args": json.dumps(call.get("args", {}), ensure_ascii=False),
                "id": call["id"], "index": index, "type": "tool_call_chunk",
            }]))
        self.audit.append(("model_finished", round_index))
        yield ChatGenerationChunk(message=AIMessageChunk(
            content="", response_metadata={"finish_reason": round_.get("finish", "stop")}))


def install(monkeypatch, script, tools=()):
    model = DeliveryScriptedChat(script=script)
    monkeypatch.setattr(EG, "get_llm", lambda: model)
    monkeypatch.setattr(EG, "get_tools", lambda _agent: list(tools))
    monkeypatch.setattr(EG, "LOCAL_PATCH_PRODUCTION_ENABLED", False)
    monkeypatch.setattr(EG, "_llm_suggest", lambda *args: None)
    monkeypatch.setattr(EG, "_log_stats", lambda *args, **kwargs: None)
    monkeypatch.setattr(EG, "TOKEN_INTERVAL", 0)
    # Test failures are deterministic; they must not incur provider retry sleeps.
    monkeypatch.setitem(EG.AR.MODEL_RETRY, "attempts", 0)

    async def no_mcp():
        return []
    monkeypatch.setattr(mcp_client, "get_mcp_tools", no_mcp)
    return model


def collect(observer=None, agent="general"):
    async def run():
        events = []
        async for event in EG.stream_agent("请分析选择与责任，不要延伸建议。", [], agent=agent, language="zh"):
            events.append(event)
            if observer:
                observer(event)
        return events
    return asyncio.run(asyncio.wait_for(run(), timeout=12))


def of(events, kind):
    return [event for event in events if event.get("type") == kind]


def answer(events):
    return "".join(event.get("content", "") for event in of(events, "token"))


def successful_done(events):
    assert not of(events, "error"), of(events, "error")
    done = of(events, "done")
    assert len(done) == 1
    assert done[0]["complete"] is True
    assert done[0]["content"] == answer(events)
    return done[0]


def all_string_values(value):
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return "".join(all_string_values(v) for v in value.values())
    if isinstance(value, (tuple, list)):
        return "".join(all_string_values(v) for v in value)
    return ""


def test_first_validated_paragraph_arrives_before_the_last_tokens_exist(monkeypatch):
    release_tail = threading.Event()
    model = install(monkeypatch, [{
        "reasoning": PRIVATE,
        "parts": list("<rationale>先辨别可选择的目标与需要承担的后果。</rationale><answer>" + FIRST)
                 + [{"gate": release_tail}, {"mark": "tail_generated"}, LAST, "</answer>"],
    }])
    early = []

    def observe(event):
        if event.get("type") == "token" and not early:
            early.append(event)
            assert ("tail_generated", 0) not in model.audit
            assert ("model_finished", 0) not in model.audit
            assert event["content"] == FIRST
            assert event["validated"] is True
            release_tail.set()

    events = collect(observe)
    successful_done(events)
    assert early and answer(events) == FIRST + LAST
    notes = "".join(e.get("content", "") for e in of(events, "thinking_summary_delta"))
    assert notes == "先辨别可选择的目标与需要承担的后果。"
    assert "".join(e["content"] for e in of(events, "provider_reasoning_delta")) == PRIVATE
    assert PRIVATE not in all_string_values([e for e in events if e["type"] != "provider_reasoning_delta"])
    assert "<answer>" not in all_string_values(events)
    assert "<rationale>" not in all_string_values(events)


def test_provider_reasoning_arrives_incrementally_before_answer_generation(monkeypatch):
    release_answer = threading.Event()
    model = install(monkeypatch, [{"reasoning": PRIVATE,
        "parts": [{"gate": release_answer}, {"mark": "answer_started"}, "<answer>", FIRST, LAST, "</answer>"]}])
    received = []

    def observe(event):
        if event["type"] == "provider_reasoning_delta":
            assert ("answer_started", 0) not in model.audit
            assert event["source"] == "deepseek"
            received.append(event["content"])
            if "".join(received) == PRIVATE:
                release_answer.set()

    events = collect(observe)
    deltas = of(events, "provider_reasoning_delta")
    assert len(deltas) > 1
    assert len({e["id"] for e in deltas}) == 1
    assert "".join(e["content"] for e in deltas) == PRIVATE
    assert PRIVATE not in all_string_values(successful_done(events))


def test_provider_reasoning_recovery_uses_separate_round_ids(monkeypatch):
    install(monkeypatch, [
        {"reasoning": "first attempt", "finish": "length"},
        {"reasoning": "second attempt", "parts": ["<answer>", FIRST, LAST, "</answer>"]},
    ])
    events = collect()
    rounds = {}
    for e in of(events, "provider_reasoning_delta"):
        rounds[e["id"]] = rounds.get(e["id"], "") + e["content"]
    assert list(rounds.values()) == ["first attempt", "second attempt"]
    successful_done(events)


def test_plan_only_recovery_cannot_publish_a_length_truncated_response(monkeypatch):
    install(monkeypatch, [
        {"parts": ["<answer>我将检索相关原文。</answer>"]},
        {"parts": ["<answer>", FIRST, "这个判断仍然取决于"], "finish": "length"},
    ])
    events = collect()
    assert any(event.get("code") == "INCOMPLETE_RESPONSE" for event in of(events, "error"))
    assert not of(events, "done")


def test_closing_general_stream_cancels_an_inflight_async_provider(monkeypatch):
    class AsyncCancellationChat(DeliveryScriptedChat):
        async def _astream(self, messages, stop=None, run_manager=None, **kwargs):
            try:
                yield ChatGenerationChunk(message=AIMessageChunk(content="<answer>" + FIRST))
                await asyncio.Event().wait()
            finally:
                self.audit.append(("provider_cancelled", 0))

    install(monkeypatch, [])
    model = AsyncCancellationChat()
    monkeypatch.setattr(EG, "get_llm", lambda: model)

    async def run():
        stream = EG.stream_agent("请分析选择与责任。", [], agent="general", language="zh")
        async for event in stream:
            if event.get("type") == "token":
                assert event["content"] == FIRST
                break
        await stream.aclose()
        async def cancelled():
            while ("provider_cancelled", 0) not in model.audit:
                await asyncio.sleep(0)
        await asyncio.wait_for(cancelled(), timeout=2)

    asyncio.run(asyncio.wait_for(run(), timeout=5))


def test_bad_later_quote_is_repaired_without_replaying_or_rewriting_published_prefix(monkeypatch):
    bad = FIRST + "> " + FAKE_QUOTE + "\n\n这段话目前没有可核对的来源。"
    repaired = FIRST + "这里应当区分是否愿意承担责任与是否碰巧获得好结果，不能拿一句未经核验的话替代论证。"
    model = install(monkeypatch, [
        {"parts": ["<answer>", FIRST, bad[len(FIRST):], "</answer>"]},
        {"parts": ["<answer>", repaired, "</answer>"]},
    ])
    events = collect()
    done = successful_done(events)
    assert model.idx == 2 and done["validation"]["repairs_used"] == 1
    assert answer(events) == repaired
    assert answer(events).count(FIRST) == 1
    assert FAKE_QUOTE not in answer(events)
    assert of(events, "token")[0]["content"] == FIRST


def test_repair_cannot_change_already_published_text(monkeypatch):
    model = install(monkeypatch, [
        {"parts": ["<answer>", FIRST, "> " + FAKE_QUOTE, "</answer>"]},
        {"parts": ["<answer>已经发布的第一段被我改成了相反的判断。现在的问题需要重新讨论。</answer>"]},
    ])
    events = collect()
    assert model.idx == 2
    assert answer(events) == FIRST
    assert any(e.get("code") == "PUBLISHED_PREFIX_CHANGED" for e in of(events, "error"))
    assert not any(e.get("complete") for e in of(events, "done"))


def test_late_safety_handling_cannot_desynchronize_done_from_visible_prefix(monkeypatch):
    install(monkeypatch, [{"parts": ["<answer>", FIRST,
        "面对如何自杀这类问题，应当鼓励当事人寻求现实中的支持。", "</answer>"]}])
    events = collect()
    complete = [e for e in of(events, "done") if e.get("complete")]
    if complete:
        assert complete[0]["content"] == answer(events)
    else:
        assert of(events, "error")


@pytest.mark.parametrize("unfinished", [
    "第一句已经结束。\n\n“跨段引文还没有闭合\n\n",
    "第一句已经结束。\n\n```text\n尚未闭合的围栏\n\n",
    "第一句已经结束。\n\n~~~text\n尚未闭合的围栏\n\n",
    "第一句已经结束。\n\n来源是【《论语》·学而篇\n\n",
    "第一句已经结束。\n\n> 引文还有后续来源标注\n\n",
])
def test_unfinished_markup_never_becomes_a_published_paragraph(unfinished):
    prefix = DS.complete_paragraph_prefix(unfinished)
    assert not prefix or prefix == "第一句已经结束。\n\n"


def test_closed_quote_and_split_citation_remain_buffered_until_source_is_verifiable(monkeypatch):
    model = install(monkeypatch, [
        {"parts": ["<answer>", FIRST, "> " + FAKE_QUOTE + "\n\n", "【《不存在之书》", "·第一章】\n\n", LAST, "</answer>"]},
        {"parts": ["<answer>", FIRST + LAST, "</answer>"]},
    ])
    events = collect()
    successful_done(events)
    assert model.idx == 2
    assert answer(events) == FIRST + LAST
    assert FAKE_QUOTE not in answer(events)
    assert "不存在之书" not in answer(events)


def test_length_continues_once_with_exactly_matching_done_content(monkeypatch):
    fragment = FIRST + "因为选择的后果"
    suffix = "也取决于他人是否愿意共同承担。"
    model = install(monkeypatch, [
        {"parts": ["<answer>", fragment], "finish": "length"},
        {"parts": ["<answer>", suffix, "</answer>"]},
    ])
    events = collect()
    successful_done(events)
    assert model.idx == 2
    assert answer(events) == fragment + suffix
    assert answer(events).count(FIRST) == 1


@pytest.mark.parametrize("parts", [[], ["<rationale>先核对问题的条件。</rationale> \n"]])
def test_reasoning_only_length_starts_a_complete_answer_without_inventing_a_prefix(monkeypatch, parts):
    model = install(monkeypatch, [
        {"reasoning": PRIVATE, "parts": parts, "finish": "length"},
        {"parts": ["<answer>", FIRST, LAST, "</answer>"]},
    ])
    inputs = []
    invoke = EG._agent_llm_invoke

    async def capture(agent, messages, **kwargs):
        inputs.append([(m.type, m.content) for m in messages])
        return await invoke(agent, messages, **kwargs)

    monkeypatch.setattr(EG, "_agent_llm_invoke", capture)
    events = collect()
    successful_done(events)
    assert model.idx == 2 and answer(events) == FIRST + LAST
    assert not any(kind == "ai" and not content.strip() for kind, content in inputs[1])
    recovery_request = next(content for kind, content in reversed(inputs[1]) if kind == "human")
    assert "尚未生成回答正文" in recovery_request
    assert "断点" not in recovery_request and "已有段落" not in recovery_request
    assert PRIVATE not in all_string_values([e for e in events if e["type"] != "provider_reasoning_delta"])


@pytest.mark.parametrize("prefix", ["", FIRST + "因为选择的后果"])
def test_length_recovery_preserves_completed_tool_context_without_reexecuting_it(monkeypatch, prefix):
    calls = []
    evidence = "RECOVERY_EVIDENCE_5D384：这是已经取得而不可凭空补造的材料。"

    def probe():
        calls.append(True)
        return {"text": evidence}

    tool = StructuredTool.from_function(func=probe, name="probe", description="Offline fixture")
    suffix = LAST if not prefix else "也需要认真面对。"
    model = install(monkeypatch, [
        {"tool_calls": [{"name": "probe", "args": {}, "id": "preserve-evidence"}]},
        {"parts": ["<answer>", prefix] if prefix else [], "finish": "length"},
        {"parts": ["<answer>", suffix, "</answer>"]},
    ], [tool])
    inputs = []
    invoke = EG._agent_llm_invoke

    async def capture(agent, messages, **kwargs):
        inputs.append([(m.type, m.content, getattr(m, "tool_calls", None),
                        getattr(m, "tool_call_id", None)) for m in messages])
        return await invoke(agent, messages, **kwargs)

    monkeypatch.setattr(EG, "_agent_llm_invoke", capture)
    events = collect()
    successful_done(events)
    assert model.idx == 3 and calls == [True]
    assert answer(events) == prefix + suffix
    recovery_input = inputs[2]
    assert any(kind == "tool" and evidence in content and call_id == "preserve-evidence"
               for kind, content, _, call_id in recovery_input)
    assert any(kind == "ai" and any(call.get("id") == "preserve-evidence" for call in (tool_calls or []))
               for kind, _, tool_calls, _ in recovery_input)


def test_reasoning_only_length_recovery_that_still_has_no_answer_never_completes(monkeypatch):
    model = install(monkeypatch, [
        {"reasoning": PRIVATE, "finish": "length"},
        {"reasoning": PRIVATE, "finish": "stop"},
    ])
    events = collect()
    assert model.idx == 2
    assert not answer(events) and not of(events, "done")
    assert any(e.get("code") == "INCOMPLETE_RESPONSE" for e in of(events, "error"))
    assert PRIVATE not in all_string_values(events)


@pytest.mark.parametrize("second_round", [
    {"parts": ["<answer>仍然没有写完"], "finish": "length"},
    {"parts": [{"raise": "Offline continuation deliberately failed"}]},
])
def test_failed_continuation_keeps_visible_prefix_but_never_claims_complete(monkeypatch, second_round):
    model = install(monkeypatch, [
        {"parts": ["<answer>", FIRST, "这一部分尚未写完"], "finish": "length"},
        second_round,
    ])
    events = collect()
    assert model.idx == 2
    assert answer(events) == FIRST
    assert any(e.get("code") == "INCOMPLETE_RESPONSE" for e in of(events, "error"))
    assert not any(e.get("complete") for e in of(events, "done"))


def test_transport_failure_after_a_published_paragraph_is_not_success(monkeypatch):
    model = install(monkeypatch, [
        {"parts": ["<answer>", FIRST, {"raise": "Offline stream deliberately interrupted"}]},
        {"parts": [{"raise": "Offline continuation deliberately failed"}]},
    ])
    events = collect()
    assert model.idx == 2
    assert answer(events) == FIRST
    assert of(events, "error") and not any(e.get("complete") for e in of(events, "done"))


def test_complete_retry_after_an_empty_failure_does_not_trigger_an_extra_continuation(monkeypatch):
    model = install(monkeypatch, [
        {"parts": [{"raise": "Offline first attempt deliberately failed before any prose"}]},
        {"parts": ["<answer>", FIRST, LAST, "</answer>"]},
    ])
    events = collect()
    successful_done(events)
    assert model.idx == 2
    assert answer(events) == FIRST + LAST
    assert not any(e.get("content") == "正在补全回答" for e in of(events, "status"))


def test_parallel_same_named_tools_deliver_fast_sibling_before_slow_finishes_once(monkeypatch):
    slow_started, release_slow = threading.Event(), threading.Event()
    actual_calls = []

    def search_books(query: str):
        actual_calls.append(("search_books", query))
        if query == "康德":
            slow_started.set()
            assert release_slow.wait(3), "Fast result was held behind its slow sibling"
        else:
            assert slow_started.wait(3)
        return {"results": [{"book_id": query, "book_title": query, "chapter_title": "序言",
                              "chapter_idx": 0, "snippet": "测试材料用于检验并行事件交付。", "score": 1}]}

    def get_book_detail(book_id: str):
        actual_calls.append(("get_book_detail", book_id))
        return {"book_id": book_id, "title": "论语", "chapters": []}

    tools = [StructuredTool.from_function(func=fn, name=fn.__name__, description="Offline fixture")
             for fn in (search_books, get_book_detail)]
    declaration = {"name": "declare_research_need", "id": "need", "args": {
        "research_need": "PRIMARY", "evidence_gap": "核对三处文本信息", "source_dependent": True}}
    install(monkeypatch, [
        {"parts": ["先检查几处独立来源。"], "tool_calls": [declaration,
            {"name": "search_books", "args": {"query": "康德"}, "id": "slow"},
            {"name": "search_books", "args": {"query": "荀子"}, "id": "fast"},
            {"name": "get_book_detail", "args": {"book_id": "论语"}, "id": "detail"}]},
        {"parts": ["<answer>", FIRST + LAST, "</answer>"]},
    ], tools)
    completion_order = []

    def observe(event):
        if event.get("type") == "tool":
            call_id = event.get("call_id")
            completion_order.append(call_id)
            if call_id == "fast":
                assert "slow" not in completion_order
                release_slow.set()

    events = collect(observe)
    done = successful_done(events)
    assert release_slow.is_set()
    assert Counter(e.get("call_id") for e in of(events, "tool_start")) == Counter(
        {"need": 1, "slow": 1, "fast": 1, "detail": 1})
    assert Counter(completion_order) == Counter({"need": 1, "slow": 1, "fast": 1, "detail": 1})
    assert len(actual_calls) == 3
    assert done["tool_loop"]["budget"]["total_executed"] == 3


def test_tool_declaration_after_answer_start_never_executes_or_completes(monkeypatch):
    called = []

    def probe():
        called.append(True)
        return {"ok": True}

    install(monkeypatch, [{"parts": ["<answer>", FIRST],
                           "tool_calls": [{"name": "probe", "args": {}, "id": "late"}]}],
            [StructuredTool.from_function(func=probe, name="probe", description="Offline fixture")])
    events = collect()
    assert answer(events) == FIRST
    assert not called
    assert any(e.get("code") == "ANSWER_PROTOCOL_ERROR" for e in of(events, "error"))
    assert not any(e.get("complete") for e in of(events, "done"))


def test_oversized_tool_artifact_reports_incomplete_delivery_separately_from_execution(monkeypatch):
    raw = {"argument": {"conclusion": "初始结论", "body": "长" * 25000, "strongest_reply": "最后的反驳"}}
    tool = StructuredTool.from_function(func=lambda text: raw, name="analyze_argument", description="Offline fixture")
    install(monkeypatch, [
        {"tool_calls": [{"name": "analyze_argument", "args": {"text": "论证"}, "id": "oversized"}]},
        {"parts": ["<answer>", FIRST + LAST, "</answer>"]},
    ], [tool])
    events = collect()
    done = successful_done(events)
    event = of(events, "tool")[0]
    assert event["status"] == "error" and event["delivery_status"] == "incomplete"
    assert event["execution_status"] == "success" and event["summary"] == "结果未完整传递。"
    assert done["tool_calls"][0]["context_delivery"]["status"] == "omitted"
    assert raw["argument"]["strongest_reply"] == "最后的反驳"


def test_legacy_unwrapped_answer_stays_buffered_until_model_finishes(monkeypatch):
    model = install(monkeypatch, [{"parts": [FIRST, LAST]}])

    def observe(event):
        if event.get("type") == "token":
            assert ("model_finished", 0) in model.audit

    events = collect(observe)
    successful_done(events)
    assert answer(events) == FIRST + LAST


def test_nietzsche_keeps_legacy_buffered_tokens_and_event_contract(monkeypatch):
    model = install(monkeypatch, [{"reasoning": PRIVATE,
                                   "parts": ["<rationale>先看这句话包含什么判断。</rationale>", FIRST, LAST]}])

    def observe(event):
        if event.get("type") == "token":
            assert ("model_finished", 0) in model.audit
            assert "validated" not in event and len(event["content"]) == 1

    events = collect(observe, agent="nietzsche")
    assert not of(events, "error")
    done = of(events, "done")[0]
    assert "content" not in done and "complete" not in done
    assert done["research_discipline"] is None
    assert answer(events) == FIRST + LAST
    assert of(events, "thinking_summary") and not of(events, "thinking_summary_delta")
    assert PRIVATE not in all_string_values(events)


def test_repeated_answer_opening_is_a_protocol_error_not_visible_markup(monkeypatch):
    install(monkeypatch, [{"parts": ["<answer>", FIRST, "<ans", "wer>", LAST, "</answer>"]}])
    events = collect()
    assert "<answer>" not in answer(events)
    assert of(events, "error")
    assert not any(e.get("complete") for e in of(events, "done"))


def test_explicit_envelope_does_not_promote_preceding_work_note_to_answer(monkeypatch):
    work_note = "这一段是准备核对问题的公开工作笔记。\n\n"
    install(monkeypatch, [{"parts": [work_note, "<answer>", FIRST, LAST, "</answer>"]}])
    events = collect()
    successful_done(events)
    assert answer(events) == FIRST + LAST
    assert work_note not in answer(events)


def test_repeating_the_whole_prefix_is_not_a_valid_length_continuation(monkeypatch):
    model = install(monkeypatch, [
        {"parts": ["<answer>", FIRST, "这一部分尚未写完"], "finish": "length"},
        {"parts": ["<answer>", FIRST, LAST, "</answer>"]},
    ])
    events = collect()
    assert model.idx == 2
    assert answer(events).count(FIRST) == 1
    if any(e.get("complete") for e in of(events, "done")):
        successful_done(events)
        # A full replacement is safe only when it preserves the delivered prefix
        # and replaces the unpublished interrupted fragment rather than appending.
        assert answer(events) == FIRST + LAST
    else:
        assert of(events, "error")


@pytest.mark.parametrize("message", [
    "请用不超过120个汉字的一段自然话回答，不要标题、列表、反问或延伸建议。",
    "不要延伸建议。",
    "总共不超过200字，不加延伸建议。",
    "不附后续问题。",
    "不提供追问。",
    "Don't add follow-up suggestions.",
    "Answer without adding any follow-up questions.",
])
def test_explicit_suggestion_opt_out_includes_negative_list_scope(message):
    assert DS.wants_suggestions(message) is False


def test_unrelated_negation_does_not_disable_requested_suggestions():
    assert DS.wants_suggestions("请不要省略例子，但可以给出后续建议。") is True


def test_followup_suggestion_preference_comes_from_current_question():
    context = {'原问题与附件': '旧问题，不加延伸建议。', '指定回答对应问题': '旧问题', '指定回答': '旧回答', '本次追问': '请查阅相关原典。'}
    message = '请围绕下列指定回答继续讨论。\n<general_followup_context>\n' + json.dumps(context, ensure_ascii=False) + '\n</general_followup_context>'
    assert DS.wants_suggestions(message) is True
    assert DS.suggestion_question(message) == context['本次追问']
    malformed = message.replace(json.dumps(context, ensure_ascii=False), json.dumps(list(context), ensure_ascii=False))
    assert DS.suggestion_question(malformed) == malformed
