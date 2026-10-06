# -*- coding: utf-8 -*-
"""V9-F1 §1: judge failure taxonomy 确定性测试。

封闭分类: HTTP_ERROR / TIMEOUT / API_RESPONSE_PARSE_ERROR / EMPTY_CONTENT /
CONTENT_JSON_PARSE_ERROR / VERDICT_SCHEMA_INVALID（+ VALID）。
每次失败必须携带可归档机械事实（http_status/exception_class/response_chars/
response_sha256/content_prefix≤300）; 模型/prompt/rubric/阈值语义零改动。
"""
import json
import os
import sys
import urllib.error

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "tools", "evaluation"))
import o7e_bakeoff_judge2 as J2


class _FakeResponse:
    def __init__(self, raw):
        self._raw = raw

    def read(self):
        return self._raw

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _raise_http_429(req, timeout=None):
    raise urllib.error.HTTPError(req.full_url, 429, "Too Many Requests",
                                 hdrs=None, fp=None)


def _raise_timeout(req, timeout=None):
    raise TimeoutError("timed out")


def test_http_error_429_classified():
    J2._orig_urlopen = J2.urllib.request.urlopen
    J2.urllib.request.urlopen = _raise_http_429
    try:
        with pytest.raises(J2.JudgeCallFailure) as ei:
            J2._call("prompt")
    finally:
        J2.urllib.request.urlopen = J2._orig_urlopen
    assert ei.value.failure_class == "HTTP_ERROR"
    assert ei.value.http_status == 429
    assert ei.value.exception_class == "HTTPError"


def test_timeout_classified():
    J2.urllib.request.urlopen = _raise_timeout
    try:
        with pytest.raises(J2.JudgeCallFailure) as ei:
            J2._call("prompt")
    finally:
        J2.urllib.request.urlopen = J2._orig_urlopen
    assert ei.value.failure_class == "TIMEOUT"
    assert ei.value.exception_class == "TimeoutError"


def test_api_outer_json_malformed(monkeypatch):
    monkeypatch.setattr(J2.urllib.request, "urlopen",
                        lambda req, timeout=None: _FakeResponse(b"NOT JSON{{"))
    with pytest.raises(J2.JudgeCallFailure) as ei:
        J2._call("prompt")
    assert ei.value.failure_class == "API_RESPONSE_PARSE_ERROR"
    assert ei.value.response_chars == len(b"NOT JSON{{")
    assert len(ei.value.response_sha256) == 64


def test_content_json_malformed():
    with pytest.raises(J2.JudgeCallFailure) as ei:
        J2._parse_verdict("这不是一个 verdict JSON", "stop")
    assert ei.value.failure_class == "CONTENT_JSON_PARSE_ERROR"
    assert ei.value.response_chars > 0
    assert len(ei.value.response_sha256) == 64
    assert ei.value.content_prefix == "这不是一个 verdict JSON"
    assert len(ei.value.content_prefix) <= 300   # bounded prefix


def test_empty_content_classified_production_call(monkeypatch):
    """EMPTY_CONTENT 必须直接测 production _call（V9-F1-R1 §3: 禁止复制逻辑假测试）"""
    raw = json.dumps({"choices": [{"message": {"content": ""}, "finish_reason": "length"}]})
    monkeypatch.setattr(J2.urllib.request, "urlopen",
                        lambda req, timeout=None: _FakeResponse(raw.encode()))
    with pytest.raises(J2.JudgeCallFailure) as ei:
        J2._call("prompt")
    assert ei.value.failure_class == "EMPTY_CONTENT"
    assert ei.value.finish_reason == "length"


def test_schema_invalid_classified():
    # V9-F1-R1 §2: _parse_verdict 仅负责 JSON decode; 结构缺失的
    # VERDICT_SCHEMA_INVALID 观测由 judge_candidate canonical 层记录
    v = J2._parse_verdict(json.dumps({"foo": 1}), "stop")
    assert isinstance(v, dict) and "dimensions" not in v


