# DeepPhilosophy

深度哲学 — 东西方及世界哲学的综合知识平台。React + Vite + FastAPI + DeepSeek AI。

## 访问方式

| 地址 | 适用场景 |
|------|---------|
| https://deepphilosophy.top | 国内直连（Cloudflare Pages 自定义域名） |
| https://deepphilosophy.pages.dev | 海外/CDN 加速（Cloudflare Pages） |
| https://deepphilosophy.vercel.app | Vercel 备用 |
| http://localhost:5173 | 本地开发 |

---

## 架构

```
浏览器 ──→ Cloudflare Pages（前端静态）── jsDelivr CDN（章节 JSON）
          │                              └── OSS CDN（书内图片）
          └── API 请求 ──→ Render ── FastAPI（仅 AI/认证/笔记）
```

- **Cloudflare Pages**：前端 HTML/JS/CSS/封面/肖像，推送即部署
- **jsDelivr CDN**：章节 JSON（免费全球加速，读取 GitHub master）
- **OSS CDN**：书内插图（阿里云 5814 张 WebP）
- **Render**：仅处理 AI 对话、用户认证、笔记同步

---

## 项目简介

DeepPhilosophy 汇集了 **743 位哲学家、111 个哲学流派、191 部著作**（107 EPUB 可读 + 84 TXT 待收录），通过现代化的 Web 界面呈现哲学思想的脉络与深度。

核心功能：
- **哲学地图** — 45+ 世界哲学热点可视化
- **流派谱系** — 博物馆级的哲学史时间轴，六大时代 111 流派
- **AI 问答** — 基于 DeepSeek 的流式哲学对话
- **阅读系统** — EPUB 在线阅读（结构化 JSON 章节 + jsDelivr CDN）+ AI 批注
- **哲学游戏** — 答案之书、PHTI 人格测试
- **哲人系统** — 743 位哲学家（东方122/西方479/世界142），AI 评分排序 + 思想星丛关系网络

---

## 本地开发

```bash
git clone git@github.com:wqx-txdsyl/DeepPhilosophy.git
cd DeepPhilosophy

# 前端（localhost:5173）
cd app && npm install && npm run dev

# 后端（新终端，localhost:8000）
pip install -r requirements.txt
python main.py
```

前端默认连接 `http://localhost:8000` 的 API。可在设置页面或 `app/.env` 中修改 `VITE_API_URL`。

- 网站入口：http://localhost:5173
- API 文档：http://localhost:8000/docs

---

## 生产构建

```bash
cd app && npm run build   # 产物在 app/dist/
```

**部署方式**：

| 组件 | 平台 | 访问 |
|------|------|------|
| 前端 | Cloudflare Pages | `deepphilosophy.top` `deepphilosophy.pages.dev` |
| 前端备用 | Vercel | `deepphilosophy.vercel.app` |
| 后端 API | Render | `deepphilosophy-7g7m.onrender.com` |
| 本地开发 | Vite | `localhost:5173` |

---

## 页面导览

| 页面 | 路由 | 说明 |
|------|------|------|
| 首页 | `/` | 世界哲学地图、每日金句、统计数据 |
| 哲学掠影 | `/genealogy` | 六大时代 111 流派谱系，东方/西方/世界视角 |
| 流派详情 | `/school/:name` | 八面内容：Hero/概述/星丛/时间轴/辞海/金句/著作/结语 |
| 哲人 | `/authors` | 743 位哲学家，AI 评分排序，肖像卡片网格，地区/流派/时代筛选 |
| 书籍 | `/books` | 191 本（107 EPUB 可读 + 84 TXT 待收录），结构化 JSON 章节，jsDelivr CDN 加载 |
| 问答 | `/qa` | DeepSeek AI 流式哲学对话 |
| 游戏 | `/games` | 答案之书、PHTI 人格测试、沙雕版 |
| 我的 | `/profile` | 登录/注册，云端同步阅读进度和对话历史 |
| 设置 | `/settings` | API Key、模型配置、移动版/暗色模式 |

---

## 图片格式

