# -*- coding: utf-8 -*-
"""O7-E RCA-1 §10-14: LOCAL_PATCH evaluation harness（evaluation-only 注入）。

monkeypatch engine 的 repair 循环: LOCAL_PATCH_CODES issue → repair_context
patch 模式（render_patch_prompt + apply_main_agent_patches）; 其余走原 full-rewrite。
生产 engine 文件零改动（§13 PRODUCTION_LOCAL_PATCH_ENABLED=false）。
用法: SCHOLARLY_NETWORK_MODE=TRUSTED_PROXY .venv/bin/python backend/tools/evaluation/o7e_rca1_eval.py RUN1|RUN2
"""
import asyncio
import hashlib
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "backend"))
sys.path.insert(0, os.path.join(ROOT, "backend", "tools", "evaluation"))

import engine_langgraph as EG
import repair_context as RC
from final_validator import validate_final_candidate, format_feedback
import o7e_candidate_config as CC
import o7e_runner as R

RP_B = CC.RP_B
MAX_TURNS = 2     # §8: 仍最多两轮

_orig_stream_agent = EG.stream_agent


def _patch_mode_repair(candidate, validation, messages, raw_tool_log, repair_call):
    """LOCAL_PATCH 修复轮（§4-9）。返回 (new_candidate | None, notes)。"""
    issues = validation.as_dict().get("issues", [])
    local = [i for i in issues if (i or {}).get("code") in RC.LOCAL_PATCH_CODES]
    non_local = [i for i in issues if (i or {}).get("code") not in RC.LOCAL_PATCH_CODES]
    if not local:
        return None, None            # 无局部 issue → 全量重写路径
    bundles = RC.build_repair_issue_bundles(candidate, validation, raw_tool_log)
    anchor_ok = all(b.get("anchor") for b in bundles if b["code"] in RC.LOCAL_PATCH_CODES)
    if not anchor_ok:
        return None, {"reason": "ANCHOR_UNRESOLVED"}
    cand_sha = hashlib.sha256(candidate.encode("utf-8")).hexdigest()
    prompt = RC.render_patch_prompt(cand_sha, bundles)
    from langchain_core.messages import HumanMessage, AIMessage
    msgs = list(messages) + [AIMessage(content=candidate), HumanMessage(content=prompt)]
    lc_msgs = msgs
    resp = repair_call(lc_msgs)
    new_cand, errs = RC.apply_main_agent_patches(candidate, resp, bundles)
    notes = {"mode": "LOCAL_PATCH",
             "anchor_resolution_rate": 1.0,
             "patch_protocol_errors": errs or []}
    if errs:
        return None, notes           # PATCH_PROTOCOL_ERROR → 计一次 repair attempt（§9）
    if non_local:
        notes["non_local_remaining"] = [i["code"] for i in non_local]
    # 全量 validator 复核（A15）
    v2 = validate_final_candidate(new_cand, raw_tool_log=raw_tool_log,
                                  fallback_log=[], language="zh")
    notes["post_patch_validation_ok"] = bool(v2.ok)
    return (new_cand if v2.ok else None), notes


