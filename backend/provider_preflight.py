# -*- coding: utf-8 -*-
"""Provider Qualification Preflight（O10-R1 §8 Cost Safety）

只做运行前基础设施检查（GO/NO-GO 依据）, 绝不在运行中自动换模型:
  PROVIDER_AUTH_OK              生产模型端点鉴权可用（最小请求 HTTP 200）
  PROVIDER_BALANCE_OR_QUOTA_OK  供应商余额/配额可用（200 = 付费通道存活; 402/403 = FAIL）
  PRIMARY_CHANNEL_OK            原典库检索通道可执行（本地语料 + 检索管线无错）
  SCHOLARLY_CHANNEL_OK          二手文献通道可执行（真实外部检索一次; offline_mode 如实标注）
  WEB_CHANNEL_OK                网络检索通道可执行

V1 事故教训: 14 题烧穿 DeepSeek 账户（402 Insufficient Balance）, 58 题未执行。
任何 qualification run 开始前必须先跑本检查; PROVIDER_* 任一 FAIL → 不得开始,
如实上报, 不换供应商、不换模型。
"""
import json
import os
import time

CHECK_TIMEOUT_S = 45


def _probe_provider():
    """生产模型最小请求（max_tokens=1）: 鉴权 + 余额一次判定"""
    from routes.agent_llm import API_KEY, API_URL, MODEL, llm_chat
    host = API_URL.split("//")[-1].split("/")[0]
    try:
        t0 = time.time()
        resp = llm_chat([{"role": "user", "content": "ping"}], temperature=0.0, max_tokens=1)
        latency = round(time.time() - t0, 2)
        ok = bool(resp and resp.get("choices"))
        return {"PROVIDER_AUTH_OK": ok, "PROVIDER_BALANCE_OR_QUOTA_OK": ok,
                "PRODUCTION_MODEL": MODEL, "PROVIDER_HOST": host,
                "probe_latency_s": latency, "error": None}
    except Exception as e:
        text = str(e)
        code = None
        if "402" in text or "Insufficient Balance" in text:
            code = "402_INSUFFICIENT_BALANCE"
        elif "401" in text or "403" in text or "authenticat" in text.lower():
            code = "401_403_AUTH"
        elif "429" in text or "rate" in text.lower():
            code = "429_RATE_LIMIT"
        return {"PROVIDER_AUTH_OK": False, "PROVIDER_BALANCE_OR_QUOTA_OK": False,
                "PRODUCTION_MODEL": MODEL, "PROVIDER_HOST": host,
                "probe_latency_s": None, "error": f"{code or 'PROVIDER_ERROR'}: {text[:160]}"}


def _probe_primary_channel():
    """原典库检索: search_books 真实执行一次（本地语料, 不产生外部费用）"""
    try:
        from routes.agent import TOOLS
        t0 = time.time()
        res = TOOLS["search_books"]["execute"]({"query": "存在", "limit": 3})
        latency = round(time.time() - t0, 2)
        err = isinstance(res, dict) and res.get("error")
        hits = len((res or {}).get("results") or [])
        return {"PRIMARY_CHANNEL_OK": not err and hits > 0,
                "probe_latency_s": latency, "sample_hits": hits, "error": str(err)[:120] if err else None}
    except Exception as e:
        return {"PRIMARY_CHANNEL_OK": False, "probe_latency_s": None,
                "sample_hits": 0, "error": str(e)[:160]}


def _probe_scholarly_channel():
    """二手文献通道: search_scholarship 真实执行一次。

    渠道可用 = 外部 provider 真实可达（无 URL_BLOCKED/网络类 provider_errors 且
    offline_mode 为假）。空结果但无错误 = 通道存活（该 query 恰无记录）。"""
    try:
        from routes.agent import TOOLS
        t0 = time.time()
        res = TOOLS["search_scholarship"]["execute"]({"query": "free will", "limit": 2})
        latency = round(time.time() - t0, 2)
        err = isinstance(res, dict) and res.get("error")
        offline = bool(isinstance(res, dict) and res.get("offline_mode"))
        n = len((res or {}).get("results") or [])
        perr = (res or {}).get("provider_errors") or []
        net_blocked = any(e.get("error") in ("URL_BLOCKED", "DNS_FAILURE", "TIMEOUT",
                                             "CONNECTION_ERROR") if isinstance(e, dict) else True
                          for e in perr)
        return {"SCHOLARLY_CHANNEL_OK": not err and not offline and not net_blocked,
                "scholarly_offline_mode": offline,
                "scholarly_provider_errors": [f"{e.get('provider')}:{e.get('error')}"
                                              for e in perr if isinstance(e, dict)][:4],
                "sample_hits": n,
                "probe_latency_s": latency,
                "error": str(err)[:120] if err else None}
    except Exception as e:
        return {"SCHOLARLY_CHANNEL_OK": False, "scholarly_offline_mode": None,
                "scholarly_provider_errors": [], "sample_hits": 0,
                "probe_latency_s": None, "error": str(e)[:160]}


def _probe_web_channel():
    """网络检索通道: websearch 真实执行一次。

    渠道可用 = 实际取回 ≥1 条结果（搜索引擎对常用词返回 0 条 = 事实不可达,
    即使执行器不报错——V1 §3.5 环境观察与本机实测的判据）。"""
    try:
        from routes.agent import TOOLS
        t0 = time.time()
        res = TOOLS["websearch"]["execute"]({"query": "philosophy", "limit": 3})
        latency = round(time.time() - t0, 2)
        err = isinstance(res, dict) and res.get("error")
        n = len((res or {}).get("results") or [])
        return {"WEB_CHANNEL_OK": not err and n > 0,
                "sample_hits": n, "probe_latency_s": latency,
                "error": str(err)[:120] if err else None}
    except Exception as e:
        return {"WEB_CHANNEL_OK": False, "sample_hits": 0,
                "probe_latency_s": None, "error": str(e)[:160]}


def run_preflight():
    """五项运行前基础设施检查（顺序执行, 供应商探针失败时通道探针照常完成）"""
    report = {"preflight": "O10_R1_PROVIDER_QUALIFICATION",
              "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
              "SCHOLARLY_NETWORK_MODE": os.environ.get("SCHOLARLY_NETWORK_MODE", "AUTO")}
    report.update(_probe_provider())
    report.update(_probe_primary_channel())
    report.update(_probe_scholarly_channel())
    report.update(_probe_web_channel())
    report["ALL_PROVIDER_GATES_PASS"] = bool(
        report.get("PROVIDER_AUTH_OK") and report.get("PROVIDER_BALANCE_OR_QUOTA_OK"))
    report["CHANNELS"] = {
        "PRIMARY_CHANNEL_OK": report.get("PRIMARY_CHANNEL_OK"),
        "SCHOLARLY_CHANNEL_OK": report.get("SCHOLARLY_CHANNEL_OK"),
        "SCHOLARLY_OFFLINE_MODE": report.get("scholarly_offline_mode"),
        "WEB_CHANNEL_OK": report.get("WEB_CHANNEL_OK")}
    report["POLICY"] = ("PROVIDER_* 任一 FAIL → 不得开始 qualification run, 如实上报; "
                        "通道 FAIL 记录后由 Reviewer 裁量, 运行中不自动换模型/供应商")
    return report


if __name__ == "__main__":
    print(json.dumps(run_preflight(), ensure_ascii=False, indent=1))
