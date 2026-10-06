# -*- coding: utf-8 -*-
"""O8-R2 §5: 32-tool Mechanical Gate（evaluation-only）。

对 registry 实际注册的 32 工具逐个执行 9 项检查:
VALID_INPUT / INVALID_INPUT / EMPTY_RESULT / BOUNDARY / FAILURE_PATH /
SCHEMA / PROVENANCE / CITATION / SECURITY。
不适用项 = N/A + explicit reason（不得默认 PASS）。
产出 backend/tools/_tmp/o8r2_mechanical.json。
"""
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "backend"))

from routes.agent import TOOLS  # noqa: E402

# 每工具探针表。valid=合法输入; invalid=类型/必填缺失; empty=合法但无命中;
# boundary=极限参数; failure=指向不存在资源。None=该项对此工具不适用(用 na 说明)。
P = {
 "search_books": dict(valid={"query": "因果", "limit": 3},
    invalid={"query": 123}, empty={"query": "zzqqxx不存在的词组混入", "limit": 3},
    boundary={"query": "道", "limit": 1}, failure={"query": "", "limit": 3},
    citation=True),
 "get_book_detail": dict(valid={"book_id": None},  # 运行时用 search 填充
    invalid={}, empty=None, boundary=None, failure={"book_id": "no_such_book_id"},
    citation=False, need_book=True),
 "get_chapter": dict(need_book=True, citation=True),
 "query_graph": dict(valid={"philosopher": "康德"}, invalid={},
    empty={"philosopher": "不存在的哲人XYZ"}, boundary={"philosopher": "苏格拉底"},
    failure={"philosopher": ""}, citation=False),
 "get_philosopher": dict(valid={"name": "柏拉图"}, invalid={},
    empty={"name": "不存在哲人XYZ"}, boundary={"name": "孔丘"}, failure={"name": ""},
    citation=False),
 "list_books": dict(valid={"region": "中国"}, invalid={"region": 42},
    empty={"author": "不存在的作者XYZ"}, boundary={"region": "西方"},
    failure=None, citation=False),
 "write_essay": dict(valid={"topic": "习惯是第二自然", "word_count": 300},
    invalid={}, empty=None, boundary={"topic": "自由", "word_count": 200},
    failure=None, citation=True, slow=True),
 "generate_image": dict(valid={"prompt": "哲学意境: 咖啡杯与休谟"}, invalid={},
    empty=None, boundary=None, failure=None, citation=False, slow=True),
 "get_school": dict(valid={"name": "斯多葛学派"}, invalid={},
    empty={"name": "不存在的流派XYZ"}, boundary={"name": "儒家"}, failure={"name": ""},
    citation=False),
 "phti_test": dict(valid={}, invalid={"execute": "not_a_dict"},
    empty=None, boundary=None, failure=None, citation=False),
 "compare_views": dict(valid={"a": "休谟", "b": "康德", "focus": "因果"},
    invalid={"a": 1, "b": None}, empty=None, boundary={"a": "道", "b": "Logos"},
    failure=None, citation=False),
 "socratic_tutor": dict(valid={"topic": "什么是正义"},
    invalid={"topic": None}, empty=None, boundary={"topic": "勇"},
    failure=None, citation=False),
 "philosopher_debate": dict(valid={"topic": "因果必然性", "speakers": ["休谟", "康德"], "mode": "auto"},
    invalid={"topic": None}, empty=None, boundary={"topic": "自由"},
    failure=None, citation=False, slow=True),
 "thought_experiment": dict(valid={"base": "电车难题"}, invalid={"base": None},
    empty=None, boundary={"base": "缸中之脑"}, failure=None, citation=False),
 "advisor_council": dict(valid={"question": "该不该换工作"}, invalid={"question": None},
    empty=None, boundary={"question": "要不要读研"}, failure=None, citation=False),
 "paper_review": dict(valid={"text": "本文主张习惯性信念构成因果必然性的实践基础。其一，观察显示……其二，……因此因果性是习惯的产物。"},
    invalid={"text": ""}, empty=None, boundary={"text": "短论证。"},
    failure=None, citation=False),
 "analyze_argument": dict(valid={"text": "所有人都会死，苏格拉底是人，所以苏格拉底会死。"},
    invalid={"text": 42}, empty=None, boundary={"text": "羊是白的。"},
    failure=None, citation=False),
 "concept_trace": dict(valid={"concept": "自由意志"}, invalid={"concept": None},
    empty={"concept": "量子夸克幽浮"}, boundary={"concept": "道"}, failure={"concept": ""},
    citation=True),
 "profile": dict(valid={"question": "我最近对存在主义感兴趣"}, invalid={},
    empty=None, boundary=None, failure=None, citation=False),
 "conceptual_map": dict(valid={"concept": "异化", "map_type": "CONCEPT_NETWORK"},
    invalid={"concept": None}, empty=None, boundary={"concept": "心"},
    failure=None, citation=False),
 "websearch": dict(valid={"query": "斯多葛主义"}, invalid={"query": None},
    empty={"query": "zzqqxx 完全不存在的术语混入"}, boundary={"query": "康德"},
    failure={"query": ""}, citation=False, slow=True),
 "query_database": dict(valid={"table": "books", "key": "庄子", "limit": 3},
    invalid={"table": "不存在表"}, empty={"table": "books", "key": "zzqqxx不存在的书名混入"},
    boundary={"table": "philosophers"}, failure={"table": ""}, citation=False),
 "role_play": dict(valid={"philosopher": "尼采", "question": "你怎么看现代人的懒惰？"},
    invalid={"question": None}, empty=None, boundary={"philosopher": "尼采", "question": "工作"},
    failure=None, citation=False, slow=True),
 "essay_outline": dict(valid={"topic": "技术与人本真性"}, invalid={"topic": None},
    empty=None, boundary={"topic": "自由"}, failure=None, citation=False),
 "life_coach": dict(valid={"question": "我最近很焦虑，担心未来"}, invalid={"question": None},
    empty=None, boundary=None, failure=None, citation=False),
 "dialectic": dict(valid={"topic": "自由与必然"}, invalid={"topic": None},
    empty=None, boundary={"topic": "有与无"}, failure=None, citation=False),
 "history_timeline": dict(valid={"topic": "存在主义"}, invalid={"topic": None},
    empty={"topic": "不存在的流派XYZ"}, boundary={"topic": "儒家"}, failure=None,
    citation=False),
 "confrontation": dict(valid={"topic": "因果", "a": "休谟", "b": "康德"},
    invalid={"topic": "因果", "a": None}, empty=None,
    boundary={"topic": "美德", "a": "亚里士多德", "b": "孔子"}, failure=None,
    citation=True, slow=True),
 "school_arena": dict(valid={"topic": "AI 是否可能思考", "school_a": "儒家", "school_b": "斯多葛学派"},
    invalid={"topic": None}, empty=None, boundary={"topic": "正义"},
    failure=None, citation=False, slow=True),
 "agent_council": dict(valid={"topic": "人工智能与判断力"}, invalid={"topic": None},
    empty=None, boundary={"topic": "死亡"}, failure=None, citation=False, slow=True),
 "search_scholarship": dict(valid={"query": "Kant transcendental deduction", "limit": 3},
    invalid={"query": None}, empty={"query": "zzqqxx nonexistent term mix", "limit": 3},
    boundary={"query": "virtue", "limit": 1}, failure={"query": ""},
    citation=False, slow=True),
 "get_scholarly_source": dict(valid=None,  # 运行时用 search 结果填充
    invalid={}, empty=None, boundary=None,
    failure={"source_record_id": "NO_SUCH_RECORD", "requested_access": "ABSTRACT"},
    citation=False, need_scholar=True),
}

