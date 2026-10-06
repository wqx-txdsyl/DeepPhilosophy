# -*- coding: utf-8 -*-
"""从 traces_run3/<ID>.json 生成单一汇总文档（回答时间/工具调用及返回/思考流/最终回答）。

输出: docs/evidence/phiagent_benchmark_v0_1/PHIAGENT_BENCHMARK_V0_1_LIVE_RUN3.md
策略与 run2（gen_bench_v01_doc_run2.py）一致: 最终回答全文; 思考流（公开笔记全文 +
原生思维链, 单轮超 6000 字截断并标注）; 工具返回 head 800 字/条（全文在 trace JSON）;
引用紧凑列表。头部如实记录相对 run2 的基线差异（SP 0.1.2 + bare 管线增量）。
"""
import json
import os
import statistics
import sys

BACKEND = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPO = os.path.dirname(BACKEND)
SUITE_DIR = os.path.join(REPO, "docs", "evidence", "phiagent_benchmark_v0_1")
TRACE_DIR = os.path.join(SUITE_DIR, "traces_run3")
OUT = os.path.join(SUITE_DIR, "PHIAGENT_BENCHMARK_V0_1_LIVE_RUN3.md")

REASON_LIMIT = 6000
TOOL_HEAD = 800

CATEGORIES = {
    "A": "日常问题的哲学化", "B": "现实制度与联网核查", "C": "概念精度与高难原典",
    "D": "引文定位与书库检索", "E": "上下文、版本与阅读能力", "F": "二级文献与多源研究",
    "G": "论证、反例与价值冲突", "H": "跨传统比较", "I": "任务边界与负对照",
    "J": "多轮追问与修正", "K": "工具故障与不可信材料", "L": "表达、出处与实际增益",
    "M": "知识、科学与存在", "N": "艺术、宗教与生命意义",
}


def _clip(text, limit, what):
    if not text:
        return ""
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n\n…（{what}共 {len(text)} 字，此处截断至 {limit}，全文见 traces_run3/）"


