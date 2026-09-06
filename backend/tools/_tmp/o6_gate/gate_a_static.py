# -*- coding: utf-8 -*-
"""O6 Gate A — 静态取证（G1/§2 + §26 + §27）。EVIDENCE-ONLY: 只读生产源码 + git O0 tag, 零修改。"""
import io
import json
import os
import re
import subprocess
import sys
import tokenize

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
OUT = os.path.join(BASE, "backend", "tools", "_tmp", "o6_gate", "gate_a")
O0 = "a69149b7288766f43fcc4be1bc822da2f59027bd"

# 生产源码范围（请求路径; 不含 tests/tools/modules 基础设施）
TOP_FILES = ["engine_langgraph.py", "agent_runtime.py", "final_validator.py", "evidence_contract.py",
             "quote_bound.py", "tool_contracts.py", "agents.py", "guard.py", "mcp_client.py",
             "philo_retrieval.py", "admin.py", "auth.py", "auth_deps.py", "config.py", "db.py",
             "eval_agent.py", "evaluation_suite.py", "fix_bios.py", "drawio_convert.py"]
ROUTES = ["agent.py", "agent_core.py", "agent_llm.py", "agent_sse.py",
          "agent_tools_eval.py", "agent_tools_memory.py", "agent_tools_retrieval.py"]
O0_EXTRA_SEMANTIC = ["answer_composer.py", "interpretation_engine.py", "epistemic_guard.py", "reasoning_plan.py"]


def git_show(rev, path):
    r = subprocess.run(["git", "-C", BASE, "show", f"{rev}:{path}"],
                       capture_output=True)
    if r.returncode != 0:
        return None
    return r.stdout.decode("utf-8", errors="replace")


def git_ls(rev):
    r = subprocess.run(["git", "-C", BASE, "ls-tree", "-r", "--name-only", rev],
                       capture_output=True)
    return [l.strip() for l in r.stdout.decode("utf-8", errors="replace").splitlines() if l.strip()]


def strip_comments(src):
    """用 tokenize 将 # 注释原地置换为空白（行号保持不变, 便于 file:line 取证）。
    返回 (stripped_text, comment_count)。tokenize 失败时正则兜底（行号仍对齐）。"""
    try:
        lines = src.splitlines(keepends=True)
        toks = list(tokenize.generate_tokens(io.StringIO(src).readline))
        n_comments = 0
        for t in toks:
            if t.type == tokenize.COMMENT:
                n_comments += 1
                srow, scol = t.start
                erow, ecol = t.end
                if srow == erow:
                    line = lines[srow - 1]
                    lines[srow - 1] = line[:scol] + " " * (ecol - scol) + line[ecol:]
        return "".join(lines), n_comments
    except Exception:
        out = []
        n = 0
        for ln in src.splitlines(keepends=True):
            if re.match(r"\s*#", ln):
                n += 1
                out.append(re.sub(r"#.*", "", ln))
            else:
                out.append(ln)
        return "".join(out), n


def scan_text(text, patterns):
    """返回 {pattern: [line_no,...]}（patterns: {label: compiled_re}）"""
    hits = {}
    lines = text.splitlines()
    for label, rex in patterns.items():
        ls = []
        for i, ln in enumerate(lines, 1):
            if rex.search(ln):
                ls.append({"line": i, "text": ln.strip()[:160]})
        if ls:
            hits[label] = ls
    return hits


# ── G1/§2: 禁止持有生产控制权的符号（符号级 + 运行时文案级）──
FORBIDDEN = {
    "Planner": re.compile(r"reasoning_plan|build_plan\b|Planner\(|plan_complexity|verif_box", re.I),
    "ObligationSystem": re.compile(r"obligation_ledger|ObligationLedger|obligations_satisfied|derive_obligations|assess_obligation"),
    "SufficiencyController": re.compile(r"sufficiency_verdict|sufficiency_hint|sufficiency_converge|SUFFICIENCY"),
    "NoGainController": re.compile(r"no_gain_verdict|no_gain_force|force_no_gain|no_gain_streak|warn_no_gain|NO_GAIN_DIRECTIVE"),
    "SemanticAdmission": re.compile(r"admission|admit_retrieval|semantic_admission|_ws_why|admission_denied"),
    "InterpretationJudge": re.compile(r"interpretation_engine|scan_interpretation|InterpretationVerdict|interpretation_verdict"),
    "AnswerComposer": re.compile(r"answer_composer|AnswerComposer|compose_answer|composition_hedge"),
    "PremiseVerifier": re.compile(r"PremiseVerifier|premise_verifier|scan_premise|epistemic_guard"),
    "RuntimeFinalWriter": re.compile(r"emit_append|_final_answer_directive|RECOVERY_SYSTEM_DIRECTIVE|_build_recovery_dicts|scan_final_consistency"),
    "AutoRead": re.compile(r"_ensure_primary_read|auto_primary_read|auto_read|AUTO_READ"),
    "AutoWebsearch": re.compile(r"auto.?websearch|AUTO_WEBSEARCH|_auto_search"),
}

