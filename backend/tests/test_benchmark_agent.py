"""Offline event-protocol tests: never invoke the provider or production DB."""
import asyncio
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import benchmark_agent as bench
from deep_context import current_account_id, current_memory_key, current_memory_overlay


def case(cid="A01", follow=(), ready=True):
    return {"id": cid, "messages": [{"role": "user", "content": f"Question {cid}?"}],
            "follow_up_turns": list(follow), "manual_prompt_ready": ready,
            "fixture_id": None if ready else "web_timeout"}


def config(tmp_path, **kwargs):
    return bench.RunConfig(output=tmp_path / "run", skip_preflight=True, **kwargs)


def done(text="Answer", profile="2.0.0", **extra):
    return {"type": "done", "content": text, "complete": True, "finish_reason": "stop",
            "release": {"prompt_version": profile, "toolset_sha256": "tools-hash", "installed_tool_count": 33},
            "main_model_usage": {"scope": "main_agent_only", "usage": {"total_tokens": 42},
                                 "includes_auxiliary_tool_models": False,
                                 "provider_model_names": ["actual-provider-model"]}, **extra}


async def plain_stream(question, history, **kwargs):
    yield {"type": "token", "content": "Answer"}
    yield done(profile=kwargs["_evaluation_prompt_profile"])


def runtime(stream=plain_stream, preflight=None):
    def release(language, profile):
        return {"runtime_profile": "bare", "prompt_version": profile, "git_commit": "fixture-commit",
                "runtime_source_sha256": {"engine.py": "fixture-hash"}, "tracked_runtime_dirty": False}
    def prompt(language, profile):
        return {"version": profile, "text": f"Exact {profile} {language} prompt", "effective_sha256": "fixture-prompt"}
    return stream, release, prompt, {"release_version": "2.0.0"}, preflight or (
        lambda: {"ALL_PROVIDER_GATES_PASS": True})


def run_suite(tmp_path, cases=None, **kwargs):
    suite = tmp_path / "suite.jsonl"
    suite.write_text("\n".join(json.dumps(c) for c in cases or [case()]) + "\n")
    return bench.RunConfig(output=tmp_path / "run", suite=suite, skip_preflight=True, **kwargs)


def test_import_has_no_runtime_imports_or_network():
    script = (
        "import socket,sys,importlib.util; "
        "socket.socket.connect=lambda *a,**k: (_ for _ in ()).throw(AssertionError('network')); "
        f"spec=importlib.util.spec_from_file_location('isolated_bench',{str(Path(bench.__file__))!r}); "
        "module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module); "
        "assert 'engine_langgraph' not in sys.modules;assert 'routes.agent_llm' not in sys.modules"
    )
    subprocess.run([sys.executable, "-c", script], check=True, capture_output=True, text=True)


def test_done_breaks_outer_loop_and_closes_before_postprocessing(tmp_path):
    state = {"after": False, "closed": False}
    async def stream(*args, **kwargs):
        try:
            yield {"type": "answer_preview", "content": "Answer"}
            yield {"type": "token", "content": "Answer"}
            yield done()
            state["after"] = True
            raise AssertionError("Optional LLM postprocessing must never execute")
        finally:
            state["closed"] = True
    result = asyncio.run(bench.collect_turn("Q?", [], config(tmp_path), stream,
                                           conversation_id="test", turn=1))
    assert state == {"after": False, "closed": True}
    assert result["status"] == "DONE" and result["done_matches_tokens"] is True
    assert result["actual_model_names"] == ["actual-provider-model"]
    assert result["main_model_usage"]["scope"] == "main_agent_only"
    assert result["auxiliary_tool_model_usage"] == "not_reported"
    assert result["events"][-1]["event"]["type"] == "done"


