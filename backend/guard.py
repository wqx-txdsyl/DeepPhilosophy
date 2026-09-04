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

# S15（audit 2026-08-17）: token 解析收敛到 auth_deps（唯一实现, 与 auth_required 同源）
from auth_deps import resolve_user

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
_MAX_BUCKETS = 5000  # S24: 限流字典上限，超过即整体清空（优雅降级），防长运行内存无限增长


def _bucket(name, key, rate, burst):
    """按 (名称, key) 隔离的令牌桶——agent 与 upload 各自的额度互不挤占"""
    with _buckets_lock:
        if len(_buckets) > _MAX_BUCKETS:
            _buckets.clear()
        b = _buckets.get((name, key))
        if b is None:
            b = _Bucket(rate, burst)
            _buckets[(name, key)] = b
        return b


def _bucket_reset(name, key):
    """清空指定令牌桶（N4: require_admin 口令校验成功后复位该 IP 的失败计数）"""
    with _buckets_lock:
        _buckets.pop((name, key), None)


def _quota_reset(key):
    """清空指定 key 的今日配额计数（测试用例复位用，与 _bucket_reset 对称）"""
    today = time.strftime("%Y-%m-%d")
    with _quota_lock:
        _quota.pop((today, key), None)


# ── 每日配额（内存计数, 按 (日期, key); 重启清零）──
_quota = {}
_quota_lock = threading.Lock()


def _quota_ok(key, day_limit):
    today = time.strftime("%Y-%m-%d")
    with _quota_lock:
        if len(_quota) > _MAX_BUCKETS:  # S24: 同上，防无限增长
            _quota.clear()
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
    # S8（audit 2026-08-17）：不再信任 x-forwarded-for 首段（客户端可伪造，绕过限流）。
    # 优先取 Cloudflare 注入的 cf-connecting-ip（不可由客户端伪造），否则用直连对端地址。
    cf = request.headers.get("cf-connecting-ip")
    if cf:
        return cf.strip()
    return request.client.host if request.client else "0.0.0.0"


# resolve_user 已收敛至 auth_deps（S15）: 本模块保留同名引用仅为兼容外部导入


def agent_guard(request: Request, authorization: str = Header(None)):
    """agent 端点依赖: 限流 + 配额 + 设置 current_user 上下文（per-user 记忆/配额）"""
    ip = client_ip(request)
    user = resolve_user(authorization)
    current_user.set({"id": user["id"] if user else None, "ip": ip})
    key = f"u{user['id']}" if user else f"ip:{ip}"
    if not _bucket("agent", key, AGENT_RATE, AGENT_BURST).consume():
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
    if not _bucket("upload", key, UPLOAD_RATE, UPLOAD_BURST).consume():
        raise HTTPException(status_code=429, detail="上传过于频繁，请稍后再试")
    return user


# AI 流式代理（/api/ai/stream）限流配置 — 与 agent 同机制、独立预算
AI_RATE, AI_BURST = 10, 20       # 每分钟 10 次, 突发 20
AI_QUOTA_ANON = 60               # 匿名每 IP 每日 60 次
AI_QUOTA_USER = 300              # 登录用户每日 300 次


def ai_guard(request: Request, authorization: str = Header(None)):
    """/api/ai/stream 依赖: 限流 + 每日配额（同 agent_guard 机制, 独立额度）
    加固（审计 S1）: 付费 LLM 代理此前无任何限制, 脚本可刷爆服务端余额"""
    ip = client_ip(request)
    user = resolve_user(authorization)
    current_user.set({"id": user["id"] if user else None, "ip": ip})
    key = f"ai:u{user['id']}" if user else f"ai:ip:{ip}"
    if not _bucket("ai", key, AI_RATE, AI_BURST).consume():
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")
    if not _quota_ok(key, AI_QUOTA_USER if user else AI_QUOTA_ANON):
        raise HTTPException(status_code=429, detail="今日 AI 额度已用完，请明日再试")
    return user


# ── require_admin 爆破限流配置（N4, audit 2026-08-18）──────────────
# 口令校验失败按 IP 计桶: 10 次/分钟、突发 10 —— 桶耗尽即该 IP 锁定（返回 429,
# 与口令是否正确无关）; 校验成功即清桶复位。复用上方令牌桶机制（滑动窗口近似）。
ADMIN_FAIL_RATE, ADMIN_FAIL_BURST = 10 / 60.0, 10


def require_admin(request: Request, x_admin_password: str = Header(None)):
    """管理写操作端点依赖: 复用 ADMIN_PASSWORD 管理口令（fail-closed）
    未配置 ADMIN_PASSWORD → 503（生产默认关）; 口令不符 → 403
    爆破限流（N4, audit 2026-08-18）: 失败按 IP 计桶（10 次/分钟）——
    桶耗尽返回 429 锁定; 校验成功清桶复位（见 test_security.py 限流用例）。
    加固（审计 S3/S4）: sync/knowledge 写端点原无鉴权, 匿名可写/删/重建"""
    from admin import ADMIN_PASSWORD
    if not ADMIN_PASSWORD:
        raise HTTPException(status_code=503, detail="管理功能未配置（请设置 ADMIN_PASSWORD 环境变量）")
    import hmac
    if not x_admin_password or not hmac.compare_digest(x_admin_password, ADMIN_PASSWORD):
        # 失败计数（按 IP）: 先取桶 token; 桶空 = 该 IP 已超限 → 429 锁定
        if not _bucket("adminfail", client_ip(request), ADMIN_FAIL_RATE, ADMIN_FAIL_BURST).consume():
            raise HTTPException(status_code=429, detail="失败次数过多，请稍后再试")
        raise HTTPException(status_code=403, detail="密码错误")
    # 校验成功 → 复位该 IP 的失败计数
    _bucket_reset("adminfail", client_ip(request))
    return True


# ── 注册/登录防刷限流（P0, 2026-08-30: agent.deepphilosophy.top 公开后新增）────────
# 注册与登录此前完全无频率限制, 公开后可被脚本刷爆用户表 / 暴力破解口令。
# 按 IP 令牌桶 + 每日配额（与 agent/ai 机制同源, 独立 key 前缀避免互挤）。
AUTH_RATE, AUTH_BURST = 10, 20          # 每分钟 10 次, 突发 20
AUTH_QUOTA = 30                         # 每 IP 每日最多 30 次（注册+登录合计）


def auth_guard(request: Request):
    """注册/登录端点依赖: 防暴力破解 + 防注册垃圾（按 IP 限流 + 每日配额）
    不校验 token（注册/登录本身无 token）；仅做频率控制，不影响正常用户。
    """
    ip = client_ip(request)
    key = f"auth:ip:{ip}"
    if not _bucket("auth", key, AUTH_RATE, AUTH_BURST).consume():
        raise HTTPException(status_code=429, detail="操作过于频繁，请稍后再试")
    if not _quota_ok(key, AUTH_QUOTA):
        raise HTTPException(status_code=429, detail="今日操作次数已达到上限，请明日再试")
    return ip


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
