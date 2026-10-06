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


# ── require_admin 爆破限流（N4, audit 2026-08-18）────────────────────
# TestClient 固定以 "testclient" 作为对端 IP; 用例末尾均 _bucket_reset 清理,
# 避免失败桶跨用例污染（后续 require_admin 用例预期 403 而非 429）。
def test_require_admin_bruteforce_lock(monkeypatch):
    """连续 10 次口令错误 → 第 11 次起 429 锁定（按 IP 计桶）"""
    import admin
    monkeypatch.setattr(admin, "ADMIN_PASSWORD", "secret-admin-1")
    from guard import require_admin, _bucket_reset
    codes = [_call_guard(require_admin, headers={"X-Admin-Password": "wrong"}).status_code
             for _ in range(11)]
    assert codes[:10] == [403] * 10, codes
    assert codes[10] == 429, codes
    # 注: 锁定按令牌桶实现, 桶随 10 次/分速率 ~6s/个回填——锁定期间任意请求（含正确口令）
    # 在桶空时同样 429, 但该行为随回填时序变化, 不在用例中断言（避免时序脆弱）。
    _bucket_reset("adminfail", "testclient")


def test_require_admin_success_resets_failures(monkeypatch):
    """成功校验复位失败计数: 9 次失败 → 1 次成功 → 再 10 次失败 → 锁定"""
    import admin
    monkeypatch.setattr(admin, "ADMIN_PASSWORD", "secret-admin-1")
    from guard import require_admin, _bucket_reset
    for _ in range(9):
        assert _call_guard(require_admin, headers={"X-Admin-Password": "wrong"}).status_code == 403
    assert _call_guard(require_admin, headers={"X-Admin-Password": "secret-admin-1"}).status_code == 200
    codes = [_call_guard(require_admin, headers={"X-Admin-Password": "wrong"}).status_code
             for _ in range(11)]
    assert codes[:10] == [403] * 10, codes
    assert codes[10] == 429, codes
    _bucket_reset("adminfail", "testclient")


# ── ai_guard 限流 ─────────────────────────────────────────────
def test_ai_guard_rate_limit():
    from guard import ai_guard, AI_BURST
    results = []
    for _ in range(AI_BURST + 6):
        resp = _call_guard(ai_guard, headers={})
        results.append(resp.status_code)
    # 突发容量内放行，超出返回 429
    assert 200 in results and 429 in results


# ── auth_guard 限流（2026-08-30: agent.deepphilosophy.top 公开后新增）────────
def test_auth_guard_rate_limit():
    """注册/登录防刷: 突发容量内放行, 超出返回 429（按 IP 计桶 + 每日配额）"""
    from guard import auth_guard, AUTH_BURST, _bucket_reset, _quota_reset
    results = []
    for _ in range(AUTH_BURST + 3):
        resp = _call_guard(auth_guard, headers={})
        results.append(resp.status_code)
    # 突发容量内放行，超出返回 429（令牌桶随时间回填, 不精确断言放行数量）
    assert 200 in results and 429 in results
    _bucket_reset("auth", "auth:ip:testclient")
    _quota_reset("auth:ip:testclient")


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
