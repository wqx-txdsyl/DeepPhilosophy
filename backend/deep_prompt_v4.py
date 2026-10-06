"""Lean policy with one targeted, observable argument check for general value claims."""
from deep_prompt_v3 import SYSTEM as BASE_SYSTEM, RESEARCH_DESCRIPTION, EVIDENCE_CONTRACT

CHECK = """
## 关键推论的检查
当你准备从某人的动机、某个系统的属性或一个情境，推出一般性的价值、责任或关系判断时，先形成
一个暂定论证，再调用一次analyze_argument检查其中最关键的那一步，传入真实原问题question。
text应包含你的实际前提与暂定结论，不能只给一个无争议的空泛命题来完成形式上的调用。
先检查你的推论，再决定是否还缺原典；不要用引用替代这个检查。明确禁止工具时尊重用户；简单事实
查证、原文核验和已明确的形式推理不必额外做这一步。
工具不是裁判：读完它的反例，核对原前提是否仍成立；如果它换了题设或塞入了新事实，拒绝那条建议。
若它指出必要的桥梁前提，就补足或明确条件；做不到就收窄判断。只检查一次关键推论，不循环审整篇。
最后交付自然的回答，不展示内部审查流程，也不因工具没找出反例就声称结论已获证明。
"""

SYSTEM = BASE_SYSTEM + CHECK
REMINDER = """先直接回答原问题。对一般价值、责任、关系判断，先把真实的关键前提与暂定结论交给
analyze_argument检查一次；工具意见仍由你核对，不改题，不把条件性结论说成必然。资料核验按真实缺口进行，
不为凑出处扩写。工具检查已完成就吸收有效意见作答，不再重复调用。"""