# §26: 功能等价物回归扫描（符号 + 特征文案; 命中须逐条人工归类）
REGRESSION_PATTERNS = {
    "semantic_admission": re.compile(r"admission|semantic_admission|准入", ),
    "sufficiency_force": re.compile(r"sufficiency|充分性"),
    "no_gain_force": re.compile(r"no_gain_verdict|no_gain_force|no_gain_streak|无增益.*(强制|提醒)"),
    "verification_intent_routing": re.compile(r"verification_intent|intent_rout|意图路由|verif_box"),
    "auto_read": re.compile(r"auto_read|auto_primary_read|代读|代执行.*读"),
    "auto_websearch": re.compile(r"auto.?websearch|自动上网|自动搜索"),
    "runtime_semantic_append": re.compile(r"emit_append|runtime_factual_append\(|尾补|正文追加"),
    "runtime_answer_rewrite": re.compile(r"sanitiz", re.I),
    "premise_verifier": re.compile(r"premise|前提核验|前提纠正"),
    "answer_composer": re.compile(r"answer_composer|AnswerComposer|答案组装"),
    "interpretation_judge": re.compile(r"interpretation_engine|interpretation_verdict|解读仲裁"),
    "ghostwriting_marks": re.compile(r"据通行理解|与库中原文近似，非逐字|原典核验：|更正：|补充：先纠正|确定性边界：|核验边界：|引用核验说明|说明：这一解读"),
    "runtime_cognitive_prose": re.compile(r"检索已收口|预算已达上限|准入未通过|系统收敛|最后核验机会"),
    "raw_reasoning_passthrough": re.compile(r"thought_stream|reasoning_content"),
}

# O0/HEAD 通用: runtime 文件集
def collect_head_sources():
    src = {}
    for f in TOP_FILES:
        p = os.path.join(BASE, "backend", f)
        if os.path.exists(p):
            src["backend/" + f] = open(p, encoding="utf-8").read()
    for f in ROUTES:
        p = os.path.join(BASE, "backend", "routes", f)
        if os.path.exists(p):
            src["backend/routes/" + f] = open(p, encoding="utf-8").read()
    return src


def collect_o0_sources(o0_files):
    src = {}
    cands = ["backend/" + f for f in TOP_FILES + O0_EXTRA_SEMANTIC] + \
            ["backend/routes/" + f for f in ROUTES]
    for p in cands:
        if p in o0_files:
            t = git_show(O0, p)
            if t is not None:
                src[p] = t
    return src


def count_loc(srcmap):
    return {p: len(t.splitlines()) for p, t in srcmap.items()}


def count_regexes(srcmap, files):
    n = 0
    sites = []
    for p in files:
        t = srcmap.get(p)
        if not t:
            continue
        for m in re.finditer(r"re\.compile\(", t):
            n += 1
        for i, ln in enumerate(t.splitlines(), 1):
            if "re.compile(" in ln or "re.match(" in ln or "re.search(" in ln:
                sites.append(f"{p}:{i}")
    return n, sites


def count_tests():
    """统计当前磁盘上 backend/tests 的文件与测试函数数（含未跟踪文件——与 pytest 实际收集一致）"""
    d = os.path.join(BASE, "backend", "tests")
    files = sorted(f for f in os.listdir(d) if f.startswith("test_") and f.endswith(".py"))
    n_funcs = 0
    per_file = {}
    import ast
    for f in files:
        tree = ast.parse(open(os.path.join(d, f), encoding="utf-8").read())
        c = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
                c += 1
        per_file[f] = c
        n_funcs += c
    extra = [f for f in sorted(os.listdir(d)) if f.endswith(".py") and not f.startswith("test_")
             and f != "__init__.py"]
    return {"test_files": len(files), "test_functions": n_funcs, "per_file": per_file,
            "non_test_named": extra}


