# 现有 PhiAgent 能力对照与毕业验收

这张表区分“课程实验已提供”和“完整复刻需要你完成”。写作时读取的是当前工作区源码；它可能包含尚未发布的修改。正式对照需冻结目标部署与 commit。

## 逐层能力矩阵

| 能力 | 现有源码入口 | 课程位置 | 实验交付 | 完整复刻验收 |
|---|---|---|---|---|
| Python 服务与路由 | [main.py](../../backend/main.py) | 02—05 | 独立 FastAPI 服务 | 目标接口契约一致、错误状态一致 |
| Agent 注册与列表 | [agents.py](../../backend/agents.py) | 17、22 | 讲解与设计作业 | 运行时角色列表、元数据与权限一致 |
| 模型适配 | [agent_llm.py](../../backend/routes/agent_llm.py) | 10 | mock / HTTP 适配与替身测试 | 真实模型协议、限流、上下文和费用验证 |
| 工具注册 | [agent_core.py](../../backend/routes/agent_core.py) | 12 | 两个可执行工具 | 对照运行时完整清单迁移 |
| 图编排 | [engine_langgraph.py](../../backend/engine_langgraph.py) | 13 | 有界图、定制流事件 | 分支、状态、异常与恢复符合目标 |
| SSE 与心跳 | [agent_sse.py](../../backend/routes/agent_sse.py) | 08、20 | SSE 与取消；无生产心跳 | 代理环境不断流、断线清理、完成语义明确 |
| 会话工作区 | [AgentPage.jsx](../../agent-app/src/pages/AgentPage.jsx) | 09、27 | 两个基础客户端 | 新建、删除、切换、重命名、草稿与恢复 |
| 流式状态归属 | [generalStream.js](../../agent-app/src/data/generalStream.js) | 08、27 | reducer 练习与竞态测试 | 双会话并行、迟到事件、停止重发不串写 |
| 本地历史 | [conversationStore.js](../../agent-app/src/data/conversationStore.js) | 05、09 | SQLite 成功历史 | 迁移、异常恢复、身份切换语义一致 |
| 登录与多用户 | [auth.jsx](../../agent-app/src/auth.jsx)、[auth.py](../../backend/auth.py) | 20 | 架构与验收，不含可公网登录实现 | 可信身份、资源归属、会话撤销与越权测试 |
| 书目与章节 | [agent_tools_retrieval.py](../../backend/routes/agent_tools_retrieval.py) | 16 | 只读真实书库适配器 | 全库、占位、目录、章节窗口和定位正确 |
| 关键词与向量 | [deep_agent_tools.py](../../backend/deep_agent_tools.py) | 14 | 关键词演示、融合数学练习 | 真实 embedding、索引版本、召回与排序评测 |
| 哲学家 / 流派 / 图谱 | [agent_tools_retrieval.py](../../backend/routes/agent_tools_retrieval.py) | 16、22 | 原理与复刻作业 | 名称别名、数据关联、空结果和引用可追溯 |
| 引用定位 | [agent.py](../../backend/routes/agent.py) | 15 | id 校验与材料展示 | 点击跳转到正确书籍、章节和原文块 |
| 逐字引语绑定 | [quote_bound.py](../../backend/quote_bound.py) | 15 | 子串匹配练习 | 归一映射、版本、跨块与不匹配分类 |
| 执行事实登记 | [evidence_contract.py](../../backend/evidence_contract.py) | 15、21 | 本轮已读材料字典 | 不把搜索摘要、失败或自述算作已读证据 |
| 回答检查与修复 | [deep_answer_review.py](../../backend/deep_answer_review.py) | 15 | 基础拒绝，修复作为作业 | 有限修复、重新验证、无新增伪证据 |
| 哲学家人格 | [agents.py](../../backend/agents.py) | 17 | 数据模型与接入作业 | 人格资产、思想时期、引文与模拟标识 |
| 长期记忆 | [deep_context.py](../../backend/deep_context.py) | 17 | 用户范围 SQLite 练习 | 偏好提取、更新、删除与跨用户隔离 |
| 辩论 / 角色扮演 | [agent_tools_memory.py](../../backend/routes/agent_tools_memory.py) | 17、28 | 状态设计与复刻作业 | 开始、继续、总结、结束的完整状态机 |
| 苏格拉底 / 顾问 / 论证 | [agent_tools_eval.py](../../backend/routes/agent_tools_eval.py) | 28 | 功能包实作方法 | 输入、状态、证据、输出与失败分支逐项通过 |
| 写作 / 论文 / 提纲 | [agent_tools_eval.py](../../backend/routes/agent_tools_eval.py)、[agent_tools_memory.py](../../backend/routes/agent_tools_memory.py) | 28 | 模板与作业 | 输出能追溯资料，区分建议与事实 |
| 学术来源 | [agent_tools_scholarly.py](../../backend/routes/agent_tools_scholarly.py) | 18 | 研究协议与作业 | 元数据、摘要、全文与访问状态准确 |
| 网页研究 | [deep_web.py](../../backend/deep_web.py) | 18、19 | 设计与边界 | 搜索、读取、重定向、来源与权限正确 |
| 研究预算与去重 | [research_discipline.py](../../backend/research_discipline.py)、[agent_runtime.py](../../backend/agent_runtime.py) | 12、18 | 有界循环、读取额度练习 | 重复复用、参数变化放行、故障恢复与预算终止 |
| 文件上传 | [upload.py](../../backend/routes/upload.py) | 19 | 分步施工任务 | TXT / EPUB / PDF / OCR 按支持范围验收 |
| 图片与图表 | [agent_assets.py](../../backend/routes/agent_assets.py)、[DrawioInline.jsx](../../agent-app/src/components/DrawioInline.jsx) | 19、28 | 产物契约与作业 | 图片真实存在、图表可渲染、归属正确 |
| MCP 接入 | [mcp_client.py](../../backend/mcp_client.py) | 19 | 适配步骤 | 工具发现、调用、超时、权限、错误归一 |
| 评测与诊断 | [evaluation_suite.py](../../backend/evaluation_suite.py) | 21、23 | 离线 runner、单元与协议测试 | 真实模型冻结题集、人工抽样、质量成本延迟 |
| 前端构建与发布 | [agent-app/package.json](../../agent-app/package.json) | 20 | React 构建通过 | 正式托管、API 代理、移动端与回滚验证 |
| 书库生产同步 | [分章标准规范](../分章标准规范.md)、[项目规范](../../AGENTS.md) | 16、20 | 只读讲解 | CDN / OSS / 本地镜像一致，生产引用实际可达 |