def test_parallel_same_name_calls_and_reasoning_identifiers_are_lossless(tmp_path):
    source_events = [
        {"type": "status", "release": {"prompt_version": "2.0.0"}},
        {"type": "runtime_metadata", "release": {"prompt_version": "2.0.0", "toolset_sha256": "abc"}},
        {"type": "provider_reasoning_delta", "id": "r1", "decision_group_id": "g1", "content": "first"},
        {"type": "provider_reasoning_delta", "id": "r1", "decision_group_id": "g1", "content": " second"},
        {"type": "tool_start", "name": "search_books", "call_id": "c1", "decision_group_id": "g1"},
        {"type": "tool_start", "name": "search_books", "call_id": "c2", "decision_group_id": "g1"},
        {"type": "tool", "name": "search_books", "call_id": "c2", "decision_group_id": "g1",
         "result": {"text": "second", "nested": [1, 2]}, "status": "success"},
        {"type": "tool", "name": "search_books", "call_id": "c1", "decision_group_id": "g1",
         "result": "first", "status": "success"},
        {"type": "assistant_commentary", "id": "n1", "content": "A"},
        {"type": "assistant_commentary", "id": "n1", "content": "AB"},
        {"type": "token", "content": "Answer"}, done(),
    ]
    async def stream(*args, **kwargs):
        for event in source_events:
            yield event
    result = asyncio.run(bench.collect_turn("Q?", [], config(tmp_path), stream,
                                           conversation_id="test", turn=1))
    assert [frame["event"] for frame in result["events"]] == source_events
    assert [f["event"]["call_id"] for f in result["tool_events"]] == ["c1", "c2", "c2", "c1"]
    assert result["reasoning_segments"][0]["content"] == "first second"
    assert result["reasoning_segments"][0]["id"] == "r1"
    assert result["reasoning_segments"][0]["decision_group_id"] == "g1"
    assert result["reasoning_segments"][1]["content"] == "AB"
    times = [frame["relative_seconds"] for frame in result["events"]]
    assert times == sorted(times)
    assert all(segment["ended_seconds"] >= segment["started_seconds"] for segment in result["reasoning_segments"])


def test_mutating_release_after_yield_cannot_rewrite_saved_status(tmp_path):
    async def stream(*args, **kwargs):
        release = {"prompt_version": "2.0.0"}
        yield {"type": "status", "release": release}
        release["toolset_sha256"] = "later"
        yield {"type": "runtime_metadata", "release": release}
        yield {"type": "token", "content": "Answer"}
        yield done()
    result = asyncio.run(bench.collect_turn("Q?", [], config(tmp_path), stream,
                                           conversation_id="test", turn=1))
    assert "toolset_sha256" not in result["events"][0]["event"]["release"]
    assert result["events"][1]["event"]["release"]["toolset_sha256"] == "later"


def test_parallel_cases_isolate_history_memory_account_and_prompt_profile(tmp_path):
    observations = []
    async def stream(question, history, **kwargs):
        overlay = current_memory_overlay.get()
        observations.append({"question": question, "history": deepcopy(history),
                             "scope": current_memory_key.get(), "account": current_account_id.get(),
                             "previous": overlay.get("marker"), "profile": kwargs["_evaluation_prompt_profile"]})
        overlay["marker"] = question
        await asyncio.sleep(0)
        answer = "Reply " + question
        yield {"type": "token", "content": answer}
        yield done(answer, kwargs["_evaluation_prompt_profile"])
    async def run():
        account_token = current_account_id.set(991)
        memory_token = current_memory_key.set("real-user-scope")
        try:
            results = await asyncio.gather(
                bench.collect_case(case("J01", ["Follow up?"]), config(tmp_path), stream, "fp"),
                bench.collect_case(case("J02", ["Another follow up?"]),
                                   config(tmp_path, prompt_profile="1.1.0"), stream, "fp"))
            assert current_account_id.get() == 991 and current_memory_key.get() == "real-user-scope"
            return results
        finally:
            current_account_id.reset(account_token)
            current_memory_key.reset(memory_token)
    results = asyncio.run(run())
    first, second = observations[:2]
    assert first["scope"] != second["scope"] and all(o["scope"].startswith("u:bench:") for o in observations)
    assert all(o["account"] is None for o in observations)
    assert all(o["history"] == [] and o["previous"] is None for o in observations[:2])
    for follow in observations[2:]:
        own_first = next(o for o in observations[:2] if o["scope"] == follow["scope"])
        assert follow["previous"] == own_first["question"]
        assert follow["history"] == [{"role": "user", "content": own_first["question"]},
                                     {"role": "assistant", "content": "Reply " + own_first["question"]}]
        assert follow["profile"] == own_first["profile"]
    assert all(r["complete"] for r in results)