def test_valid_verdict_passes():
    v = J2._parse_verdict(json.dumps({"dimensions": {"textual_grounding": {
        "score": 4, "applicability": "REQUIRED"}}}), "stop")
    assert v["dimensions"]["textual_grounding"]["score"] == 4


# ═══════════════════════════════════════════════════════
# V9-F1-R1 §3: judge_candidate 完整 retry pipeline 测试
# ═══════════════════════════════════════════════════════
_RUNS = [{"case_id": "TAX-1", "delivery": {"published": True},
          "answer": "回答正文。", "evidence_digest": {}, "citations": [],
          "quote_bound": [], "scholarly_provenance": {}}]
_MANIFEST = [{"case_id": "TAX-1", "question": "q", "task_category": "t",
              "agent_identity": "A", "applicability": {}}]
_VALID_VERDICT = {"dimensions": {"textual_grounding": {"applicability": "OPTIONAL",
                                                       "score": 4}},
                  "fatal_flags": {}, "judge_confidence": 0.9,
                  "overall_scholarly_assessment": "ok"}


@pytest.fixture
def pipeline_env(monkeypatch, tmp_path):
    """judge_candidate 隔离环境: tmp runs/manifest/out; canonical validate_verdict
    用真实 O7A 实现（pipeline 测试与 canonical 校验零耦合点）。"""
    runs_p = tmp_path / "runs.json"
    man_p = tmp_path / "man.json"
    runs_p.write_text(json.dumps(_RUNS), encoding="utf-8")
    man_p.write_text(json.dumps(_MANIFEST), encoding="utf-8")
    tag = f"tmp_taxonomy_{abs(hash(str(tmp_path))) % 10 ** 8}"
    yield {"runs": str(runs_p), "man": str(man_p), "tag": tag}
    for f in (f"{J2.ROOT}/backend/tools/_tmp/{tag}.json",
              f"{J2.ROOT}/backend/tools/_tmp/{tag}_summary.json"):
        if os.path.exists(f):
            os.remove(f)


def _valid_verdict():
    dims = {}
    flags = {}
    for d in ("textual_grounding", "argument_reconstruction",
              "interpretive_plurality", "historical_discipline",
              "literature_orientation"):
        dims[d] = {"applicability": "OPTIONAL", "score": 4,
                   "rationale": "测试 rationale"}
    for f in ("FABRICATED_BIBLIOGRAPHY", "FABRICATED_SCHOLAR_ATTRIBUTION",
              "PRIMARY_TEXT_MISREPRESENTATION", "MAJOR_ANACHRONISM",
              "FALSE_EXACT_QUOTE", "LITERATURE_ACCESS_OVERCLAIM"):
        flags[f] = {"value": False}
    return {"dimensions": dims, "fatal_flags": flags,
            "judge_confidence": 0.9, "overall_scholarly_assessment": "ok"}


def _patch_call(monkeypatch, seq):
    """循环消耗 seq（每 vote 独立循环 → 计数确定）; 记录调用次数。"""
    calls = {"n": 0}

    def fake_call(prompt):
        item = seq[calls["n"] % len(seq)]
        calls["n"] += 1
        if isinstance(item, J2.JudgeCallFailure):
            raise item
        return (item, "stop")

    monkeypatch.setattr(J2, "_call", fake_call)
    return calls


def test_p1_content_malformed_then_valid_vote_valid(monkeypatch, pipeline_env):
    calls = _patch_call(monkeypatch, ["NOT JSON verdict", json.dumps(_valid_verdict())])
    J2.judge_candidate("deepseek-v4-flash", runs_path=pipeline_env["runs"],
                       out_tag=pipeline_env["tag"], manifest_path=pipeline_env["man"])
    assert calls["n"] == 6                       # 3 votes × (malformed + valid retry)
    j = json.load(open(f"{J2.ROOT}/backend/tools/_tmp/{pipeline_env['tag']}.json"))
    vote = next(v for v in j[0]["votes_archive"] if v.get("vote_index") == 0)
    assert vote["valid"] is True
    classes = [a["failure_class"] for a in j[0].get("attempt_log", [])
               if a.get("vote_index") == 0]
    assert classes == ["CONTENT_JSON_PARSE_ERROR"]