def o0_tests():
    files = [p for p in git_ls(O0) if p.startswith("backend/tests/test_")]
    n = 0
    per = {}
    import ast
    for p in files:
        t = git_show(O0, p)
        if t is None:
            continue
        try:
            tree = ast.parse(t)
        except Exception:
            continue
        c = sum(1 for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"))
        per[p] = c
        n += c
    extra = [p for p in git_ls(O0) if p.startswith("backend/tests/") and p.endswith(".py")
             and not os.path.basename(p).startswith("test_") and not p.endswith("__init__.py")]
    return {"test_files": len(files), "test_functions": n, "per_file": per, "non_test_named": extra}


def tool_registry_current():
    """当前 TOOLS 注册表名集（routes/agent_core.TOOLS 由各 agent_tools_*.py register）"""
    sys.path.insert(0, os.path.join(BASE, "backend"))
    import routes.agent_core as AC
    return sorted(AC.TOOLS.keys())


def tool_registry_o0():
    t = git_show(O0, "backend/routes/agent.py")
    m = re.search(r"_TOOL_REGISTER_ORDER\s*=\s*\[(.*?)\]", t, re.S)
    if not m:
        return []
    return re.findall(r'"([a-z_]+)"', m.group(1))


def main():
    report = {}
    o0_files = git_ls(O0)
    head_src = collect_head_sources()
    o0_src = collect_o0_sources(o0_files)

    # ── 1. G1/§2: 剥注释后 forbidden 扫描（HEAD）──
    stripped_scan = {}
    for p, t in head_src.items():
        st, _nd = strip_comments(t)
        h = scan_text(st, FORBIDDEN)
        if h:
            stripped_scan[p] = h
    report["G1_forbidden_comment_stripped"] = stripped_scan
    report["G1_forbidden_raw"] = {p: scan_text(t, FORBIDDEN) for p, t in head_src.items()
                                  if scan_text(t, FORBIDDEN)}

    # ── 2. §26: 功能等价物扫描（HEAD, 剥注释）──
    reg_scan = {}
    for p, t in head_src.items():
        st, _nd = strip_comments(t)
        h = scan_text(st, REGRESSION_PATTERNS)
        if h:
            reg_scan[p] = h
    report["S26_regression_scan_comment_stripped"] = reg_scan

    # ── 3. §27: BEFORE/AFTER 指标 ──
    head_loc = count_loc(head_src)
    o0_loc = count_loc(o0_src)
    report["S27_loc_head"] = head_loc
    report["S27_loc_o0"] = o0_loc
    report["S27_loc_totals"] = {
        "head_total": sum(head_loc.values()),
        "o0_total": sum(o0_loc.values()),
        "o0_semantic_policy_LOC": sum(o0_loc.get("backend/" + f, 0) for f in O0_EXTRA_SEMANTIC),
        "head_semantic_policy_LOC": 0,
        "engine_langgraph": {"O0": o0_loc.get("backend/engine_langgraph.py"),
                             "O6": head_loc.get("backend/engine_langgraph.py")},
        "agent_runtime": {"O0": o0_loc.get("backend/agent_runtime.py"),
                          "O6": head_loc.get("backend/agent_runtime.py")},
    }

    # semantic regex 计数: O0 语义策略模块; HEAD final_validator/quote_bound/evidence_contract（机械核验）
    o0_sem_files = ["backend/" + f for f in O0_EXTRA_SEMANTIC]
    n0, _ = count_regexes(o0_src, o0_sem_files)
    n6, sites6 = count_regexes(head_src, ["backend/final_validator.py", "backend/quote_bound.py",
                                          "backend/evidence_contract.py", "backend/tool_contracts.py"])
    report["S27_semantic_regex"] = {"O0_semantic_modules": n0, "O6_mechanical_validator_modules": n6,
                                    "O6_sites": sites6[:40]}

    # runtime semantic mutators（O0 检测点）
    mut0 = {}
    for p in ["backend/engine_langgraph.py", "backend/routes/agent.py", "backend/routes/agent_sse.py",
              "backend/quote_bound.py", "backend/evidence_contract.py"]:
        t = o0_src.get(p, "")
        c = len(re.findall(r"LiveCitationSanitizer|QuoteBoundSanitizer|TermClaimGate|scan_final_consistency|emit_append|_final_answer_directive|_build_recovery_dicts", t))
        if c:
            mut0[p] = c
    # HEAD 检测点（应为 0——引用核验只检测不改写）
    mut6 = {}
    for p, t in head_src.items():
        c = len(re.findall(r"LiveCitationSanitizer|QuoteBoundSanitizer|TermClaimGate|scan_final_consistency|emit_append|_final_answer_directive|_build_recovery_dicts", strip_comments(t)[0]))
        if c:
            mut6[p] = c
    report["S27_runtime_semantic_mutator_sites"] = {"O0": mut0, "O6": mut6}

    # hidden cognitive tools（auto-read / auto-websearch 证据）
    hid0 = {}
    eng0 = o0_src.get("backend/engine_langgraph.py", "")
    hid0["auto_read__ensure_primary_read"] = len(re.findall(r"_ensure_primary_read", eng0))
    hid0["auto_websearch"] = len(re.findall(r"auto.?websearch", eng0))
    hid0["thought_stream_yields"] = len(re.findall(r'"type":\s*"thought_stream"', eng0))
    hid6 = {}
    eng6 = head_src.get("backend/engine_langgraph.py", "")
    hid6["auto_read__ensure_primary_read"] = len(re.findall(r"_ensure_primary_read", strip_comments(eng6)[0]))
    hid6["auto_websearch"] = len(re.findall(r"auto.?websearch", strip_comments(eng6)[0]))
    hid6["thought_stream_yields"] = len(re.findall(r'"type":\s*"thought_stream"', strip_comments(eng6)[0]))
    report["S27_hidden_cognitive_and_raw_reasoning"] = {"O0": hid0, "O6": hid6}

    # tests
    report["S27_tests"] = {"O0": o0_tests(), "O6_worktree": count_tests()}

    # tool registry（O0 注册序; O6 current 由 runtime_tool_surface.py 以 get_tools 实测 dump）
    try:
        cur = "see runtime_tool_surface.json (get_tools live dump)"
    except Exception as e:
        cur = f"ERROR: {e}"
    report["S27_tool_registry"] = {"O0_routes_agent": tool_registry_o0(), "O6_current": cur}

    # 8 项零指标的代码锚点（HEAD, engine_langgraph done payload 硬编码值）
    anchors = {}
    for label, pat in {
        "ENGINE_COGNITIVE_AUTO_TOOLS": r'"engine_cognitive_auto_tools":\s*(\d+)',
        "RUNTIME_SEMANTIC_MUTATORS": r'"semantic_mutators":\s*(\d+)',
        "RUNTIME_FACTUAL_APPENDS": r'"runtime_factual_appends":\s*(\d+)',
        "FINAL_RETRACT_SEMANTIC_USE": r'"final_retract_semantic_use":\s*(\d+)',
        "INVALID_FINAL_PUBLICLY_STREAMED": r'"invalid_final_publicly_streamed":\s*(\w+)',
        "MAIN_AGENT_FINAL_OWNERSHIP_RATE": r'"main_agent_final_ownership_rate":\s*([\d.]+)',
        "FINAL_TEXT_OWNER": r'"final_text_owner":\s*"(\w+)"',
        "THINKING_SOURCES": r'"thinking_sources":\s*"([\w_]+)"',
        "PROVENANCE_CAUSAL": r'"provenance":\s*"(o\d)"',
    }.items():
        m = re.search(pat, eng6)
        anchors[label] = m.group(1) if m else None
    report["zero_metric_code_anchors_engine"] = anchors

    with open(os.path.join(OUT, "static_analysis.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1, default=str)

    # 可读摘要
    lines = ["# O6 Gate A static analysis (comment-stripped scans)", ""]
    lines.append("## G1 forbidden-control scan (comment-stripped, production sources)")
    if not stripped_scan:
        lines.append("NO HITS (code-level) in any production file.")
    for p, h in stripped_scan.items():
        for label, ls in h.items():
            for l in ls:
                lines.append(f"HIT {label} @ {p}:{l['line']}: {l['text']}")
    lines.append("")
    lines.append("## G1 forbidden-control scan (raw incl. comments/docstrings)")
    for p, h in report["G1_forbidden_raw"].items():
        for label, ls in h.items():
            lines.append(f"RAW-HIT {label} @ {p}: {len(ls)} site(s) -> {[x['line'] for x in ls][:12]}")
    lines.append("")
    lines.append("## §26 regression scan (comment-stripped)")
    if not reg_scan:
        lines.append("NO HITS in any production file.")
    for p, h in reg_scan.items():
        for label, ls in h.items():
            for l in ls:
                lines.append(f"HIT {label} @ {p}:{l['line']}: {l['text']}")
    lines.append("")
    lines.append("## §27 metrics")
    lines.append(json.dumps({k: v for k, v in report.items() if k.startswith("S27") or k == "zero_metric_code_anchors_engine"},
                            ensure_ascii=False, indent=1, default=str))
    open(os.path.join(OUT, "static_analysis_summary.txt"), "w", encoding="utf-8").write("\n".join(lines))
    print("\n".join(lines[:60]))
    print("... full output in static_analysis_summary.txt")


if __name__ == "__main__":
    main()
