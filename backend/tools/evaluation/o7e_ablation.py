# -*- coding: utf-8 -*-
"""O7-E Bakeoff V2.1: Matched Repair Configuration Ablation。

Stage A = config verification（RP-A/RP-B 各 8 fixtures × 2, 单一 client 源,
trial 记录 identity/finish/content_chars/reasoning_chars）。
Stage B = sequential gate（§6: 先 1 轮, 7/8+conv≥0.8 才跑第 2 轮确认）。
用法: SCHOLARLY_NETWORK_MODE=TRUSTED_PROXY .venv/bin/python backend/tools/evaluation/o7e_ablation.py A RP-A|RP-B
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "backend"))
sys.path.insert(0, os.path.join(ROOT, "backend", "tools", "evaluation"))

import o7e_candidate_config as CC
from final_validator import validate_final_candidate
import engine_langgraph as EG

TMP = os.path.join(ROOT, "backend", "tools", "_tmp")
RP = {"RP-A": CC.RP_A, "RP-B": CC.RP_B}


def base_system():
    src = open(os.path.join(ROOT, "backend/engine_langgraph.py"), encoding="utf-8").read()
    contract = src.split('SCHOLARLY_CONTRACT = """')[1].split('"""')[0]
    protocol = src.split('REPAIR_SYSTEM_PROTOCOL = """')[1].split('"""')[0]
    return ("你是深哲——严谨的哲学智能体, 基于403本哲学原著工作。\n"
            + contract + protocol)


def stage_a(rp_id):
    cfg = CC.v4pro_config(dict(RP[rp_id], id=rp_id))
    # V2.1+ §1: Stage A/B 同一 LangChain client（关 client-path confound）
    _lc = CC.build_candidate_langchain_client(cfg, "repair")

    def client(messages):
        from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
        lc = [SystemMessage(content=m["content"]) if m["role"] == "system"
              else AIMessage(content=m["content"]) if m["role"] == "assistant"
              else HumanMessage(content=m["content"]) for m in messages]
        resp = _lc.invoke(lc)
        return {"content": resp.content or "",
                "response_model": getattr(resp, "response_metadata", {}).get("model_name"),
                "finish_reason": "stop",
                "content_chars": len(resp.content or ""),
                "reasoning_chars": len(getattr(resp, "additional_kwargs", {}).get("reasoning_content") or ""),
                "config_echo": {"requested_model": cfg.requested_model,
                                "temperature": cfg.repair["temperature"],
                                "max_tokens": cfg.repair["max_tokens"],
                                "thinking": cfg.repair.get("thinking"),
                                "reasoning_effort": cfg.repair.get("reasoning_effort")}}
    sys_blob = base_system()
    fixtures = json.load(open(os.path.join(TMP, "o7e_bakeoff_fixtures.json"),
                              encoding="utf-8"))
    out_path = os.path.join(TMP, f"o7e_ablation_A_{rp_id}.json")
    results = []
    if os.path.exists(out_path):
        results = json.load(open(out_path, encoding="utf-8"))
    done = {(r["fixture_id"], r["run"]) for r in results}
    for fx in fixtures:
        for run in (1, 2):
            if (fx["fixture_id"], run) in done:
                continue
            messages = [{"role": "system", "content": sys_blob},
                        {"role": "user", "content": fx["question"]},
                        {"role": "assistant", "content": fx["invalid_candidate"]},
                        {"role": "user", "content": fx["repair_feedback"]}]
            try:
                out = client(messages)
            except Exception as e:
                out = {"content": "", "response_model": None,
                       "finish_reason": "CALL_ERROR:" + str(e)[:80],
                       "content_chars": 0, "reasoning_chars": 0, "config_echo": {}}
            v = validate_final_candidate(out["content"],
                                         raw_tool_log=fx["raw_tool_log"],
                                         fallback_log=[], language="zh")
            results.append({
                "fixture_id": fx["fixture_id"], "run": run,
                "valid": bool(v.ok),
                "new_fatal": any(i.code in ("FABRICATED_BIBLIOGRAPHY",
                                            "FALSE_EXACT_QUOTE") for i in v.issues),
                "empty": not out["content"].strip(),
                "requested_model": out.get("config_echo", {}).get("requested_model"),
                "response_model": out.get("response_model"),
                "temperature": out.get("config_echo", {}).get("temperature"),
                "max_tokens": out.get("config_echo", {}).get("max_tokens"),
                "thinking_mode": out.get("config_echo", {}).get("thinking"),
                "reasoning_effort": out.get("config_echo", {}).get("reasoning_effort"),
                "finish_reason": out.get("finish_reason"),
                "content_chars": out.get("content_chars"),
                "reasoning_chars": out.get("reasoning_chars")})
            json.dump(results, open(out_path, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)
            print(f"  {fx['fixture_id']}/r{run} valid={v.ok} "
                  f"finish={out.get('finish_reason')} "
                  f"content={out.get('content_chars')} "
                  f"reasoning={out.get('reasoning_chars')}", flush=True)
    valid = sum(1 for r in results if r["valid"])
    empty = sum(1 for r in results if r["empty"])
    fatal = sum(1 for r in results if r["new_fatal"])
    mismatch = sum(1 for r in results
                   if r.get("response_model") and
                   r["response_model"] != r.get("requested_model"))
    out = {"config": RP[rp_id], "candidate": cfg.candidate_id,
           "TRIALS": len(results), "VALID": valid,
           "RELIABILITY": round(valid / max(len(results), 1), 3),
           "EMPTY": empty, "NEW_FATAL": fatal,
           "MODEL_ID_MISMATCH": mismatch,
           "QUALIFIED": valid / max(len(results), 1) >= 0.8125 and empty == 0
                        and fatal == 0 and mismatch == 0}
    json.dump(out, open(out_path.replace(".json", "_summary.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False))



def stage_b(rp_id, run_tag="RUN1"):
    """§6 sequential gate: matched-config E2E（normal=V4PRO_NORMAL 冻结;
    repair=RP 配置; 两客户端均出自 o7e_candidate_config 单一真源）。"""
    import o7e_runner as R
    import o7e_evidence_checks as EVCHK
    import routes.agent as AG
    import engine_langgraph as EG
    from langchain_deepseek import ChatDeepSeek

    rp = RP[rp_id]
    cfg = CC.v4pro_config(dict(rp, id=rp_id))
    key = cfg.api_key()

    def mk(mode):
        m = cfg.normal if mode == "normal" else cfg.repair
        extra = {}
        if m.get("thinking"):
            extra = {"thinking": {"type": m["thinking"]}}
            if m.get("reasoning_effort"):
                extra["reasoning_effort"] = m["reasoning_effort"]
        return ChatDeepSeek(model=cfg.requested_model, api_key=key,
                            base_url=cfg.base_url,
                            temperature=m["temperature"],
                            max_tokens=m["max_tokens"], extra_body=extra)

    orig = (AG.API_KEY, AG.API_URL, AG.MODEL, EG.get_llm, EG.get_repair_llm)
    AG.API_KEY, AG.API_URL, AG.MODEL = key, cfg.base_url, cfg.requested_model
    EG.get_llm = lambda: mk("normal")
    EG.get_repair_llm = lambda: mk("repair")
    EG._llm = None
    EG._llm_repair = None

    out_path = os.path.join(TMP, f"o7e_ablation_B_{rp_id}_{run_tag}.json")
    runs = []
    if os.path.exists(out_path):
        runs = json.load(open(out_path, encoding="utf-8"))
    done = {r["case_id"] for r in runs}
    pool = json.load(open(os.path.join(TMP, "o7e_rp2_repair_pool.json"),
                          encoding="utf-8"))
    try:
        for p in pool:
            if p["case_id"] in done:
                continue
            case = {"case_id": p["case_id"], "category": "ablation_b",
                    "question": p["question"], "persona": "general",
                    "applicability": {}, "evidence_expectation": "PRIMARY_REQUIRED"}
            print(f"== {p['case_id']}", flush=True)
            try:
                r = R.run_case(case)
            except Exception as e:
                r = {"case_id": p["case_id"], "delivery": {
                    "run_status": "RUN_ERROR", "published": None}}
                print("   err", str(e)[:100], flush=True)
            try:
                r["primary_gate"] = EVCHK.check_case(case, r)
            except Exception:
                r["primary_gate"] = {}
            runs = [x for x in runs if x["case_id"] != p["case_id"]] + [r]
            json.dump(runs, open(out_path, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)
            d = r.get("delivery", {})
            print(f"   {d.get('run_status')} pub={d.get('published')} "
                  f"rep={d.get('repair_attempts')}", flush=True)
    finally:
        AG.API_KEY, AG.API_URL, AG.MODEL = orig[:3]
        EG.get_llm, EG.get_repair_llm = orig[3:]
        EG._llm = None
        EG._llm_repair = None
    comp = [r for r in runs if r.get("delivery", {}).get("run_status") == "COMPLETED"]
    pub = [r for r in comp if r["delivery"].get("published")]
    trig = [r for r in comp if (r["delivery"].get("repair_attempts") or 0) > 0]
    conv = [r for r in trig if r["delivery"].get("published")]
    traces = [t for r in comp for t in (r.get("repair_trace") or [])]
    out = {"config": rp, "candidate": cfg.candidate_id, "run": run_tag,
           "COMPLETED": len(comp), "PUBLISHED": len(pub),
           "REPAIR_TRIGGERED": len(trig), "REPAIR_CONVERGED": len(conv),
           "REPAIR_CONVERGENCE": round(len(conv) / max(len(trig), 1), 3)
                             if trig else None,
           "EMPTY_FINAL": sum(1 for r in comp if "EMPTY_FINAL" in
                              (r["delivery"].get("final_validation_issue_codes") or [])),
           "E2E_PROTOCOL_RATE": round(
               sum(1 for t in traces if t.get("system_protocol_injected")) /
               max(len(traces), 1), 3) if traces else None}
    json.dump(out, open(out_path.replace(".json", "_summary.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    if sys.argv[1] == "A":
        stage_a(sys.argv[2])
    elif sys.argv[1] == "B":
        stage_b(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "RUN1")

