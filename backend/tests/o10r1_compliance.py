# -*- coding: utf-8 -*-
"""O10-R1 测试合规 helper: 历史回归 harness 的脚本化 Main Agent 合规化。

O10-R1 后的生产合同: 检索类工具执行前必须先 declare_research_need 登记研究需求。
历史循环回归测试（O1 因果 / O2 所有权 / O3 工具权威 / Phase A 预算 / O7E 修复收敛等）
的脚本化模型在"检索前声明"这一新合同生效前写成——comply() 把脚本转换为合规流形
（首个含工具宣告的轮次前插一条 declare_research_need, 类别按该批工具通道机械推导）,
使这些测试继续验证它们原本的命题（因果/所有权/判重/预算上限…）。

被拒绝路径（未声明/类别禁止/软预算/无新信息循环/缺口闭合）的覆盖在
test_o10_r1_research_discipline.py 显式进行——不依赖本 helper。
"""
from langchain_core.messages import AIMessage

_SCHOLARLY_TOOLS = {"search_scholarship", "get_scholarly_source"}
_WEB_TOOLS = {"websearch"}


def _class_for(tool_names):
    s = set(tool_names)
    if s & _SCHOLARLY_TOOLS or s & _WEB_TOOLS:
        return "MIXED"
    return "PRIMARY"


def comply(script, enabled=True):
    """脚本 → O10-R1 合规脚本: 在每个含工具宣告的 AIMessage 批次前插入
    declare_research_need（同批, 声明在前）。零工具轮不插——不检索无需声明。
    enabled=False（哲学家 agent harness）原样返回——检索纪律是 general 专属。"""
    if not enabled:
        return script
    out = []
    for m in script:
        tcs = list(getattr(m, "tool_calls", None) or [])
        if tcs and not (tcs[0].get("name") == "declare_research_need"):
            names = [t.get("name") for t in tcs if isinstance(t, dict)]
            decl = {"name": "declare_research_need",
                    "args": {"research_need": _class_for(names),
                             "evidence_gap": "合规 harness 声明（O10-R1 测试合同）",
                             "source_dependent": True},
                    "id": f"decl-{len(out)}"}
            out.append(AIMessage(content=m.content or "", tool_calls=[decl] + tcs))
        else:
            out.append(m)
    return out