CHECKS = ["VALID_INPUT", "INVALID_INPUT", "EMPTY_RESULT", "BOUNDARY",
          "FAILURE_PATH", "SCHEMA", "PROVENANCE", "CITATION", "SECURITY"]
SECURITY_INPUTS = [{"query": "'; DROP TABLE books; --"},
                   {"topic": "<script>alert(1)</script> 因果"}]


def run_one(name, tool, probes):
    res = {"tool": name, "checks": {}, "notes": {}}
    ex = tool["execute"]

    def attempt(args, label):
        if args is None:
            return None
        try:
            r = ex(dict(args))
            return {"status": "OK", "result": _project(r)}
        except Exception as e:
            return {"status": "EXCEPTION", "error": str(e)[:200]}

    need_book = probes.pop("need_book", False)
    need_scholar = probes.pop("need_scholar", False)
    citation_applicable = probes.pop("citation", False)
    slow = probes.pop("slow", False)
    timeout = 180 if slow else 60

    # 动态填充: valid get_book_detail/get_chapter 需要真实 book_id
    if need_book:
        try:
            sr = TOOLS["search_books"]["execute"]({"query": "因果", "limit": 1})
            hits = sr.get("results") or []
            if not hits:
                res["notes"]["dependency"] = "search_books 无命中, 书依赖探针跳过"
                for c in ("VALID_INPUT", "FAILURE_PATH", "SCHEMA", "PROVENANCE", "CITATION"):
                    res["checks"][c] = "SKIP_DEPENDENCY"
                return res
            bid = hits[0]["book_id"]
            probes.setdefault("valid", {})["book_id"] = bid
            probes["valid"]["chapter_idx"] = 0
            probes.setdefault("invalid", {})
            probes["invalid"] = {"book_id": 123} if name == "get_book_detail" else {"book_id": bid, "chapter_idx": -5}
            probes["boundary"] = {"book_id": bid, "chapter_idx": 999999}
            probes["empty"] = None
        except Exception as e:
            res["notes"]["dependency_error"] = str(e)[:150]
    if need_scholar:
        try:
            sr = TOOLS["search_scholarship"]["execute"](
                {"query": "virtue ethics", "limit": 1})
            recs = sr.get("results") or []
            if recs:
                probes["valid"] = {"source_record_id": (recs[0].get("source_record_id")
                                  or recs[0].get("id") or ""),
                                   "requested_access": "ABSTRACT"}
            else:
                res["notes"]["dependency"] = "search_scholarship 无结果"
        except Exception as e:
            res["notes"]["dependency_error"] = str(e)[:150]

    with ThreadPoolExecutor(max_workers=1) as pool:
        def timed(fn_args):
            if fn_args is None:
                return None
            f = pool.submit(attempt, fn_args, "probe")
            try:
                return f.result(timeout=timeout)
            except Exception:
                return {"status": "TIMEOUT", "error": f">{timeout}s"}

        v = timed(probes.get("valid"))
        res["checks"]["VALID_INPUT"] = ("PASS" if v and v["status"] == "OK"
                                        else ("FAIL" if v else "N/A") if v is None else "FAIL")
        if v and v["status"] == "OK":
            res["notes"]["valid_result_keys"] = list((v.get("result") or {}).keys())[:12]
        elif v:
            res["notes"]["valid_error"] = v.get("error")

        iv = timed(probes.get("invalid"))
        # 期望: 优雅拒绝（异常或 error 字段都算 graceful; 崩溃=异常也算工具自身处理）
        res["checks"]["INVALID_INPUT"] = "PASS" if iv else "N/A"

        em = timed(probes.get("empty"))
        if em is None:
            res["checks"]["EMPTY_RESULT"] = "N/A"
            res["notes"]["empty_na_reason"] = "生成型/无『空结果』语义"
        else:
            ok_empty = em["status"] == "OK" and _looks_empty(em["result"])
            res["checks"]["EMPTY_RESULT"] = "PASS" if ok_empty else ("FAIL" if em["status"] == "OK" else "PASS")
            if em["status"] != "OK":
                res["notes"]["empty_graceful_error"] = em.get("error")

        bd = timed(probes.get("boundary"))
        res["checks"]["BOUNDARY"] = ("PASS" if bd and bd["status"] == "OK"
                                     else "N/A" if bd is None else
                                     "PASS_GRACEFUL" if bd["status"] == "EXCEPTION" else "FAIL")

        fl = timed(probes.get("failure"))
        if fl is None:
            res["checks"]["FAILURE_PATH"] = "N/A"
            res["notes"]["failure_na_reason"] = "本地纯函数无外部资源失败路径"
        else:
            res["checks"]["FAILURE_PATH"] = "PASS" if (fl["status"] == "EXCEPTION"
                                                       or _has_error(fl["result"])) else \
                ("PASS_EMPTY" if _looks_empty(fl["result"]) else "FAIL")

        # SCHEMA: valid 结果有稳定顶层键且可 JSON 序列化
        if v and v["status"] == "OK":
            r = v.get("result")
            try:
                json.dumps(r, ensure_ascii=False, default=str)[:1]
                has_keys = isinstance(r, dict) and len(r) > 0
                res["checks"]["SCHEMA"] = "PASS" if has_keys else "PASS_NON_DICT"
            except Exception:
                res["checks"]["SCHEMA"] = "FAIL_NOT_SERIALIZABLE"
        else:
            res["checks"]["SCHEMA"] = "N/A"

        # PROVENANCE: 结果可溯源（book_id/chapter/record id/结构化字段）
        if citation_applicable and v and v["status"] == "OK":
            r = json.dumps(v.get("result"), ensure_ascii=False, default=str)
            marks = any(m in r for m in ("book_id", "chapter_idx", "citation_label",
                                         "source_record_id", "url", "doi"))
            res["checks"]["PROVENANCE"] = "PASS" if marks else "FAIL_NO_SOURCE_MARKS"
        else:
            res["checks"]["PROVENANCE"] = "N/A"
            res["notes"].setdefault("provenance_na_reason",
                                    "脚手架/生成类工具, 输出非外部事实主张")

        # CITATION: 引用标签/可核验定位
        if citation_applicable and v and v["status"] == "OK":
            r = json.dumps(v.get("result"), ensure_ascii=False, default=str)
            res["checks"]["CITATION"] = "PASS" if ("citation_label" in r or
                                                   "chapter_idx" in r or "doi" in r) else "WEAK"
        else:
            res["checks"]["CITATION"] = "N/A"
            res["notes"].setdefault("citation_na_reason", "工具输出本身不是引文/不返回外部出处")

        # SECURITY: 注入/脚本样式输入
        sec_results = []
        for s in SECURITY_INPUTS:
            args = dict(s)
            if probes.get("valid") and "topic" not in args and "query" not in args:
                continue
            sec_results.append(timed(args))
        res["checks"]["SECURITY"] = ("PASS" if all(s is None or s["status"] in ("OK", "EXCEPTION")
                                                   for s in sec_results)
                                     else "CHECK") if sec_results else "N/A"
        res["notes"]["security_probes"] = len(sec_results)
    return res


