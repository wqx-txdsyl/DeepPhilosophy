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
import sys, os, hashlib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scholarly_sources as SS
from routes.agent_core import TOOLS, register_tool, _int_arg, _str_arg


def _exec_search_scholarship(args):
    query = _str_arg(args, "query")
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
    # V5-F2 §C: 机械派生可读计数——search 只是 discovery, 内容性归因前必须
    # get_scholarly_source; 模型需要显式知道结果里有多少条可读、是哪些
    views = [SS.model_view(r) for r in out["results"]]
    _readable = [r for r in views
                 if r.get("access_level") in ("ABSTRACT_AVAILABLE",
                                              "FULL_TEXT_AVAILABLE", "FULL_TEXT_READ")]
    resp = {"query": out["query"],
            "results": views,
            "READABLE_RESULT_COUNT": len(_readable),
            "READABLE_SOURCE_IDS": [r.get("source_record_id") for r in _readable],
            "providers_queried": out["providers_queried"]}
    for key in ('status','provider_attempts','relevance_gate','query_reformulation','offline_mode'):
        if key in out:
            resp[key] = out[key]
    if out["errors"]:
        resp["provider_errors"] = out["errors"]
        resp["note"] = ("部分 provider 检索失败（见 provider_errors）——"
                        "检索失败不等于没有相关文献")
    elif not out["results"]:
        resp["note"] = "0 结果只表示该 provider/query 无记录, 不表示学界没有研究"
    elif _readable:
        resp["note"] = (f"结果中有 {len(_readable)} 条可读来源（access_level ≥ "
                        "ABSTRACT_AVAILABLE, 见 READABLE_SOURCE_IDS）。access_level 只反映"
                        "已实际取得的证据; 对任何来源作内容性归因前必须先用 "
                        "get_scholarly_source 读取, 不得仅凭标题/记忆陈述其观点")
    else:
        resp["note"] = ("记录为真实检索所得, 但全部为 METADATA_ONLY（无可读内容）——"
                        "只能陈述书目存在性, 不得凭标题推断内容")
    if out.get('cached'):
        resp['cached'] = True
        resp['cache_created_at'] = out.get('cache_created_at')
        resp['note'] = '返回10分钟内的检索缓存，本轮未重新访问外部数据源。' + resp.get('note', '')
    return resp


