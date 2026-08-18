# DeepPhilosophy「深哲」× PhiAgent

> 横跨五千年的人类思想史长卷 —— 402 部哲学经典 · 737 位哲学家 · 111 个哲学流派 · 一个能对话、思辨、创作的哲学智能体

**单仓库双应用**（2026-08-14 合并）：`app/` 是开放的哲学知识平台（阅读/探索/问答，生产部署在 [deepphilosophy.top](https://deepphilosophy.top)）；`agent-app/` + `backend/` 是哲学智能体平台（LangGraph 驱动的「深哲」与由 AIAuthor 六库数字人格构建的「尼采」）；`backend/tools/` 承载 402 部原典的数字化工序（导入/OCR/章节重建/向量化/同步）。

---

## 📖 平台功能（deepphilosophy.top）

- **402 部哲学经典在线阅读**：312 本结构化章节 + 书内插图，章节走 OSS/jsDelivr 双轨 CDN（秒开级加载），阅读中可 AI 批注、与书对话
- **737 位哲学家 / 111 个流派**（哲学家数以 `backend/data/philosophers.json` 实际条目数为准，2026-08-18 核对）：肖像画廊（地区/流派/时代筛选）、流派谱系时间轴、思想星丛关系网络、概念跨书溯源
- **AI 问答**：DeepSeek 流式对话（思考过程可见）、深度思考模式、支持自配 API Key 直连
- **思想游戏**：答案之书、PHTI 哲学人格测试
- **账号云同步（可选）**：阅读进度/对话/批注跨设备；PWA 可安装为桌面应用

## 🤖 智能体平台（PhiAgent）

- **深哲（通用）**：30 工具全量——原典检索/思辨（苏格拉底追问、辩论、流派 PK）/写作/疏导/生图/概念脑图
- **尼采（哲学家）**：AIAuthor 六库数字人格（23 本著作 6488 chunks 语料、1296 实体知识图谱、564 条记忆、早/中/晚期人格快照）——以本人人格思考作答，引文全部来自真实原典
- **流式体验**：思考流逐字流出 → 并行工具调用卡片 → o1 风格推理摘要 → 出处【《书名》·章节】点击跳转原典阅读器
- **评估与护栏**：四维评估基准、安全护栏（拦教唆不拦批判）、请求监控 JSONL、话题延续建议

## 🏗 技术架构

```
浏览器 ──→ Cloudflare Pages（平台前端）── 章节：OSS CDN 优先 + jsDelivr 兜底
                                      └── API：Cloudflare Workers（auth + api，D1）
本地 ──→ agent-app（Vite :5201）── backend（FastAPI :8011，智能体 + 书库工具）
```

- **平台生产**：React 19 + Vite → Cloudflare Pages；API 全在 Workers（Hono + D1），零传统服务器
- **智能体**：LangGraph 流式编排（`backend/engine_langgraph.py`）+ DeepSeek thinking 模式
- **数据流（单向）**：`backend/tools/` 构建/修复 → `backend/data/book_chapters`（git 跟踪，唯一章节源）→ CDN 分发 → 前端只读
- **Worker 静态资产**：`workers/api/src/books.json` 是 **CDN manifest**（书 id → OSS/GitHub 文件直链映射，`backend/tools/generate_worker_assets.py` 从 `oss_manifest.json` + `github_manifest.json` 生成），与 `app/public/books.json`（前端书单，`dp_sync_books.py` 生成）是两份不同结构/来源/用途的文件，**非重复副本**（N7，2026-08-18）
- **数据库**：生产 = D1（`deepphilosophy-db`）；本地开发 = SQLite（同 schema，见 [docs/DATABASE.md](docs/DATABASE.md)）

## 🛠 本地开发

```bash
git clone git@github.com:wqx-txdsyl/DeepPhilosophy.git
cd DeepPhilosophy

# 后端（智能体 + 平台 API，端口 8011；Python 3.12+，依赖见 requirements.txt）
python -m pip install -r requirements.txt
cd backend && python main.py
#   管理写操作端点（/api/sync/upload、/api/sync/delete、/api/knowledge/init）鉴权:
#   在 backend/.env 设置 ADMIN_PASSWORD=你的口令（未设置时这些端点默认 503 拒绝），
#   请求时带请求头 X-Admin-Password: 你的口令 即可启用（与 /api/admin/stats 同源口令）。

# 平台前端（localhost:5173）
cd app && npm install && npm run dev

# 智能体前端（localhost:5201）
cd agent-app && npm install && npm run dev
```

## 🚀 部署（平台生产）

1. `git push origin master` → Cloudflare Pages 自动构建 `app/`
2. CF 构建完成后同步构建产物到 OSS（**每次改了 `app/` 源码都需要**）：
   ```bash
   python backend/tools/dp_grab_cf_assets.py https://deepphilosophy.pages.dev --upload
   ```
   管线自带完整性校验（抓取重试 + 上传后逐引用校验，缺失即报错）。
3. 纯 `backend/`、`data/`、`tools/` 改动**无需**同步 OSS（commit hash 已解耦，仅影响章节 CDN 引脚，随构建自动更新）。

## 📁 项目结构

完整文件树见 [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)（由 `backend/tools/gen_structure.py` 生成）。

```
DeepPhilosophy/
├── app/                    # 平台前端（React + Vite，Cloudflare Pages 构建根）
│   ├── src/                # 页面/组件/数据层/工具
│   └── public/             # 数据与静态资源（git 全跟踪，前端唯一数据源）
├── agent-app/              # 智能体前端（本地 Vite :5201；public/ 为工作副本不入库）
├── backend/                # ★ 统一 Python 后端（FastAPI :8011）
│   ├── main.py             # 入口（智能体路由 + 书库 API + 上传 + SPA）
│   ├── routes/agent.py     # 30 工具注册表 + stream_lg(LangGraph) + cite（旧引擎已删）
│   ├── engine_langgraph.py # LangGraph 流式编排（深哲/尼采）
│   ├── agents.py           # 智能体注册表（nietzsche 人格包 → data/ai_author）
│   ├── guard.py            # 端点鉴权/限流/每日配额 + per-user 上下文
│   ├── tools/              # 书库构建/修复/同步/OCR/向量全套工具（含部署管线）
│   └── data/               # 章节源（git 跟踪，CDN 读这份）+ 运行时数据（gitignore）
├── data/ai_author/         # AIAuthor 六库数字人格数据（1.6GB，不入库，仅本地）
├── docs/                   # 项目文档（NOWSTATE 现状快照 / DATABASE 数据库规范）
├── workers/                # Cloudflare Workers API（auth + api，Hono + D1）
└── .github/workflows/      # CI
```

## 📊 数据规模（2026-08 快照）

| 类别 | 数量 |
|---|---|
| 经典著作 | 402 部（312 可读 + 90 TXT 占位） |
| 哲学家 | 737 位 |
| 哲学流派 | 111 个 |
| 章节 | 12210 个（312 本书） |
| AIAuthor 尼采语料 | 23 本著作 · 6488 chunks · 1296 实体图谱 · 564 条记忆 |

## 开发者

[@txdsyl_](https://github.com/wqx-txdsyl) · MIT License

<p align="center"><i>从古埃及到当代，人类一直在追问——现在，这些追问都在这里。</i></p>