def test_p2_three_malformed_exactly_three_attempts(monkeypatch, pipeline_env):
    calls = _patch_call(monkeypatch, ["BAD"])
    J2.judge_candidate("deepseek-v4-flash", runs_path=pipeline_env["runs"],
                       out_tag=pipeline_env["tag"], manifest_path=pipeline_env["man"])
    assert calls["n"] == 9                       # 3 votes × 恰 3 attempts
    j = json.load(open(f"{J2.ROOT}/backend/tools/_tmp/{pipeline_env['tag']}.json"))
    vote = next(v for v in j[0]["votes_archive"] if v.get("vote_index") == 0)
    assert vote["valid"] is False
    assert vote["failure_classes"] == ["CONTENT_JSON_PARSE_ERROR"] * 3


def test_p3_http_429_then_valid_vote_valid(monkeypatch, pipeline_env):
    calls = _patch_call(monkeypatch, [
        J2.JudgeCallFailure("HTTP_ERROR", "http 429", http_status=429,
                            exception_class="HTTPError"),
        json.dumps(_valid_verdict())])
    J2.judge_candidate("deepseek-v4-flash", runs_path=pipeline_env["runs"],
                       out_tag=pipeline_env["tag"], manifest_path=pipeline_env["man"])
    assert calls["n"] == 6                       # 3 votes × (HTTP_ERROR + valid retry)
    j = json.load(open(f"{J2.ROOT}/backend/tools/_tmp/{pipeline_env['tag']}.json"))
    classes = [a["failure_class"] for a in j[0].get("attempt_log", [])]
    assert classes.count("HTTP_ERROR") == 3      # 每 vote 一次 HTTP_ERROR


def test_p4_empty_content_then_valid_vote_valid(monkeypatch, pipeline_env):
    calls = _patch_call(monkeypatch, [
        J2.JudgeCallFailure("EMPTY_CONTENT", "empty", finish_reason="length"),
        json.dumps(_valid_verdict())])
    J2.judge_candidate("deepseek-v4-flash", runs_path=pipeline_env["runs"],
                       out_tag=pipeline_env["tag"], manifest_path=pipeline_env["man"])
    assert calls["n"] == 6                       # 3 votes × (EMPTY_CONTENT + valid retry)
    j = json.load(open(f"{J2.ROOT}/backend/tools/_tmp/{pipeline_env['tag']}.json"))
    vote = next(v for v in j[0]["votes_archive"] if v.get("vote_index") == 0)
    assert vote["valid"] is True


def test_p5_schema_invalid_no_extra_llm_call(monkeypatch, pipeline_env):
    # JSON 可解析但缺 dimensions → 不新增 LLM retry（旧行为）;
    # VERDICT_SCHEMA_INVALID 记录于 attempt_log; canonical 校验判 vote invalid
    calls = _patch_call(monkeypatch, [json.dumps({"foo": 1})])
    J2.judge_candidate("deepseek-v4-flash", runs_path=pipeline_env["runs"],
                       out_tag=pipeline_env["tag"], manifest_path=pipeline_env["man"])
    assert calls["n"] == 3                       # 3 votes × 恰 1 call（零重试）
    j = json.load(open(f"{J2.ROOT}/backend/tools/_tmp/{pipeline_env['tag']}.json"))
    vote = next(v for v in j[0]["votes_archive"] if v.get("vote_index") == 0)
    assert vote["valid"] is False                # 真实 validate_verdict 判 invalid
    obs = [a["failure_class"] for a in j[0].get("attempt_log", [])]
    assert obs == ["VERDICT_SCHEMA_INVALID"] * 3   # 3 votes 各记录一次观测


