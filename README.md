# DeepPhilosophy

深哲 — 东西方及世界哲学的综合知识平台。React + FastAPI + DeepSeek AI，部署于 Render。

**线上地址**：https://deep-philosophy-frontend.onrender.com

---

## 项目简介

DeepPhilosophy 是一个面向哲学爱好者、研究者和普通读者的综合性知识平台。平台汇集了 **600 位哲学家、103 个哲学流派、300+ 部著作** 和 **665 条金句**，通过现代化的 Web 界面呈现哲学思想的脉络与深度。

核心功能包括：
- **哲学地图** — 45+ 世界哲学热点可视化
- **流派谱系** — 博物馆级的哲学史时间轴
- **AI 问答** — 基于 DeepSeek 的哲学对话
- **阅读系统** — 支持 PDF/EPUB 在线阅读
- **哲学游戏** — 答案之书、PHTI 人格测试

---

## 快速开始

### 在线使用

打开网站即可浏览全部内容，无需注册。如需同步阅读进度和聊天历史，在「我的」页面注册账号即可。

### 自部署

```bash
git clone git@github.com:wqx-txdsyl/DeepPhilosophy.git
cd DeepPhilosophy

# 前端
cd app && npm install && npm run dev    # http://localhost:5173

# 后端（新终端）
cd backend && pip install -r requirements.txt
KNOWLEDGE_DIR=F:/philosophy python main.py   # http://localhost:8000

# 生产构建
cd app && npm run build
rm -rf ../backend/app-dist && cp -r dist ../backend/app-dist
```

### Render 部署

Fork 本项目 → Render Dashboard 创建 Web Service → 选择 Docker → 设置 `DEEPSEEK_API_KEY` 等环境变量 → 推送自动部署。

---

## 页面导览

| 页面 | 路由 | 说明 |
|------|------|------|
| 首页 | `/` | 世界哲学地图（45+ 热点）、每日金句、三列时间轴 |
| 哲学掠影 | `/genealogy` | 六大时代 103 流派谱系，东方/西方/世界视角 |
| 流派详情 | `/school/:name` | 八面内容：Hero/概述/星丛/时间轴/辞海/金句/著作/结语 |
| 哲人 | `/authors` | 600 位哲学家，按国家/流派/时代标签筛选 |
| 书籍 | `/books` | 300+ 本哲学经典，支持 PDF/EPUB 在线阅读 |
| 问答 | `/qa` | DeepSeek AI 流式哲学对话 |
| 游戏 | `/games` | 答案之书（161条）、PHTI 人格测试（496题）、沙雕版 |
| 我的 | `/profile` | 登录/注册，云端同步阅读进度和对话历史 |
| 设置 | `/settings` | API Key、模型配置、退出登录、删除账号 |

---

## 移动端

在设置中开启「手机版」或直接手机浏览器访问，响应式布局自动适配。

---

## 数据规模

| 指标 | 数量 |
|------|------|
| 哲学流派 | 103 + 6 子流派 |
| 哲学家 | 600 位 |
| 著作 | 300+ 本 |
| 金句 | 665 条 |
| 答案之书 | 161 条 |
| 国家/地区 | 91 个 |

---

## 技术栈

| 层 | 技术 |
|------|------|
| 前端 | React 19, React Router, Vite |
| 后端 | FastAPI, SQLite, ChromaDB |
| AI | DeepSeek API（流式对话） |
| 部署 | Docker, Render |

---

## 项目结构

```
DeepPhilosophy/
├── app/                          # React 前端 (Vite)
│   ├── src/
│   │   ├── pages/                # 21 个页面组件
│   │   ├── components/           # WorldMap, Timeline, school/ 等
│   │   └── data/                 # 金句/答案之书/PHTI 题库
│   ├── public/
│   │   ├── philosopher/          # 哲人头像 + thumb/
│   │   ├── schools/              # 流派背景图 + thumb/
│   │   └── gene/                 # 博物馆素材
│   └── package.json
├── backend/                      # FastAPI 后端
│   ├── main.py                   # API 入口 + 路由
│   ├── auth.py                   # 用户认证 (SQLite + OSS)
│   ├── philosophers_db.py        # 哲学家数据库
│   ├── modules/                  # RAG 模块
│   └── data/                     # philosophers.json 等
├── scripts/                      # 数据构建/维护脚本
│   ├── add_author.py             # 添加哲学家
│   ├── add_school.py             # 添加流派
│   ├── fetch_philosopher_img.py  # 爬取头像
│   ├── gen_portrait.py           # AI 生成肖像
│   ├── _normalize_tags.py        # 标签规范化
│   └── ...
├── .claude/skills/               # 11 个自动化 Skill
├── Dockerfile
└── render.yaml                   # Render 部署配置
```

---

## 开发者

[@txdsyl_](https://github.com/wqx-txdsyl) · MIT License
