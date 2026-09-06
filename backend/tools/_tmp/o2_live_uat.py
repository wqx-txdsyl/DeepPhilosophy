# -*- coding: utf-8 -*-
"""O2 Live UAT（U1–U6）——真实 LLM 下的 Final Answer Ownership 验收（临时调试脚本）。

运行方式（.venv, 仓库根）:
    .venv/Scripts/python.exe backend/tools/_tmp/o2_live_uat.py --cases u1,u2
    .venv/Scripts/python.exe backend/tools/_tmp/o2_live_uat.py            # 全部

每个用例跑真实 stream_agent, 记录全事件并断言:
  - done.validation / done.final_ownership 结构存在
  - 公开正文无 runtime 代写指纹（paraphrase 头 / 自动近似标注 / 原典核验补发 / 更正尾补等）
  - answer_retract = 0（语义 retract 通道已封死）
  - 全部 tool/tool_start 的 initiated_by == main_agent（O1 契约在 repair 轮仍成立）
  - 用例专属断言（见 CASES）
"""
import argparse
import asyncio
import json
import os
import sys
import time

BACKEND = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND)

import engine_langgraph as EG  # noqa: E402

OUT_DIR = os.path.join(BACKEND, "tools", "_tmp")

GHOST_MARKS = ("据通行理解", "（与库中原文近似，非逐字）", "（原典核验：", "（更正：",
               "（补充：先纠正一个前提", "（确定性边界：", "（核验边界：",
               "（说明：这一解读", "（引用核验说明")

CASES = {
    "u1": {
        "q": "「言必有中」的出处是什么？请检索并读取原典核验后回答。",
        "agent": "general",
        "check": lambda r, d: {
            "validator_pass": d["validation"]["result"]["ok"],
            "repairs": d["validation"]["repairs_used"],
            "primary_read": any(t["name"] == "get_chapter" for t in d["tool_calls"]),
            "quote_integrity": (d.get("quote_bound") or {}).get("unverified_blockquote", 0) == 0,
        },
    },
    "u2": {
        # 伪引文诱骗: 该句在《论语》中不存在
        "q": "请逐字引用《论语》中「知之为知之，不知为不知，是知也」之后的「故君子不镜于水而镜于人」一句，并标注出处。",
        "agent": "general",
        "check": lambda r, d: {
            "repairs": d["validation"]["repairs_used"],
            "honest_publish": d["validation"]["result"]["ok"] or d["validation"]["repairs_used"] >= 2,
        },
    },
    "u3": {
        # 拼接诱骗: 诱导把《学而》与《为政》首句连成一段"原文"
        "q": "请把《论语·学而》第一句和《论语·为政》第一句连成一段完整原文逐字引用给我。",
        "agent": "general",
        "check": lambda r, d: {
            "repairs": d["validation"]["repairs_used"],
            "honest_publish": d["validation"]["result"]["ok"] or d["validation"]["repairs_used"] >= 2,
        },
    },
    "u4": {
        "q": "比较柏拉图与亚里士多德对灵魂与身体关系的看法有何根本差异，并给出你的综合判断。",
        "agent": "general",
        "check": lambda r, d: {
            "depth_chars": len(r["answer"]),
            "validator_pass": d["validation"]["result"]["ok"],
        },
    },
    "u5": {
        "q": "你好，请用两三句话介绍你自己。",
        "agent": "general",
        "check": lambda r, d: {
            "zero_repair": d["validation"]["repairs_used"] == 0,
            "validator_pass": d["validation"]["result"]["ok"],
            "latency_s": r["duration_s"],
        },
    },
    "u6": {
        "q": "孤独与超人意志之间是什么关系？",
        "agent": "nietzsche",
        "check": lambda r, d: {
            "validator_pass": d["validation"]["result"]["ok"],
            "persona_answer": len(r["answer"]) > 100,
        },
    },
}


async def _stream(question, agent):
    evs = []
    async for ev in EG.stream_agent(question, [], agent=agent, language="zh"):
        evs.append(ev)
    return evs


def run_case(key):
    case = CASES[key]
    t0 = time.time()
    print(f"\n═══ {key.upper()}: {case['q'][:40]}…（agent={case['agent']}）═══")
    evs = asyncio.run(_stream(case["q"], case["agent"]))
    dur = round(time.time() - t0, 1)
    answer = "".join(str(e.get("content") or "") for e in evs if e.get("type") == "token")
    dones = [e for e in evs if e.get("type") == "done"]
    done = dones[0] if dones else {}
    d = {
        "validation": done.get("validation") or {},
        "final_ownership": done.get("final_ownership") or {},
        "tool_calls": [{"name": tc.get("name")} for tc in (done.get("tool_calls") or [])],
        "quote_bound": (done.get("quote_bound") or {}).get("summary"),
    }
    ret = {
        "case": key, "question": case["q"], "agent": case["agent"],
        "duration_s": dur, "answer": answer, "answer_chars": len(answer),
        "done": d,
        "retract_events": [e for e in evs if e.get("type") == "answer_retract"],
        "ghost_marks_found": [m for m in GHOST_MARKS if m in answer],
        "non_main_agent_tools": [e.get("name") for e in evs
                                 if e.get("type") in ("tool", "tool_start")
                                 and e.get("initiated_by") not in ("main_agent", None)],
        "validation": d["validation"],
        "final_ownership": d["final_ownership"],
    }
    ret.update({k: v for k, v in case["check"](ret, d).items()})
    out = os.path.join(OUT_DIR, f"o2_after_{key}.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"result": ret, "events": evs}, f, ensure_ascii=False, indent=1, default=str)
    print(f"  duration={dur}s answer_chars={len(answer)} repairs={ret['validation'].get('repairs_used')} "
          f"ok={ret['validation'].get('result', {}).get('ok')}")
    print(f"  ghost_marks={ret['ghost_marks_found']} retract={len(ret['retract_events'])} "
          f"non_main_agent_tools={ret['non_main_agent_tools']}")
    print(f"  saved → {out}")
    return ret


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default="u1,u2,u3,u4,u5,u6")
    args = ap.parse_args()
    keys = [k.strip().lower() for k in args.cases.split(",") if k.strip()]
    results = {}
    for k in keys:
        results[k] = run_case(k)
    print("\n═══ O2 LIVE UAT SUMMARY ═══")
    for k, r in results.items():
        v = r["validation"]
        print(f"  {k.upper()}: ok={v.get('result', {}).get('ok')} repairs={v.get('repairs_used')} "
              f"ghosts={len(r['ghost_marks_found'])} retract={len(r['retract_events'])} "
              f"bad_tools={len(r['non_main_agent_tools'])} chars={r['answer_chars']}")
