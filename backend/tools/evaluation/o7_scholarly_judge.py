# -*- coding: utf-8 -*-
"""O7-A Scholarly Judge Harness（EVALUATION-ONLY, 禁止任何生产模块导入）。

O7-A 任务书 §8-§12/§29: 独立 LLM judge = 测量仪器; 最终裁决权在 Reviewer (GPT-5.6 Sol)。
TESTED_MODEL (deepseek-chat) != JUDGE_MODEL (glm-4-plus); temperature 固定。

本模块:
- 不 import engine_langgraph / final_validator / quote_bound / routes / agents 等任何生产代码;
- 不写入 runtime 事件、不注册工具、不改 prompt;
- 只提供: judge 输入/输出合同、schema 校验、N/A 除外聚合、致命 flag 独立结构、
  Claim Ledger（数据类）、校准与稳定性计算、reviewer 抽样清单。
"""
from __future__ import annotations

import json
import os
import random
import re
import urllib.request
import urllib.error
from dataclasses import dataclass, field, asdict

# ── 常量宪法（§22-§26/§25 规范记录; 只定义, 不实施）──────────────────
JUDGE_MODEL = "glm-4-plus"
JUDGE_BASE_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
JUDGE_TEMPERATURE = 0.0          # 低且固定（§8）; 校准稳定性要求 → 0
TESTED_MODEL = "deepseek-chat"   # O6 线被测模型（必须 != JUDGE_MODEL）

DIMENSIONS = ["textual_grounding", "argument_reconstruction", "interpretive_plurality",
              "historical_discipline", "literature_orientation"]
APPLICABILITY = ("REQUIRED", "OPTIONAL", "NOT_APPLICABLE")
FATAL_FLAGS = ["FABRICATED_BIBLIOGRAPHY", "FABRICATED_SCHOLAR_ATTRIBUTION",
               "PRIMARY_TEXT_MISREPRESENTATION", "MAJOR_ANACHRONISM",
               "FALSE_EXACT_QUOTE", "LITERATURE_ACCESS_OVERCLAIM"]
ACCESS_LEVELS = ["METADATA_ONLY", "ABSTRACT_AVAILABLE", "FULL_TEXT_AVAILABLE", "FULL_TEXT_READ"]
CLAIM_TYPES = ["PRIMARY_TEXT_ASSERTION", "TEXTUAL_INFERENCE", "ARGUMENT_RECONSTRUCTION",
               "SCHOLARLY_CONSENSUS", "CONTESTED_INTERPRETATION", "HISTORICAL_CONTEXT",
               "TERMINOLOGICAL_CLAIM", "BIBLIOGRAPHIC_CLAIM", "AGENT_SYNTHESIS"]
SUPPORT_LEVELS = ("SUPPORTED", "PARTIAL", "UNSUPPORTED", "NOT_APPLICABLE")
LOCATOR_KINDS = ["CANONICAL", "EDITION_SPECIFIC", "STRUCTURAL"]
LOCATOR_SCHEMES = ["STEPHANUS", "BEKKER", "KANT_AB", "AKADEMIE", "APHORISM",
                   "PROPOSITION", "SECTION"]
CITATION_PRECISION_LADDER = ["CANONICAL_LOCATOR", "EDITION_SPECIFIC_PAGE",
                             "SECTION_OR_APHORISM_OR_PROPOSITION", "CHAPTER_OR_PART", "WORK"]
METADATA_SOURCE_TIERS = [
    ("TIER1", "当前实际版本自身: 版权页/扉页/译者说明/出版说明/目录/内嵌 canonical locator"),
    ("TIER2", "国家图书馆/CALIS/出版社官方目录/学术图书馆 catalogue"),
    ("TIER3", "WorldCat/Crossref/等价权威书目记录"),
    ("TIER4", "豆瓣等一般图书站（仅 discovery, 不作权威来源）"),
]

