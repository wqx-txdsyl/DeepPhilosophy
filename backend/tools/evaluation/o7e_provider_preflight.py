# -*- coding: utf-8 -*-
"""V5-F2 §F: qualification provider preflight——显式报告网络/可达性状态,
禁止把 provider blockage 静默当作正常在线运行。

用法:
  SCHOLARLY_NETWORK_MODE=TRUSTED_PROXY .venv/bin/python \
      backend/tools/evaluation/o7e_provider_preflight.py [--out PATH]

输出字段（任务书 §F 冻结名称）:
  NETWORK_MODE / CROSSREF_REACHABLE / OPENALEX_REACHABLE /
  LIVE_PROVIDER_AVAILABLE / OFFLINE_MODE
"""
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "backend"))

import scholarly_sources as SS  # noqa: E402


def _probe(fn):
    t0 = time.time()
    try:
        fn("test", limit=1)
        return True, None, round(time.time() - t0, 2)
    except SS.ProviderError as e:
        return False, f"{e.kind}: {e.detail}"[:200], round(time.time() - t0, 2)
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)[:150]}", round(time.time() - t0, 2)


def preflight():
    cr_ok, cr_err, cr_ms = _probe(SS.search_crossref)
    oa_ok, oa_err, oa_ms = _probe(SS.search_openalex)
    return {
        "V5_F2_PROVIDER_PREFLIGHT": True,
        "NETWORK_MODE": SS._network_mode(),
        "CROSSREF_REACHABLE": cr_ok,
        "CROSSREF_ERROR": cr_err,
        "CROSSREF_LATENCY_S": cr_ms if cr_ok else None,
        "OPENALEX_REACHABLE": oa_ok,
        "OPENALEX_ERROR": oa_err,
        "OPENALEX_LATENCY_S": oa_ms if oa_ok else None,
        "LIVE_PROVIDER_AVAILABLE": bool(cr_ok or oa_ok),
        "OFFLINE_MODE": not (cr_ok or oa_ok),
        "note": ("OFFLINE_MODE=true 时 scholarly 发现层只剩本地 curated registry; "
                 "qualification 结果解释必须显式携带该状态, 不得静默当作在线运行"),
    }


if __name__ == "__main__":
    out = preflight()
    for a in sys.argv[1:]:
        if a.endswith(".json"):
            json.dump(out, open(a, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
