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
    # V9-F1-R1 §2: schema-invalid 不新增 retry——_parse_verdict 正常返回 dict,
    # 结构缺失仅产生 VERDICT_SCHEMA_INVALID 观测分类（下游 canonical 校验不变）
    v = J2._parse_verdict(json.dumps({"foo": 1}), "stop")
    assert J2._verdict_schema_observation(v) == "VERDICT_SCHEMA_INVALID"
    # 有 dimensions 的 dict → 无 schema 观测
    assert J2._verdict_schema_observation(
        J2._parse_verdict(json.dumps({"dimensions": {}}), "stop")) is None


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