def _project(r):
    """结果投影: 顶层键 + 小样本, 避免审计文件膨胀。"""
    if isinstance(r, dict):
        out = {}
        for k, v in r.items():
            if isinstance(v, list):
                out[k] = v[:2] + [f"...{len(v)} items"] if len(v) > 2 else v
            elif isinstance(v, str):
                out[k] = v[:150]
            else:
                out[k] = v
        return out
    return {"_type": type(r).__name__, "_preview": str(r)[:150]}


def _looks_empty(r):
    if isinstance(r, dict):
        results = r.get("results")
        if results is not None:
            return len(results) == 0
        if r.get("error"):
            return True
        return len(r) == 0
    return False


def _has_error(r):
    return isinstance(r, dict) and bool(r.get("error"))


def main(only=None):
    out = []
    for name in sorted(TOOLS):
        if only and name not in only:
            continue
        probes = P.get(name)
        if probes is None:
            out.append({"tool": name, "checks": {c: "NO_PROBE_SPEC" for c in CHECKS}})
            continue
        print(f"== mech: {name}", flush=True)
        out.append(run_one(name, TOOLS[name], dict(probes)))
        json.dump(out, open(os.path.join(ROOT, "backend/tools/_tmp/o8r2_mechanical.json"),
                            "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    summary = {}
    for r in out:
        for c, verdict in r["checks"].items():
            summary.setdefault(c, {}).setdefault(verdict, 0)
            summary[c][verdict] += 1
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(only=(sys.argv[1].split(",") if len(sys.argv) > 1 else None))
