# PhiAgent 哲学家测试版

新增 119 位哲学家，与既有尼采合计 120 位；另有通用深哲。尼采仍使用原有 AIAuthor 数据包与 LangGraph 路径。

## 人格与运行

- 清单：`backend/philosopher_agents/catalog.json`，保存名称、传统、作者别名及原典检索线索。
- 每人唯一人格来源：`backend/philosopher_agents/{key}/soul.md`，含立场、方法、误读边界、原典与引用纪律。
- 运行：`backend/soul_agent_runtime.py`，只安装 `search_primary_texts` 和 `read_primary_text`。不加载尼采数据包、额外人格记忆、知识图谱、时期快照或 MCP 工具。
- 每个角色使用现有模型服务，不代表 119 个独立训练模型。前端显示“测试版”。

## 原典范围

本地只读现有 `app/public/books.json` 对应的 `backend/data/book_chapters/`。书名/作者匹配后仍需实际读取章节；书目不等于正文可读。没有本地正文或需要外部材料时发现公开原典候选，再读取网页。外部候选始终保留待核对状态，模型须确认作者、作品与正文，百科及评论不充作原典。来源缺失须如实说明，不能伪造引文。

苏格拉底、惠施、希帕提娅等以历史见证为主的人物，需注明记录者。现代思想家可能只有合法公开片段，不能声称所有原典全文已收录。

## 上线

沿用本机生产部署：构建 PhiAgent → 同步 `backend/static/` → 重启 `com.deepphilosophy.backend`。验证公开 `/api/agents` 为 121 个入口（深哲 + 尼采 + 119 测试角色），并检查公开 SSE 对话。该变更不修改书库与章节数据，不涉及平台 CF Pages 或 OSS 章节同步。

## 检查

`pytest backend/tests/test_soul_agents.py` 覆盖全员注册与执行、原典工具范围、跨作者隔离、外部候选、读取分页、来源展示及 SSE。现有前端测试、构建与深哲/尼采回归另外执行；这不等同全部哲学回答质量已验证。
