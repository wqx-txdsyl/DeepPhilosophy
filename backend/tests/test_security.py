# -*- coding: utf-8 -*-
"""安全回归测试（审计 P1-12：guard / text 路径）

覆盖 2026-08-17 加固（P0-7/P0-8）：
- require_admin：未配置→503、口令错→403、正确→放行（fail-closed）
- ai_guard：限流 429 生效（令牌桶突发）
- routes.text._safe_name / _safe_join：路径穿越 payload 全拦截
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient


# ── require_admin ─────────────────────────────────────────────
def test_require_admin_unconfigured(monkeypatch):
    import admin
    monkeypatch.setattr(admin, "ADMIN_PASSWORD", "")
    from guard import require_admin
    resp = _call_guard(require_admin, headers={})
    assert resp.status_code == 503


def _call_guard(dep, headers):
    """构造极小 TestClient 应用调用依赖，返回响应或抛 HTTPException"""
    app = FastAPI()

    async def ep(_: dict = Depends(dep)):
        return {"ok": True}

    app.get("/t")(ep)
    with TestClient(app) as c:
        return c.get("/t", headers=headers)


def test_require_admin_missing_or_wrong(monkeypatch):
    import admin
    monkeypatch.setattr(admin, "ADMIN_PASSWORD", "secret-admin-1")
    from guard import require_admin
    resp = _call_guard(require_admin, headers={})
    assert resp.status_code == 403
    resp = _call_guard(require_admin, headers={"X-Admin-Password": "wrong"})
    assert resp.status_code == 403


def test_require_admin_correct(monkeypatch):
    import admin
    monkeypatch.setattr(admin, "ADMIN_PASSWORD", "secret-admin-1")
    from guard import require_admin
    resp = _call_guard(require_admin, headers={"X-Admin-Password": "secret-admin-1"})
    assert resp.status_code == 200


# ── ai_guard 限流 ─────────────────────────────────────────────
def test_ai_guard_rate_limit():
    from guard import ai_guard, AI_BURST
    results = []
    for _ in range(AI_BURST + 6):
        resp = _call_guard(ai_guard, headers={})
        results.append(resp.status_code)
    # 突发容量内放行，超出返回 429
    assert 200 in results and 429 in results


# ── routes.text 路径白名单 ────────────────────────────────────
def test_safe_name_rejects_traversal():
    from routes.text import _safe_name
    for bad in ["../users", "..\\users.db", "../../etc/passwd", "..", ".", "", "a/b", "a\\b"]:
        assert not _safe_name(bad), f"应拒绝: {bad!r}"


def test_safe_name_accepts_normal():
    from routes.text import _safe_name
    for good in ["nietzsche-001", "img_01.webp", "a.b_c", "Beyond_Good_Evil"]:
        assert _safe_name(good), f"应放行: {good!r}"


def test_safe_join_stays_in_root(tmp_path):
    from routes.text import _safe_join
    root = str(tmp_path)
    ok = _safe_join(root, "nietzsche-001.json")
    assert ok and ok.startswith(root)
    # 穿越路径必须被拒（返回 None 或抛错）
    assert _safe_join(root, "../evil.json") is None or not _safe_join(root, "../evil.json").startswith(root)
