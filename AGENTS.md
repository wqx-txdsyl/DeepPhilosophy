# AGENTS.md — DeepPhilosophy 项目规范

## 架构

```
浏览器 → Cloudflare Pages（前端静态） → jsDelivr CDN（章节数据）
                                      → OSS CDN（书内图片）
                                      → Cloudflare Workers API（AI/认证/笔记）
```

- **前端不依赖任何传统后端**：书籍/作者/章节/图片全部走 CDN + OSS + 本地 JSON
- **API 全量在 Cloudflare Workers**：`workers/auth`（/api/auth/*，JWT）+ `workers/api`（/api/*，AI 流式/问答/历史/笔记/文件 302），D1 数据库 `deepphilosophy-db`
- **Render 已完全退役（2026-08-11）**：看到 onrender/Render 引用直接清

## 项目结构（2026-08-14 PhiAgent 已并入本仓库）

```
DeepPhilosophy/
├── app/                    # 平台前端（React + Vite，CF Pages 构建根）
│   ├── src/
│   │   ├── pages/          # 页面组件
│   │   ├── components/     # 可复用组件
│   │   ├── data/           # 数据层（缓存/题库/工具函数）
│   │   └── utils/          # API/SEO 工具
│   └── public/             # 静态资源（切勿改路径！前端引用死依赖）
│       ├── books.json      # 书籍目录（402 本）
│       ├── philosophers.json  # 哲学家数据
│       ├── book_detail/    # 每书独立 JSON（402 个，git 全跟踪，正式源）
│       ├── philosopher/    # 肖像 + data/ 详情 JSON
│       ├── schools/        # 流派图片 + data/ JSON
│       ├── covers/         # 封面 WebP
│       ├── gene/           # 谱系素材
│       └── icons/          # PNG 图标
├── agent-app/              # PhiAgent 智能体前端（本地 Vite :5201；public/ 不入库）
├── backend/                # ★ 统一 Python 后端（FastAPI :8011）——智能体 + 平台 API 单一体
│   ├── main.py             # 入口（agent 路由 + 书库 + 上传 + SPA）
│   ├── routes/agent.py     # 29 工具注册表 + SSE + cite（LangGraph 引擎复用 TOOLS）
│   ├── engine_langgraph.py # LangGraph 流式编排（深哲/尼采）
│   ├── agents.py           # 智能体注册表（nietzsche 人格包 → data/ai_author）
│   ├── mcp_client.py       # MCP 外部工具接入
│   ├── tools/              # 书库构建/修复/同步/OCR/向量全套工具（34+，含 dp_grab_cf_assets）
│   └── data/               # 运行时数据（book_chapters 是 git 跟踪源，CDN 读它；embeddings/agent_memory 等 gitignore）
├── data/ai_author/         # AIAuthor 六库（1.6GB，gitignore，仅本地）
├── workers/                # Cloudflare Workers API（Hono + D1）
│   ├── auth/               # /api/auth/* 登录注册 JWT
│   └── api/                # /api/* AI 流式/问答/历史/笔记/文件 302
├── scripts/                # 内容运营（肖像爬取/add_*）
└── .github/workflows/      # pages CI
```

## 核心规则

### 0. 最高优先级：不要破坏能跑的东西
- **不要改 `app/public/` 的文件路径**：前端组件引用死依赖这些路径
- **不要删 `backend/data/book_chapters/`**：CDN（jsDelivr 读 GitHub）依赖它
- **不要改前端路由/组件名**：会被 React lazy import 引用
- **改代码前先 grep 所有引用**：确认影响范围再动手

### 1. 数据流
- **书籍列表**：前端直读 `/books.json`，不调 API
- **书籍详情**：前端直读 `/book_detail/{id}.json`，不调 API（正式源 = `app/public/book_detail/`）
- **章节内容**：前端从 jsDelivr CDN 读取（`backend/data/book_chapters/` 在 git 中，唯一跟踪源）
- **书内图片**：直连 OSS CDN（`deepphilosophy.oss-cn-shanghai.aliyuncs.com/book_images/`）
- **封面**：`/covers/{name}.webp` 静态文件
- **哲学家**：前端直读 `/philosophers.json`，详情读 `/philosopher/data/{name}.json`

### 2. 数据一致性（双写规则）
- `app/public/` 是前端直接读取的 **唯一数据源**
- `backend/data/book_chapters/` 是章节数据的 git 跟踪源（CDN 读 GitHub 上这份）
- 章节双写：`backend/data/` → `app/public/backend/data/book_chapters/`（vite dev 镜像，**已 git rm --cached 解除跟踪**，仅本地开发用；MD5 必须一致，verify_book 查）
- `books.json` 和 `book_detail/{id}.json` 的 `chapterCount` 必须一致
- 改动章节文件（合并/删除编号）时 public 副本必须同步处理，不能只动 backend 源

### 3. 书籍构建与修复（工具在本仓库 `backend/tools/`，2026-08-14 已并入）
- **章节文件/分章/toc 格式唯一标准：`docs/分章标准规范.md`（硬标准，任何章节写入前必读）**：章节文件顶层必须 dict（`{index,title,content}`）、toc 分级 part/chapter/section（section 锚点 sec=块号）、标题清洗规则、四层同步、交付验收清单。注：规范成文于 PhiAgent 并入前，其「DP 层（PhiAgent/backend/data）」现即本仓库 `backend/data/`，同步层现为三层
- **书库构建/修复/同步/向量/OCR 全套工具在本仓库 `backend/tools/`**（用 `.venv` 运行；Python 3.12+，依赖见根 `requirements.txt`）
- 新 EPUB/PDF 源文件放 `F:/philosophy/{区域}/{作者}/`，用 `dp_pdf_import.py` / `rebuild_spine.py` 处理
- 导入/修复后：`dp_sync_books.py` 汇总生成 `app/public/books.json` + 双写章节 + 同步 detail，最后 `verify_book.py <bid> --vite-check` 全绿
- **部署管线**：`dp_grab_cf_assets.py <部署URL> --upload` 抓 CF 产物 → `dp_sync_oss_static.py` 传 OSS（含懒加载 chunk，抓取后须确认完整性）

### 4. 脚本规范
- `backend/tools/` — 书库构建/修复/同步/OCR/向量全套工具（单一目录，勿拆）
- `scripts/` — 内容运营（add_author/add_book/add_school/add_subschool、肖像爬取 fetch_*、gen_portrait/gen_school_bg 等）
- 所有脚本使用 `BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))` 定位 backend
- API 密钥从根目录 `.env` 读取
- 临时调试脚本放 `backend/tools/_tmp/` 随用随删，不提交 git

### 5. 前端开发
- `npm run dev` 在 `app/` 下运行
- `npm run build` 产物在 `app/dist/`（gitignored）
- Vite proxy 把 `/api` 转发到 Cloudflare Workers（本地 dev 需要）
- 生产环境 `__COMMIT_HASH__` 自动注入到 CDN URL

### 6. 提交规范
- commit message 格式：`type: 描述`
- type: `feat`/`fix`/`refactor`/`chore`/`docs`/`perf`
- **不要提交 `backend/data/book_images/` 之外的巨型二进制文件**
- **精确 pathspec add，禁用 `git add -A`**（避免误提交）
- 章节数据变更后务必 `git push`，CDN 走 jsDelivr 读取 GitHub
- 提交消息用 `git commit -F` 文件方式（PowerShell here-string 遇 ASCII 双引号会崩溃）

### 7. 绝对禁止
- ❌ 删 `app/public/` 下任何被前端引用的文件/目录
- ❌ 改 `app/public/` 的目录名（covers/philosopher/schools/gene/icons）
- ❌ 提交 `.env` 文件
- ❌ 提交 `backend/data/`（被 gitignore；79 个历史已跟踪文件例外）
- ❌ 移动 `backend/tools/` 下被其他脚本 import 的文件

---

## 2026-08-14 现状快照（PhiAgent 并入后）

- **书库**：402 本（312 本可读 + 90 TXT 占位），detail 正式源 = `app/public/book_detail/`
- **章节 git 跟踪**：`backend/data/book_chapters/`（唯一）；`app/public/backend/data/book_chapters/`（vite 镜像）已解除跟踪
- **统一后端**：`backend/` = FastAPI :8011（智能体 + 平台 API）；生产 API 仍走 Cloudflare Workers（auth + api 双 worker + D1 `deepphilosophy-db`），`https://deepphilosophy.top/api/health` 可验证
- **AIAuthor**：`data/ai_author/`（1.6GB，gitignore，仅本地；agents.py 的 bundle 指向此处）
