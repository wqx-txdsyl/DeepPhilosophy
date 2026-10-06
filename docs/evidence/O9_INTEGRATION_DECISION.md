# O9 Integration Decision — MetaSo / Research Retrieval

> DECISION = **CONDITIONAL_PROVIDER**（DECISION_EVIDENCE_COMPLETE=false：MetaSo 实测双腿因无
> credential 暂停；OpenAlex 腿因外部日配额耗尽暂停——两者均为外部硬约束，非测量结论缺失于己方）

## 1. 测量基础（同一冻结 30-query set, TOP_K=10）

| 配置 | 状态 | TOP_K_RELEVANCE | DOI | 可读证据(abstract) | 元数据完整 | 重复率 |
|---|---|---|---|---|---|---|
| A = Crossref | ✅ 完成 | 0.89 | 1.00 | 0.26 | 0.79 | 0.03 |
| B = OpenAlex | ⛔ 外部配额（429, Remaining=0, Retry-After=31830s） | — | — | — | — | — |
| C = Crossref+OpenAlex | ⚠️ 退化为 A（B 腿被阻） | 0.89 | 1.00 | 0.26 | 0.79 | 0.03 |
| D = MetaSo | ⛔ AUTHENTICATION_REQUIRED（无 credential） | — | — | — | — | — |
| E = MetaSo+C+O | ⛔ 同 D | — | — | — | — | — |

分类别（Crossref）：西文 1.00 / 争议综述 1.00 / 罕见非西方 0.97 / 中文哲学 0.817 /
跨语言书目 0.65——中文与跨语言书目正是基线的相对弱区，也是 MetaSo 合同的潜在强区。

## 2. 决定与理由

**CONDITIONAL_PROVIDER（条件路由，条件未满足前不集成）：**

1. **合同审计**（O9_API_CONTRACT.json）：MetaSo = 中文 AI 搜索 + 网页阅读 + RAG 问答。
   无结构化书目元数据合同（DOI/venue/year/authors）→ 对 PhiAgent 的 scholarly 结构化层
   无可证增益，不应替代 Crossref/OpenAlex。
2. **潜在增益点（合同推断，未实测）**：中文网页/文档/论文多域发现（scope=paper/document）
   + metaso_web_reader 原文阅读 → 可能改善中文学术发现与可读证据率（基线弱区 0.817/0.65/0.26）。
3. **不能 INTEGRATE**：无 MetaSo 实测数据（auth 阻断），不满足「稳定、实质增益」标准。
4. **不能 REJECT**：同样缺少实测反驳；且合同强项恰好对准基线弱区，证据不支持全盘排除。
5. **条件（满足后才可升级/降级）**：
   a. 用户提供 MetaSo API key（用户决策项，credential 属 Human Decision Gate）；
   b. 以同一 30-query set 补测 D/E（metaso_web_search scope=paper/document，Top-K=10 对齐）；
   c. 增益判准：中文类/跨语言类 TOP_K_RELEVANCE 或可读证据率相对基线 ≥10 个百分点的稳定提升，
      且元数据/重复率无恶化。
6. **集成形态（若条件满足）**：按任务书 §5 目标架构，MetaSo 仅作为 External Retrieval Layer 的
   条件路由 provider（中文/跨语言发现 + reader 原文抓取），绝不作为回答大脑（metaso_chat 不路由）。

## 3. 边界与诚实声明

- B 腿：OpenAlex 共享出口 IP 日配额耗尽（X-RateLimit-Remaining: 0 / Retry-After 31830s，
  实测响应头归档于 O9_COMPARISON.json）——外部硬墙，恢复后需重测 B/C。
- MetaSo 无凭证实测错误行为已归档（JSON-RPC -32603「API密钥无效」）。
- COST=null / COST_SOURCE=UNAVAILABLE（两 provider 均无公开定价来源）。
- O8 发现全部冻结未动（无 production 变更；O9 仅 evaluation-only 脚本 + docs/evidence）。
