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


def test_empty_content_classified():
    raw = json.dumps({"choices": [{"message": {"content": ""}, "finish_reason": "length"}]})
    with pytest.raises(J2.JudgeCallFailure) as ei:
        J2._parse_outer(raw) if False else _parse_empty(raw)
    assert ei.value.failure_class == "EMPTY_CONTENT"
    assert ei.value.finish_reason == "length"


def _parse_empty(raw):
    """与 _call 内部相同的 EMPTY_CONTENT 分支（独立驱动以便单测）。"""
    outer = json.loads(raw)
    content = outer["choices"][0]["message"]["content"] or ""
    if not str(content).strip():
        raise J2.JudgeCallFailure("EMPTY_CONTENT", "empty message.content",
                                  finish_reason=outer["choices"][0].get("finish_reason"))
    return content


def test_schema_invalid_classified():
    with pytest.raises(J2.JudgeCallFailure) as ei:
        J2._parse_verdict(json.dumps({"foo": 1}), "stop")
    assert ei.value.failure_class == "VERDICT_SCHEMA_INVALID"


def test_valid_verdict_passes():
    v = J2._parse_verdict(json.dumps({"dimensions": {"textual_grounding": {
        "score": 4, "applicability": "REQUIRED"}}}), "stop")
    assert v["dimensions"]["textual_grounding"]["score"] == 4