def case_md(trace):
    cid = trace["case_id"]
    L = []
    if trace.get("status") == "SKIPPED_NOT_READY":
        L.append(f"## {cid} · 未实测（skipped）")
        L.append(f"- 状态：{trace.get('status')} — {trace.get('reason')}"
                 f"（fixture={trace.get('fixture_id')}）")
        L.append(f"- 原题：{trace.get('prompt', '')}")
        return "\n".join(L)

    multi = len(trace.get("turns") or []) > 1
    head = (f"## {cid} · {CATEGORIES.get(cid[0], '')} · {trace.get('status')}"
            f" · 总耗时 {trace.get('total_wall_s')}s · {len(trace.get('turns') or [])} 轮")
    L.append(head)
    L.append(f"**题目**：{trace.get('prompt')}")
    if trace.get("follow_up_turns"):
        L.append("**追问**：" + " / ".join(f"（{i}）{t}" for i, t in
                                         enumerate(trace["follow_up_turns"], 1)))
    for tr in trace.get("turns") or []:
        if multi:
            L.append("")
            L.append(f"### 第 {tr['turn']} 轮 · {tr.get('question')}")
        L.append("")
        L.append(f"**回答时间**：{tr.get('wall_s')}s（首 token {tr.get('ttft_s')}s，"
                 f"引擎计时 {tr.get('engine_duration_s')}s，finish={tr.get('finish_reason')}）"
                 f" · 状态 {tr.get('status')} · 回答 {tr.get('answer_chars')} 字"
                 + (f" · token/内容一致：{'是' if tr.get('done_matches_tokens') else '否'}"
                    if tr.get("status") == "DONE" else ""))
        if tr.get("token_usage"):
            tu = tr["token_usage"]
            L.append(f"**token 用量**：输入 {tu.get('input_tokens')} / 输出 {tu.get('output_tokens')}"
                     f" / 合计 {tu.get('total_tokens')}")
        if tr.get("stream_error"):
            L.append(f"**流错误**：{tr['stream_error']}")

        # 思考流
        L.append("")
        L.append("#### 思考流")
        notes = tr.get("public_notes") or []
        reasoning = tr.get("provider_reasoning") or ""
        if not notes and not reasoning:
            L.append("（本轮无思考流事件）")
        for n in notes:
            tag = n.get("phase") or n.get("source") or ""
            body = _clip(n.get("content") or "", REASON_LIMIT, "笔记")
            L.append(f"- [{tag}] {body}")
        if reasoning:
            L.append("")
            L.append("**模型原生思维链（provider reasoning）**：")
            L.append("")
            L.append("> " + _clip(reasoning, REASON_LIMIT, "思维链").replace("\n", "\n> "))

        # 工具调用与返回
        L.append("")
        L.append("#### 工具调用与返回")
        calls = tr.get("tool_calls_full") or []
        timeline = tr.get("tool_timeline") or []
        if not calls and not timeline:
            L.append("（本轮无工具调用）")
        for i, c in enumerate(calls, 1):
            L.append("")
            args = json.dumps(c.get("args"), ensure_ascii=False)
            L.append(f"{i}. `{c.get('name')}` · status={c.get('status')}")
            if args and args != "null":
                L.append(f"   - 参数：`{args}`")
            if c.get("duration_seconds") is not None:
                L.append(f"   - 耗时：{c['duration_seconds']}s")
            res = c.get("result_full")
            if res is None:
                res = c.get("result_summary") or ""
            res = str(res)
            L.append(f"   - 返回（{len(res)} 字，head {TOOL_HEAD}）：")
            L.append("")
            L.append("     ```")
            for ln in _clip(res, TOOL_HEAD, "返回").splitlines() or [""]:
                L.append("     " + ln)
            L.append("     ```")
        declared = [t for t in timeline if t.get("phase") == "start"]
        cancelled = [e for e in (tr.get("events") or []) if e.get("ev") == "tool_cancel"]
        if len(declared) != len(calls):
            L.append("")
            L.append(f"（流内宣告 {len(declared)} 次 / 落盘结果 {len(calls)} 条"
                     + (f"，取消 {len(cancelled)} 次" if cancelled else "") + "）")

        # 最终回答
        L.append("")
        L.append("#### 最终回答")
        L.append("")
        ans = tr.get("answer") or "（无回答）"
        if tr.get("status") != "DONE" and tr.get("done_content"):
            ans = tr["done_content"]
        L.append(ans)

        # 引用
        cits = tr.get("citations") or []
        if cits:
            L.append("")
            L.append("#### 引用（done.citations）")
            for c in cits:
                loc = []
                for k in ("book", "chapter", "author", "source_type"):
                    if c.get(k):
                        loc.append(str(c[k]))
                pos = []
                if c.get("book_id"):
                    pos.append(f"book_id={c['book_id']}")
                if c.get("chapter_idx") is not None:
                    pos.append(f"chapter_idx={c['chapter_idx']}")
                exc = (c.get("excerpt") or "").replace("\n", " ")[:80]
                L.append(f"- 《{'·'.join(loc)}》 {', '.join(pos)} — “{exc}…”"
                         if exc else f"- 《{'·'.join(loc)}》 {', '.join(pos)}")
    return "\n".join(L)


