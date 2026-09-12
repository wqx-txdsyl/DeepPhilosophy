# -*- coding: utf-8 -*-
"""O7-E Model Bakeoff（§4-§12）——生产 Main-Agent 候选模型遴选。

Stage A: 8 个冻结 repair fixtures × 2 runs × 候选模型（repair-only, 确定性解码）
  → REPAIR_RELIABILITY >= 0.80 才进 Stage B
Stage B: 8-case 全链路 E2E（合格候选）
唯一裁判 = 现行 final_validator（同一 PASS 标准, 零 reference answer）。

用法: SCHOLARLY_NETWORK_MODE=TRUSTED_PROXY .venv/bin/python backend/tools/evaluation/o7e_bakeoff.py A|B <candidate_id>
候选: deepseek-chat | glm-4-plus | glm-4.6 | glm-4-air
"""
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "backend"))
sys.path.insert(0, os.path.join(ROOT, "backend", "tools", "evaluation"))

import o7e_cases as CASES
from final_validator import validate_final_candidate
import engine_langgraph as EG
import scholarly_sources  # noqa: F401 registration

TMP = os.path.join(ROOT, "backend", "tools", "_tmp")
ENVKEY = {"deepseek-chat": "DEEPSEEK_API_KEY", "glm-4-plus": "ZHIPU_API_KEY",
          "glm-4.6": "ZHIPU_API_KEY", "glm-4-air": "ZHIPU_API_KEY",
          "deepseek-v4-pro": "DEEPSEEK_API_KEY", "deepseek-flash": "DEEPSEEK_API_KEY",
          "glm-5.3": "ZHIPU_API_KEY", "glm-5.3-flash": "ZHIPU_API_KEY"}
PROVIDER = {"deepseek-chat": ("deepseek", "https://api.deepseek.com"),
            "glm-4-plus": ("bigmodel", "https://open.bigmodel.cn/api/paas/v4"),
            "glm-4.6": ("bigmodel", "https://open.bigmodel.cn/api/paas/v4"),
            "glm-4-air": ("bigmodel", "https://open.bigmodel.cn/api/paas/v4"),
            "deepseek-v4-pro": ("deepseek", "https://api.deepseek.com"),
            "deepseek-flash": ("deepseek", "https://api.deepseek.com"),
            "glm-5.3": ("bigmodel", "https://open.bigmodel.cn/api/paas/v4"),
            "glm-5.3-flash": ("bigmodel", "https://open.bigmodel.cn/api/paas/v4")}
sys.path.insert(0, ROOT)


def _key(mid):
    for l in open(os.path.join(ROOT, ".env"), encoding="utf-8"):
        if l.startswith(ENVKEY[mid] + "="):
            return l.split("=", 1)[1].strip().strip('"').strip("'")


def _call_repair(mid, question, invalid_candidate, feedback):
    """repair-only 微调用: 同一候选模型确定性解码, 产出替换候选。"""
    import urllib.request
    prov, url = PROVIDER[mid]
    sys_msg = EG.SYSTEM_PROMPT_BASE if hasattr(EG, "SYSTEM_PROMPT_BASE") else None
    base_prompt = ("你是深哲——严谨的哲学智能体, 基于403本哲学原著工作。\n"
                   + getattr(EG, "SCHOLARLY_CONTRACT", "") + "\n"
                   + getattr(EG, "REPAIR_SYSTEM_PROTOCOL", ""))
    msgs = [{"role": "system", "content": base_prompt},
            {"role": "user", "content": question},
            {"role": "assistant", "content": invalid_candidate},
            {"role": "user", "content": feedback}]
    payload = {"model": mid, "temperature": 0, "max_tokens": 4000,
               "messages": msgs}
    if prov == "deepseek":
        payload["extra_body"] = None
        del payload["extra_body"]
    req = urllib.request.Request(
        url + "/chat/completions", data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + _key(mid)})
    with urllib.request.urlopen(req, timeout=240) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"] or ""


def stage_a(mid):
    """8 frozen repair fixtures × 2 runs。fixtures 由 production validator/
    quote_bound/packet 在真实校准失败案例上机械冻结（Round 9 artifact 提取）。"""
    fx_path = os.path.join(TMP, "o7e_bakeoff_fixtures.json")
    fixtures = json.load(open(fx_path, encoding="utf-8"))
    out_path = os.path.join(TMP, f"o7e_bakeoff_A_{mid.replace('.', '_')}.json")
    results = []
    if os.path.exists(out_path):
        results = json.load(open(out_path, encoding="utf-8"))
    done = {(r["fixture_id"], r["run"]) for r in results}
    for fx in fixtures:
        for run in (1, 2):
            if (fx["fixture_id"], run) in done:
                continue
            try:
                cand = _call_repair(mid, fx["question"], fx["invalid_candidate"],
                                    fx["repair_feedback"])
            except Exception as e:
                cand = ""
                print(f"  {fx['fixture_id']}/r{run} call err: {str(e)[:80]}", flush=True)
            v = validate_final_candidate(cand, raw_tool_log=fx["raw_tool_log"],
                                         fallback_log=[], language="zh")
            results.append({"fixture_id": fx["fixture_id"], "run": run,
                            "valid": bool(v.ok),
                            "new_fatal": any(i.code in ("FABRICATED_BIBLIOGRAPHY",
                                                        "FALSE_EXACT_QUOTE")
                                             for i in v.issues),
                            "empty": not cand.strip(),
                            "len": len(cand)})
            json.dump(results, open(out_path, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)
            print(f"  {fx['fixture_id']}/r{run} valid={v.ok} empty={not cand.strip()}",
                  flush=True)
    valid = sum(1 for r in results if r["valid"])
    empty = sum(1 for r in results if r["empty"])
    fatal = sum(1 for r in results if r["new_fatal"])
    n = len(results)
    out = {"candidate": mid, "REPAIR_TRIALS": n, "REPAIR_VALID": valid,
           "REPAIR_RELIABILITY": round(valid / max(n, 1), 3),
           "EMPTY": empty, "NEW_FATAL_ERRORS": fatal,
           "QUALIFIED": valid / max(n, 1) >= 0.8 and empty == 0 and fatal == 0}
    json.dump(out, open(out_path.replace(".json", "_summary.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    stage, mid = sys.argv[1], sys.argv[2]
    if stage == "A":
        stage_a(mid)
