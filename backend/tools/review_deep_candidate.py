"""Evaluate one public answer with an explicitly configured advisory reviewer.

This command never generates or replaces a main-agent answer. A completed
review is fallible advice, not a semantic pass. It makes at most one request.
"""
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = Path(BASE).parent
sys.path.insert(0, BASE)

from dotenv import load_dotenv
from deep_peer_review import ReviewConfig, ReviewConfigurationError, request_review, review_messages


def evaluate(config, input_path, output_path):
    try:
        with input_path.open("r", encoding="utf-8") as source:
            raw = source.read(1_000_001)
        if len(raw) > 1_000_000:
            raise ValueError("Input file is too large")
        data = json.loads(raw)
        if not isinstance(data, dict) or set(data) - {"question", "candidate", "evidence"}:
            raise ValueError("Expected question, candidate and optional evidence")
        messages = review_messages(data.get("question"), data.get("candidate"), data.get("evidence", []))
        # Save precisely the public material sent, not unknown fields from the file.
        material = json.loads(messages[1]["content"])
    except (OSError, UnicodeError, ValueError, TypeError):
        print(json.dumps({"status": "rejected_input", "error": "INVALID_REVIEW_INPUT"}))
        return 2

    report = {"meta": {"started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "input_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        "messages_sha256": hashlib.sha256(json.dumps(messages, ensure_ascii=False).encode("utf-8")).hexdigest(),
        "request_limit": 1, "automatic_retries": 0, "production_changed": False,
        "scope": "Evaluation only; the main model and chat engine are unchanged."},
        "material": material, "result": {"status": "running", "semantic_verdict": "NOT_ASSESSED"}}
    try:
        output = output_path.open("x", encoding="utf-8")
    except OSError:
        print(json.dumps({"status": "output_unavailable", "error": "OUTPUT_MUST_BE_NEW_AND_WRITABLE"}))
        return 2

    with output:
        def save():
            output.seek(0)
            json.dump(report, output, ensure_ascii=False, indent=2)
            output.write("\n")
            output.truncate()
            output.flush()

        save()
        try:
            report["result"] = asyncio.run(request_review(config, material["question"], material["candidate"], material["evidence"]))
        except KeyboardInterrupt:
            report["result"] = {"status": "cancelled", "semantic_verdict": "NOT_ASSESSED"}
            save()
            return 130
        save()
    result = report["result"]
    print(json.dumps({"status": result["status"], "semantic_verdict": result["semantic_verdict"]}))
    return 0 if result["status"] == "reviewed" else (2 if result["status"] == "disabled" else 1)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="JSON with question, candidate and optional evidence")
    parser.add_argument("--output", type=Path, help="New report path; existing reports are never overwritten")
    parser.add_argument("--check-config", action="store_true", help="Check configuration without making a request")
    args = parser.parse_args(argv)
    if not args.check_config and (args.input is None or args.output is None):
        parser.error("--input and --output are required unless --check-config is used")
    load_dotenv(ROOT / ".env", override=False)
    try:
        config = ReviewConfig.from_env()
    except ReviewConfigurationError as exc:
        print(json.dumps({"status": "invalid_configuration", "error": str(exc)}))
        return 2
    if args.check_config:
        print(json.dumps({"status": "configured" if config else "disabled", "network_request": False}))
        return 0
    return evaluate(config, args.input, args.output)


if __name__ == "__main__":
    sys.exit(main())