def test_fixture_cases_are_skipped_without_stream_or_account_context(tmp_path):
    def forbidden(*args, **kwargs):
        raise AssertionError("K fixture was executed")
    result = asyncio.run(bench.collect_case(case("K01", ready=False), config(tmp_path), forbidden, "fp"))
    assert result["status"] == "SKIPPED_NOT_READY" and result["complete"] and result["turns"] == []


@pytest.mark.parametrize("mode,status", [("mismatch", "TOKEN_MISMATCH"), ("length", "DONE_INCOMPLETE"),
                                         ("ended", "STREAM_END_NO_DONE"), ("profile", "RELEASE_MISMATCH")])
def test_incomplete_turns_are_not_reusable(tmp_path, mode, status):
    async def stream(*args, **kwargs):
        yield {"type": "token", "content": "Answer"}
        if mode != "ended":
            yield done("Different" if mode == "mismatch" else "Answer",
                       "1.1.0" if mode == "profile" else "2.0.0",
                       finish_reason="length" if mode == "length" else "stop")
    result = asyncio.run(bench.collect_case(case(), config(tmp_path), stream, "fp"))
    assert result["turns"][0]["status"] == status and result["complete"] is False
    assert bench.reusable_trace(result, case(), "fp") is False


def test_timeout_closes_generator_and_preserves_partial_events(tmp_path):
    closed = []
    async def stream(*args, **kwargs):
        try:
            yield {"type": "provider_reasoning_delta", "id": "r1", "content": "partial"}
            await asyncio.sleep(10)
        finally:
            closed.append(True)
    result = asyncio.run(bench.collect_case(case(), config(tmp_path, turn_timeout=0.01), stream, "fp"))
    assert result["turns"][0]["status"] == "EVALUATION_TIMEOUT" and closed == [True]
    assert result["turns"][0]["events"][0]["event"]["content"] == "partial"


def test_atomic_run_snapshots_and_matching_resume_do_not_rerun(tmp_path):
    calls = []
    async def stream(question, history, **kwargs):
        calls.append(question)
        async for event in plain_stream(question, history, **kwargs):
            yield event
    cfg = run_suite(tmp_path, [case(), case("K01", ready=False)])
    first = asyncio.run(bench.run_benchmark(cfg, runtime=runtime(stream), sources={"dirty_paths": [{"path": "edited.py"}]}))
    assert first["status"] == "COMPLETED"
    assert first["attempts"][0]["preflight"]["status"] == "SKIPPED"
    assert first["configuration"]["prompt"]["text"] == "Exact 2.0.0 zh prompt"
    assert (cfg.output / "_SUITE.jsonl").read_bytes() == cfg.suite.read_bytes()
    assert (cfg.output / "_PROMPT.txt").read_text() == "Exact 2.0.0 zh prompt"
    assert json.loads((cfg.output / "_RELEASE_MANIFEST.json").read_text()) == {"release_version": "2.0.0"}
    trace_before = (cfg.output / "A01.json").read_bytes()
    second = asyncio.run(bench.run_benchmark(cfg, runtime=runtime(stream), sources={}))
    assert calls == ["Question A01?"] and second["attempts"][-1]["reused_cases"] == ["A01", "K01"]
    assert (cfg.output / "A01.json").read_bytes() == trace_before


