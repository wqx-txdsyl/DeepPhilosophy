# -*- coding: utf-8 -*-
"""V12-M1: production runtime model source-of-truth contract tests。

证明真实 PhiAgent 应用 runtime（无 evaluation 注入）的 canonical model 为
deepseek-flash。全部为真实行为测试: reload 真实模块 / 构建真实引擎 client。"""
import importlib
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TARGET = "deepseek-flash"


def test_default_or_deployed_runtime_model_is_deepseek_flash(monkeypatch):
    """repo 默认（无 AGENT_MODEL env）即 canonical: routes.agent_llm.MODEL == deepseek-flash"""
    import routes.agent_llm as L
    monkeypatch.delenv("AGENT_MODEL", raising=False)
    L2 = importlib.reload(L)
    try:
        assert L2.MODEL == TARGET
    finally:
        importlib.reload(L)   # 恢复进程级真实配置（.env 未设 AGENT_MODEL → 仍 deepseek-flash）


def test_engine_uses_runtime_model():
    """engine_langgraph.get_llm() 真实构建的 client 请求模型 == runtime MODEL
    （无任何 evaluation 注入, 真实 application config）"""
    import routes.agent_llm as L
    import engine_langgraph as EG
    assert L.MODEL == TARGET
    EG._llm = None
    EG._llm_repair = None
    try:
        llm = EG.get_llm()
        assert getattr(llm, "model_name", None) == TARGET
    finally:
        EG._llm = None
        EG._llm_repair = None


def test_repair_engine_uses_runtime_model():
    """get_repair_llm() 同样使用 runtime MODEL（production repair 路径）"""
    import routes.agent_llm as L
    import engine_langgraph as EG
    assert L.MODEL == TARGET
    EG._llm = None
    EG._llm_repair = None
    try:
        llm = EG.get_repair_llm()
        assert getattr(llm, "model_name", None) == TARGET
    finally:
        EG._llm = None
        EG._llm_repair = None


def test_no_eval_injection_required():
    """runtime model 选择不依赖 evaluation 注入: get_llm() 全程无
    o7e_candidate_config 导入发生（快照 sys.modules 前后对照, 行为级证明）"""
    import engine_langgraph as EG
    EG._llm = None
    EG._llm_repair = None
    try:
        before = set(sys.modules)
        llm = EG.get_llm()
        after = set(sys.modules)
        assert getattr(llm, "model_name", None) == TARGET
        assert not any("o7e_candidate_config" in m or "o7e_production_calibration" in m
                       for m in after - before)
    finally:
        EG._llm = None
        EG._llm_repair = None