def test_p6_valid_first_attempt_exactly_one_call_per_vote(monkeypatch, pipeline_env):
    calls = _patch_call(monkeypatch, [json.dumps(_valid_verdict())])
    J2.judge_candidate("deepseek-v4-flash", runs_path=pipeline_env["runs"],
                       out_tag=pipeline_env["tag"], manifest_path=pipeline_env["man"])
    assert calls["n"] == 3                       # 3 votes × 恰 1 call
    j = json.load(open(f"{J2.ROOT}/backend/tools/_tmp/{pipeline_env['tag']}.json"))
    vote = next(v for v in j[0]["votes_archive"] if v.get("vote_index") == 0)
    assert vote["valid"] is True


# ═══════════════════════════════════════════════════════
# V9-F1-R2: canonical schema invalid 全量可观测
# ═══════════════════════════════════════════════════════
def _verdict_missing_dim():
    v = _valid_verdict()
    v["dimensions"].pop("historical_discipline")   # 缺一个冻结维度
    return v


def _verdict_bad_score():
    v = _valid_verdict()
    v["dimensions"]["textual_grounding"]["score"] = 5   # 越界（0-4）
    return v


def _verdict_required_missing_score():
    v = _valid_verdict()
    man = [{"case_id": "TAX-1", "question": "q", "task_category": "t",
            "agent_identity": "A",
            "applicability": {"TEXTUAL_GROUNDING": "REQUIRED"}}]
    v["dimensions"]["textual_grounding"] = {"applicability": "REQUIRED"}  # 无 score
    return v, man


def _verdict_missing_fatal():
    v = _valid_verdict()
    v["fatal_flags"].pop("FABRICATED_BIBLIOGRAPHY")
    return v


def _verdict_missing_rationale():
    v = _valid_verdict()
    v["dimensions"]["textual_grounding"]["rationale"] = None
    return v


def _run_canonical(monkeypatch, pipeline_env, verdict, man=None):
    calls = _patch_call(monkeypatch, [json.dumps(verdict)])
    man_path = pipeline_env["man"]
    if man is not None:
        man_path = str(pipeline_env["man_path_override"])
        open(man_path, "w", encoding="utf-8").write(json.dumps(man))
    J2.judge_candidate("deepseek-v4-flash", runs_path=pipeline_env["runs"],
                       out_tag=pipeline_env["tag"], manifest_path=man_path)
    j = json.load(open(f"{J2.ROOT}/backend/tools/_tmp/{pipeline_env['tag']}.json"))
    return calls, j


def _schema_obs(j):
    return [a for a in j[0].get("attempt_log", [])
            if a.get("failure_class") == "VERDICT_SCHEMA_INVALID"]


def test_r2_missing_dimension_observable(monkeypatch, pipeline_env):
    calls, j = _run_canonical(monkeypatch, pipeline_env, _verdict_missing_dim())
    assert calls["n"] == 3                       # 零额外 retry
    vote = next(v for v in j[0]["votes_archive"] if v.get("vote_index") == 0)
    assert vote["valid"] is False
    obs = _schema_obs(j)
    assert len(obs) == 3                         # 每 vote 一条观测
    assert all(a.get("observation_only") for a in obs)
    assert any("historical_discipline" in r for a in obs
               for r in a.get("canonical_reasons", []))


def test_r2_bad_score_observable(monkeypatch, pipeline_env):
    calls, j = _run_canonical(monkeypatch, pipeline_env, _verdict_bad_score())
    vote = next(v for v in j[0]["votes_archive"] if v.get("vote_index") == 0)
    assert vote["valid"] is False
    obs = _schema_obs(j)
    assert len(obs) == 3
    assert any("0-4" in r for a in obs for r in a.get("canonical_reasons", []))


# （test_r2_missing_required_score_observable 已被 V9-F1-R3 修正拆分:
#  manifest-only 场景 → test_r3_pure_manifest_mismatch_no_schema_label;
#  canonical REQUIRED 场景 → test_r3_canonical_required_missing_score_observable）


