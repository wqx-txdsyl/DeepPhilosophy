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
浏览器 ──→ Cloudflare Pages (前端) ── 全球 330 节点 CDN ── HTML/JS/CSS/图片
                │
                └── API 请求 ──→ Render (后端) ── FastAPI + SQLite + DeepSeek
```

- **Cloudflare Pages**：前端静态资源，全球 CDN，推送即部署
- **Render**：纯 API 服务器（`/api/*`），仅传 JSON 数据

---

## 项目简介

DeepPhilosophy 汇集了 **743 位哲学家、111 个哲学流派、120 部 EPUB 著作**（东方 33 本/西方 87 本），通过现代化的 Web 界面呈现哲学思想的脉络与深度。

核心功能：
- **哲学地图** — 45+ 世界哲学热点可视化
- **流派谱系** — 博物馆级的哲学史时间轴，六大时代 111 流派
- **AI 问答** — 基于 DeepSeek 的流式哲学对话
- **阅读系统** — 支持 PDF/EPUB 在线阅读 + AI 批注
- **哲学游戏** — 答案之书、PHTI 人格测试
- **哲人系统** — 743 位哲学家（东方120/西方479/世界144），AI 评分排序 + 思想星丛关系网络

---

## 本地开发

```bash
git clone git@github.com:wqx-txdsyl/DeepPhilosophy.git
cd DeepPhilosophy

# 前端（localhost:5173）
cd app && npm install && npm run dev

# 后端（新终端，localhost:8000）
cd backend && pip install -r requirements.txt
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

---

## 项目结构

```
DeepPhilosophy/
├── app/                              # React 前端 (Vite)
│   ├── src/
│   │   ├── pages/                    # 页面组件（Home,Books,Authors,Reader等）
│   │   ├── components/               # Icon, WorldMap, ChapterReader 等
│   │   ├── data/                     # 数据层 + 缓存 + 题库
│   │   └── utils/                    # SEO, API 工具
│   ├── public/
│   │   ├── books.json                # 书籍目录（60KB，192本）
│   │   ├── philosophers.json         # 哲学家数据（743位）
│   │   ├── philosopher_network.json  # 思想星丛关系网络
│   │   ├── book_detail/              # 每本书独立 JSON（摘要/标签）
│   │   ├── book_chapters/            # 章节 JSON（CDN 加载）
│   │   ├── covers/ + covers.json     # 书籍封面 WebP
│   │   ├── philosopher/              # 哲学家肖像 WebP
│   │   ├── schools/                  # 流派背景 WebP + data/
│   │   ├── gene/                     # 博物馆素材
│   │   └── icons/                    # PNG 图标
│   └── package.json
├── backend/                          # FastAPI 后端
│   ├── main.py                       # API 入口
│   ├── config.py                     # 配置
│   ├── auth.py                       # 认证
│   ├── admin.py                      # 管理后台
│   ├── db.py                         # 哲学家数据库
│   ├── routes/                       # API 路由（health/text/auth/ai...）
│   ├── services/                     # 业务逻辑（summaries/book_scanner）
│   ├── modules/                      # RAG 模块（embedding/vector_store/llm...）
│   ├── models/                       # 数据模型
│   ├── tools/                        # 数据构建工具
│   │   ├── rebuild_spine.py          # EPUB → 章节 JSON
│   │   ├── build_book_json.py        # EPUB → 结构化 JSON
│   │   ├── build_philosopher_network.py  # 哲学家星丛网络
│   │   ├── build_covers_manifest.py  # 封面提取
│   │   ├── gen_summaries.py          # AI 批量生成摘要标签
│   │   ├── download_gutenberg.py     # Gutenberg 公版书下载
│   │   └── sync_to_cloud.py          # 云端同步
│   ├── tests/                        # 测试
│   └── data/                         # 数据存储
│       ├── book_chapters/            # 章节 JSON
│       ├── book_detail/              # 书籍详情
│       ├── book_images/              # 书内插图（OSS 同步）
│       └── ...
├── scripts/                          # 维护脚本
│   ├── add_author.py                 # 添加哲学家
│   ├── add_book.py                   # 添加书籍
│   ├── add_school.py                 # 添加流派
│   ├── fetch_philosopher_img.py       # 爬取哲学家头像
│   └── gen_portrait.py               # AI 生成肖像
├── .claude/skills/                   # 自动化 Skill
├── .github/workflows/                # CI/CD
├── Dockerfile                        # Render 部署
└── render.yaml
```

---

## 开发者

[@txdsyl_](https://github.com/wqx-txdsyl) · MIT License
