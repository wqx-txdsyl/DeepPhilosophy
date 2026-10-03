# DeepPhilosophy × PhiAgent NOWSTATE（当前状态快照）

> 生成：2026-08-14 · 单仓库双应用（平台 + 智能体 + 书库工具链）
> 完整文件树见 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)，项目总览见 [README.md](../README.md)

---

## 1. 这是什么

| 组成部分 | 说明 | 运行方式 |
|---|---|---|
| **平台**（`app/`） | 哲学知识平台：402 部原典在线阅读 / 737 哲人（以 backend/data/philosophers.json 为准）/ 111 流派 / AI 问答 | 生产：Cloudflare Pages（deepphilosophy.top）；本地：Vite :5173 |
| **智能体**（`agent-app/` + `backend/`） | LangGraph 哲学智能体：深哲（30 工具）+ 尼采（AIAuthor 六库数字人格） | 本地：后端 FastAPI :8011 + Vite :5201 |
| **书库工具链**（`backend/tools/`） | 402 部原典数字化：导入/OCR/章节重建/向量化/同步/部署管线 | 命令行，`.venv` 运行 |
| **生产 API**（`workers/`） | Cloudflare Workers（auth + api，Hono + D1），零传统服务器 | 云端 |

## 2. 本地服务（当前正在运行）

| 端口 | 服务 | 启动命令 |
|---|---|---|
| 8011 | 统一后端（智能体 + 平台 API） | `cd backend && python main.py`（Python 3.12+，依赖见根 `requirements.txt`） |
| 5173 | 平台前端 | `cd app && npm run dev`（`/api` 代理 → 8011） |
| 5201 | 智能体前端 | `cd agent-app && npm run dev`（`/api` 代理 → 8011） |

## 3. 生产架构与数据流

```
浏览器 ──→ Cloudflare Pages（平台前端）── 章节：OSS CDN 优先 + jsDelivr 兜底
                                      └── API：Cloudflare Workers（auth + api，D1）
数据流（单向）：backend/tools/ 构建 → backend/data/book_chapters（git 唯一章节源）→ CDN → 前端只读
```

- **数据库**：生产 = D1 `deepphilosophy-db`；本地 = SQLite（同 schema）→ [docs/DATABASE.md](DATABASE.md)
- **智能体数据**：`data/ai_author/`（1.6GB，gitignore，仅本地）+ `backend/data/embeddings/`（向量索引）

## 4. 部署流程（平台生产）

1. `git push origin master` → CF Pages 自动构建 `app/`
2. 改了 `app/` 源码时：CF 构建完成后
   `python backend/tools/dp_grab_cf_assets.py https://deepphilosophy.pages.dev --upload`
   （管线自带重试 + 完整性校验 + OSS 逐引用校验，缺失即报错）
3. 纯 `backend/`、`data/`、`tools/` 改动**无需**同步 OSS（commit hash 已解耦：postbuild 注入
   `<meta name="dp-commit">`，JS 包内容跨 commit 稳定，章节 CDN 引脚随构建自动更新）

## 5. 安全现状（2026-08-14 已落地）

**已修复**：
- agent 4 端点：鉴权（可选登录）+ 限流 + 每日配额（`backend/guard.py`，agent 10/min·突发20 / upload 20/min·突发40；匿名 60 次/日、登录 300 次/日）
- 全局记忆 per-user 隔离（作文/生图/实验/辩论按用户分槽 + 原子写）
- Workers 密码 PBKDF2（10 万次）+ 登录/注册限流 + admin 改 header 恒定时间比较
- 路径穿越修复：`read_chapter` bid 白名单 / `serve_spa` resolve 约束 / upload 文件名消毒
- 旧引擎删除（-550 行，仅 stream_lg）；错误脱敏；`auth._sync_db` 整库上传 GitHub 禁用
- 硬检索上限不再丢弃已宣告的工具调用（补执行一轮再强制结束）

