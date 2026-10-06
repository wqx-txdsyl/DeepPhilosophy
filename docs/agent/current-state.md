# 当前Agent状态

更新时间：2026-10-03。本页是本轮协作的入口，不宣称核查了所有线上实例。

通用深哲登记提示词为v0.1.5，工具契约0.1.2，默认bare运行，工具总预算为null。实际生产进程是否已重载应以版本接口为准；本轮整理没有修改运行逻辑或重启服务。

接口入口是[engine_langgraph.py](../../backend/engine_langgraph.py)，general默认委托[deep_bare_agent.py](../../backend/deep_bare_agent.py)。因此不能仅凭入口文件名判断运行的是旧controlled LangGraph闭环。版本配置在[agent_release.json](../../backend/agent_release.json)。

现有RUN1–RUN6与外部答卷已登记。主表为冻结R1：同一60道分析与研究题，单一总分；5道纯核验单列，5道故障fixture未跑。原始题集、量尺及已有等级保留，R1不是受控模型能力排行。

v0.1.2的总分高受评审覆盖与运行混杂影响，不能据此认定应该回滚。当前证据仍显示动机归因、条件扩大和材料桥接问题。[比较说明](../evaluation/version-comparison.md)有具体依据。

本阶段先完成文档整理；尚未追加v0.1.6，也不自动进入v0.2.0工具调优。下一步由用户确定优化范围，依据已核缺陷，不以一次总分波动替代分析。
