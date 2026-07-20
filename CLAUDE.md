# CLAUDE.md — DeepPhilosophy 项目规范

## 架构

```
浏览器 → Cloudflare Pages（前端静态） → jsDelivr CDN（章节数据）
                                       → OSS CDN（书内图片）
                                       → Render API（仅 AI/认证/笔记）
```

- **前端不依赖 Render**：书籍/作者/章节/图片全部走 CDN + OSS + 本地 JSON
- **Render 仅处理**：AI 对话、用户认证、笔记同步、阅读历史

## 项目结构

```
DeepPhilosophy/
├── app/                    # React + Vite 前端
│   ├── src/
│   │   ├── pages/          # 页面组件
│   │   ├── components/     # 可复用组件
│   │   ├── data/           # 数据层（缓存/题库/工具函数）
│   │   └── utils/          # API/SEO 工具
│   └── public/             # 静态资源（切勿改路径！前端引用死依赖）
│       ├── books.json      # 书籍目录
│       ├── philosophers.json  # 哲学家数据
│       ├── book_detail/    # 每书独立 JSON（摘要/标签）
│       ├── philosopher/    # 肖像 + data/ 详情 JSON
│       ├── schools/        # 流派图片 + data/ JSON
│       ├── covers/         # 封面 WebP
│       ├── gene/           # 谱系素材
│       └── icons/          # PNG 图标
├── backend/                # FastAPI + 数据工具
│   ├── main.py             # API 入口
│   ├── routes/             # API 路由
│   ├── services/           # 业务逻辑
│   ├── modules/            # RAG 模块
│   ├── tools/              # 数据构建脚本（可复用）
│   └── data/               # 运行时数据（book_chapters/book_images）
├── scripts/                # 维护脚本
└── .claude/skills/         # 自动化 Skill
```

## 核心规则

### 0. 最高优先级：不要破坏能跑的东西
- **不要改 `app/public/` 的文件路径**：前端组件引用死依赖这些路径
- **不要删 `backend/data/book_chapters/`**：CDN 依赖它
- **不要改前端路由/组件名**：会被 React lazy import 引用
- **改代码前先 grep 所有引用**：确认影响范围再动手

### 1. 数据流
- **书籍列表**：前端直读 `/books.json`，不调 API
- **书籍详情**：前端直读 `/book_detail/{id}.json`，不调 API
- **章节内容**：前端从 jsDelivr CDN 读取（`backend/data/book_chapters/` 在 git 中）
- **书内图片**：直连 OSS CDN（`deepphilosophy.oss-cn-shanghai.aliyuncs.com/book_images/`）
- **封面**：`/covers/{name}.webp` 静态文件
- **哲学家**：前端直读 `/philosophers.json`，详情读 `/philosopher/data/{name}.json`

### 2. 数据一致性
- `app/public/` 是前端直接读取的 **唯一数据源**
- `backend/data/book_chapters/` 是章节数据的 git 追踪源
- 修改数据后必须同步两份：`backend/data/` → `app/public/`
- `books.json` 和 `book_detail/{id}.json` 的 `chapterCount` 必须一致

### 3. EPUB 处理
- 新 EPUB 放到 `F:/philosophy/{区域}/{作者}/` 
- 运行 `cd backend && python tools/rebuild_spine.py` 生成章节
- 运行 `python tools/build_covers_manifest.py` 提取封面
- 全部推送到 git，CDN 自动刷新

### 4. 脚本规范
- `backend/tools/` — 可复用的数据构建工具
- `scripts/` — 一次性维护操作
- 所有脚本使用 `BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))` 定位 backend
- API 密钥从根目录 `.env` 读取

### 5. 前端开发
- `npm run dev` 在 `app/` 下运行
- `npm run build` 产物在 `app/dist/`（gitignored）
- Vite proxy 把 `/api` 转发到 Render（本地 dev 需要）
- 生产环境 `__COMMIT_HASH__` 自动注入到 CDN URL

### 6. 提交规范
- commit message 格式：`type: 描述`
- type: `feat`/`fix`/`refactor`/`chore`/`docs`/`perf`
- **不要提交 `backend/data/book_images/` 之外的巨型二进制文件**
- 章节数据变更后务必 `git push`，CDN 走 jsDelivr 读取 GitHub

### 7. 绝对禁止
- ❌ 删 `app/public/` 下任何被前端引用的文件/目录
- ❌ 改 `app/public/` 的目录名（covers/philosopher/schools/gene/icons）
- ❌ 在 EPUB 阅读流程中引入 Render API 依赖
- ❌ 提交 `.env` 文件
- ❌ 移动 `backend/tools/` 下被其他脚本 import 的文件
