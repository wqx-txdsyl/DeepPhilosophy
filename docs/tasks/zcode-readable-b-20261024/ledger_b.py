# -*- coding: utf-8 -*-
"""任务B逐人台账写入工具。用法: python3 ledger_b.py <person> <objectId> <done|doing> <brief-json-file>"""
import json, sys, os

B = "/Users/sen/.zcode/worktrees/zcode-readable-b-20261024/DeepPhilosophy"
OUT = f"{B}/docs/tasks/zcode-readable-b-20261024"


def append(path, obj):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def write_progress(cursor_done, next_name, seq):
    p = f"{OUT}/progress-b.json"
    pr = json.load(open(p, encoding="utf-8"))
    pr["cursor"] = {"phase": pr["cursor"]["phase"], "seq": seq, "done": cursor_done, "nextName": next_name}
    json.dump(pr, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    person, oid, status, brieffile = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    brief = json.load(open(brieffile, encoding="utf-8"))
    # coverage entry(s)
    for cov in brief.get("coverage", []):
        cov.setdefault("objectId", oid)
        cov.setdefault("person", person)
        cov.setdefault("completedAt", "2026-10-24")
        cov.setdefault("publicationStatus", "committed-local")
        append(f"{OUT}/coverage-b.jsonl", cov)
    if brief.get("changes"):
        brief["changes"].setdefault("objectId", oid)
        brief["changes"].setdefault("person", person)
        brief["changes"].setdefault("at", "2026-10-24")
        append(f"{OUT}/changes-b.jsonl", brief["changes"])
    if brief.get("blockers"):
        for blk in brief["blockers"]:
            blk.setdefault("objectId", oid)
            blk.setdefault("person", person)
            blk.setdefault("at", "2026-10-24")
            append(f"{OUT}/blockers-b.jsonl", blk)
    if brief.get("validation"):
        brief["validation"].setdefault("objectId", oid)
        brief["validation"].setdefault("person", person)
        brief["validation"].setdefault("at", "2026-10-24")
        append(f"{OUT}/validation-b.jsonl", brief["validation"])
    pr = json.load(open(f"{OUT}/progress-b.json", encoding="utf-8"))
    pr["objects"][oid] = {"name": person, "phase": pr["objects"].get(oid, {}).get("phase", "phase1"),
                          "status": f"done-local" if status == "done" else "in-progress",
                          "completedAt": "2026-10-24" if status == "done" else None,
                          "verified": brief.get("verified", False)}
    json.dump(pr, open(f"{OUT}/progress-b.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("ledger updated for", person)