@pytest.mark.parametrize("change", ["profile", "concurrency", "question", "source", "stored_case"])
def test_resume_conflict_is_detected_before_writes_or_provider_calls(tmp_path, change):
    cfg = run_suite(tmp_path)
    asyncio.run(bench.run_benchmark(cfg, runtime=runtime(), sources={}))
    changed_runtime = runtime()
    if change == "profile":
        cfg = replace(cfg, prompt_profile="1.1.0")
    elif change == "concurrency":
        cfg = replace(cfg, concurrency=3)
    elif change == "question":
        modified = case(); modified["messages"][0]["content"] = "Changed question?"
        cfg.suite.write_text(json.dumps(modified))
    elif change == "source":
        values = list(changed_runtime)
        release = values[1]("zh", "2.0.0")
        release["runtime_source_sha256"]["engine.py"] = "changed-hash"
        values[1] = lambda *args: release
        changed_runtime = tuple(values)
    else:
        path = cfg.output / "A01.json"
        trace = json.loads(path.read_text()); trace["question_fingerprint"] = "tampered"
        bench.atomic_json(path, trace)
    before = {p.name: p.read_bytes() for p in cfg.output.iterdir() if p.is_file()}
    with pytest.raises(bench.ResumeConflict):
        asyncio.run(bench.run_benchmark(cfg, runtime=changed_runtime, sources={}))
    assert before == {p.name: p.read_bytes() for p in cfg.output.iterdir() if p.is_file()}


def test_matching_partial_attempt_is_archived_and_restarted_with_fresh_scope(tmp_path):
    cfg = run_suite(tmp_path)
    async def partial(*args, **kwargs):
        yield {"type": "token", "content": "unfinished"}
    first = asyncio.run(bench.run_benchmark(cfg, runtime=runtime(partial), sources={}))
    before = json.loads((cfg.output / "A01.json").read_text())
    assert first["status"] == "INCOMPLETE"
    second = asyncio.run(bench.run_benchmark(cfg, runtime=runtime(), sources={}))
    assert second["status"] == "COMPLETED"
    after = json.loads((cfg.output / "A01.json").read_text())
    archives = list((cfg.output / "attempts").glob("A01-*.json"))
    assert len(archives) == 1 and json.loads(archives[0].read_text()) == before
    assert before["memory_scope"] != after["memory_scope"]


def test_resume_rechecks_raw_event_completeness(tmp_path):
    trace = asyncio.run(bench.collect_case(case(), config(tmp_path), plain_stream, "fp"))
    assert bench.reusable_trace(trace, case(), "fp") is True
    trace["turns"][0]["events"].pop()
    assert bench.reusable_trace(trace, case(), "fp") is False


def test_preflight_failure_blocks_execution_and_is_recorded(tmp_path):
    cfg = replace(run_suite(tmp_path), skip_preflight=False)
    def forbidden(*args, **kwargs):
        raise AssertionError("Model executed despite preflight failure")
    report = {"ALL_PROVIDER_GATES_PASS": False, "SCHOLARLY_CHANNEL_OK": False}
    result = asyncio.run(bench.run_benchmark(cfg, runtime=runtime(forbidden, lambda: report), sources={}))
    assert result["status"] == "PREFLIGHT_BLOCKED"
    assert result["attempts"][0]["preflight"]["report"] == report
    assert not (cfg.output / "A01.json").exists()


def test_nonempty_legacy_directory_and_unknown_ids_are_never_overwritten(tmp_path):
    cfg = run_suite(tmp_path)
    cfg.output.mkdir()
    legacy = cfg.output / "A01.json"
    legacy.write_text('{"old_run":true}')
    with pytest.raises(bench.ResumeConflict):
        asyncio.run(bench.run_benchmark(cfg, runtime=runtime(), sources={}))
    assert legacy.read_text() == '{"old_run":true}'
    with pytest.raises(ValueError, match="Unknown cases"):
        bench.load_suite(replace(cfg, cases=("X99",)))


def test_cli_requires_output_without_loading_runtime():
    with pytest.raises(SystemExit) as exc:
        bench.main([])
    assert exc.value.code == 2
