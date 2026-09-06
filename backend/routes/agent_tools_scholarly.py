# -*- coding: utf-8 -*-
"""O7-C 工具域——二手学术文献检索（2 个 Main-Agent 工具）。

- search_scholarship: 发现真实 scholarly records + bibliographic identity +
  access level（只报告已实际取得的证据层级）
- get_scholarly_source: 按 source_record_id 取实际可读 evidence（abstract /
  合法 OA 全文节选）, 严格访问状态机

Main Agent 拥有全部研究选择（是否搜/搜什么/读不读/何时停）;
runtime 只做 execute/normalize/dedup/cache/timeout/provenance/access honesty。
输入只接受 source_record_id（非任意 URL, §51/§52 SSRF 边界在 scholarly_sources）。
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scholarly_sources as SS
from routes.agent_core import TOOLS, register_tool, _int_arg


def _exec_search_scholarship(args):
    query = (args.get("query") or "").strip()
    if not query:
        return {"error": "query 不能为空"}
    limit = _int_arg(args, "limit", 8, 1, 10)
    def _year(k):
        v = args.get(k)
        try:
            return int(v) if v not in (None, "") else None
        except (TypeError, ValueError):
            return None
    out = SS.search_scholarship(query, philosopher=args.get("philosopher"),
                                work=args.get("work"),
                                year_from=_year("year_from"), year_to=_year("year_to"),
                                limit=limit)
    resp = {"query": out["query"],
            "results": [SS.model_view(r) for r in out["results"]],
            "providers_queried": out["providers_queried"]}
    if out["errors"]:
        resp["provider_errors"] = out["errors"]
        resp["note"] = ("部分 provider 检索失败（见 provider_errors）——"
                        "检索失败不等于没有相关文献")
    else:
        resp["note"] = ("0 结果只表示该 provider/query 无记录, 不表示学界没有研究"
                        if not out["results"] else
                        "记录为真实检索所得; access_level 只反映已实际取得的证据")
    return resp


def _exec_get_scholarly_source(args):
    sid = (args.get("source_record_id") or "").strip()
    requested = args.get("requested_access") or "ABSTRACT"
    if requested not in ("ABSTRACT", "FULL_TEXT_IF_LEGALLY_AVAILABLE"):
        return {"error": "requested_access 只支持 ABSTRACT | FULL_TEXT_IF_LEGALLY_AVAILABLE"}
    rec = SS.get_record(sid)
    if not rec:
        return {"error": f"未找到 source_record_id {sid}（先用 search_scholarship 检索）"}
    rec, info = SS.get_evidence(rec, requested)
    SS._load_cache()["records"][sid] = rec   # access 状态更新回缓存
    SS._save_cache()
    out = {"source_record_id": sid,
           "bibliographic_record": SS.model_view(rec),
           "access_level_before": info["access_level_before"],
           "access_level_after": info["access_level_after"],
           "returned_evidence_level": info.get("returned_evidence_level"),
           "full_text_status": info["full_text_status"],
           "source_url": info["source_url"],
           "content_hash": info["content_hash"],
           "access_notes": info["access_notes"],
           "note": "access_notes 明确说明实际读到了什么; 不得超出该证据描述文献内容"}
    if info.get("abstract"):
        out["abstract"] = {"text": info["abstract"]["text"][:1800],
                           "source": info["abstract"]["source"],
                           "hash": info["abstract"]["hash"]}
    if info.get("evidence_passages"):
        out["evidence_passages"] = info["evidence_passages"]
        out["passage_locators"] = [p.get("locator") for p in info["evidence_passages"]]
    return out


register_tool(
    "search_scholarship",
    "检索真实学术文献记录（期刊论文/专著章节等; Crossref+OpenAlex 双源）。"
    "记录可能是 scholarly secondary、reference、primary publication 或尚未分类——"
    "由 source_category 字段如实标注。access_level（METADATA_ONLY/ABSTRACT_AVAILABLE/"
    "FULL_TEXT_AVAILABLE/FULL_TEXT_READ）只反映已实际取得的证据层级。"
    "是否检索、检索什么、选哪篇由你决定; 记录存在不等于论文已被阅读, 不得凭标题推断论文内容。",
    {"type": "object",
     "properties": {"query": {"type": "string", "description": "研究主题/论证/争议关键词"},
                    "philosopher": {"type": "string", "description": "哲学家名（可选, 限定检索）"},
                    "work": {"type": "string", "description": "作品名（可选）"},
                    "year_from": {"type": "integer"}, "year_to": {"type": "integer"},
                    "limit": {"type": "integer", "description": "返回上限 1-10"}},
     "required": ["query"]},
    _exec_search_scholarship,
)

register_tool(
    "get_scholarly_source",
    "按 source_record_id 取得实际可读证据: requested_access=ABSTRACT 取真实摘要; "
    "FULL_TEXT_IF_LEGALLY_AVAILABLE 尝试合法开放获取全文并返回节选段落（访问边界诚实: "
    "未读全文不会谎报已读）。输入只接受检索返回的 source_record_id。",
    {"type": "object",
     "properties": {"source_record_id": {"type": "string", "description": "search_scholarship 返回的记录 ID"},
                    "requested_access": {"type": "string", "enum": ["ABSTRACT", "FULL_TEXT_IF_LEGALLY_AVAILABLE"]}},
     "required": ["source_record_id"]},
    _exec_get_scholarly_source,
)
