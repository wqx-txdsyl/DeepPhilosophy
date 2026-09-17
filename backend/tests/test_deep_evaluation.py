"""The evaluator must not turn partial delivery or private reasoning into success."""
import asyncio
from types import SimpleNamespace

from langchain_core.messages import ToolMessage

from tools.evaluate_deep_agent import collect_case, inspect_tool_context


def test_evaluation_requires_authoritative_completion_and_does_not_capture_private_events():
    async def stream(*_args, **_kwargs):
        yield {"type": "thought_stream", "content": "PRIVATE_SENTINEL"}
        yield {"type": "token", "content": "尚未完成"}
        yield {"type": "done", "content": "尚未完成", "complete": False}
    saved = []
    result = asyncio.run(collect_case(SimpleNamespace(stream_agent=stream),
                        {"id": "partial", "question": "fixture"}, 1, saved.append))
    assert result["answer"] == "尚未完成"
    assert result["transport_complete"] is False
    assert result["quality_verdict"] == "NOT_SCORED"
    assert "PRIVATE_SENTINEL" not in str(result)


def test_evaluation_timeout_closes_upstream_and_retains_received_answer():
    closed = []
    async def stream(*_args, **_kwargs):
        try:
            yield {"type": "token", "content": "已经收到的部分。"}
            await asyncio.Event().wait()
        finally:
            closed.append(True)
    result = asyncio.run(collect_case(SimpleNamespace(stream_agent=stream),
                        {"id": "timeout", "question": "fixture"}, .02, lambda _: None))
    assert closed == [True]
    assert result["execution_status"] == "timeout" and not result["transport_complete"]
    assert result["answer"] == "已经收到的部分。"


def test_tool_context_audit_measures_wire_content_not_hidden_full_result():
    hidden = {"argument": {"counterexample": "tail hidden from model"}}
    message = ToolMessage(content='{"argument":{"conclusion":"partial', name="analyze_argument",
                          tool_call_id="call", additional_kwargs={"_result_full": hidden})
    row = inspect_tool_context([message])[0]
    assert not row["json_valid"]
    assert "tail hidden from model" not in str(row)
    assert row["chars"] == len(message.content)