全部图片已迁移至 **WebP**，无 JPG/PNG 残留（icons 除外）。无缩略图——WebP 足够小，`loading="lazy"` 确保仅可见区域加载。

---

## 技术栈

| 层 | 技术 |
|------|------|
| 前端 | React 19, React Router, Vite 8 |
| 后端 | FastAPI, SQLite, ChromaDB |
| AI | DeepSeek API（流式对话） |
| 部署 | Cloudflare Pages + Render (Docker) |
| CDN | jsDelivr（章节 JSON）+ 阿里云 OSS（书内图） |

---

## 项目结构

```
DeepPhilosophy/
├── .gitignore
├── .env                    # 全局环境变量（API keys）
├── .dockerignore
├── Dockerfile              # Render 部署
├── requirements.txt        # Python 依赖
├── render.yaml
├── vercel.json
├── README.md
├── REMOVED_PDFS.txt        # 待替换 PDF 清单（123本）
├── .claude/                # Claude Code 配置
│   ├── CLAUDE.md           # 项目规范（AI 严格执行）
│   ├── settings.local.json
│   └── skills/             # 15 个自动化 Skill
├── app/                    # React 前端 (Vite)
│   ├── src/
│   │   ├── pages/          # 22 个页面组件
│   │   ├── components/     # 22 个 UI 组件
│   │   ├── data/           # 数据层（缓存/题库/封面查找）
│   │   ├── utils/          # API/SEO 工具
│   │   └── contexts/       # Toast 通知系统
│   ├── public/             # 静态资源（切勿改路径！）
│   │   ├── books.json      # 书籍目录（60KB，191本）
│   │   ├── philosophers.json  # 哲学家（743位，AI评分排序）
│   │   ├── philosopher_network.json  # 星丛关系网络
│   │   ├── book_detail/    # 191 个独立书籍详情 JSON
│   │   ├── covers/         # 99 张书籍封面 WebP
│   │   ├── philosopher/    # 758 张肖像 + data/ 详情
│   │   ├── schools/        # 111 张流派图 + data/ JSON
│   │   ├── gene/           # 13 张谱系素材
│   │   └── icons/          # 86 个 PNG 图标
│   ├── electron/           # Electron 桌面端入口
│   ├── vite.config.js
│   └── package.json
├── backend/                # FastAPI + 数据工具
│   ├── main.py             # API 入口
│   ├── config.py           # 配置
│   ├── auth.py             # 认证 + OSS 同步
│   ├── admin.py            # 管理后台
│   ├── db.py               # 哲学家数据库
│   ├── routes/             # 10 个 API 路由
│   ├── services/           # 3 个业务模块
│   ├── modules/            # 7 个 RAG 模块
│   ├── models/             # Pydantic 请求模型
│   ├── tools/              # 11 个数据构建脚本
│   │   ├── rebuild_spine.py           # EPUB → 章节 JSON
│   │   ├── build_book_json.py         # EPUB → 结构化 JSON
│   │   ├── build_philosopher_network.py  # 哲学家星丛网络
│   │   ├── build_covers_manifest.py   # 封面提取
│   │   ├── gen_summaries.py           # AI 批量生成摘要
│   │   ├── download_gutenberg.py      # Gutenberg 下载
│   │   └── sync_to_cloud.py           # 云端数据同步
│   ├── tests/              # 3 个测试文件
│   └── data/               # 运行时数据
│       ├── book_chapters/  # 章节 JSON（git 追踪，CDN 加载）
│       ├── book_images/    # 书内插图（5814 张，OSS 同步）
│       └── ...
├── scripts/                # 9 个维护脚本
│   ├── add_author.py       # 添加哲学家
│   ├── add_book.py         # 添加书籍
│   ├── add_school.py       # 添加流派
│   ├── fetch_philosopher_img.py  # 爬取头像
│   └── gen_portrait.py     # AI 生成肖像
└── .github/workflows/      # keepalive + pages CI
```

---

## 开发者

[@txdsyl_](https://github.com/wqx-txdsyl) · MIT License
