# 第 28 章：亲手实现一个超出聊天的功能——哲学观点比较

本章示范完整产品能力的开发方法。做懂这一包后，你可以用同样结构实现苏格拉底导师、论证分析、论文评阅和时间线。

## 28.1 把自然语言需求转换为契约

需求：比较 A 与 B 对主题 T 的观点，呈现共识、分歧、支持材料和适用限制。明确失败：人物不存在、题目过宽、一方资料缺失、资料冲突、超时。

输入模型：

```python
from pydantic import BaseModel, Field, ConfigDict

class CompareInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    thinker_a: str = Field(min_length=1, max_length=80)
    thinker_b: str = Field(min_length=1, max_length=80)
    topic: str = Field(min_length=2, max_length=300)
```

这里验证形式，不宣称名字一定对应真实哲学家。下一步用人物注册表解析，遇到重名或别名要返回明确结果。

## 28.2 证据先于比较结论

分别检索两方；读取相关文本；给材料分配系统生成 evidence_id；必要时检索二手解释；然后生成结构化比较。没有 B 的证据时，可以输出“B 暂无足够依据”，不能为了表格对称补造观点。

预期输出结构：topic、participants、dimensions、agreements、disagreements、limitations、sources。每个比较维度包含两方的论断和各自的证据 id。

## 28.3 保持领域函数与 HTTP 解耦

设计一个 `compare_views(input, repository, model)` 服务函数。HTTP 路由、Agent 工具和后台评测都调用同一个服务，而不是复制三份提示词。服务返回领域结果，协议适配层决定怎样流式展示或保存。

独立检索可以并行，但后续生成依赖检索完成。使用有界并发，保留某一方失败的状态。并发异常不能吞掉另一方已经取得的材料。

## 28.4 两阶段生成与验证

先生成结构化结果，验证所有 evidence_id 都存在于已读集合；逐条检查重要引语；然后渲染为表格或卡片。模型输出 JSON 失败时有限次修复；仍失败则返回可诊断错误。

不要把“两个 Agent 分别扮演两位哲学家”当作必要前提。一次模型生成也能完成比较，多角色讨论是否提高质量需要对照实验。

## 28.5 前端组件

`ComparisonCard` 接收验证后的数据，渲染维度和来源按钮。点击来源使用系统 id 查询证据详情，不让模型提供任意可执行链接。没有来源的维度显示未核实状态。

长比较可以分区折叠；保留普通文字版本，方便复制与阅读器使用。不要只生成一张图片，否则文字检索、复制和可访问性都会受损。

## 28.6 测试样例

- 两方均有材料：每个核心维度有对应依据。
- 一方无材料：明确不完整，不补造。
- 模型返回未知 id：验证失败，不能呈现为可信引用。
- 返回格式不合法：有限修复且有上限。
- 重复请求：幂等结果或明确的运行状态。
- 跨会话并行：产物归属正确。
- 用户改题：新调用不能覆盖旧题的已保存产物。

## 28.7 从这一包迁移其他能力

论文评阅的领域结果变成 claim、objection、suggestion；苏格拉底导师变成 concept、student_answer、next_question；时间线变成 event、date_precision、source；概念图变成 nodes、edges、relation、evidence。

生成图片工具则增加外部任务 id、轮询、产物存储和失败恢复。它与检索工具共享调用框架，但重试和副作用策略不同。

## 28.8 你的交付

实现该功能包的输入模型、服务函数、工具注册、API、前端卡片和测试；对照真实 `agent_tools_eval.py` 的 compare_views 分析差异。写一页说明：你保留了哪些行为、改进了什么、哪些尚未达到原版。

完成这一步才算掌握一个完整功能，而不只是会调用一次模型。

<!-- NAV -->

[课程目录](../README.md) · [上一章](27-javascript-typescript.md) · [下一章](29-graduation-project.md)
