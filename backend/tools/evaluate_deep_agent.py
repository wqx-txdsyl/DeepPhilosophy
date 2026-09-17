"""Run a frozen question set through the real general engine, with public evidence.

This makes real provider requests. Example from the repository root:
  .venv/bin/python backend/tools/evaluate_deep_agent.py --cases cases.json --output report.json

An exit code of zero means complete, consistent transport; philosophical quality
still requires reading the answers against the frozen criteria. No private
provider reasoning, credentials, or full request bodies are recorded.
"""
import argparse
import asyncio
from contextvars import ContextVar
import hashlib
import inspect
import json
import os
from pathlib import Path
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = Path(BASE).parent
ACTIVE_RUN = ContextVar("deep_evaluation_run", default=None)


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def inspect_tool_context(messages):
    """Observe what reaches the model, not full-result metadata hidden from it."""
    out = []
    for message in messages:
        if getattr(message, "type", None) != "tool":
            continue
        content = message.content if isinstance(message.content, str) else ""
        row = {"name": message.name, "chars": len(content), "sha256": digest(content),
               "delivery": message.additional_kwargs.get("_context_delivery")}
        try:
            value = json.loads(content)
            row["json_valid"] = True
            if isinstance(value, dict):
                row["fields"] = list(value)
                row["structure_fields"] = {key: list(value[key]) for key in ("argument", "review")
                                           if isinstance(value.get(key), dict)}
        except (ValueError, TypeError):
            row["json_valid"] = False
        out.append(row)
    return out


async def collect_case(engine, case, timeout, save):
    started = time.perf_counter()
    row = {"id": case["id"], "category": case.get("category"), "question": case["question"],
           "execution_status": "running", "answer": "", "public_notes": [], "tools": [],
           "errors": [], "main_calls": [], "quality_verdict": "NOT_SCORED"}
    token = ACTIVE_RUN.set((row, started))
    chunks = []
    done = None
    save(row)

    async def collect():
        nonlocal done
        async for event in engine.stream_agent(case["question"], case.get("history") or [],
                                               agent="general", language="zh"):
            elapsed = round(time.perf_counter() - started, 3)
            row.setdefault("first_event_s", elapsed)
            kind = event.get("type")
            if kind == "token":
                row.setdefault("first_answer_token_s", elapsed)
                chunks.append(event.get("content") or "")
            elif kind in {"thinking_summary", "thinking_summary_delta"}:
                row["public_notes"].append({"elapsed_s": elapsed, **{key: event[key]
                    for key in ("type", "id", "phase", "content") if key in event}})
            elif kind in {"tool_start", "tool", "tool_cancel"}:
                row["tools"].append({"elapsed_s": elapsed, **{key: event[key]
                    for key in ("type", "name", "call_id", "tool_call_id", "status", "args", "summary", "delivery_status") if key in event}})
            elif kind == "error":
                row["errors"].append({key: event[key] for key in ("code", "content") if key in event})
            elif kind == "done":
                done = event
                row["done_at_s"] = elapsed
                row["done"] = {key: event[key] for key in ("complete", "validation", "citations", "safety") if key in event}
            save(row)

    try:
        await asyncio.wait_for(collect(), timeout)
        row["execution_status"] = "finished"
    except asyncio.TimeoutError:
        row["execution_status"] = "timeout"
    except Exception as exc:
        row["execution_status"] = "exception"
        row["exception_class"] = type(exc).__name__
    finally:
        ACTIVE_RUN.reset(token)
    row["elapsed_s"] = round(time.perf_counter() - started, 3)
    row["streamed_answer"] = "".join(chunks)
    row["answer"] = (done or {}).get("content", row["streamed_answer"])
    row["stream_matches_done"] = bool(done is not None and "content" in done and row["streamed_answer"] == done["content"])
    row["transport_complete"] = bool(row["execution_status"] == "finished" and done
        and done.get("complete") is True and row["answer"].strip()
        and row["stream_matches_done"] and not row["errors"])
    save(row)
    return row


