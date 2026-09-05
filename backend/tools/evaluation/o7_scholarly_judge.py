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
   仅当回答完全不涉及该维时才允许 null。整份评审至少要有三维给出整数分。
2. interpretive_plurality 与 historical_discipline、literature_orientation 允许 NOT_APPLICABLE;
   禁止因为回答"没有列两派/没有学者名"而在不适用时扣分——争议模板不是万能格式。
3. 反风格偏置: 更长、引用更多、外语更多、学者名更多、语气更像论文, 本身不得加分。
   只奖励 correctness/grounding/argument/discipline/真实文献导向。
4. 六类致命错误与分数完全分离（true/false + offending_span + reason + evidence_ref + confidence）:
   评审每个 fixture 时, 先逐句核对回答中的事实性主张与输入证据/记录, 再给分; flag 判定独立于分数。
   逐 flag 操作性判定（宁确勿漏——对显式植入的错误必须 flag）:
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


def run_judge(inp: dict, transport=None, attempts: int = 3) -> dict:
    """调用独立 judge（或注入 transport 以便离线测试）; 解析/校验失败带反馈重试; 返回已校验 verdict。"""
    prompt = render_judge_prompt(inp)
    feedback = ""
    last_err = None
    for _ in range(attempts):
        if transport is None:
            payload = {
                "model": JUDGE_MODEL, "temperature": JUDGE_TEMPERATURE,
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


def calibration_gate(results: dict, expected_flags: dict):
    """§16-§17: results={fixture_id: verdict}, expected_flags={fixture_id: [flags]}。
    返回 gate 指标: GOOD>MID>BAD、fatal recall、false-fatal、稳定性由外部双跑对比。"""
    def mean(group):
        vals = [scholarly_mean(results[f]) for f in group if results.get(f)]
        vals = [v for v in vals if v is not None]
        return round(sum(vals) / len(vals), 3) if vals else None
    good, mid, bad = mean(results.get("__good__", [])), mean(results.get("__mid__", [])), mean(results.get("__bad__", []))
    detected, missed = 0, []
    for fid, flags in (expected_flags or {}).items():
        got = set(raised_fatal_flags(results.get(fid) or {}))
        for f in flags:
            if f in got:
                detected += 1
            else:
                missed.append((fid, f))
    total = sum(len(v) for v in (expected_flags or {}).values())
    false_fatal = [(fid, f) for fid, v in (results or {}).items()
                   if isinstance(v, dict)
                   for f in raised_fatal_flags(v)
                   if str(fid).startswith(("good", "mid"))]
    return {"good_mean": good, "mid_mean": mid, "bad_mean": bad,
            "ordering_ok": bool(good is not None and bad is not None and good > bad),
            "expected_fatal_total": total, "expected_fatal_detected": detected,
            "expected_fatal_recall": round(detected / total, 3) if total else None,
            "missed_fatal": missed,
            "false_fatal_on_goodmid_count": len(false_fatal)}


def stability_compare(run_a: dict, run_b: dict):
    """§17: 同一 fixture 双跑对比。run_x = {fixture_id: verdict}"""
    dims_le1 = tot = 0
    flag_agree = appl_agree = appl_tot = 0
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
        pa = {d: (va.get("dimensions") or {}).get(d, {}).get("applicability") for d in DIMENSIONS}
        pb = {d: (vb.get("dimensions") or {}).get(d, {}).get("applicability") for d in DIMENSIONS}
        appl_tot += 1
        appl_agree += int(pa == pb)
    return {"repeat_pairs": tot,
            "dimension_diff_le1_rate": round(dims_le1 / tot, 3) if tot else None,
            "fatal_flag_agreement": round(flag_agree / tot, 3) if tot else None,
            "applicability_agreement": round(appl_agree / tot, 3) if tot else None,
            "per_fixture": diffs}


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