def _exec_get_scholarly_source(args):
    sid = _str_arg(args, "source_record_id")
    requested = args.get("requested_access") or "ABSTRACT"
    if requested not in ("ABSTRACT", "FULL_TEXT_IF_LEGALLY_AVAILABLE"):
        return {"error": "requested_access 只支持 ABSTRACT | FULL_TEXT_IF_LEGALLY_AVAILABLE"}
    offset=args.get('offset') if args.get('offset') is not None else 0
    window=args.get('max_chars') if args.get('max_chars') is not None else 2800
    if type(offset) is not int or offset<0 or type(window) is not int or window<1:
        return {'error':'INVALID_EVIDENCE_WINDOW','message':'offset 应为非负整数，max_chars 应为正整数。'}
    def finish(out):
        out={**out,'requested_access':requested}
        abstract=out.get('abstract')
        if isinstance(abstract,dict) and isinstance(abstract.get('text'),str):
            text=abstract['text'];start=min(offset,len(text));end=min(start+window,len(text))
            out['abstract']={**abstract,'text':text[start:end],
                'excerpt_start':start,'excerpt_end':end,'total_characters':len(text),
                'has_more':end<len(text),'next_offset':end if end<len(text) else None,
                'truncated':start>0 or end<len(text),'content_sha256':hashlib.sha256(text.encode()).hexdigest(),
                'window_covers_available_text':start==0 and end==len(text),
                'source_abstract_completeness':'unverified'}
        passages=out.get('evidence_passages') or []
        if passages:
            out['read_scope']='full_text_excerpts'
            out['whole_document_returned']=False
            out['note']=out.get('note','')+' 返回的是正文节选，不能据此声称模型已通读整篇；历史证据也不证明当前网址可达。'
        elif isinstance(out.get('abstract'),dict) and out['abstract'].get('text'):
            out['read_scope']='abstract_excerpt' if out['abstract']['truncated'] else 'available_abstract'
            out['whole_document_returned']=False
            out['note']=out.get('note','')+' 只返回当前来源提供的摘要文本；has_more/total_characters 仅针对已取得文本，上游可能已截断，不能据此认定原始摘要完整。若有 has_more，可按 next_offset 续读，不等于论文全文。'
        else:
            if isinstance(abstract,dict) and abstract.get('text') and offset>=len(abstract['text']):
                out['read_scope']='empty_window'
                out['error']='ABSTRACT_OFFSET_OUT_OF_RANGE'
                out['note']='摘要存在，但请求起点超出已取得摘要范围；这不是资料缺失。'
            else:out['read_scope']='metadata_only'
            out['whole_document_returned']=False
        return out
    try:
        from research_bridge import evidence_result
        indexed = evidence_result(sid, requested)
        if indexed:
            return finish(indexed)
    except Exception:
        pass  # Optional DB outage must not break the existing evidence reader.
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
        out["abstract"] = {"text": info["abstract"].get("text") or "",
                           "source": info["abstract"].get("source"),
                           "hash": info["abstract"].get("hash")}
    if info.get("historical_evidence_level"):
        out["historical_evidence_level"] = info["historical_evidence_level"]
    for item in info.get("_evidence_origin_items") or []:
        out.setdefault("evidence_origin", item["evidence_origin"])
    if info.get("evidence_passages"):
        out["evidence_passages"] = info["evidence_passages"]
        out["passage_locators"] = [p.get("locator") for p in info["evidence_passages"]]
    if info.get('full_text_attempts'):out['full_text_attempts']=info['full_text_attempts']
    return finish(out)


register_tool(
    "search_scholarship",
    "检索真实学术文献记录（期刊论文/专著章节等; Crossref+OpenAlex 双源）。"
    "⚠ metadata/discovery only: 只返回书目与访问层级信息, 内容归因必须再用 "
    "get_scholarly_source 取得摘要/正文证据。"
    "记录可能是 scholarly secondary、reference、primary publication 或尚未分类——"
    "由 source_category 字段如实标注。access_level（METADATA_ONLY/ABSTRACT_AVAILABLE/"
    "FULL_TEXT_AVAILABLE/FULL_TEXT_READ）只反映已实际取得的证据层级; "
    "ABSTRACT_AVAILABLE 表示有摘要可读, 不表示已读。"
    "是否检索、检索什么、选哪篇由你决定; 记录存在不等于论文已被阅读, 不得凭标题推断论文内容。"
    "查询构造建议（非英语哲学家/术语/经典尤适用）: 依次尝试原语言名称、通行英文名、"
    "罗马化/别名、核心概念的通行英译、人物+概念、作品+概念; 首轮结果明显离题时, "
    "换语言或关键词重新表述再检索。",
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
    "未读全文不会谎报已读）。摘要支持 offset/max_chars 续读；read_scope 明确区分摘要、正文节选与书目。"
    "完整摘要不是论文全文；方法/论证细节超出摘要时须实际读取对应正文或保留未知。输入只接受检索返回的 source_record_id。",
    {"type": "object",
     "properties": {"source_record_id": {"type": "string", "description": "search_scholarship 返回的记录 ID"},
                    "requested_access": {"type": "string", "enum": ["ABSTRACT", "FULL_TEXT_IF_LEGALLY_AVAILABLE"]},
                    "offset": {'type':'integer','description':'摘要字符起点，默认0；续读用上次 next_offset。'},
                    "max_chars": {'type':'integer','description':'摘要窗口字符数，默认2800，可按需要增大。'}},
     "required": ["source_record_id"]},
    _exec_get_scholarly_source,
)
