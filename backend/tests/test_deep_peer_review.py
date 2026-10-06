import asyncio
import json

import httpx
import pytest

from deep_peer_review import ReviewConfig, ReviewConfigurationError, parse_review, request_review, review_messages

TEXT = "A shared benefit automatically creates a payment obligation."


def config(**kwargs):
    return ReviewConfig("https://review.example/v1", "review-model", "PRIVATE_KEY", **kwargs)


def response(content, finish="stop", **extra):
    return httpx.Response(200, json={"model": "actual-review-model", "choices": [{"finish_reason": finish,
        "message": {"content": content, "reasoning_content": "PRIVATE_REASONING"}}], **extra})


def test_disabled_review_never_constructs_a_client(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: pytest.fail("No network while disabled"))
    assert ReviewConfig.from_env({"DEEP_REVIEW_API_KEY": "PRIVATE_KEY"}) is None
    assert asyncio.run(request_review(None, "q", TEXT))["status"] == "disabled"


def test_configuration_is_explicit_and_does_not_expose_credentials():
    assert "PRIVATE_KEY" not in repr(config())
    with pytest.raises(ReviewConfigurationError, match="Missing"):
        ReviewConfig.from_env({"DEEP_REVIEW_ENABLED": "true"})
    for url in ("http://public.example/v1", "https://user:PRIVATE_KEY@example.org/v1", "https://example.org/v1?key=PRIVATE_KEY"):
        with pytest.raises(ReviewConfigurationError) as caught:
            ReviewConfig.from_env({"DEEP_REVIEW_ENABLED": "1", "DEEP_REVIEW_BASE_URL": url,
                                   "DEEP_REVIEW_MODEL": "model", "DEEP_REVIEW_API_KEY": "PRIVATE_KEY"})
        assert "PRIVATE_KEY" not in str(caught.value)


def test_review_materials_preserve_scope_and_only_allow_explicit_source_fields():
    messages = review_messages("original question", TEXT, [{"id": "read-1", "text": "actual passage",
        "scope": "search_excerpt", "reasoning_content": "PRIVATE_REASONING", "api_key": "PRIVATE_KEY"}])
    sent = json.loads(messages[1]["content"])
    assert sent["candidate"] == TEXT and sent["evidence"][0]["scope"] == "search_excerpt"
    assert "PRIVATE_" not in str(messages)
    with pytest.raises(ValueError, match="not truncated"):
        review_messages("q" * 100001, TEXT)


def test_review_requires_a_real_contiguous_candidate_quote():
    issue = {"quote": TEXT, "problem": "A bridging premise is missing.", "revision_direction": "State the relevant consent or reciprocity conditions."}
    assert parse_review(json.dumps({"issues": [issue]}), TEXT) == [issue]
    issue["quote"] = "A quote the candidate did not say"
    with pytest.raises(ValueError, match="exact candidate span"):
        parse_review(json.dumps({"issues": [issue]}), TEXT)


def test_real_request_shape_and_response_do_not_masquerade_as_semantic_certification():
    requests = []
    def handle(request):
        requests.append(request)
        return response('{"issues":[]}')
    result = asyncio.run(request_review(config(token_parameter="max_completion_tokens"), "q", TEXT,
                         transport=httpx.MockTransport(handle)))
    body = json.loads(requests[0].content)
    assert body["max_completion_tokens"] == 16384 and "max_tokens" not in body
    assert requests[0].headers["authorization"] == "Bearer PRIVATE_KEY"
    assert result["status"] == "reviewed" and result["semantic_verdict"] == "ADVISORY_ONLY"
    assert result["final_answer_owner"] == "MAIN_AGENT" and result["requested_model"] == "review-model"
    assert "PRIVATE_" not in str(result)


@pytest.mark.parametrize("reply,expected", [(response('{"issues":[]}', "length"), "incomplete"),
    (response('{"issues":'), "invalid"), (response('{"issues":[{"quote":"invented","problem":"p","revision_direction":"r"}]}'), "invalid"),
    (httpx.Response(302, headers={"location": "https://other.example"}), "unavailable"),
    (httpx.Response(500, text="PRIVATE_KEY PRIVATE_REASONING"), "unavailable")])
def test_invalid_partial_or_redirected_reviews_do_not_trigger_retries_or_pass(reply, expected):
    calls = []
    result = asyncio.run(request_review(config(), "q", TEXT,
        transport=httpx.MockTransport(lambda request: calls.append(request) or reply)))
    assert len(calls) == 1 and result["status"] == expected
    assert result["semantic_verdict"] == "NOT_ASSESSED" and "PRIVATE_" not in str(result)