> 此文件位于 `docs/course/`，表内源码链接以仓库为目标。若导出到别处，应一并保留源码或使用你冻结的 Git commit 链接。

## 功能是否完成的记录模板

```text
能力名称：
目标版本 / commit / 数据版本：
用户输入与操作步骤：
预期行为：
我的实现位置：
自动测试：
人工验收记录：
与原版差异：
未完成项：
```

## 毕业关卡

### G1：语言与链路

- [ ] 不看源码重写两个工具与有界循环。
- [ ] 能解释 Python 对象、异步、异常与资源生命周期。
- [ ] 能用 JS 写表单、fetch、流式解析和不可变更新。
- [ ] 能定位一次从浏览器到工具再到数据库的请求。

### G2：完整产品复刻

- [ ] 冻结目标版本和运行时工具清单。
- [ ] UI、协议、数据兼容和所有目标功能都有验收记录。
- [ ] 真实书库、人格资产与外部服务已经准备。
- [ ] 跨用户、跨会话、断流、失败与恢复测试通过。
- [ ] 关键原典引用能从正式页面点击核查。
- [ ] 部署、监控、回滚和数据迁移可复现。

### G3：超越原版

- [ ] 看结果前确定主要指标与代价预算。
- [ ] 冻结保留测试集，避免泄漏到调参过程。
- [ ] 相同条件成对比较，并报告按题型结果。
- [ ] 人工检查典型成功与失败案例。
- [ ] 没有用更长回答、更多工具调用代替质量证据。
- [ ] 结论注明范围、模型、资料、样本量与不确定性。

完成 G1 说明掌握核心链路；完成 G2 才可称完整复刻；G3 的实验支持改进后，才能在对应指标上称超越。
