"""Versioned, resumable collection of the real PhiAgent event protocol.

No model, database, or network module is imported until execution. This runner
does not change agent budgets or environment variables. --turn-timeout is only
an evaluation timeout. DONE closes the stream before optional UI generation.
"""
from __future__ import annotations

import argparse
import asyncio
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import uuid

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = Path(BASE).parent
DEFAULT_SUITE = REPO / "docs/evidence/phiagent_benchmark_v0_1/prompts.jsonl"
RUNNER_VERSION = "2.0.0"


class ResumeConflict(ValueError):
    """Existing evidence belongs to a different configuration or question."""


@dataclass(frozen=True)
class RunConfig:
    output: Path
    suite: Path = DEFAULT_SUITE
    cases: tuple[str, ...] | None = None
    prompt_profile: str = "2.0.0"
    concurrency: int = 2
    turn_timeout: float = 600
    skip_preflight: bool = False
    language: str = "zh"


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _hash(value):
    data = value if isinstance(value, bytes) else json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def _atomic_bytes(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    filename = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix="." + path.name,
                                         suffix=".tmp", delete=False) as target:
            filename = target.name
            target.write(data)
            target.flush()
            os.fsync(target.fileno())
        os.replace(filename, path)
    finally:
        if filename and os.path.exists(filename):
            os.unlink(filename)


def atomic_json(path, value):
    _atomic_bytes(path, (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode())


def _backend_path():
    if BASE not in sys.path:
        sys.path.insert(0, BASE)


def _load_runtime():
    _backend_path()
    # Load the project's normal .env before taking its effective release snapshot.
    from routes import agent_llm  # noqa: F401
    from engine_langgraph import stream_agent
    from agent_release import release_descriptor, prompt_spec, MANIFEST
    from provider_preflight import run_preflight
    return stream_agent, release_descriptor, prompt_spec, deepcopy(MANIFEST), run_preflight


def source_snapshot():
    """Paths/hashes only; never collect environment values or credential files."""
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO,
                                         stderr=subprocess.DEVNULL, text=True).strip()
        raw = subprocess.check_output(["git", "status", "--porcelain=v1", "-z",
                                       "--untracked-files=all"], cwd=REPO,
                                      stderr=subprocess.DEVNULL).decode()
        entries, parts, index = [], raw.split("\0"), 0
        while index < len(parts):
            part = parts[index]
            index += 1
            if not part:
                continue
            entry = {"status": part[:2], "path": part[3:]}
            if "R" in part[:2] or "C" in part[:2]:
                entry["original_path"] = parts[index]
                index += 1
            entries.append(entry)
        return {"git_commit": commit, "dirty_paths": entries}
    except (OSError, subprocess.CalledProcessError, IndexError):
        return {"git_commit": None, "dirty_paths": None}


def case_turns(case):
    messages = case.get("messages")
    if (not isinstance(messages, list) or not messages or not isinstance(messages[-1], dict)
            or messages[-1].get("role") != "user"):
        raise ValueError(f"{case.get('id')}: messages must end with a user question")
    for message in messages:
        if (not isinstance(message, dict) or message.get("role") not in {"user", "assistant"}
                or not isinstance(message.get("content"), str)):
            raise ValueError(f"{case.get('id')}: unsupported message")
    following = case.get("follow_up_turns") or []
    if not isinstance(following, list) or not all(isinstance(q, str) and q.strip() for q in following):
        raise ValueError(f"{case.get('id')}: invalid follow_up_turns")
    return [messages[-1]["content"], *following], deepcopy(messages[:-1])