**遗留待办**：
- [ ] OSS 566 个孤儿对象清理（破坏性，需确认）
- [x] 日志统一（loguru 清理残留 `print`）—— 2026-08-15 核心服务代码已清，`tools/` CLI 脚本 print 属正常用法保留
- [x] 前端 TOOL_META 图标覆盖补齐 —— 2026-08-15 补齐 13 个缺失工具，覆盖后端全部 30 工具
- [ ] 端到端 UI 回归（沙箱已验协议层，交互层待人工）
- [ ] "原典模式" UI 开关（提示词版「📖 原典路径」已上线）
- [ ] 前端 react-hooks 新规则告警清理（26 项，涉及行为需谨慎分批处理）

## 6. 智能体能力现状

- **深哲**：30 工具（原典检索/思辨/写作/疏导/生图/脑图），LangGraph 流式引擎（`engine_langgraph.py`）
- **尼采**：AIAuthor 六库人格（23 著作 6488 chunks 语料 / 1296 实体图谱 / 564 记忆 / 早中晚期快照）
- **证据纪律**（提示词铁律 9-12）：证据分级（记忆≠已核验原文）/ 区分四层（事实·解释·争议·判断）/ 原典路径 / 跨哲人关联
- **引用**：正文【《书名》·章节】可点击 → 阅读器定位；`/api/cite` 未匹配返回 `matched:false`
- **记忆持久化**：对话 localStorage 按智能体分开（`dp_agent_msgs_{agent}`）；多轮修改记忆 per-user 存 `backend/data/agent_memory.json`

## 7. 记录持久化现状（回答"会不会丢记录"）

| 场景 | 平台（app/） | 智能体（agent-app/） |
|---|---|---|
| 本地主存储 | `dp_userdata` localStorage（聊天≤500条 + 阅读进度）+ `dp_chat_sessions` | `dp_agent_msgs_{agent}` localStorage（2026-08-14 修复，此前仅内存） |
| 云端同步 | 登录后 fire-and-forget POST（阅读/聊天），ProfilePage 可读回合并 | 登录后逐条 POST `/api/history/chat`，登录时读回 |
| 后端重启 | **不丢**（localStorage 为主，云端在 D1/SQLite） | **不丢**（localStorage 为主） |
| 会丢的情况 | 匿名 + 清浏览器缓存/换设备；云端 POST 失败静默（无重试队列） | 同左；换浏览器/设备无云端读回前丢失 |

## 8. 近期变更（2026-08-14）

- 双仓库合并为单仓库（PhiAgent → agent-app + 统一 backend + data/ai_author），旧 PhiAgent 目录已清理
- 部署管线加固（完整性校验 + commit hash 解耦），修复两次"OSS 资产漏传白屏"
- 安全 P0 全套落地（见 §5）
- 旧引擎删除 + 引擎补执行修复 + 话题建议注入主题 + 对话 localStorage 持久化
- 提示词升级：证据分级 / 原典路径 / 层次区分 / 跨哲人关联

### 8.1 代码质量与一致性修复（2026-08-15）

- **安全**：admin 密码比较改 `hmac.compare_digest`（main.py + routes/admin_routes.py）；auth/api worker CORS 从 `*` 收紧为域名白名单；electron 静态服务加路径穿越防护
- **密码哈希统一**：本地 SQLite 从 scrypt 改为 PBKDF2（10 万次，与 Workers 生产一致），旧 scrypt / SHA-256 登录时自动升级（`backend/auth.py`）
- **凭据**：`scripts/ai_verify_portraits.py` 硬编码 Agnes Key → 从根 `.env` 读取
- **日志**：核心服务代码 print 残留 → loguru（auth/config/engine_langgraph/routes.agent/routes.ai/routes.text/mcp_client/llm_client）；裸 `except: pass` 补日志
- **前端真 bug**：`BookDetailPage.jsx` 缓存键 `ck` 未定义（本地回退路径卡 loading）→ 修复为 `book_v2_{bookId}`；`tagMaps.js` 6 处重复键清理
- **标签映射同步**：`app/src/data/tagMaps.js` 与 `backend/data/tag_normalization.json` 合并统一（194/28/17 键零差异），消除前后端筛选/分类不一致