# §25: Q2 交付可靠性基线冻结（O7-E 第二轴 baseline, 不是 O7-A gate 指标）
Q2_DELIVERY_BASELINE = {
    "SAME_SET_SINGLE": "22/32 = 68.75%",
    "SAME_SET_MULTI": "19/24 = 79.2%",
    "REPAIR_SUCCESS_SINGLE": "15/25 = 60%",
    "REPAIR_EXHAUSTION_SINGLE": "10/25 = 40%",
    "FRESH_PUBLICATION": "13/16 = 81.25%",
    "VALIDATOR_FN": 0,
    "VALIDATOR_FP": 0,
    "INVALID_FINAL_PUBLIC": 0,
}

EVALUATION_ONLY = True
RUNTIME_IMPORTS = 0
PRODUCTION_AUTHORITY = 0


# ── 数据结构 ──────────────────────────────────────────────────────
@dataclass
class LedgerEntry:
    claim_id: str
    claim_span: str
    claim_type: str
    evidence_refs: list = field(default_factory=list)
    source_level: str = ""
    scholar_attribution: list = field(default_factory=list)
    interpretation_status: str = ""
    access_level: str = ""          # ACCESS_LEVELS 之一或 ""
    support: str = "NOT_APPLICABLE"  # SUPPORT_LEVELS 之一
    notes: str = ""


def validate_ledger_entry(e: dict) -> list:
    errs = []
    for k in ("claim_id", "claim_span", "claim_type"):
        if not str(e.get(k) or "").strip():
            errs.append(f"ledger missing {k}")
    if e.get("claim_type") not in CLAIM_TYPES:
        errs.append(f"unknown claim_type {e.get('claim_type')!r}")
    if e.get("support") not in SUPPORT_LEVELS:
        errs.append(f"unknown support {e.get('support')!r}")
    al = e.get("access_level") or ""
    if al and al not in ACCESS_LEVELS:
        errs.append(f"unknown access_level {al!r}")
    return errs


def build_judge_input(user_question: str, task_category: str, answer: str,
                      agent_identity: str, evidence_digest: str,
                      primary_text_evidence=None, bibliographic_records=None,
                      secondary_source_records=None, access_levels=None,
                      claim_ledger=None) -> dict:
    """§9 Judge Input Contract——judge 不得只读最终答案。"""
    return {
        "USER_QUESTION": user_question,
        "TASK_CATEGORY": task_category,
        "ANSWER": answer,
        "AGENT_IDENTITY": agent_identity,
        "RETRIEVED_EVIDENCE_DIGEST": evidence_digest,
        "PRIMARY_TEXT_EVIDENCE": primary_text_evidence or [],
        "BIBLIOGRAPHIC_RECORDS": bibliographic_records or [],
        "SECONDARY_SOURCE_RECORDS": secondary_source_records or [],
        "ACCESS_LEVELS": access_levels or [],
        "CLAIM_LEDGER": claim_ledger or [],
    }