def load_suite(config):
    raw = Path(config.suite).read_bytes()
    cases = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    seen = set()
    for case in cases:
        cid = case.get("id")
        if not isinstance(cid, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", cid) or cid in seen:
            raise ValueError("Case IDs must be unique safe filename components")
        seen.add(cid)
        case_turns(case)
    if config.cases is not None:
        unknown = set(config.cases) - seen
        if unknown:
            raise ValueError(f"Unknown cases: {', '.join(sorted(unknown))}")
        selected = [case for case in cases if case["id"] in config.cases]
    else:
        selected = cases
    if not selected:
        raise ValueError("No cases selected")
    return raw, selected


def _balance_error(text):
    return any(marker in text.lower() for marker in ("insufficient balance", "余额不足", "402"))


def _derived(events):
    tokens, segments, tools, releases, errors = [], {}, [], [], []
    first_token = first_preview = None
    for frame in events:
        event, elapsed = frame["event"], frame["relative_seconds"]
        kind = event.get("type")
        if kind == "token":
            if first_token is None:
                first_token = elapsed
            tokens.append(event.get("content") or "")
        if kind == "answer_preview" and first_preview is None:
            first_preview = elapsed
        if kind in {"tool_start", "tool", "tool_cancel", "tool_note"}:
            tools.append(deepcopy(frame))  # No name-based joins: parallel names can repeat.
        if kind in {"provider_reasoning_delta", "assistant_commentary", "thinking_summary",
                    "thinking_summary_delta"}:
            identity = event.get("id")
            key = (kind, identity or f"event:{frame['sequence']}", event.get("decision_group_id"))
            segment = segments.setdefault(key, {
                "type": kind, "id": identity, "decision_group_id": event.get("decision_group_id"),
                "started_seconds": elapsed, "ended_seconds": elapsed,
                "event_sequences": [], "content": ""})
            segment["ended_seconds"] = elapsed
            segment["event_sequences"].append(frame["sequence"])
            text = event.get("content") or ""
            if kind.endswith("_delta"):
                segment["content"] += text
            else:
                segment["content"] = text  # Commentary events can be cumulative snapshots.
        if isinstance(event.get("release"), dict):
            releases.append({"event_sequence": frame["sequence"], "type": kind,
                             "release": deepcopy(event["release"])})
        if kind == "error":
            errors.append(deepcopy(event))
    return {"answer": "".join(tokens), "first_token_seconds": first_token,
            "first_preview_seconds": first_preview, "reasoning_segments": list(segments.values()),
            "tool_events": tools, "release_events": releases, "stream_errors": errors}


async def collect_turn(question, history, config, stream_factory, *, conversation_id, turn):
    """Collect in the same task as its ContextVars and close immediately at DONE."""
    start, started_at = time.monotonic(), _now()
    events, done, failure, close_error = [], None, None, None
    stream = None
    try:
        async with asyncio.timeout(config.turn_timeout):
            stream = stream_factory(question, deepcopy(history), agent="general", language=config.language,
                                    conversation_id=conversation_id, message_id=f"{conversation_id}:turn:{turn}",
                                    _evaluation_prompt_profile=config.prompt_profile)
            async for event in stream:
                # Round-trip immediately: future runtime mutations cannot rewrite old events.
                snapshot = json.loads(json.dumps(event, ensure_ascii=False))
                events.append({"sequence": len(events),
                               "relative_seconds": round(time.monotonic() - start, 6), "event": snapshot})
                if snapshot.get("type") == "done":
                    done = snapshot
                    break
                if snapshot.get("type") == "error" and _balance_error(str(snapshot)):
                    failure = {"type": "BALANCE_ERROR", "message": "Provider reported insufficient balance"}
                    break
    except TimeoutError:
        failure = {"type": "EVALUATION_TIMEOUT", "seconds": config.turn_timeout}
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        failure = {"type": type(exc).__name__, "message": str(exc)}
    finally:
        if stream is not None:
            try:
                # Cleanup is bounded separately and does not resume the model loop.
                async with asyncio.timeout(10):
                    await stream.aclose()
            except Exception as exc:
                close_error = {"type": type(exc).__name__, "message": str(exc)}
    derived = _derived(events)
    matches = isinstance((done or {}).get("content"), str) and done["content"] == derived["answer"]
    release = (done or {}).get("release") or (
        derived["release_events"][-1]["release"] if derived["release_events"] else None)
    prompt_matches = None if not release else release.get("prompt_version") == config.prompt_profile
    usage = (done or {}).get("main_model_usage")
    if failure:
        status = failure["type"]
    elif close_error:
        status = "CLOSE_ERROR"
    elif done is None:
        status = "STREAM_END_NO_DONE"
    elif not matches:
        status = "TOKEN_MISMATCH"
    elif not derived["answer"].strip():
        status = "DONE_EMPTY"
    elif derived["stream_errors"]:
        status = "STREAM_ERROR"
    elif done.get("complete") is False or done.get("finish_reason") not in {None, "stop"}:
        status = "DONE_INCOMPLETE"
    elif prompt_matches is False:
        status = "RELEASE_MISMATCH"
    else:
        status = "DONE"
    return {"turn": turn, "question": question, "status": status, "started_at": started_at,
            "finished_at": _now(), "wall_seconds": round(time.monotonic() - start, 6),
            "events": events, **derived, "done": done, "done_matches_tokens": matches,
            "finish_reason": (done or {}).get("finish_reason"),
            "engine_duration_seconds": (done or {}).get("duration_seconds"),
            "release": release, "requested_prompt_matches_release": prompt_matches,
            "main_model_usage": usage, "auxiliary_tool_model_usage": "not_reported",
            "actual_model_names": usage.get("provider_model_names") if isinstance(usage, dict) else None,
            "failure": failure, "close_error": close_error}


async def collect_case(case, config, stream_factory, config_fingerprint, checkpoint=None):
    _backend_path()
    from deep_context import current_memory_key, current_memory_overlay, current_account_id

    scope = f"u:bench:{uuid.uuid4().hex}:{case['id']}"
    questions, history = case_turns(case)
    trace = {"schema_version": RUNNER_VERSION, "case_id": case["id"], "case": deepcopy(case),
             "question_fingerprint": _hash(case), "configuration_fingerprint": config_fingerprint,
             "status": "RUNNING", "complete": False, "started_at": _now(), "turns": [],
             "memory_scope": scope, "account_id": None, "persistent_memory_writes": False}
    if case.get("manual_prompt_ready") is False:
        trace.update(status="SKIPPED_NOT_READY", complete=True, finished_at=_now(), wall_seconds=0,
                     reason="manual_prompt_ready=false; required fixture is not installed")
        if checkpoint:
            checkpoint(trace)
        return trace
    start = time.monotonic()
    overlay = {"essays": {}, "image": None, "experiment": None, "debate": None, "socratic": None}
    tokens = [(current_memory_key, current_memory_key.set(scope)),
              (current_memory_overlay, current_memory_overlay.set(overlay)),
              (current_account_id, current_account_id.set(None))]
    try:
        for index, question in enumerate(questions, 1):
            record = await collect_turn(question, history, config, stream_factory,
                                        conversation_id=scope, turn=index)
            trace["turns"].append(record)
            if checkpoint:
                checkpoint(trace)
            if record["status"] != "DONE":
                break
            history.extend([{"role": "user", "content": question},
                            {"role": "assistant", "content": record["answer"]}])
        complete = len(trace["turns"]) == len(questions) and all(t["status"] == "DONE" for t in trace["turns"])
        trace.update(status="COMPLETED" if complete else "INCOMPLETE", complete=complete)
    except asyncio.CancelledError:
        trace.update(status="INTERRUPTED", complete=False)
        raise
    finally:
        trace.update(finished_at=_now(), wall_seconds=round(time.monotonic() - start, 6))
        for variable, token in reversed(tokens):
            variable.reset(token)
        if checkpoint:
            checkpoint(trace)
    return trace


def reusable_trace(trace, case, fingerprint):
    if (trace.get("configuration_fingerprint") != fingerprint
            or trace.get("question_fingerprint") != _hash(case) or trace.get("case") != case):
        raise ResumeConflict(f"{case['id']}: existing configuration or question does not match")
    if case.get("manual_prompt_ready") is False:
        return trace.get("status") == "SKIPPED_NOT_READY" and trace.get("complete") is True
    questions, _ = case_turns(case)
    turns = trace.get("turns") or []
    def valid_turn(turn, question):
        events = turn.get("events") or []
        if not events or events[-1].get("event", {}).get("type") != "done":
            return False
        try:
            answer = "".join(frame["event"].get("content") or "" for frame in events
                             if frame["event"].get("type") == "token")
        except (KeyError, TypeError):
            return False
        return (turn.get("status") == "DONE" and turn.get("question") == question
                and turn.get("done_matches_tokens") is True and bool(answer.strip())
                and turn.get("answer") == answer and turn.get("done") == events[-1]["event"]
                and events[-1]["event"].get("content") == answer)
    return (trace.get("status") == "COMPLETED" and trace.get("complete") is True
            and len(turns) == len(questions) and all(
                valid_turn(turn, question) for question, turn in zip(questions, turns)))


async def run_benchmark(config, *, runtime=None, sources=None):
    """runtime is injectable for fully offline protocol tests."""
    if config.concurrency < 1 or config.turn_timeout <= 0:
        raise ValueError("concurrency and turn-timeout must be positive")
    raw_suite, cases = load_suite(config)
    stream_factory, descriptor_factory, prompt_factory, manifest, preflight_factory = runtime or _load_runtime()
    release = descriptor_factory(config.language, config.prompt_profile)
    prompt = prompt_factory(config.language, config.prompt_profile)
    if release.get("runtime_profile") != "bare":
        raise ValueError("This comparison collector requires the bare runtime; no environment is changed")
    if release.get("prompt_version") != config.prompt_profile or prompt.get("version") != config.prompt_profile:
        raise ValueError("Prompt selector did not resolve to the requested profile")
    configuration = {"runner_version": RUNNER_VERSION, "agent": "general", "language": config.language,
                     "prompt_profile": config.prompt_profile, "concurrency": config.concurrency,
                     "evaluation_turn_timeout_seconds": config.turn_timeout,
                     "skip_preflight": config.skip_preflight, "suite_sha256": _hash(raw_suite),
                     "selected_cases": [c["id"] for c in cases], "release": release,
                     "prompt": prompt, "release_manifest": manifest,
                     "collector_sha256": _hash(Path(__file__).read_bytes())}
    fingerprint = _hash(configuration)
    output = Path(config.output)
    meta_path = output / "_RUN_META.json"
    if output.exists() and any(output.iterdir()) and not meta_path.exists():
        raise ResumeConflict("Nonempty output has no collector manifest; refusing to overwrite evidence")
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        if meta.get("configuration_fingerprint") != fingerprint or meta.get("configuration") != configuration:
            raise ResumeConflict("Run configuration changed; choose a new --output directory")
    else:
        meta = {"run_id": uuid.uuid4().hex, "created_at": _now(), "configuration": configuration,
                "configuration_fingerprint": fingerprint, "attempts": []}
    pending, reused, previous = [], [], {}
    for case in cases:
        target = output / f"{case['id']}.json"
        if target.exists():
            trace = json.loads(target.read_text())
            if reusable_trace(trace, case, fingerprint):
                reused.append(case["id"])
                continue
            previous[case["id"]] = trace
        pending.append(case)
    # All conflicts are checked before touching existing files or using the network.
    attempt = {"attempt_id": uuid.uuid4().hex, "started_at": _now(),
               "source_snapshot": sources if sources is not None else source_snapshot(),
               "reused_cases": reused, "pending_cases": [c["id"] for c in pending], "preflight": None}
    meta["attempts"].append(attempt)
    meta["status"] = "RUNNING"
    _atomic_bytes(output / "_SUITE.jsonl", raw_suite)
    _atomic_bytes(output / "_PROMPT.txt", prompt["text"].encode())
    atomic_json(output / "_RELEASE_MANIFEST.json", manifest)
    atomic_json(meta_path, meta)
    ready = any(c.get("manual_prompt_ready") is not False for c in pending)
    if not ready:
        attempt["preflight"] = {"status": "NOT_RUN", "reason": "No pending runnable cases"}
    elif config.skip_preflight:
        attempt["preflight"] = {"status": "SKIPPED", "reason": "Explicit --skip-preflight"}
    else:
        try:
            report = await asyncio.to_thread(preflight_factory)
            if not isinstance(report, dict):
                raise TypeError("Preflight did not return a structured report")
            attempt["preflight"] = {"status": "COMPLETED", "report": report}
        except Exception as exc:
            report = {}
            attempt["preflight"] = {"status": "ERROR", "error_type": type(exc).__name__, "message": str(exc)}
        if not report.get("ALL_PROVIDER_GATES_PASS"):
            attempt["finished_at"] = _now()
            meta["status"] = "PREFLIGHT_BLOCKED"
            atomic_json(meta_path, meta)
            return meta
    atomic_json(meta_path, meta)
    semaphore, abort = asyncio.Semaphore(config.concurrency), asyncio.Event()
    batch_start = time.monotonic()

    async def worker(case):
        async with semaphore:
            if abort.is_set():
                return
            if case["id"] in previous:
                atomic_json(output / "attempts" / f"{case['id']}-{attempt['attempt_id']}.json", previous[case["id"]])
            trace = await collect_case(case, config, stream_factory, fingerprint,
                                       lambda value: atomic_json(output / f"{case['id']}.json", value))
            if any(turn["status"] == "BALANCE_ERROR" for turn in trace["turns"]):
                abort.set()
            print(f"{case['id']}: {trace['status']} ({len(trace['turns'])} turns)", flush=True)

    tasks = [asyncio.create_task(worker(case)) for case in pending]
    try:
        await asyncio.gather(*tasks)
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        attempt["finished_at"] = _now()
        attempt["batch_wall_seconds"] = round(time.monotonic() - batch_start, 6)
        statuses, case_seconds = Counter(), 0.0
        for case in cases:
            path = output / f"{case['id']}.json"
            if path.exists():
                record = json.loads(path.read_text())
                statuses[record["status"]] += 1
                case_seconds += record.get("wall_seconds", 0)
            else:
                statuses["NOT_EXECUTED"] += 1
        meta.update(status="COMPLETED" if all(k in {"COMPLETED", "SKIPPED_NOT_READY"} for k in statuses)
                    else "INCOMPLETE", case_status_counts=dict(statuses), summed_case_wall_seconds=round(case_seconds, 6))
        atomic_json(meta_path, meta)
    return meta


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="New evidence directory, or identical run to resume")
    parser.add_argument("--suite", type=Path, default=DEFAULT_SUITE)
    parser.add_argument("--cases", help="Comma-separated case IDs; omitted means the complete suite")
    parser.add_argument("--prompt-profile", default="2.0.0")
    parser.add_argument("--concurrency", type=int, default=2)
    parser.add_argument("--turn-timeout", type=float, default=600)
    parser.add_argument("--skip-preflight", action="store_true", help="Explicitly record that provider checks were skipped")
    args = parser.parse_args(argv)
    config = RunConfig(**{**vars(args), "cases": tuple(s.strip() for s in args.cases.split(",") if s.strip()) if args.cases else None})
    try:
        result = asyncio.run(run_benchmark(config))
    except (ValueError, OSError) as exc:
        parser.exit(2, f"benchmark: {exc}\n")
    return 0 if result["status"] == "COMPLETED" else 2 if result["status"] == "PREFLIGHT_BLOCKED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