def main():
    cases = [json.loads(l) for l in open(os.path.join(SUITE_DIR, "prompts.jsonl"),
                                         encoding="utf-8") if l.strip()]
    order = [c["id"] for c in cases]
    traces = {}
    for fn in os.listdir(TRACE_DIR):
        if fn.endswith(".json") and not fn.startswith("_"):
            traces[fn[:-5]] = json.load(open(os.path.join(TRACE_DIR, fn), encoding="utf-8"))
    missing = [i for i in order if i not in traces]

    meta = {}
    mp = os.path.join(TRACE_DIR, "_RUN_META.json")
    if os.path.exists(mp):
        meta = json.load(open(mp, encoding="utf-8"))
    pf = {}
    pp = os.path.join(TRACE_DIR, "_PREFLIGHT.json")
    if os.path.exists(pp):
        pf = json.load(open(pp, encoding="utf-8"))

    ran = [traces[i] for i in order if i in traces]
    ok = [t for t in ran if t.get("status") == "COMPLETED"]
    skipped = [t for t in ran if t.get("status") == "SKIPPED_NOT_READY"]
    turns = [t for tr in ran for t in (tr.get("turns") or [])]
    total_wall = sum(t.get("total_wall_s") or 0 for t in ran)
    total_ans = sum(t.get("answer_chars") or 0 for t in turns)
    total_tools = sum(len(t.get("tool_calls_full") or []) for t in turns)
    tok_in = sum((t.get("token_usage") or {}).get("input_tokens") or 0 for t in turns)
    tok_out = sum((t.get("token_usage") or {}).get("output_tokens") or 0 for t in turns)
    ttfts = [t.get("ttft_s") for t in turns if isinstance(t.get("ttft_s"), (int, float))]
    med_ttft = round(statistics.median(ttfts), 1) if ttfts else None
    tool_status = {}
    for t in turns:
        for c in (t.get("tool_calls_full") or []):
            s = c.get("status") or "unknown"
            tool_status[s] = tool_status.get(s, 0) + 1
    tool_status_str = " / ".join(f"{k} {v}" for k, v in sorted(tool_status.items()))

    # 类别统计
    by_cat = {}
    for t in ran:
        c = t["case_id"][0]
        d = by_cat.setdefault(c, {"n": 0, "ok": 0, "wall": 0.0, "tools": 0, "ans": 0})
        d["n"] += 1
        d["ok"] += 1 if t.get("status") == "COMPLETED" else 0
        d["wall"] += t.get("total_wall_s") or 0
        d["tools"] += sum(len(x.get("tool_calls_full") or []) for x in (t.get("turns") or []))
        d["ans"] += sum(x.get("answer_chars") or 0 for x in (t.get("turns") or []))

    L = []
    L.append("# PhiAgent Benchmark v0.1 实测记录（LIVE RUN 3）")
    L.append("")
    L.append(f"- 执行日期：{meta.get('started', '（见 traces_run3/_RUN_META.json）')}"
             f" ~ {meta.get('finished', '未完成/进行中')}")
    L.append(f"- 代码版本：git `{meta.get('git_head', '?')}`"
             f"（工作区 {meta.get('git_dirty_files', '?')} 个未提交条目，未逐一归类）"
             f" · 活动提示词：agent_release active_prompt_version="
             f"`{meta.get('active_prompt_version', '?')}`（879 字符；run2 记录口径为 642 字符≈0.1.1）"
             f" · 引擎：`{meta.get('engine', 'engine_langgraph.stream_agent（进程内直调, 等价 /api/agent/stream_lg）')}`"
             " · agent=general · language=zh")
    L.append("- 相对 run2 基线（ea2c286b）的代码增量（如实记录，非引擎不变重跑）："
             "bare 管线新增装载 account `memory_tools()` 并支持个性化上下文注入（本采集以 account_id=null 运行，"
             "不触发账户记忆）；SP 改由 `agent_release.prompt_spec` 按版本提供（0.1.2）；"
             "`tool_status` 判定收紧（返回体 success=false/ok=false 记 error）；模型流开启 stream_usage；"
             "`engine_langgraph.py`/`scholarly_sources.py`/`routes/agent_tools_scholarly.py`/`evidence_contract.py`/`routes/agent_sse.py` 有增量改动。"
             "因此 run3 与 run1/run2 的差异（SP、引擎、日期、外部来源）同时变化，只可做现象对比，不能归因单一因素。")
    L.append(f"- 模型（preflight）：{pf.get('PRODUCTION_MODEL', '?')}"
             f" · 主渠道 {'OK' if pf.get('PRIMARY_CHANNEL_OK') else 'FAIL'}"
             f" · 联网渠道 {'OK' if pf.get('WEB_CHANNEL_OK') else 'FAIL'}"
             f" · 学术渠道 {'OK' if pf.get('SCHOLARLY_CHANNEL_OK') else 'FAIL（本地缓存兜底）'}")
    L.append("- 学术出网口径与 run2 相同：`SCHOLARLY_NETWORK_MODE=TRUSTED_PROXY`"
             "（本机 TUN 代理 fake-IP 段 198.18.0.0/15，代码内置显式信任模式）；"
             "`backend/data/scholarly_cache.json` 根值为 dict（run2 自 `.t1pre-bak` 恢复的同一份，"
             "后续评测有增量；run1 根值为 null 致 82 次学术调用全灭，null 留档 `.null-bak-20261002`）。")
    L.append(f"- 执行口径：done 即停（跳过 suggestions 后处理）；单轮超时 "
             f"{meta.get('turn_timeout_s', 600)}s；并发 2；每请求独立记忆（无 conversation_id）；"
             "J 组追问通过显式 history 传递")
    L.append("- 运行时：`DEEP_AGENT_RUNTIME` 默认 bare → 实际管线 `deep_bare_agent.stream_bare_agent`"
             "（与生产 /api/agent/stream_lg 同一委托路径）；该管线 `validation.enabled=false，"
             "suggestions_status=unavailable`；工具返回为工具事件的完整 JSON 序列化")
    L.append(f"- 覆盖：{len(ran)}/70 题（K 组 5 题 manual_prompt_ready=false 未实测，见文末）"
             f"；完成 {len(ok)} 题，含追问共 {len(turns)} 轮对话；"
             "I02 于管线冒烟阶段先行执行（同一代码/同一环境/同一口径），其余题目批量执行")
    anomalies = [t for t in ran if t.get("status") == "COMPLETED_NO_ANSWER"
                 or (t.get("status") or "").startswith("PARTIAL_")
                 or t.get("status") in ("ABORTED_BALANCE",)]
    if anomalies:
        parts = []
        for t in anomalies:
            for tr in (t.get("turns") or []):
                if tr.get("status") == "DONE" and not (tr.get("answer") or "").strip():
                    parts.append(f"{t['case_id']} 轮次 DONE 但零 token 正文输出"
                                 f"（finish={tr.get('finish_reason')}，工具调用 "
                                 f"{len(tr.get('tool_calls_full') or [])} 次，思维链 "
                                 f"{len(tr.get('provider_reasoning') or '')} 字）")
                elif tr.get("status") != "DONE":
                    parts.append(f"{t['case_id']} 末轮 {tr.get('status')}: {tr.get('stream_error')}")
        L.append(f"- **异常**：{'；'.join(parts)} → 状态如实落盘，未重跑"
                 if parts else f"- **异常**：{', '.join(t['case_id'] for t in anomalies)}")
    L.append(f"- 合计：逐题耗时合计 {round(total_wall / 60, 1)} 分钟 · 工具调用 {total_tools} 次"
             f"（{tool_status_str}） · 回答总字数 {total_ans}"
             + (f" · 首 token 中位数 {med_ttft}s（采集口径：token/answer_preview 首到，"
                "非思考流首包）" if med_ttft is not None else "")
             + (f" · token 输入 {tok_in} / 输出 {tok_out}（仅计入引擎上报轮次）" if (tok_in or tok_out) else ""))
    if missing:
        L.append(f"- **缺轨迹**（未执行/中止）：{', '.join(missing)}")
    L.append("")
    L.append("## 分类统计")
    L.append("")
    L.append("| 组 | 主题 | 题数 | 完成 | 总耗时(s) | 工具次数 | 回答字数 |")
    L.append("|---|---|---|---|---|---|---|")
    for c in sorted(by_cat):
        d = by_cat[c]
        L.append(f"| {c} | {CATEGORIES.get(c, '')} | {d['n']} | {d['ok']} | "
                 f"{round(d['wall'])} | {d['tools']} | {d['ans']} |")
    L.append("")
    L.append("> 完整原始轨迹（含全量工具返回、事件时间线）：`traces_run3/<ID>.json`。"
             "本文档中思考流单轮超 6000 字、工具返回超 800 字作截断。")
    L.append("")
    L.append("---")
    L.append("")
    for i in order:
        if i in traces:
            L.append(case_md(traces[i]))
            L.append("")
            L.append("---")
            L.append("")
    if missing:
        L.append("## 未执行题目")
        for i in missing:
            L.append(f"- {i}：轨迹缺失（执行中止或未跑到）")
        L.append("")
    doc = "\n".join(L)
    open(OUT, "w", encoding="utf-8").write(doc)
    print(f"wrote {OUT}: {len(doc)} chars, cases={len(ran)}, ok={len(ok)}, "
          f"skipped={len(skipped)}, turns={len(turns)}, missing={missing}")


if __name__ == "__main__":
    sys.exit(main())
