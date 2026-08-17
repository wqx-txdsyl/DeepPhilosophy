# -*- coding: utf-8 -*-
"""统一鉴权依赖（S15, audit 2026-08-17）: 收敛 auth_routes/history/account/guard
四处重复的 Bearer token 解析——改鉴权逻辑只需改这一处。
- auth_required : 强制登录依赖（无/无效 token → 401），供需登录端点使用
- resolve_user  : 可选登录解析（无/无效 token → None），供限流/匿名降级使用（guard 原实现）
"""
from fastapi import Header, HTTPException

from auth import get_user_by_token


def resolve_user(authorization):
    """可选登录解析: Bearer token → user dict; 无 token / 无效 token → None（不抛错）"""
    if authorization and authorization.startswith("Bearer "):
        try:
            u = get_user_by_token(authorization[7:])
            if u:
                return u
        except Exception:
            return None
    return None


def auth_required(authorization: str = Header(None)) -> dict:
    """强制登录依赖: 无 token 或 token 无效 → 401（行为与原 4 处复制实现完全一致）"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    token = authorization[7:]
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    return user