def test_timeout_closes_transport_without_hiding_cancellation():
    closed = []
    async def handle(request):
        try:
            await asyncio.Event().wait()
        finally:
            closed.append(True)
    result = asyncio.run(request_review(config(timeout_seconds=.01), "q", TEXT,
                         transport=httpx.MockTransport(handle)))
    assert result["error"] == "REVIEW_TIMEOUT" and closed == [True]


@pytest.mark.parametrize("body", [[], {"choices": ["unexpected"]}, {"choices": []},
    {"choices": [{"finish_reason": "stop", "message": []}]},
    {"choices": [{"finish_reason": "stop", "message": {"content": {}}}]}])
def test_malformed_envelopes_are_reported_without_an_unhandled_exception(body):
    result = asyncio.run(request_review(config(), "q", TEXT,
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=body))))
    assert result["status"] == "invalid" and result["semantic_verdict"] == "NOT_ASSESSED"


def test_provider_metadata_and_excessive_body_are_not_copied_to_result():
    result = asyncio.run(request_review(config(), "q", TEXT, transport=httpx.MockTransport(lambda request:
        httpx.Response(200, json={"model": {"reasoning": "PRIVATE_REASONING"},
            "choices": [{"finish_reason": "PRIVATE_KEY"}]}))))
    assert result["status"] == "incomplete" and result["finish_reason"] == "unknown"
    assert "PRIVATE_" not in str(result)
    result = asyncio.run(request_review(config(), "q", TEXT,
        transport=httpx.MockTransport(lambda request: httpx.Response(200, content=b"x" * (512 * 1024 + 1)))))
    assert result["error"] == "REVIEW_RESPONSE_TOO_LARGE" and result["semantic_verdict"] == "NOT_ASSESSED"


def test_cancel_propagates_and_closes_the_active_transport():
    closed = []
    async def scenario():
        started = asyncio.Event()
        async def handle(request):
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                closed.append(True)
        task = asyncio.create_task(request_review(config(), "q", TEXT, transport=httpx.MockTransport(handle)))
        await started.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    asyncio.run(scenario())
    assert closed == [True]


def test_invalid_source_types_are_rejected_before_any_request():
    for evidence in ("not a source list", [{"text": "public", "scope": {"private": "reasoning"}}]):
        with pytest.raises(ValueError):
            review_messages("q", TEXT, evidence)


def test_cli_does_not_overwrite_reports_or_call_a_disabled_reviewer(tmp_path, monkeypatch):
    from tools.review_deep_candidate import evaluate
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "result.json"
    input_path.write_text(json.dumps({"question": "q", "candidate": TEXT}), encoding="utf-8")
    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: pytest.fail("No network while disabled"))
    assert evaluate(None, input_path, output_path) == 2
    saved = output_path.read_text()
    assert json.loads(saved)["result"]["status"] == "disabled"
    assert evaluate(config(), input_path, output_path) == 2
    assert output_path.read_text() == saved


def test_cli_rejects_unknown_input_fields_before_creating_a_report(tmp_path):
    from tools.review_deep_candidate import evaluate
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "result.json"
    input_path.write_text(json.dumps({"question": "q", "candidate": TEXT, "reasoning_content": "PRIVATE_REASONING"}))
    assert evaluate(None, input_path, output_path) == 2
    assert not output_path.exists()


def test_loopback_review_bypasses_environment_proxy(monkeypatch):
    calls = {"target": 0, "proxy": 0}
    async def scenario():
        async def respond(reader, writer, kind):
            try:
                headers = await reader.readuntil(b"\r\n\r\n")
                length = next((int(line.split(b":", 1)[1]) for line in headers.split(b"\r\n")
                               if line.lower().startswith(b"content-length:")), 0)
                await reader.readexactly(length)
                calls[kind] += 1
                body = json.dumps({"choices": [{"finish_reason": "stop", "message": {"content": '{"issues":[]}'}}]}).encode()
                writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: " + str(len(body)).encode() + b"\r\nConnection: close\r\n\r\n" + body)
                await writer.drain()
            finally:
                writer.close()
                await writer.wait_closed()
        target = await asyncio.start_server(lambda r, w: respond(r, w, "target"), "127.0.0.1", 0)
        proxy = await asyncio.start_server(lambda r, w: respond(r, w, "proxy"), "127.0.0.1", 0)
        async with target, proxy:
            target_port = target.sockets[0].getsockname()[1]
            proxy_port = proxy.sockets[0].getsockname()[1]
            for name in ("HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy"):
                monkeypatch.setenv(name, f"http://127.0.0.1:{proxy_port}")
            for name in ("NO_PROXY", "no_proxy"):
                monkeypatch.setenv(name, "")
            result = await request_review(ReviewConfig(f"http://127.0.0.1:{target_port}/v1", "local", "LOCAL_TEST_KEY"), "q", TEXT)
            assert result["status"] == "reviewed"
    asyncio.run(scenario())
    assert calls == {"target": 1, "proxy": 0}