JUDGE_SYSTEM_PROMPT = """你是哲学学术质量评审器（measurement instrument）。按以下宪法评审:

1. 五维各 0-4 分: textual_grounding / argument_reconstruction / interpretive_plurality /
   historical_discipline / literature_orientation。每维先判 applicability
   (REQUIRED/OPTIONAL/NOT_APPLICABLE)。NOT_APPLICABLE 的维 score=null, 绝不计 0。
   REQUIRED 维必须给 0-4 整数分; OPTIONAL 维在回答实质涉及该维时必须打分,
   仅当回答完全不涉及该维时才允许 null; 不确定是否涉及时倾向打分而非 null。
   整份评审至少要有三维给出整数分。
2. interpretive_plurality 与 historical_discipline、literature_orientation 允许 NOT_APPLICABLE;
   禁止因为回答"没有列两派/没有学者名"而在不适用时扣分——争议模板不是万能格式。
3. 反风格偏置: 更长、引用更多、外语更多、学者名更多、语气更像论文, 本身不得加分。
   只奖励 correctness/grounding/argument/discipline/真实文献导向。
4. 六类致命错误与分数完全分离（true/false + offending_span + reason + evidence_ref + confidence）:
   评审每个 fixture 时, 先逐句核对回答中的事实性主张与输入证据/记录, 再给分; flag 判定独立于分数。
   逐 flag 操作性判定（宁确勿漏——对显式植入的错误必须 flag）:
   【强制核对程序】给分之前必须先做 6 项 flag 核对: 对每一项, 先从输入的
   BIBLIOGRAPHIC_RECORDS/SECONDARY_SOURCE_RECORDS/RETRIEVED_EVIDENCE 中摘出相关记录字段,
   再对照回答中的引文/书目字段/访问声明, 然后给出 value——任何书目字段
   （DOI/页码/译者/出版社/年份/期刊/卷号）都必须与记录逐一比对。
   - FABRICATED_BIBLIOGRAPHY: 回答出现任何书目字段（译者/出版社/出版年/页码/DOI/期刊/卷号）,
     而 BIBLIOGRAPHIC_RECORDS/SECONDARY_SOURCE_RECORDS/证据摘要未提供该字段 → true
     （即使现实世界碰巧为真——证据未支持该精度即越界）。
   - FABRICATED_SCHOLAR_ATTRIBUTION: 把具体观点/论证/著作/优先权归属给某学者,
     而证据不支持该归属（含张冠李戴、时代错置的归属）→ true。
   - PRIMARY_TEXT_MISREPRESENTATION: 把原典没有明确说的内容表述成"作者原文/作者明确说/"
     出自某篇"（含篇名误置、把转述标成原文）→ true。
   - MAJOR_ANACHRONISM: 用作者晚期/后世概念体系描述其早期思想, 且实质改变解读 → true。
   - FALSE_EXACT_QUOTE: 回答声称逐字原文/直接引语（引号+出处）, 而该措辞未在所给证据文本中
     逐字出现（近似/改写/仅凭记忆均算未支持）→ true。
   - LITERATURE_ACCESS_OVERCLAIM: 记录 access_level 为 METADATA_ONLY 或 ABSTRACT_AVAILABLE 时,
     回答描述了该文献的内部结构/章节/论证步骤 → true; 只复述摘要明示内容 → false;
     FULL_TEXT_READ 的记录按其内容判。
   - 【访问级别上限·一般规则】Evidence access level places an upper bound on what can be claimed
     about a source: METADATA_ONLY 只支持所给记录中实际存在的书目/存在性事实——不支持任何关于
     内部章节/论证步骤/文本措辞/结论的主张, 除非这些事实本身明确出现在所给记录中;
     ABSTRACT_AVAILABLE 只支持所给摘要+元数据能支撑的主张;
     FULL_TEXT_AVAILABLE 只代表文本可获取, 不等于已读或已作为证据提供;
     FULL_TEXT_READ 才允许基于所给全文证据的主张。
     "根据记录""该来源显示"之类的修辞性来源声明不提高实际访问级别。
5. 你的输入包含问题/任务类别/回答/身份/检索证据摘要/原文证据/书目记录/访问级别/主张清单——
   必须依据这些评审, 不得只凭答案文风。
6. 严格输出 JSON（无多余文本）:
{"dimensions":{"<dim>":{"applicability":"...","score":0,"rationale":"...","supporting_spans":[],
"missing_requirements":[]}, ... 五维全部},
"fatal_flags":{"<FLAG>":{"value":false,"offending_spans":[],"reason":"","evidence_refs":[],
"confidence":0.9}, ... 六个全部},
"claim_ledger":[{"claim_id":"","claim_span":"","claim_type":"","evidence_refs":[],
"source_level":"","scholar_attribution":[],"interpretation_status":"","access_level":"",
"support":"SUPPORTED|PARTIAL|UNSUPPORTED|NOT_APPLICABLE","notes":""}],
"overall_scholarly_assessment":"","judge_confidence":0.0}
7. 每一分必须有具体 rationale; 禁止 "score=3.7, reason=overall strong" 式输出。
8. 你无权给出任何阶段 PASS/FAIL 结论——只能输出测量。"""