### 8.2 架构与数据运维（2026-08-15）

- **main.py 拆分**（2209 行 → 160 行装配）：books/authors/upload/account 拆为 `routes/` 新模块；main.py 只保留 app 创建 + 中间件 + SPA + 路由注册。顺带修复 `services/book_scanner.py` 潜伏 bug（`_classify_book`/`_book_sort_key`/`_load_summaries_cache` 未定义——此前该模块从未真正生效，main.py 的旧实现遮蔽了它）；routes/ai.py 新版（thinking 模式/ASR）此前被 main.py 旧版遮蔽，现在真正生效
- **前端 lint 债务**：no-unused-vars 43 处 + no-empty 26 处清零（含 HomePage 7 个死代码块 ~230 行删除）；`no-empty` 配置 `allowEmptyCatch` 表达刻意容错；剩余 26 项为 react-hooks 行为类规则（purity/set-state-in-effect 等），涉及行为变更留待分批处理
- **agent-app React 18→19**：`react@19.2.8` + `react-dom@19.2.8`（react-drawio peerDeps 已含 ^19），构建通过
- **scripts/ 归档**：24 个一次性脚本 `git mv` 至 `scripts/archive/`（fetch_philosopher_img/gen_portrait 虽标归档但被 .claude/skills 引用，保留原位）；修复 archive/fix_map_coords.py 的 `_lib` 导入路径
- **Git LFS**：新增 `.gitattributes`——大 JSON（philosophers/books/philosopher_network/book_summaries）走 LFS，章节 JSON 刻意不走（工具链频繁重写）；不迁移历史
- **TOOL_META 图标补齐**：agent-app 前端补齐 13 个缺失工具图标（socratic_tutor/analyze_argument/concept_trace/conceptual_map/confrontation/dialectic/essay_outline/history_timeline/life_coach/profile/role_play/school_arena/agent_council），覆盖后端全部 30 工具，不再走通用 icon-cog 回退
- **数据一致性**：补 2 本 txt 占位书缺的 `book_detail`，同步 `src/assets/books.json`，`dp_consistency_check.py` 本地 PASS
- **`.gitignore` 编码修复**（乱码行清理，UTF-8）

## 9. 文档索引

| 文档 | 位置 | 内容 |
|---|---|---|
| 项目总览 | [README.md](../README.md) | 功能/架构/开发/部署 |
| 全文件结构 | [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | 完整文件树（gen_structure.py 生成） |
| 数据库规范 | [docs/DATABASE.md](DATABASE.md) | D1/SQLite schema、迁移流程 |
| 工具索引 | [backend/tools/TOOLS_INDEX.md](../backend/tools/TOOLS_INDEX.md) | 书库工具分类与状态 |
| 书库台账 | [backend/tools/CHKLIST.md](../backend/tools/CHKLIST.md) | 402 本逐本验收 |
| OCR 质检 | [backend/tools/OCR_CHECKLIST.md](../backend/tools/OCR_CHECKLIST.md) | OCR 质量清单 |
| 章节规范 | [backend/tools/分章标准规范.md](../backend/tools/分章标准规范.md) | 章节 JSON 结构 |
| 开发规范（本地） | `.claude/CLAUDE.md`（gitignore，不入库） | 项目约定与红线 |

## 10. 备注：根目录 log 文件

仓库根目录**没有** log 文件（`*.log` 已在 .gitignore）。若在工作区根看到 `_srv_backend.log` /
`_srv_agent.log` / `_srv_app.log`，那是本地 dev 服务的 stdout 捕获（非项目文件，可随时删除）；
`app/vite-debug.log` / `vite-debug.err.log` 为 vite 遗留调试日志（gitignore，可删）。
