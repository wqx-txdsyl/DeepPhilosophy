# DeepPhilosophy「深哲」

> 横跨五千年的人类思想史长卷 —— 402 部哲学经典 · 744 位哲学家 · 111 个哲学流派

**DeepPhilosophy（深哲）** 是一个开放的哲学知识平台：从古埃及到当代，从东方到西方，我们把人类思想史上最重要的原典、人物与流派组织成一个可以**阅读、探索、对话**的数字世界。全部内容免费开放，无需注册即可阅读。

👉 **立即访问：[deepphilosophy.top](https://deepphilosophy.top)**

---

## 📖 你能在这里做什么

### 1. 在线阅读 402 部哲学经典

- **402 部经典著作**：312 本可直接在线阅读（结构化章节 + 书内插图），90 本 TXT 占位待收录
- 收录范围横跨中西：柏拉图、亚里士多德、康德、尼采、萨特、马克思…以及中国哲学诸子与东方思想
- **秒开级加载**：章节数据走全球 CDN 双轨加速（OSS + jsDelivr 自动切换），翻页几乎零等待
- **AI 批注**：阅读中随时选中提问、写批注，与书对话

### 2. 探索 744 位哲学家与 111 个流派

- **哲学家画廊**：744 位哲学家肖像与生平，支持地区/流派/时代筛选，AI 评分排序
- **流派谱系**：111 个哲学流派的完整谱系——六大时代时间轴（博物馆级视觉），每个流派含概述、代表哲人、时间线、著作
- **思想星丛**：哲学家之间的师承/影响/论敌关系网络，看思想如何在人与人之间流动
- **概念溯源**：一个概念的跨书演变轨迹

### 3. 与 AI 讨论哲学

- **流式哲学问答**：基于 DeepSeek 的实时流式对话，思考过程可见
- **深度思考模式**：复杂问题开启更长推理链
- 支持**自配 API Key**（设置页）直连，随时可用

### 4. 思想游戏

- **答案之书**：随手一翻，哲人箴言回应你的问题
- **PHTI 哲学人格测试**：5 题维度，测出你的哲学人格画像

### 5. 账号与云端同步（可选）

- 注册登录后，**阅读进度、对话历史、AI 批注**全部云端同步，换设备不丢
- 登录即用，无需付费

### 6. 安装为桌面/手机应用（PWA）

浏览器打开网站即可"安装"成独立应用——有专属图标（金色哲学徽章）、独立窗口、离线可用外壳。Chrome/Edge 地址栏右侧安装按钮，或菜单 →「安装 DeepPhilosophy」。

---

## 📊 数据规模（2026-08 实测快照）

| 类别 | 数量 |
|---|---|
| 经典著作 | 402 部（312 可读 + 90 TXT 占位） |
| 哲学家 | 744 位 |
| 哲学流派 | 111 个 |
| 书内插图 | 数千张（WebP 优化） |

---

## 🏗 技术架构（简要）

```
浏览器 ──→ Cloudflare Pages（静态前端）── 章节：OSS CDN 优先 + jsDelivr 兜底
                                        └── 图片：阿里云 OSS CDN
                                        └── API：Cloudflare Workers（Hono + D1）
```

- **前端**：React 19 + Vite，全静态托管于 Cloudflare Pages，推送即部署
- **API**：Cloudflare Workers 双 worker（auth 认证 + api 业务），D1 数据库，零冷启动
- **章节**：结构化 JSON + OSS/jsDelivr 双轨 CDN（2s 超时自动切换）
- **AI**：DeepSeek 流式（服务器中转 + 用户自配 key 直连双路径）
- **零传统服务器**：无 VPS，无订阅成本，CDN 全免费层级

---

## 🛠 本地开发

```bash
git clone git@github.com:wqx-txdsyl/DeepPhilosophy.git
cd DeepPhilosophy

# 前端（localhost:5173）
cd app && npm install && npm run dev

# Workers API 本地调试（需 wrangler 登录）
cd workers/auth && npm install && npx wrangler dev
cd workers/api && npm install && npx wrangler dev
```

生产构建：`cd app && npm run build`（产物在 `app/dist/`，推送 master 即触发 Cloudflare Pages 自动部署）。

**数据侧说明**：书籍/哲学家/流派数据以 `app/public/` 为唯一数据源（git 全量跟踪）；章节数据 `backend/data/book_chapters/` 为 git 跟踪源，经 CDN 分发；书库构建/修复/OCR 流水线在 [PhiAgent](https://github.com/wqx-txdsyl/PhiAgent) 仓库。

---

## 📁 项目结构（2026-08-14 合并 PhiAgent 后）

```
DeepPhilosophy/
├── app/                    # React 前端（平台，Cloudflare Pages 构建根）
│   ├── src/                # 页面/组件/数据层/工具
│   └── public/             # 数据与静态资源（books.json、philosophers.json、book_detail/、covers/、philosopher/、schools/…）
├── agent-app/              # PhiAgent 智能体前端（本地 Vite :5201，public/ 为本地工作副本不入库）
├── backend/                # ★ 统一 Python 后端（FastAPI :8011，智能体 + 平台 API）
│   ├── main.py             # 入口（智能体路由 + 书库 API + SPA）
│   ├── routes/agent.py     # 智能体工具集 + SSE（29 工具 + 尼采人格）
│   ├── engine_langgraph.py # LangGraph 流式引擎
│   ├── agents.py           # 智能体注册表（深哲 / 尼采）
│   ├── tools/              # 书库构建/修复/同步/OCR/向量全套工具（34+）
│   └── data/               # 章节源（git 跟踪，CDN 读这份）+ 运行时数据（gitignore）
├── data/ai_author/         # AIAuthor 六库数字人格数据（1.6GB，不入库）
├── workers/                # Cloudflare Workers API（auth + api，Hono + D1）
└── .github/workflows/      # CI（Pages 构建 + 数据一致性检查）
```

**数据流（单向）**：`backend/tools/` 构建/修复 → `backend/data/book_chapters`（git 跟踪，唯一章节源）→ jsDelivr/OSS CDN 分发 → `app/` 与 `agent-app/` 前端只读。生产 API 走 Cloudflare Workers（D1）；Python 后端服务智能体与本地开发。

完整技术细节见 [.claude/CLAUDE.md](.claude/CLAUDE.md)（项目规范）与 [PhiAgent](https://github.com/wqx-txdsyl/PhiAgent)（书库构建引擎）。

---

## 开发者

[@txdsyl_](https://github.com/wqx-txdsyl) · MIT License

<p align="center"><i>从古埃及到当代，人类一直在追问——现在，这些追问都在这里。</i></p>
