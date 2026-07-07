# DeepPhilosophy

深度哲 — 东西方及世界哲学的综合知识平台。React + Vite + FastAPI + DeepSeek AI。

**线上地址**：https://wqx-txdsyl.github.io/DeepPhilosophy/

---

## 架构

```
浏览器 ──→ GitHub Pages (前端) ── 全球 CDN ── HTML/JS/CSS/图片
                │
                └── API 请求 ──→ Render (后端) ── FastAPI + SQLite + DeepSeek
```

- **GitHub Pages**：前端静态资源，全球 CDN，170MB WebP 图片就近加载
- **Render**：纯 API 服务器（`/api/*`），仅传 JSON 数据，不扛图片流量

---

## 项目简介

DeepPhilosophy 汇集了 **758 位哲学家、111 个哲学流派、300+ 部著作**，通过现代化的 Web 界面呈现哲学思想的脉络与深度。

核心功能：
- **哲学地图** — 45+ 世界哲学热点可视化
- **流派谱系** — 博物馆级的哲学史时间轴，六大时代 111 流派
- **AI 问答** — 基于 DeepSeek 的流式哲学对话
- **阅读系统** — 支持 PDF/EPUB 在线阅读 + AI 批注
- **哲学游戏** — 答案之书、PHTI 人格测试
- **哲人系统** — 758 位哲学家，按流派/时代/国家标签筛选，时序排列

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

| 组件 | 平台 | 部署方式 |
|------|------|---------|
| 前端 | GitHub Pages | 推送 master → Actions 自动部署到 `gh-pages` 分支 |
| 后端 | Render | Docker 自动构建，仅包含 API + 最小静态文件 |
| 图片 | GitHub Pages CDN | 170MB WebP 走全球 CDN，Render 不承载 |

---

## 页面导览

| 页面 | 路由 | 说明 |
|------|------|------|
| 首页 | `/` | 世界哲学地图、每日金句、统计数据 |
| 哲学掠影 | `/genealogy` | 六大时代 111 流派谱系，东方/西方/世界视角 |
| 流派详情 | `/school/:name` | 八面内容：Hero/概述/星丛/时间轴/辞海/金句/著作/结语 |
| 哲人 | `/authors` | 758 位哲学家，按流派/世纪/国家标签筛选，时序排列 |
| 书籍 | `/books` | 300+ 本哲学经典，支持 PDF/EPUB 在线阅读 |
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
| 部署 | GitHub Pages + Render (Docker) |

---

## 项目结构

```
DeepPhilosophy/
├── app/                          # React 前端 (Vite)
│   ├── src/
│   │   ├── pages/                # 21 个页面组件
│   │   ├── components/           # Icon, WorldMap, Timeline, school/ 等
│   │   ├── data/                 # 数据层 + 缓存 + 金句/PHTI 题库
│   │   └── utils/                # SEO, API 工具
│   ├── public/
│   │   ├── philosopher/          # 758 张哲人 WebP 头像
│   │   ├── schools/              # 流派背景 WebP + data/ JSON
│   │   ├── gene/                 # 博物馆素材 WebP
│   │   └── icons/                # PNG 图标（仅此保留 PNG）
│   └── package.json
├── backend/                      # FastAPI 后端
│   ├── main.py                   # API 入口 + 路由
│   ├── auth.py                   # 用户认证
│   ├── philosophers_db.py        # 哲学家数据库
│   ├── modules/                  # RAG 模块
│   └── data/                     # philosophers.json 等
├── scripts/                      # 数据维护脚本
│   ├── add_author.py             # 添加哲学家
│   ├── add_school.py             # 添加流派
│   ├── fetch_philosopher_img.py  # 爬取头像
│   ├── gen_portrait.py           # AI 生成肖像
│   └── ...
├── .claude/skills/               # 13 个自动化 Skill
├── .github/workflows/            # CI/CD (pages.yml 等)
├── Dockerfile                    # 多阶段构建（Node + Python）
└── render.yaml
```

---

## 开发者

[@txdsyl_](https://github.com/wqx-txdsyl) · MIT License
