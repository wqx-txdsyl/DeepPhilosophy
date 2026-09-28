# 两个检索工具的实际可用性核查

日期：2026-09-28。结论：联网搜索当前链路未通过可用性检查；学术检索部分可用，但长查询会丢失候选，且存在上游限流。界面“已完成”不能代表检索成功。

方法：读取本机 backend LaunchAgent 的非敏感运行配置（PHI_RESEARCH_DB_ENABLED=1），在新进程调用生产代码的工具执行函数；使用独立空缓存，关闭学术发现记录的持久化写入。不是对线上会话的 HTTP 回放，没有调用回答模型、重启服务或修改实现。最初未带启动配置的探针走了另一条旧传输路径，出现 URL_BLOCKED，不纳入下面的运行配置结论。

## 实测

|工具|查询|结果|
|---|---|---|
|websearch|冯苇杭|0 条|
|websearch|Immanuel Kant|0 条|
|websearch|教育部 严禁教师 违规收受 礼品礼金|0 条|
|search_scholarship|gift giving reciprocity obligation in hierarchical relationships ethics|0 条；两次 OpenAlex RATE_LIMITED|
|search_scholarship|gift reciprocity|8 条，其中 6 条为 ABSTRACT_AVAILABLE；本次无 provider_errors|
|get_scholarly_source|上一条实际返回的第一条可读记录|成功取得 492 字符摘要；不是全文阅读|

简短学术查询的首批结果包含 LIVE_OPENALEX 记录：The Flow of Gifts: Reciprocity and Social Networks in a Chinese Village、The Currency of Reciprocity: Gift Exchange in the Workplace 等。这里只证明能够检索和读取摘要，不证明这些记录足以回答用户的伦理问题，也没有验收全文可达性。

## 联网链路

实际实现为 Bing HTML 解析 → 英文维基 API → 中文维基 API。不是秘塔，也不是稳定的通用搜索服务 API。

对 Immanuel Kant 的逐上游检查：

- Bing HTTP 200，但重定向到 `https://www.bing.com/?q=Immanuel%20Kant&mkt=zh-CN`，页面没有 b_algo 结果块。HTTP 成功不等于检索成功。
- 与工具一致的不带显式 User-Agent 的英文及中文维基请求，本次均收到 HTTP 403。
- 英文维基同查询加 `User-Agent: Mozilla/5.0` 后 HTTP 200，返回 4 条记录，包括 Immanuel Kant。这定位了当前请求方式的问题，不表示所有查询或所有时间都保证可用。
- 三段异常均被 `except Exception: pass` 吞掉；通用工具包装又统一成“未取得可用搜索结果”。用户无法区分拒绝访问、异常网页和真正零命中。结果还会按查询缓存 10 分钟。

相关代码：`backend/routes/agent_tools_retrieval.py` 的 `_exec_websearch` / `_websearch_inner`；`backend/deep_agent_tools.py` 的 `websearch`。

## 学术链路

截图对应的 search_scholarship 实际只调用 LOCAL_CURATED、Crossref、OpenAlex。虽然另有 research_providers 适配器声明 Semantic Scholar 和秘塔，它们不在这条主工具检索链中。当前配置检查也未发现 OpenAlex、Semantic Scholar 或秘塔专用 API key；只记录“是否配置”，未输出密钥。

长查询的 Crossref 单独复测实际返回 **8 条候选**。例如：

- Obligation, choice, and gift-giving in close relationships：标题等字段命中 4/7 查询词。
- Gift Giving, Reciprocity, and Exchange：命中 3/7。
- Gift Giving, Bribery and Corruption: Ethical Management of Business Relationships in China：命中 3/7。

`research_relevance.assess` 要求较长查询在标题/作者/别名中命中至少 ceil(词数×0.67)，该查询需要 5/7；摘要仅在包含完整查询短语时提供另一通过路径。8 条全部被标为 RELEVANCE_UNVERIFIED 并排除。它不能证明这些候选都不相关，尤其不能代表学界没有材料。

`_reformulate_query` 主要截取前六个英文词；并非语义层面的概念拆分。OpenAlex 对原查询和变体的两次限流分别写入 errors，因此截图里的重复错误有对应调用原因，不是两个独立 OpenAlex 服务。较短对照查询又能成功，不能据此断言 OpenAlex 永久不可达。

## 为什么显示“已完成”

`backend/deep_bare_agent.py` 在生成工具事件时只把顶层 error 或 accepted=false 判断为失败，其余设为 success。空 results、provider_errors 和可读记录为 0 都未参与状态判定。`GeneralAnswer.jsx` 按 success 展示勾号及“已完成”。这是事件状态语义缺陷，不是学术成功的证据。

## 修复优先级（本轮只核查，未实施）

1. 让状态区分“成功取得结果”“检索完成但未命中”“部分来源失败”“检索失败”，保留每个上游状态及缓存来源。
2. 修复联网请求与非结果页识别，返回可操作错误；维基成功仅是词条兜底，不能冒充完整网络搜索能力。
3. 将学术候选发现与相关性审阅分开，避免长查询的硬词面门槛清空候选；保留过滤原因和改写查询供审计。
4. 对限流遵守供应商返回的重试信息，配置有效凭据或合适来源；不要靠无意义重复调用绕过限制。
5. 分别验收搜索、读摘要和读全文，不能因为注册了工具或返回书目就算全部可用。

原始工具返回及诊断见 `search_tool_audit_20260928/`。这些是当次观察，不是长期可用率测量。
