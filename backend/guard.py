# -*- coding: utf-8 -*-
"""端点保护: 可选登录 + IP/用户限流 + 每日配额 + 请求用户上下文（per-user 记忆）

2026-08-14 安全加固（P0）: agent 端点此前完全匿名无限制, 脚本可刷爆 DeepSeek 余额;
全局记忆无用户隔离, 用户 A 的作文/辩论会话可被用户 B 读取/修改。

用法（FastAPI 依赖）:
  @router.post("/api/agent/stream_lg")
  async def stream_lg(req, _g: dict = Depends(agent_guard)):
      ...

  current_user 上下文变量: 由 agent_guard 设置, 供 per-user 记忆等使用
  （经 asyncio.to_thread 传播到工具执行线程）。
"""
import threading
import time
from contextvars import ContextVar

from fastapi import Header, HTTPException, Request

current_user: ContextVar = ContextVar("dp_user", default=None)  # {"id":..,"ip":..} 或 None

# ── 内存令牌桶（单进程; 多副本/生产 VPS 可换 Redis 实现）──
class _Bucket:
    __slots__ = ("rate", "burst", "tokens", "last", "lock")

    def __init__(self, rate, burst):
        self.rate = rate
        self.burst = float(burst)
        self.tokens = float(burst)
        self.last = time.monotonic()
        self.lock = threading.Lock()

    def consume(self, n=1):
        with self.lock:
            now = time.monotonic()
            self.tokens = min(self.burst, self.tokens + (now - self.last) * self.rate)
            self.last = now
            if self.tokens >= n:
                self.tokens -= n
                return True
            return False


_buckets = {}
_buckets_lock = threading.Lock()


def _bucket(key, rate, burst):
    with _buckets_lock:
        b = _buckets.get(key)
        if b is None:
            b = _Bucket(rate, burst)
            _buckets[key] = b
        return b


# ── 每日配额（内存计数, 按 (日期, key); 重启清零）──
_quota = {}
_quota_lock = threading.Lock()


def _quota_ok(key, day_limit):
    today = time.strftime("%Y-%m-%d")
    with _quota_lock:
        k = (today, key)
        n = _quota.get(k, 0)
        if n >= day_limit:
            return False
        _quota[k] = n + 1
        return True


# agent 端点限流配置（LLM 代理成本保护）
AGENT_RATE, AGENT_BURST = 10, 20      # 每分钟 10 次, 突发 20
AGENT_QUOTA_ANON = 60                 # 匿名每 IP 每日 60 次
AGENT_QUOTA_USER = 300                # 登录用户每日 300 次

# 上传端点（文件/识图, 资源消耗较小）
UPLOAD_RATE, UPLOAD_BURST = 20, 40


def client_ip(request: Request) -> str:
    ff = request.headers.get("x-forwarded-for")
    if ff:
        return ff.split(",")[0].strip()
    return request.client.host if request.client else "0.0.0.0"


def resolve_user(authorization):
    if authorization and authorization.startswith("Bearer "):
        try:
            from auth import get_user_by_token
            u = get_user_by_token(authorization[7:])
            if u:
                return u
        except Exception:
            return None
    return None


def agent_guard(request: Request, authorization: str = Header(None)):
    """agent 端点依赖: 限流 + 配额 + 设置 current_user 上下文（per-user 记忆/配额）"""
    ip = client_ip(request)
    user = resolve_user(authorization)
    current_user.set({"id": user["id"] if user else None, "ip": ip})
    key = f"u{user['id']}" if user else f"ip:{ip}"
    if not _bucket(key, AGENT_RATE, AGENT_BURST).consume():
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")
    if not _quota_ok(key, AGENT_QUOTA_USER if user else AGENT_QUOTA_ANON):
        raise HTTPException(status_code=429, detail="今日对话额度已用完，请明日再试")
    return user


def upload_guard(request: Request, authorization: str = Header(None)):
    """上传端点依赖: 限流（文件内容进上下文, 匿名可用但受限）"""
    ip = client_ip(request)
    user = resolve_user(authorization)
    current_user.set({"id": user["id"] if user else None, "ip": ip})
    key = f"u{user['id']}" if user else f"ip:{ip}"
    if not _bucket(key, UPLOAD_RATE, UPLOAD_BURST).consume():
        raise HTTPException(status_code=429, detail="上传过于频繁，请稍后再试")
    return user


def user_memory_key() -> str:
    """per-user 记忆槽 key: 登录按用户, 匿名按 IP, 兜底 default"""
    u = current_user.get()
    if not u:
        return "default"
    if u.get("id"):
        return f"u{u['id']}"
    if u.get("ip"):
        return f"ip:{u['ip']}"
    return "default"