def test_r2_missing_fatal_flag_observable(monkeypatch, pipeline_env):
    calls, j = _run_canonical(monkeypatch, pipeline_env, _verdict_missing_fatal())
    vote = next(v for v in j[0]["votes_archive"] if v.get("vote_index") == 0)
    assert vote["valid"] is False
    obs = _schema_obs(j)
    assert len(obs) == 3
    assert any("FABRICATED_BIBLIOGRAPHY" in r
               for a in obs for r in a.get("canonical_reasons", []))


def test_r2_missing_rationale_observable(monkeypatch, pipeline_env):
    calls, j = _run_canonical(monkeypatch, pipeline_env, _verdict_missing_rationale())
    vote = next(v for v in j[0]["votes_archive"] if v.get("vote_index") == 0)
    assert vote["valid"] is False
    obs = _schema_obs(j)
    assert len(obs) == 3
    assert any("rationale" in r for a in obs for r in a.get("canonical_reasons", []))


def test_r2_canonical_valid_no_schema_observation(monkeypatch, pipeline_env):
    calls, j = _run_canonical(monkeypatch, pipeline_env, _valid_verdict())
    assert _schema_obs(j) == []


# ═══════════════════════════════════════════════════════
# V9-F1-R3: manifest 层与 canonical schema 两层分离
# ═══════════════════════════════════════════════════════
def test_r3_pure_manifest_mismatch_no_schema_label(monkeypatch, pipeline_env):
    """pure manifest applicability mismatch → invalid vote + mismatch reason +
    VERDICT_SCHEMA_INVALID 计数 0 + 每 vote 恰 1 LLM call（零重试）"""
    verdict = _valid_verdict()
    verdict["dimensions"]["textual_grounding"] = {
        "applicability": "OPTIONAL", "score": None, "rationale": "合法 rationale"}
    man = [{"case_id": "TAX-1", "question": "q", "task_category": "t",
            "agent_identity": "A",
            "applicability": {"TEXTUAL_GROUNDING": "REQUIRED"}}]
    man_path = str(pipeline_env["man"]) + ".mismatch.json"
    open(man_path, "w", encoding="utf-8").write(json.dumps(man))
    calls = _patch_call(monkeypatch, [json.dumps(verdict)])
    J2.judge_candidate("deepseek-v4-flash", runs_path=pipeline_env["runs"],
                       out_tag=pipeline_env["tag"], manifest_path=man_path)
    assert calls["n"] == 3                       # 每 vote 恰 1 call, 零重试
    j = json.load(open(f"{J2.ROOT}/backend/tools/_tmp/{pipeline_env['tag']}.json"))
    vote = next(v for v in j[0]["votes_archive"] if v.get("vote_index") == 0)
    assert vote["valid"] is False                # mismatch → vote invalid
    assert any("applicability" in str(rsn) or "!= manifest" in str(rsn)
               for rsn in vote.get("reasons") or [])
    assert _schema_obs(j) == []                  # 零 canonical schema 误标


def test_r3_canonical_required_missing_score_observable(monkeypatch, pipeline_env):
    """verdict 自身标 REQUIRED 且无 score → O7A canonical 判定 → 可观测"""
    v = _valid_verdict()
    v["dimensions"]["textual_grounding"] = {"applicability": "REQUIRED"}  # 无 score
    calls = _patch_call(monkeypatch, [json.dumps(v)])
    J2.judge_candidate("deepseek-v4-flash", runs_path=pipeline_env["runs"],
                       out_tag=pipeline_env["tag"], manifest_path=pipeline_env["man"])
    assert calls["n"] == 3                       # 零重试
    obs = _schema_obs(json.load(open(
        f"{J2.ROOT}/backend/tools/_tmp/{pipeline_env['tag']}.json")))
    assert len(obs) == 3
    assert any("REQUIRED" in r for a in obs for r in a.get("canonical_reasons", []))
