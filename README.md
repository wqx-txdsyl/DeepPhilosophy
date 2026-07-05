# DeepPhilosophy — 深哲

东西方及世界哲学的综合知识平台。React + FastAPI + DeepSeek AI，部署于 Render。

---

## 快速开始

打开网站即可使用，无需注册。如需同步阅读进度和聊天历史，在「我的」页面注册账号。

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

> 部署到 Render：fork 项目 → 在 Render Dashboard 创建 Web Service → 选择 Docker → 设置 `DEEPSEEK_API_KEY` 等环境变量 → 推送即可自动部署。

---

## 页面导览

### 首页 `/`
世界哲学地图（45+ 热点）、每日金句、三列历史时间轴。

### 哲学掠影 `/genealogy`
博物馆级谱系图录，按六大时代排列 103 个流派。点击任意流派卡片进入详情。顶部可切换东方/西方/世界视角。

### 流派详情 `/school/:name`
每个流派包含八面内容，向下滚动浏览：
- **Hero** — 封面名言与背景图
- **Overview** — 流派概述
- **Constellation** — 星丛人物关系图
- **Timeline** — 历史时间轴
- **Glossary** — 术语辞海
- **Quotes** — 金句画廊
- **Works** — 代表著作
- **Epilogue** — 结语与尾名言

### 哲人 `/authors`
599 位哲学家列表。顶部可按国家/流派/时代标签筛选。点击进入详情页，查看生平、头像、著作、流派归属。

### 书籍 `/books`
东西方哲学经典，支持按地区/作者/标签筛选。点击进入详情后开始阅读，支持 PDF/EPUB 格式。

### 问答 `/qa`
基于 DeepSeek AI 的哲学问答。输入问题后流式输出回答，支持多轮对话。可在设置页填入自己的 API Key。

### 游戏 `/games`
- **答案之书** — 心中默问，翻页揭晓
- **PHTI** — 哲学人格测试（496 题）
- **PHTI 沙雕版** — 不正经版

### 我的 `/profile`
登录/注册，同步阅读进度和聊天历史到云端。登录后数据自动备份。

### 设置 `/settings`
配置 AI API Key、模型、API 地址。可在此退出登录或删除账号。

---

## 移动端

在 App 设置中开启「手机版」，界面适配移动端触摸操作。或直接在手机浏览器打开网站。

---

## 数据规模

| 指标 | 数量 |
|------|------|
| 哲学流派 | 103 + 6 子流派 |
| 哲学家 | 599 位 |
| 著作 | 300+ 本 |
| 金句 | 665 条 |
| 答案之书 | 161 条 |
| 国家/地区 | 91 个 |

---

## 技术栈

React 19 · FastAPI · DeepSeek AI · SQLite · ChromaDB · Render Docker

---

开发者：[@txdsyl_](https://github.com/wqx-txdsyl)