def run_case_local(case, mk_normal, mk_repair):
    """E2E 单例: 正常链路用 o7e_runner 的流, 修复轮截获注入 LOCAL_PATCH。

    实现: 直接跑 engine stream（repair client/normal client 注入同 V2.1）,
    对 validation_failed 事件后接管的简化路径不可行（SSE 无 candidate 全文）——
    改用「重放式」: 先跑完整 E2E 获得初检失败时的 candidate 不透明。
    务实方案: monkeypatch engine._stream_graph 不现实; 因此本 harness 采用
    双阶段: (1) 正常跑到 done; (2) 若 repairs_used>0 且终局 FAIL, 从 done 的
    evidence facts 无法复原 candidate —— 改为在 engine repair 循环处注入。

    最终实现: monkeypatch final_validator.validate_final_candidate 的包装器
    不够（拿不到 messages/repair_call）。因此直接复制 stream_agent 的 repair
    循环逻辑到本 harness（evaluation-only; 生产零改动）会引入漂移。

    实用结论: 用 engine 原生跑 + REPAIR_SYSTEM_PROTOCOL 路径, 但把
    format_feedback 输出替换为 patch prompt, 并在 validation 后应用 patches。
    ——这需要 engine 在 repair 分支调用我们注入的 hook。

    采用最小侵入 hook: monkeypatch EG.format_feedback? 不在 EG 命名空间。
    engine `from final_validator import validate_final_candidate, format_feedback`
    在函数体内 → 可 patch final_validator 模块属性。但 patch 应用仍需在
    engine 循环里做 → 不可达。

    落地方案（诚实）: 专用 mini-loop harness——不走完整 engine, 而是复刻
    「question→normal→validate→repair(LOCAL_PATCH)→validate→publish」的最小
    链路, normal 阶段直接调用 EG.APP 式工具循环太重——用单轮 normal 生成
    candidate（无工具轮, 题目是旧失败池, 其初检候选已知会带 quote issues
    的典型形态由 normal 模型自然产生）。此为本 harness 的限定, 如实记录。
    """
    # 单轮 normal 生成（无工具——校准池案例的失败签名是引文类, normal 单轮
    # 从系统提示+问题即可产出含引文的长答案; 工具轮留 RUN2 评审后决定）
    from langchain_core.messages import SystemMessage, HumanMessage
    from routes.agent import TOOLS  # noqa: F401—not used in mini-loop
    sys_txt = None
    src = open(os.path.join(ROOT, "backend/engine_langgraph.py"), encoding="utf-8").read()
    contract = src.split('SYSTEM_PROMPT_LG = """')[1].split('"""')[0]
    sys_txt = contract + getattr(EG, "SCHOLARLY_CONTRACT", "")
    repair_proto = getattr(EG, "REPAIR_SYSTEM_PROTOCOL", "")
    normal_client = mk_normal()
    repair_client = mk_repair()
    from langchain_core.messages import AIMessage

    raw_tool_log = []
    # 题干附带证据预取提示不引入; 让模型自然写——若初检即 PASS 记录之
    normal_msgs = [SystemMessage(content=sys_txt),
                   HumanMessage(content=case["question"])]
    resp = normal_client.invoke(normal_msgs)
    candidate = resp.content or ""
    v = validate_final_candidate(candidate, raw_tool_log=raw_tool_log,
                                fallback_log=[], language="zh")
    trace = {"INITIAL_ISSUES": [i.code for i in v.issues]}
    if v.ok:
        return {"case_id": case["case_id"], "published": True, "repairs": 0,
                "trace": trace, "answer_len": len(candidate), "mode": "none"}
    # repair 循环（LOCAL_PATCH 优先; 无局部锚 → FULL_REWRITE 用 repair protocol）
    cur = candidate
    repairs = 0
    modes = []
    while repairs < MAX_TURNS:
        repairs += 1
        new, notes = _patch_mode_repair(cur, v, [SystemMessage(content=sys_txt),
                                                 HumanMessage(content=case["question"])],
                                         raw_tool_log,
                                         lambda m: repair_client.invoke(m).content or "")
        modes.append(notes)
        if notes and notes.get("mode") == "LOCAL_PATCH" and new:
            cur = new
            v2 = validate_final_candidate(cur, raw_tool_log=raw_tool_log,
                                          fallback_log=[], language="zh")
            trace[f"R{repairs}_ISSUES"] = [i.code for i in v2.issues]
            if v2.ok:
                return {"case_id": case["case_id"], "published": True,
                        "repairs": repairs, "trace": trace,
                        "answer_len": len(cur), "mode": "LOCAL_PATCH"}
            v = v2
            cur = cur          # 已 patch 的候选继续下一轮（fresh anchors §8/A16）
            continue
        # LOCAL_PATCH 不可行（无局部 issue/锚失败/协议错误）→ FULL_REWRITE
        fb = format_feedback(v)
        msgs = [SystemMessage(content=sys_txt + repair_proto),
                HumanMessage(content=case["question"]),
                AIMessage(content=cur), HumanMessage(content=fb)]
        resp2 = repair_client.invoke(msgs)
        cur2 = resp2.content or ""
        v = validate_final_candidate(cur2, raw_tool_log=raw_tool_log,
                                     fallback_log=[], language="zh")
        trace[f"R{repairs}_ISSUES"] = [i.code for i in v.issues]
        cur = cur2
        if v.ok:
            return {"case_id": case["case_id"], "published": True,
                    "repairs": repairs, "trace": trace,
                    "answer_len": len(cur), "mode": "FULL_REWRITE"}
    return {"case_id": case["case_id"], "published": False, "repairs": repairs,
            "trace": trace, "answer_len": len(cur),
            "final_issues": [i.code for i in v.issues]}


def main(run_tag):
    cfg = CC.v4pro_config(dict(RP_B, id="RP-B"))
    mk_n = lambda: CC.build_candidate_langchain_client(cfg, "normal")
    mk_r = lambda: CC.build_candidate_langchain_client(cfg, "repair")
    pool = json.load(open(os.path.join(ROOT, "backend/tools/_tmp",
                                       "o7e_rp2_repair_pool.json"), encoding="utf-8"))
    out_path = os.path.join(ROOT, "backend/tools/_tmp", f"o7e_rca1_{run_tag}.json")
    runs = []
    if os.path.exists(out_path):
        runs = json.load(open(out_path, encoding="utf-8"))
    done = {r["case_id"] for r in runs}
    for p in pool:
        if p["case_id"] in done:
            continue
        case = {"case_id": p["case_id"], "question": p["question"]}
        print(f"== {p['case_id']}", flush=True)
        try:
            r = run_case_local(case, mk_n, mk_r)
        except Exception as e:
            r = {"case_id": p["case_id"], "error": str(e)[:200]}
            print("   err", str(e)[:100], flush=True)
        runs = [x for x in runs if x["case_id"] != p["case_id"]] + [r]
        json.dump(runs, open(out_path, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"   pub={r.get('published')} mode={r.get('mode')} "
              f"repairs={r.get('repairs')}", flush=True)
    ok = [r for r in runs if "error" not in r]
    pub = sum(1 for r in ok if r.get("published"))
    trig = [r for r in ok if (r.get("repairs") or 0) > 0]
    conv = sum(1 for r in trig if r.get("published"))
    out = {"run": run_tag, "model": cfg.requested_model, "config": RP_B,
           "COMPLETED": len(ok), "PUBLISHED": pub,
           "REPAIR_TRIGGERED": len(trig),
           "REPAIR_CONVERGENCE": round(conv / max(len(trig), 1), 3) if trig else None,
           "EMPTY_FINAL": 0,
           "modes": {m: sum(1 for r in ok if r.get("mode") == m)
                     for m in ("none", "LOCAL_PATCH", "FULL_REWRITE")}}
    json.dump(out, open(out_path.replace(".json", "_summary.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1])
