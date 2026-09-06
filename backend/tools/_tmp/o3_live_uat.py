# -*- coding: utf-8 -*-
"""O3 Live UAT（U1–U7）——真实模型下的 Tool Authority 验收（临时调试脚本）。

运行: .venv/Scripts/python.exe backend/tools/_tmp/o3_live_uat.py [--cases u1,u2,...]
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

SEMANTIC_REJECT_MARKS = ("检索准入未通过", "技能重入被拦截", "核验配额", "义务已满足",
                         "已被收敛机制取消", "最后核验机会")

CASES = {
    "u1": {"q": "「言必有中」的出处是什么？请检索并读取原典核验后回答。", "agent": "general"},
    "u2": {"q": "尼采「上帝已死」这一命题在《快乐的科学》与《查拉图斯特拉如是说》中分别如何出现？"
                "请尽量定位原始文本位置后再回答。", "agent": "general"},
    "u3": {"q": "比较康德的义务论与密尔的功利主义在「能否为说谎辩护」上的根本分歧，并给出你的综合评价。", "agent": "general"},
    "u4": {"q": "「zqxvoronovism」这个概念的出处是什么？", "agent": "general"},   # 本地必空的生造词
    "u5": {"q": "请用两三句话解释什么是思想实验。", "agent": "general"},
    "u6": {"q": "请逐字引用《论语》中「宰予昼寝」一章孔子原话并标注出处。", "agent": "general"},
    "u7": {"q": "请对比柏拉图与尼采对「真理」的态度差异。", "agent": "general"},   # 诱发 compare_views（模型自愿）
}


async def _stream(question, agent):
    evs = []
    async for ev in EG.stream_agent(question, [], agent=agent, language="zh"):
        evs.append(ev)
    return evs


def run_case(key):
    case = CASES[key]
    t0 = time.time()
    print(f"\n═══ {key.upper()}: {case['q'][:36]}…（agent={case['agent']}）═══")
    evs = asyncio.run(_stream(case["q"], case["agent"]))
    dur = round(time.time() - t0, 1)
    answer = "".join(str(e.get("content") or "") for e in evs if e.get("type") == "token")
    done = next((e for e in evs if e.get("type") == "done"), {})
    tool_seq = [t.get("name") for t in (done.get("tool_calls") or [])]
    thoughts = [str(t.get("thought") or "") for t in (done.get("tool_calls") or [])]
    ret = {
        "case": key, "question": case["q"], "agent": case["agent"],
        "duration_s": dur, "answer_chars": len(answer), "answer": answer[:1200],
        "tool_seq": tool_seq,
        "validation": done.get("validation"),
        "causal": done.get("causal"),
        "budget": (done.get("tool_loop") or {}).get("budget"),
        "semantic_reject_marks": [m for m in SEMANTIC_REJECT_MARKS
                                  for t in thoughts if m in t],
        "retract_events": len([e for e in evs if e.get("type") == "answer_retract"]),
        "validation_failed_events": len([e for e in evs if e.get("type") == "validation_failed"]),
    }
    out = os.path.join(OUT_DIR, f"o3_after_{key}.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"result": ret, "events": evs}, f, ensure_ascii=False, indent=1, default=str)
    v = ret["validation"] or {}
    print(f"  duration={dur}s chars={ret['answer_chars']} tools={len(tool_seq)} seq={tool_seq}")
    print(f"  validator ok={v.get('result', {}).get('ok')} repairs={v.get('repairs_used')} "
          f"semantic_rejects={ret['semantic_reject_marks']} retract={ret['retract_events']}")
    print(f"  saved → {out}")
    return ret


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default="u1,u2,u3,u4,u5,u6,u7")
    args = ap.parse_args()
    results = {}
    for k in [x.strip().lower() for x in args.cases.split(",") if x.strip()]:
        results[k] = run_case(k)
    print("\n═══ O3 LIVE UAT SUMMARY ═══")
    for k, r in results.items():
        v = r["validation"] or {}
        print(f"  {k.upper()}: ok={v.get('result', {}).get('ok')} repairs={v.get('repairs_used')} "
              f"tools={len(r['tool_seq'])} semantic_rejects={len(r['semantic_reject_marks'])} "
              f"retract={r['retract_events']} chars={r['answer_chars']} dur={r['duration_s']}s")
