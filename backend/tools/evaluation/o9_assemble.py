# -*- coding: utf-8 -*-
"""O9 deliverables assembly（evaluation-only）: contract/audit/comparison/decision。"""
import json
import os
import statistics

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
EVID = os.path.join(ROOT, "docs/evidence")
TMP = os.path.join(ROOT, "backend/tools/_tmp")


def contract():
    out = {
        "O9_API_CONTRACT": True,
        "as_of": "2026-09-12",
        "metaso_official_sources": [
            "https://www.modelscope.cn/mcp/servers/metasota/metaso-search（官方 @metasota MCP 页面, 内容源=https://metaso.cn/api/mcp, 更新 2026.09.11）",
            "https://metaso.cn/api/mcp（官方 MCP 端点本体）",
            "https://metaso.cn/search-api/api-keys（官方 API key 控制台, 需注册登录）",
            "https://metaso.cn/（官方主站）",
        ],
        "protocol": "MCP over HTTP（JSON-RPC 2.0）",
        "endpoint": "https://metaso.cn/api/mcp",
        "authentication": {
            "scheme": "Authorization: Bearer <API_KEY>",
            "key_console": "https://metaso.cn/search-api/api-keys（需注册登录账号）",
            "empirical_no_credential_probe": {
                "tools/list without key": "{\"jsonrpc\":\"2.0\",\"id\":2,\"error\":{\"code\":-32603,\"message\":\"Internal error: API密钥无效\",\"data\":null}}",
                "note": "端点存活, 无效 key 返回 JSON-RPC -32603; 请求被正常路由",
            },
        },
        "tools": {
            "metaso_web_search": {
                "params": {"q": "required string", "scope": "webpage|document|paper|image|video|podcast",
                           "includeSummary": "boolean（网页摘要增强召回）",
                           "includeRawContent": "boolean（抓取来源页原文）", "size": "int, default 10"},
                "structured_bibliographic_metadata": "官方文档未提供 DOI/作者/期刊/年份等结构化书目字段",
            },
            "metaso_web_reader": {"params": {"url": "required string", "format": "json|markdown"}},
            "metaso_chat": {"params": {"message": "required string", "model": "default fast（RAG 问答）"}},
        },
        "quota": "官方提示存在 API 调用配额限制（具体数值未公开文档化）",
        "cost": None, "COST_SOURCE": "UNAVAILABLE",
        "mcp_server_registry": "ModelScope 官方注册: metasota/metaso-search（52.0k 引用, 84 收藏）",
        "phiagent_relevant_assessment": {
            "strengths_contractual": ["中文网页/文档/论文多域搜索", "includeRawContent 网页原文抓取（可读证据层）",
                                       "metaso_web_reader URL 阅读", "中文生态覆盖（秘塔主站为中文搜索产品）"],
            "gaps_contractual": ["无结构化书目元数据（DOI/venue/year/authors 未文档化为结构化返回）",
                                  "无年份过滤/排序合同字段（对比 Crossref filter、OpenAlex filter）",
                                  "认证与配额未公开数值", "metaso_chat 为 RAG 生成层——PhiAgent 架构原则要求 provider 只找材料不作答"],
        },
    }
    json.dump(out, open(os.path.join(EVID, "O9_API_CONTRACT.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=1)


def comparison():
    raw = json.load(open(os.path.join(TMP, "o9_provider_results.json"), encoding="utf-8"))
    qs = json.load(open(os.path.join(EVID, "O9_QUERYSET.json"), encoding="utf-8"))

    def agg(provider):
        rel, doi, absr, meta, dup, n, lat, cjk, errs = ([] for _ in range(9))
        for r in raw:
            p = r["providers"].get(provider)
            if not p:
                continue
            m = p["metrics"]
            rel.append(m["TOP_K_RELEVANCE"]); doi.append(m["DOI_COVERAGE"])
            absr.append(m["ABSTRACT_RATE"]); meta.append(m["METADATA_ACCURACY"])
            dup.append(m["DUPLICATE_RATE"]); n.append(len(p["raw"]))
            cjk.append(m["CJK_TITLES"])
            if p.get("error"):
                errs.append(r["query_id"])
            if p.get("latency_s") is not None:
                lat.append(p["latency_s"])
        mean = lambda x: round(statistics.mean(x), 3) if x else None
        return {"queries_completed": len(n), "errors": len(errs),
                "error_detail": "OpenAlex: PROVIDER_RATE_LIMIT 429（X-RateLimit-Remaining: 0, "
                                "Retry-After: 31830s, 共享出口 IP 日配额耗尽——外部硬墙）" if errs and provider == "B_openalex" else None,
                "TOP_K_RELEVANCE": mean(rel), "DOI_COVERAGE": mean(doi),
                "READABLE_EVIDENCE_RATE(abstract)": mean(absr),
                "METADATA_ACCURACY": mean(meta), "DUPLICATE_RATE": mean(dup),
                "LATENCY_S_mean": mean(lat),
                "CHINESE_COVERAGE_note": "CJK 命中仅出现在中/跨语言类查询, 见 per-category"}

    by_cat = {}
    for r in raw:
        by_cat.setdefault(r["category"], []).append(
            r["providers"]["A_crossref"]["metrics"])
    cat_table = {c: {"TOP_K_RELEVANCE": round(statistics.mean(x["TOP_K_RELEVANCE"] for x in ms), 3),
                     "ABSTRACT_RATE": round(statistics.mean(x["ABSTRACT_RATE"] for x in ms), 3),
                     "METADATA_ACCURACY": round(statistics.mean(x["METADATA_ACCURACY"] for x in ms), 3)}
                 for c, ms in by_cat.items()}
    blocked = {"status": "BLOCKED_AUTH", "AUTHENTICATION_REQUIRED": True,
               "reason": "MetaSo API key 需注册登录获取（https://metaso.cn/search-api/api-keys）; "
                         "当前环境无 credential（.env 无 METASO* 键）; 无凭证 MCP 实测返回 "
                         "JSON-RPC -32603 API密钥无效; 获取 credential 属用户决策项",
               "METASO_AUTH_REQUIRED": True}
    out = {
        "O9_COMPARISON": True,
        "QUERYSET_FROZEN_BEFORE_RUN": True, "QUERY_COUNT": 30, "TOP_K": 10,
        "SAME_QUERYSET_ACROSS_PROVIDERS": True, "TOP_K_CONSTANT": True,
        "RAW_RESULTS_PRESERVED": "backend/tools/_tmp/o9_provider_results.json（30 行全量原始结果）",
        "A_crossref": agg("A_crossref"),
        "B_openalex": agg("B_openalex"),
        "C_crossref+openalex": {**agg("C_crossref+openalex"),
                                "degraded_note": "B 腿被 OpenAlex 日配额耗尽(429, Retry-After 31830s)全阻, "
                                                 "C 实际=A; B 恢复后需重测"},
        "D_metaso": {**blocked, "metrics": None},
        "E_metaso+crossref+openalex": {**blocked, "metrics": None},
        "crossref_by_category": cat_table,
    }
    json.dump(out, open(os.path.join(EVID, "O9_COMPARISON.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=1)
    return out


def results_canonical():
    raw = json.load(open(os.path.join(TMP, "o9_provider_results.json"), encoding="utf-8"))
    out = {"O9_PROVIDER_RESULTS": True, "raw_rows": raw}
    json.dump(out, open(os.path.join(EVID, "O9_PROVIDER_RESULTS.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    contract()
    cmp_ = comparison()
    results_canonical()
    print("O9 deliverables: O9_API_CONTRACT.json / O9_COMPARISON.json / O9_PROVIDER_RESULTS.json")
    print(json.dumps(cmp_["A_crossref"], ensure_ascii=False, indent=1))
    print(json.dumps(cmp_["crossref_by_category"], ensure_ascii=False, indent=1))
