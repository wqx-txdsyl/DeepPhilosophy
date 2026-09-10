"""PF-RP4B-R1: final-gate 检查器加载 helper（供 parity 测试复用）。"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "tools", "evaluation"))
from o7e_final_gate import check_final_gate  # noqa: F401


def load_v3_summary():
    """canonical gate 输入 = judge summary ⊕ run summary（delivery 字段在 run 侧）。"""
    base = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))), "docs/evidence")
    judge = json.load(open(os.path.join(base, "V3_FINAL_HOLDOUT_JUDGE_summary.json"),
                           encoding="utf-8"))
    run = json.load(open(os.path.join(base, "o7e_calib_V3_HOLDOUT_summary.json"),
                         encoding="utf-8"))
    merged = dict(run)
    merged.update(judge)
    return merged