def render_judge_prompt(inp: dict) -> str:
    parts = []
    for k, v in inp.items():
        parts.append(f"## {k}\n{json.dumps(v, ensure_ascii=False, indent=1) if not isinstance(v, str) else v}")
    return "\n\n".join(parts)


def _extract_json(text: str):
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find('{')
    if start >= 0:
        depth = in_str = esc = 0
        for i in range(start, len(text)):
            ch = text[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == '\\':
                    esc = True
                elif ch == '"':
                    in_str = 0
            elif ch == '"':
                in_str = 1
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return json.loads(text[start:i + 1])
    raise ValueError("未找到可解析的 JSON 对象")


def validate_verdict(v: dict) -> list:
    """§10 输出合同校验; 同时强制 §12: judge 无权输出阶段 PASS。"""
    errs = []
    dims = v.get("dimensions") or {}
    for d in DIMENSIONS:
        dd = dims.get(d)
        if not isinstance(dd, dict):
            errs.append(f"missing dimension {d}")
            continue
        if dd.get("applicability") not in APPLICABILITY:
            errs.append(f"{d}: bad applicability {dd.get('applicability')!r}")
        sc = dd.get("score")
        if dd.get("applicability") == "NOT_APPLICABLE":
            if sc is not None:
                errs.append(f"{d}: N/A 必须 score=null")
        elif sc is None:
            if dd.get("applicability") == "REQUIRED":
                errs.append(f"{d}: REQUIRED 维缺 score")
        elif not isinstance(sc, int) or not 0 <= sc <= 4:
            errs.append(f"{d}: score 必须 0-4 整数, got {sc!r}")
        if not str(dd.get("rationale") or "").strip():
            errs.append(f"{d}: 缺 rationale")
    flags = v.get("fatal_flags") or {}
    if not any(isinstance((dims.get(d) or {}).get("score"), int) for d in DIMENSIONS):
        errs.append("至少一维需要 0-4 整数分（全 null 视为无效测量）")
    for f in FATAL_FLAGS:
        ff = flags.get(f)
        if not isinstance(ff, dict) or not isinstance(ff.get("value"), bool):
            errs.append(f"fatal flag {f} 缺失或无 bool value")
    for banned in ("phase_verdict", "verdict", "O7 PASS", "gate_result"):
        if banned in json.dumps(v).lower():
            errs.append(f"judge 输出含越权字段 {banned!r}（judge 无权签 PASS）")
    for e in (v.get("claim_ledger") or []):
        # judge 输出的 ledger 枚举为建议词表（§7 "建议 claim types"）——只强制身份字段;
        # 规范枚举由 validate_ledger_entry 在 fixture/authoring 层强制。
        if not str(e.get("claim_id") or "").strip() or not str(e.get("claim_span") or "").strip():
            errs.append("ledger entry 缺 claim_id/claim_span")
    return errs


def run_judge(inp: dict, transport=None, attempts: int = 3, model: str = None,
              temperature: float = None) -> dict:
    """调用独立 judge（或注入 transport 以便离线测试）; 解析/校验失败带反馈重试; 返回已校验 verdict。
    model/temperature 仅作为 provider invocation adapter（JR1 bakeoff）, 语义 prompt 不变。"""
    prompt = render_judge_prompt(inp)
    feedback = ""
    last_err = None
    for _ in range(attempts):
        if transport is None:
            payload = {
                "model": model or JUDGE_MODEL, "temperature": JUDGE_TEMPERATURE
                if temperature is None else temperature,
                "response_format": {"type": "json_object"},
                "messages": [{"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                             {"role": "user", "content": prompt + feedback}],
            }
            body = json.dumps(payload).encode()
            key = None
            for line in open(os.path.join(os.path.dirname(os.path.dirname(
                    os.path.dirname(os.path.abspath(__file__)))), "..", ".env"),
                    encoding="utf-8", errors="replace"):
                if line.strip().startswith("ZHIPU_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
            req = urllib.request.Request(JUDGE_BASE_URL, data=body, headers={
                "Content-Type": "application/json", "Authorization": "Bearer " + (key or "")})
            try:
                with urllib.request.urlopen(req, timeout=300) as r:
                    data = json.loads(r.read())
            except urllib.error.HTTPError as e:
                if e.code == 400:   # 端点不支持 response_format → 去掉重试一次
                    payload.pop("response_format")
                    body = json.dumps(payload).encode()
                    req = urllib.request.Request(JUDGE_BASE_URL, data=body, headers={
                        "Content-Type": "application/json", "Authorization": "Bearer " + (key or "")})
                    with urllib.request.urlopen(req, timeout=300) as r:
                        data = json.loads(r.read())
                else:
                    raise
            raw = data["choices"][0]["message"]["content"] or ""
            try:
                verdict = _extract_json(raw)
            except json.JSONDecodeError as e:
                last_err = e
                feedback = ("\n\n你上一次输出无法解析为 JSON（" + str(e) +
                            "）。请只输出一个严格合法的 JSON 对象: 字符串内不得使用未转义的英文双引号"
                            "（引用原文请用中文引号“”）；不要输出 JSON 以外的任何文字。")
                continue
        else:
            verdict = _extract_json(transport(prompt + feedback))
        errs = validate_verdict(verdict)
        if not errs:
            return verdict
        last_err = ValueError("judge verdict 校验失败: " + "; ".join(errs[:6]))
        feedback = ("\n\n你上一次输出不合规: " + str(last_err) +
                    "。请修正后重新只输出严格合法 JSON。")
    raise last_err


# ── 聚合 / 校准 / 抽样 ────────────────────────────────────────────
def dimension_scores(verdict: dict):
    """返回 [(dim, score)] —— 仅含 NOT_APPLICABLE 以外的维（§5: N/A 不入均值）。"""
    out = []
    for d, dd in (verdict.get("dimensions") or {}).items():
        if dd.get("applicability") == "NOT_APPLICABLE":
            continue
        if isinstance(dd.get("score"), int):
            out.append((d, dd["score"]))
    return out


def scholarly_mean(verdict: dict):
    sc = [s for _, s in dimension_scores(verdict)]
    return round(sum(sc) / len(sc), 3) if sc else None


def raised_fatal_flags(verdict: dict):
    return [f for f, ff in (verdict.get("fatal_flags") or {}).items() if ff.get("value")]


def calibration_gate(results: dict, expected_flags: dict, negative_pool=None):
    """§16(任务书 RP1 §5/§6): results={fixture_id: verdict}, expected_flags={fixture_id: [flags]}。
    分母 = 显式植入的 (fixture, flag) 断言数; negative_pool = 设计上无致命错误的 fixture 集合,
    其上任何 raised flag 都计为 FALSE_FATAL_ASSERTION。"""
    def mean(group):
        vals = [scholarly_mean(results[f]) for f in group if results.get(f)]
        vals = [v for v in vals if v is not None]
        return round(sum(vals) / len(vals), 3) if vals else None
    good, mid, bad = mean(results.get("__good__", [])), mean(results.get("__mid__", [])), mean(results.get("__bad__", []))
    detected, missed = 0, []
    per_flag = {f: [0, 0] for f in FATAL_FLAGS}   # [detected, expected]
    for fid, flags in (expected_flags or {}).items():
        got = set(raised_fatal_flags(results.get(fid) or {}))
        for f in flags:
            per_flag[f][1] += 1
            if f in got:
                per_flag[f][0] += 1
                detected += 1
            else:
                missed.append((fid, f))
    total = sum(len(v) for v in (expected_flags or {}).values())
    neg = set(negative_pool if negative_pool is not None else
              [fid for fid in results if not str(fid).startswith("__")
               and not (expected_flags or {}).get(fid)])
    false_fatal = sorted({(fid, f) for fid in neg if isinstance(results.get(fid), dict)
                          for f in raised_fatal_flags(results[fid])})
    def _recall(fr):
        return round(fr[0] / fr[1], 3) if fr[1] else None
    return {"good_mean": good, "mid_mean": mid, "bad_mean": bad,
            "ordering_ok": bool(good is not None and bad is not None and good > bad),
            "expected_fatal_total": total, "expected_fatal_detected": detected,
            "expected_fatal_recall": round(detected / total, 3) if total else None,
            "per_flag_recall": {f: _recall(fr) for f, fr in per_flag.items()},
            "missed_fatal": missed,
            "no_fatal_expected_assertions": len(neg),
            "false_fatal_assertions": false_fatal}


def applicability_metrics(run_a: dict, run_b: dict):
    """RP1 §7/§11 口径: 逐维一致率(主) + REQUIRED↔N/A 临界矛盾(硬) + 整向量(仅诊断)。"""
    per_dim_tot = per_dim_agree = 0
    critical = 0
    whole_agree = whole_tot = 0
    for fid in run_a:
        va, vb = run_a[fid], run_b.get(fid)
        if not isinstance(vb, dict):
            continue
        whole_tot += 1
        case_agree = True
        for d in DIMENSIONS:
            la = (va.get("dimensions") or {}).get(d, {}).get("applicability")
            lb = (vb.get("dimensions") or {}).get(d, {}).get("applicability")
            per_dim_tot += 1
            if la == lb:
                per_dim_agree += 1
            else:
                case_agree = False
            if {la, lb} == {"REQUIRED", "NOT_APPLICABLE"}:
                critical += 1
        if case_agree:
            whole_agree += 1
    return {"per_dimension_applicability_exact_agreement":
            round(per_dim_agree / per_dim_tot, 3) if per_dim_tot else None,
            "required_na_critical_contradictions": critical,
            "whole_vector_exact_agreement": round(whole_agree / whole_tot, 3) if whole_tot else None,
            "per_dimension_comparisons": per_dim_tot}


def stability_compare(run_a: dict, run_b: dict):
    """§17: 同一 fixture 双跑对比。run_x = {fixture_id: verdict}"""
    dims_le1 = tot = 0
    flag_agree = 0
    diffs = []
    for fid, va in run_a.items():
        vb = run_b.get(fid)
        if not vb:
            continue
        tot += 1
        sa = dict(dimension_scores(va)); sb = dict(dimension_scores(vb))
        common = set(sa) & set(sb)
        dmax = max((abs(sa[k] - sb[k]) for k in common), default=0)
        diffs.append({"fixture": fid, "max_dim_abs_diff": dmax})
        if dmax <= 1:
            dims_le1 += 1
        fa, fb = set(raised_fatal_flags(va)), set(raised_fatal_flags(vb))
        flag_agree += int(fa == fb)
    appl = applicability_metrics(run_a, run_b)
    return {"repeat_pairs": tot,
            "dimension_diff_le1_rate": round(dims_le1 / tot, 3) if tot else None,
            "fatal_flag_agreement": round(flag_agree / tot, 3) if tot else None,
            "dimension_diff_le1_rate_detail": diffs,
            "per_dimension_applicability_exact_agreement":
                appl["per_dimension_applicability_exact_agreement"],
            "required_na_critical_contradictions":
                appl["required_na_critical_contradictions"],
            "whole_vector_exact_agreement_diagnostic":
                appl["whole_vector_exact_agreement"]}


def review_manifest(verdicts: dict, threshold: float = 2.0, sample_rate: float = 0.2,
                    seed: int = 7):
    """§34: REVIEW_REQUIRED_CASES + RANDOM_PASS_SAMPLE_POOL（Reviewer 专属, judge 无权签 PASS）。"""
    required, pool = [], []
    for fid, v in verdicts.items():
        dims = v.get("dimensions") or {}
        low = [d for d, dd in dims.items()
               if dd.get("applicability") == "REQUIRED" and isinstance(dd.get("score"), int)
               and dd["score"] < threshold]
        flags = raised_fatal_flags(v)
        low_conf = (v.get("judge_confidence") or 1.0) < 0.6
        if low or flags or low_conf:
            required.append({"case": fid, "low_dims": low, "fatal_flags": flags,
                             "low_confidence": low_conf})
        else:
            pool.append(fid)
    k = max(1, int(round(sample_rate * len(pool)))) if pool else 0
    return {"REVIEW_REQUIRED_CASES": required,
            "RANDOM_PASS_SAMPLE_POOL": sorted(random.Random(seed).sample(pool, k)) if k else []}


if __name__ == "__main__":  # pragma: no cover - 手动校准入口（evaluation-only）
    import argparse
    from o7_scholarly_cases import calibration_fixtures, expected_fatal_flags
    ap = argparse.ArgumentParser()
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--repeat", type=int, default=2)
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    if a.calibrate:
        fixtures = calibration_fixtures()
        dest = a.out or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", "_tmp", "o7a_calibration.json")
        runs = []
        for i in range(a.repeat):
            res = {}
            for fid, f in sorted(fixtures.items()):
                res[fid] = run_judge(f["judge_input"])
                with open(dest, "w", encoding="utf-8") as fh:   # 增量落盘, 防中途丢失
                    json.dump({"run": i, "partial": res}, fh, ensure_ascii=False, indent=1, default=str)
                print(f"[run{i}] {fid} ok", flush=True)
            runs.append(res)
        gate = calibration_gate(
            {**runs[0], "__good__": [k for k, f in fixtures.items() if f["tier"] == "GOOD"],
             "__mid__": [k for k, f in fixtures.items() if f["tier"] == "MID"],
             "__bad__": [k for k, f in fixtures.items() if f["tier"] == "BAD"]},
            expected_fatal_flags())
        stab = stability_compare(runs[0], runs[-1]) if a.repeat > 1 else {}
        out = {"gate": gate, "stability": stab,
               "runs": [{k: v for k, v in r.items()} for r in runs]}
        dest = a.out or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", "_tmp", "o7a_calibration.json")
        with open(dest, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1, default=asdict)
        print(json.dumps({"gate": gate, "stability": stab}, ensure_ascii=False, indent=1))


# ── RP2: Hybrid instrument（机械探针 + k-of-3 ensemble + 确定性聚合）────
def aggregate_ensemble(verdicts: list, mechanical_f5=None,
                       evidence_scope: str = "COMPLETE_FOR_FIXTURE") -> dict:
    """RP2 §7-§9: 3 个 raw verdict → 确定性聚合。
    分数=中位数; applicability=多数(三票各一→AMBIGUOUS+review);
    语义致命 flag(F1/F2/F3/F4/F6)=多数(≥2/3); F5=机械权威(COMPLETE)/多数(PARTIAL)。
    保留 raw_judgments / vote_distribution / minority_flags / 机械-LLM 冲突。"""
    import statistics
    if len(verdicts) != 3:
        raise ValueError("ensemble 需要 3 个 raw verdict")
    agg_dims, appl_disagree = {}, {}
    for d in DIMENSIONS:
        scores = [v["dimensions"][d].get("score") for v in verdicts]
        appls = [v["dimensions"][d].get("applicability") for v in verdicts]
        scored = [s for s in scores if isinstance(s, int)]
        med = int(statistics.median(scored)) if scored else None
        lab = max(set(appls), key=appls.count)
        if len(set(appls)) == len(appls):     # 三票各一
            lab = "AMBIGUOUS"
            appl_disagree[d] = appls
        agg_dims[d] = {"applicability": lab, "score": med,
                       "rationale": "ensemble median/majority of 3 raw judgments",
                       "supporting_spans": [], "missing_requirements": [],
                       "vote_distribution": {"scores": scores, "applicability": appls}}
    flags, vote_dist, minority, mech_conflict = {}, {}, [], []
    for f in FATAL_FLAGS:
        vals = []
        for v in verdicts:
            ff = v["fatal_flags"][f]
            vals.append(bool(ff.get("value")))
        truth = sum(vals) >= 2
        if f == "FALSE_EXACT_QUOTE" and evidence_scope == "COMPLETE_FOR_FIXTURE" \
                and mechanical_f5 is not None:
            truth = bool(mechanical_f5)
            if truth != (sum(vals) >= 2):
                mech_conflict.append({"flag": f, "mechanical": truth, "llm_votes": vals})
        flags[f] = {"value": truth,
                    "offending_spans": sorted({s for v in verdicts
                                               for s in (v["fatal_flags"][f].get("offending_spans") or [])}),
                    "reason": f"majority({sum(vals)}/3)" if f != "FALSE_EXACT_QUOTE"
                              or mechanical_f5 is None else f"mechanical authority ({sum(vals)}/3 llm)",
                    "evidence_refs": [], "confidence": round(1 - abs(truth - sum(vals) / 3), 3)}
        vote_dist[f] = vals
        if 0 < sum(vals) < len(vals):
            minority.append({"flag": f, "votes": vals})
    review_required = bool(appl_disagree or mech_conflict or minority)
    return {
        "dimensions": agg_dims, "fatal_flags": flags,
        "claim_ledger": verdicts[0].get("claim_ledger") or [],
        "overall_scholarly_assessment": verdicts[0].get("overall_scholarly_assessment") or "",
        "judge_confidence": round(sum(v.get("judge_confidence") or 0 for v in verdicts) / 3, 3),
        "raw_judgments": verdicts,
        "vote_distribution": vote_dist,
        "minority_flags": minority,
        "applicability_disagreement": appl_disagree,
        "mechanical_llm_conflict": mech_conflict,
        "review_required": review_required,
    }


def run_ensemble(judge_input: dict, transport=None, evidence_scope: str = "COMPLETE_FOR_FIXTURE",
                 k: int = 3) -> dict:
    """RP2 §1: 机械探针 → k 次 LLM → 确定性聚合。"""
    from o7_quote_probe import probe_from_judge_input
    pr = probe_from_judge_input(judge_input, evidence_scope)
    raws = [run_judge(judge_input, transport=transport) for _ in range(k)]
    agg = aggregate_ensemble(raws, mechanical_f5=pr["mechanical_f5"],
                             evidence_scope=evidence_scope)
    agg["quote_probe"] = pr
    agg["evidence_scope"] = evidence_scope
    return agg


def ensemble_manifest(aggregates: dict) -> dict:
    """RP2 §19: Reviewer manifest 增补项。"""
    dissent, ambig, spread, conflicts = [], [], [], []
    for fid, a in (aggregates or {}).items():
        if any(0 < sum(a["vote_distribution"][f]) < len(a["vote_distribution"][f])
               for f in FATAL_FLAGS):
            dissent.append(fid)
        if a.get("applicability_disagreement"):
            ambig.append(fid)
        for d, dd in (a.get("dimensions") or {}).items():
            sc = [x for x in (dd.get("vote_distribution", {}).get("scores") or [])
                  if isinstance(x, int)]
            if sc and max(sc) - min(sc) > 1:
                spread.append({"case": fid, "dim": d, "scores": sc})
        if a.get("mechanical_llm_conflict"):
            conflicts.append(fid)
    return {"ANY_1_OF_3_FATAL_DISSENT": sorted(set(dissent)),
            "ANY_APPLICABILITY_1_1_1": sorted(set(ambig)),
            "ANY_SCORE_SPREAD_GT1": sorted({(c["case"], c["dim"]) for c in spread}),
            "MECHANICAL_LLM_CONFLICT": sorted(set(conflicts))}