async def run(args):
    raw = args.cases.read_text(encoding="utf-8")
    dataset = json.loads(raw)
    cases = dataset["cases"]
    if not isinstance(cases, list) or not cases or len(cases) > 100:
        raise ValueError("Expected 1 to 100 frozen cases")
    if len({case["id"] for case in cases}) != len(cases):
        raise ValueError("Case identifiers must be unique")
    if any(not isinstance(case.get("question"), str) or not case["question"].strip() for case in cases):
        raise ValueError("Every case needs a nonempty question")
    # Exclusive creation prevents replacing an earlier run with a favorable rerun.
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as file:
        file.write("{}\n")
    sys.path.insert(0, BASE)
    from loguru import logger
    logger.remove()
    import engine_langgraph as engine
    client = engine._llm_for_agent("general")
    report = {"meta": {
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "cases_sha256": digest(raw),
        "cases_file": str(args.cases), "model": engine.AG.MODEL,
        "reasoning_effort": (getattr(client, "extra_body", None) or {}).get("reasoning_effort"),
        "max_tokens": getattr(client, "max_tokens", None), "concurrency": args.concurrency,
        "timeout_seconds_per_case": args.timeout_seconds,
        "prompt_sha256": digest(engine.get_system_prompt("general")),
        "full_system_context_sha256": digest("\n".join(message.content for message in
            engine._build_context_messages("general", "zh"))),
        "context_builder_sha256": digest(inspect.getsource(engine._build_context_messages)),
        "source_sha256": {name: hashlib.sha256((Path(BASE) / name).read_bytes()).hexdigest()
                           for name in ("engine_langgraph.py", "deep_reasoning_tools.py", "deep_agent_tools.py",
                                        "deep_tool_context.py", "deep_streaming.py", "deep_result_contracts.py")
                           if (Path(BASE) / name).is_file()},
        "privacy": "Only public output and scalar request metadata; no private reasoning text.",
        "scope": "General engine entry; not browser, route authentication, or a semantic correctness judge.",
    }, "runs": []}
    rows = {}

    def save(row):
        rows[row["id"]] = row
        report["runs"] = [rows[c["id"]] for c in cases if c["id"] in rows]
        temporary = args.output.with_suffix(args.output.suffix + ".tmp")
        temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(args.output)

    invoke = engine._agent_llm_invoke

    async def observed(agent, messages, *positional, **kwargs):
        active = ACTIVE_RUN.get()
        row, started = active if active else (None, None)
        context = inspect_tool_context(messages)
        result = await invoke(agent, messages, *positional, **kwargs)
        if row is not None:
            response = result[0]
            metadata = getattr(response, "response_metadata", None) or {}
            row["main_calls"].append({"completed_at_s": round(time.perf_counter() - started, 3),
                "model": metadata.get("model_name") or metadata.get("model"),
                "finish_reason": metadata.get("finish_reason"), "tool_context": context,
                "usage": getattr(response, "usage_metadata", None)})
            save(row)
        return result

    engine._agent_llm_invoke = observed
    semaphore = asyncio.Semaphore(args.concurrency)

    async def execute(case):
        async with semaphore:
            print(json.dumps({"started": case["id"]}), flush=True)
            row = await collect_case(engine, case, args.timeout_seconds, save)
            print(json.dumps({"finished": case["id"], "status": row["execution_status"],
                "transport_complete": row["transport_complete"], "elapsed_s": row["elapsed_s"],
                "quality_verdict": "NOT_SCORED"}), flush=True)
            return row
    try:
        results = await asyncio.gather(*(execute(case) for case in cases))
    finally:
        engine._agent_llm_invoke = invoke
    return 0 if all(row["transport_complete"] for row in results) else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--concurrency", type=int, choices=(1, 2), default=2)
    parser.add_argument("--timeout-seconds", type=int, choices=range(1, 601), default=300, metavar="1..600")
    sys.exit(asyncio.run(run(parser.parse_args())))
