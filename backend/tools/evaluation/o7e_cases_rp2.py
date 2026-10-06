# -*- coding: utf-8 -*-
"""O7-E RP2 §10: thin loader——canonical source = PHIAGENT_O7E_RP2_HOLDOUT_CASES.json。
禁止在此文件维护独立 case 定义（PYTHON_JSON_CASE_DRIFT=0）。"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
_JSON = os.path.join(ROOT, "docs", "evidence", "PHIAGENT_O7E_RP2_HOLDOUT_CASES.json")

_d = json.load(open(_JSON, encoding="utf-8"))
HOLDOUT_CASES_RP2 = _d["cases"]
HOLDOUT_CASE_UNIVERSE_HASH = _d["holdout_case_universe_hash"]
assert len(HOLDOUT_CASE_UNIVERSE_HASH) == 64, "V2 宇宙 hash 漂移"
