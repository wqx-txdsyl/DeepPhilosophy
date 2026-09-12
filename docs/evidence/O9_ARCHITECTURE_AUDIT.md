# O9 Architecture / Contract Audit — MetaSo / Research Retrieval

> as of 2026-09-12；官方来源见 O9_API_CONTRACT.json。
> 结论先行：MetaSo 是「中文 AI 搜索 + 网页阅读 + RAG 问答」的 MCP 服务，**不是结构化书目元数据 API**。
> 无 credential 可用 → METASO_AUTH_REQUIRED=true，MetaSo 实测部分暂停（符合任务书 §7）。

## 1. MetaSo（秘塔）研究编排分析

产品矩阵：metaso.cn（AI 搜索：简洁/深入/深度研究模式）、metaso_web_reader（URL 阅读）、
metaso_chat（RAG 问答）、API/MCP 开放（官方 @metasota 注册于 ModelScope，端点 https://metaso.cn/api/mcp，
更新 2026.09.11，52.0k 引用）。

research orchestration 能力对照（任务书 §1 各项）：

| 能力 | MetaSo 合同事实 |
|---|---|
| search | metaso_web_search: q + scope(webpage/document/paper/image/video/podcast) + size(默认10) |
| scholar | scope=paper 模式；无 DOI/venue/year/authors 结构化书目字段文档化 |
| document/library | scope=document + includeRawContent 抓原文；无个人 library API 文档 |
| reader | metaso_web_reader: url → json/markdown（可读证据层，强项） |
| deep research | 主站「深度研究」模式未开放 API 合同 |
| multi-query | 无多查询编排合同字段 |
| source ranking | 未文档化排序合同（黑盒） |
| citation | 未文档化结构化引用字段 |
| API/MCP | MCP over HTTP, JSON-RPC 2.0, Bearer 认证 ✓（实测端点存活） |

## 2. API Contract 实测/核对（2026-09-12 事实）

- 认证：Bearer API key（key 控制台 https://metaso.cn/search-api/api-keys，需注册登录）。
- **无凭证实测**：POST tools/list → `{"error":{"code":-32603,"message":"Internal error: API密钥无效"}}`
  ——端点存活、路由正常、无 key 被拒。
- 配额：官方提示存在调用配额限制，数值未公开。
- 成本：无公开定价来源 → COST=null / COST_SOURCE=UNAVAILABLE。
- 条款：metaso.cn/meta-user-policy（用户协议存在）；缓存/再分发合同未细化文档化。

## 3. 与 PhiAgent External Retrieval Layer 的映射

目标架构（任务书 §5）：Main Agent → External Retrieval Layer(Crossref/OpenAlex/MetaSo) →
Evidence Store → Reasoning。Provider finds material; PhiAgent judges/reads/compares/answers。

- **结构化书目层（DOI/venue/year/作者）**：Crossref/OpenAlex 已覆盖（O9 基准：Crossref
  DOI 覆盖 1.00、相关性 0.89、元数据完整率 0.79）。MetaSo 合同不提供结构化书目字段 → 此层无增益证据。
- **可读证据层（原文抓取/阅读）**：MetaSo metaso_web_reader + includeRawContent 是合同强项；
  与 PhiAgent get_scholarly_source 的 access 四态阅读器同域，可能提升中文来源的可读证据率。
- **中文学术发现层**：scope=paper 的中文学术覆盖是 Crossref/OpenAlex 的已知弱区
  （O9 基准：Crossref 中文类查询相关性 0.817，低于西文 1.00；跨语言书目类 0.65）——
  MetaSo 可能有优势，**但需要 credential 后实测**。

## 4. 凭证状态

当前环境无 MetaSo credential（.env 无 METASO* 键）。按任务书 §7：
AUTHENTICATION_REQUIRED=true——仅暂停需认证的 MetaSo 实测（D/E 配置），公开架构/合同/基线
provider 工作已全部完成。获取 credential（注册账号+申请 key）属用户决策项
（AUTONOMOUS_HANDOFF_CONTRACT human_decision_gate: credential/authentication）。
