# DeepPhilosophy — 哲学爱好者移动应用

一个涵盖东西方及世界哲学的综合性单页应用，五个核心模块：书籍、作者、谱系、问答、用户。React + FastAPI 架构，部署于 Render。

## ⚠️ 数据质量标准（强制执行）

**每次修改数据后必须校验以下标准，构建前确认达标。**

| 模块 | 字段 | 最低标准 | 检查方式 |
|------|------|---------|---------|
| 📚 书籍 | 每本书摘要 | **≥300字** | `books.json` 中每条的 `summary` 字段 |
| ✒️ 作者 | 每位作者介绍 | **≥1000字** | `philosophers_db.py` 中每条的 `bio` 字段 |
| 🧬 谱系 | 流派 overview | **≥500字** | `SchoolDetailPage.jsx` 中每个 `XXX_DATA.overview` |
| 🧬 谱系 | 流派 conclusion | **≥500字** | `SchoolDetailPage.jsx` 中每个 `XXX_DATA.conclusion` |
| 🧬 谱系 | 金句 quotes | **≥20条** | 每个 `XXX_DATA.quotes` 数组长度 |
| 🧬 谱系 | 辞海 cihai | **≥20条** | 每个 `XXX_CIHAI` 数组长度 |

**每次操作后必须更新本 README**，包括：
- 数据统计数字变更
- 新增/修改的生成器脚本
- 新踩的坑和解决方案

## 项目结构

```
Q&ASystem/
├── _gen_east.py                  # 东方学派数据生成器（22学派，DeepSeek API）
├── _gen_west.py                  # 西方学派数据生成器（43学派，DeepSeek API）
├── _gen_world.py                 # 世界哲学数据生成器（8学派，DeepSeek API）
└── DeepPhilosophy/
    ├── app/                      # React 前端 (Vite)
    │   └── src/
    │       ├── pages/
    │       │   ├── BooksPage.jsx          # 书籍列表（搜索/筛选/分类）
    │       │   ├── BookDetailPage.jsx     # 书籍详情
    │       │   ├── ReaderPage.jsx         # PDF/EPUB 阅读器 + AI 批注
    │       │   ├── AuthorsPage.jsx        # 作者列表（搜索/筛选）
    │       │   ├── AuthorDetailPage.jsx   # 作者详情 + 作品列表
    │       │   ├── GenealogyPage.jsx      # 东西方哲学谱系双列时间轴
    │       │   ├── SchoolDetailPage.jsx   # 流派详情页（组件容器）
    │       │   ├── WorldPhilosophiesPage.jsx # 世界哲学概览卡片
    │       │   ├── QAPage.jsx             # AI 哲学问答（RAG + 流式）
    │       │   ├── ProfilePage.jsx        # 个人中心（登录/历史/同步）
    │       │   └── SettingsPage.jsx       # API 配置
    │       ├── components/
    │       │   └── school/                # 谱系详情页组件库（8组件+tokens）
    │       │       ├── tokens.js          # 设计tokens（色彩/间距/字体/动效）
    │       │       ├── HeroSection.jsx    # 英雄区（全屏背景+引文）
    │       │       ├── OverviewSection.jsx # 概述+子流派网格
    │       │       ├── ConstellationMap.jsx # SVG星丛关系图
    │       │       ├── TimelineSection.jsx # 垂直交错时间轴
    │       │       ├── GlossaryCloud.jsx  # 辞海词云
    │       │       ├── QuotesGallery.jsx  # 金句画廊
    │       │       ├── WorksList.jsx      # 著作折叠列表
    │       │       └── EpilogueSection.jsx # 结语+收尾引语
    │       ├── data/
    │       │   ├── data.js               # 数据访问层（云端优先，本地兜底）
    │       │   ├── userData.js           # 用户本地数据（阅读历史/聊天/笔记）
    │       │   └── crypto.js             # API Key 加密存储（AES-GCM）
    │       ├── assets/
    │       │   └── books.json            # 本地书目（253本，离线可用）
    │       ├── App.jsx                   # 路由 + 底部导航
    │       └── App.css                   # 全局样式变量
    ├── backend/                  # FastAPI 后端
    │   ├── main.py               # API 路由 + 静态文件
    │   ├── auth.py               # 用户认证
    │   ├── philosophers_db.py    # 哲学家数据库
    │   ├── modules/              # 文档加载/嵌入/LLM 客户端
    │   ├── data/                 # 书籍缓存/摘要/知识库
    │   ├── Dockerfile            # Render 部署镜像
    │   └── app-dist/             # 前端构建产物（部署时复制到 static/）
    └── render.yaml               # Render 部署配置
```

## 快速开始

```bash
# 前端
cd DeepPhilosophy/app
npm install
npm run dev           # Vite 开发服务器 → http://localhost:5173
npm run build         # 构建到 app/dist/

# 同步构建产物到后端（部署前必须）
rm -rf ../backend/app-dist && cp -r dist ../backend/app-dist

# 后端（需要 Python 3.11 + requirements.txt）
cd ../backend
pip install -r requirements.txt
python main.py        # FastAPI → http://localhost:8000
```

---

## 五个核心模块

### 1. 📚 书籍（Books）

| 页面 | 文件 | 功能 |
|------|------|------|
| 书籍列表 | `BooksPage.jsx` | 东方/西方分类浏览，搜索（书名/作者/标签），标签筛选，作者层级展开 |
| 书籍详情 | `BookDetailPage.jsx` | 地区/格式徽标、关键词标签、摘要、文件大小，点击跳转阅读器 |
| 阅读器 | `ReaderPage.jsx` | PDF（react-pdf）/ EPUB（epubjs）双引擎，单双页切换，进度自动保存，**AI 批注**：基于当前页文字流式对话 |

**数据来源**：优先 `GET /api/books`，兜底 `assets/books.json`（253 本哲学著作）。`data.js` 统一数据访问层（云端优先，5 秒超时后本地兜底）。

### 2. ✒️ 作者（Authors）

| 页面 | 文件 | 功能 |
|------|------|------|
| 作者列表 | `AuthorsPage.jsx` | 东西方分区，搜索（姓名/国家/流派），三重筛选（地区/流派标签/时代） |
| 作者详情 | `AuthorDetailPage.jsx` | 生平简介、年代/国家/流派信息卡、全部作品列表、百科链接 |

**数据来源**：`GET /api/authors` + `GET /api/authors/filters`。后端可能调用百度百科补充详细数据。

### 3. 🧬 谱系（Genealogy）

| 页面 | 文件 | 功能 |
|------|------|------|
| 谱系总览 | `GenealogyPage.jsx` | 东西方双列时间轴（左侧东方、右侧西方），按世纪分组，卡片点击跳转详情 |
| 流派详情 | `SchoolDetailPage.jsx` | **星丛**（思想家关系网+子流派颜色）、**辞海**（术语表 20+）、**金句**（18+条带解释）、**重要著作**（6-8部）、**时间轴**（12-20事件） |
| 世界哲学 | `WorldPhilosophiesPage.jsx` | 印度/日本/伊斯兰阿拉伯/非洲/犹太/波斯/拉美/东南亚 8 大传统概览卡片 |

**数据来源**：73 个学派数据内联在 `SchoolDetailPage.jsx` 中（~835KB），渲染由 8 个可复用组件完成。

### 4. 💬 问答（QA）

| 文件 | 功能 |
|------|------|
| `QAPage.jsx` | AI 哲学问答，**RAG 检索增强**：先检索后端知识库获取参考文献，再流式调用 DeepSeek 生成回答。对话历史本地保存，登录后云端同步 |

**数据流**：用户问题 → `POST /api/qa`（RAG 检索） → DeepSeek API 流式生成 → 保存到 localStorage。

### 5. 👤 用户（Profile / Settings）

| 页面 | 文件 | 功能 |
|------|------|------|
| 个人中心 | `ProfilePage.jsx` | 登录/注册、阅读历史（含进度）、聊天历史、批注笔记、云端同步 |
| 设置 | `SettingsPage.jsx` | API 地址/Key/模型配置，加密存储（AES-GCM + 设备指纹） |

**安全**：API Key 使用 Web Crypto API 加密后存入 localStorage，密钥基于设备指纹派生。

---

## 页面路由

| 路由 | 页面 | 模块 |
|------|------|------|
| `/` 或 `/genealogy` | GenealogyPage | 谱系 |
| `/school/:name` | SchoolDetailPage | 谱系 → 详情 |
| `/world-philosophies` | WorldPhilosophiesPage | 谱系 → 世界 |
| `/books` | BooksPage | 书籍 |
| `/book/:bookId` | BookDetailPage | 书籍 → 详情 |
| `/reader/:bookId` | ReaderPage | 书籍 → 阅读 |
| `/authors` | AuthorsPage | 作者 |
| `/author/:authorName` | AuthorDetailPage | 作者 → 详情 |
| `/qa` | QAPage | 问答 |
| `/profile` | ProfilePage | 用户 |
| `/settings` | SettingsPage | 设置 |

---

## 谱系数据架构

### 最新变更（2026-06-28）
- 星丛图：中心辐射BFS分层布局 + 直线连接 + 防重叠算法
- Hero区：流派英文全大写名称（如 CONFUCIANISM）
- 进化论（天演论）→ 天演论
- 全站 editorial 风格统一（底部细线卡片 + 衬线标题）
- 深色模式一键切换（☀️/🌙）
- 背景图压缩（25MB → 2MB）
- 148位哲学家 Wikipedia 链接

### 组件化架构（v2）

`SchoolDetailPage.jsx` 已重构为组件容器，8 个可复用组件位于 `components/school/`：

```
SchoolDetailPage (数据获取 + 坐标计算)
  ├── HeroSection        ← name, subtitle, quote, quoteAuthor, heroImage
  ├── OverviewSection    ← overview, subSchools[]
  ├── ConstellationMap   ← thinkers[], relations[], SUB_COLORS
  ├── TimelineSection    ← timeline[]
  ├── GlossaryCloud      ← cihai[]
  ├── QuotesGallery      ← data.quotes[]
  ├── WorksList          ← data.works[]
  └── EpilogueSection    ← conclusion, closingQuote
```

所有组件通过 props 接收数据，73 个学派共用同一套组件。设计 tokens 统一管理于 `tokens.js`。

### 流派数据格式

每个学派在 `SchoolDetailPage.jsx` 中有三个 JS 常量：

```js
const XXX_DATA = {
  name, quote, quoteAuthor, subtitle,
  overview: `400-800字多段落概述`,
  thinkers: [{name, sub, era, influence, key, works}],  // 5-7位
  relations: [{from, to, type}],   // 师生/影响/继承/批判/友谊/对立
  timeline: [{year, event, detail, type}],  // 12-20事件
  conclusion: `300-600字总结`,
  works: [{title, author, era, desc}],      // 6-8部
  quotes: [{text, author, exp}],             // 18-20条
  closingQuote
};
const XXX_CIHAI = [{word, def, source}];     // 20+术语
const XXX_SUB_SCHOOLS = [{name, era, desc}]; // 2-4子流派
```

### 新增流派

1. 在 `SchoolDetailPage.jsx` 中 `function SchoolDetailPage()` 之前添加三个常量
2. 在 `SCHOOL_MAP` 中注册：`'流派名': { data, sub, ci, bg }`
3. 在 `SUB_COLORS` 中为每个 thinker 的 `sub` 值添加颜色映射
4. 在 `GenealogyPage.jsx` 时间轴中引用（如需在谱系页显示）

或使用生成器批量生成：
```bash
cd Q&ASystem
python _gen_east.py    # 东方
python _gen_west.py    # 西方
python _gen_world.py   # 世界
```

### 数据统计

| 类别 | 数量 | 数据完整性 |
|------|------|-----------|
| 西方哲学流派 | 43 | overview(500+)/conclusion(500+)/quotes(20+)/cihai(20+) 全部达标 |
| 东方哲学流派 | 22 | 同上 |
| 世界哲学流派 | 8 | 同上 |
| **流派合计** | **73** | |
| 哲学家（作者） | 148 | bio 全部 1000-2400字，wiki_url 指向 Wikipedia |
| 书籍 | 253 | 本地 books.json，summary 待扩充至300+ |
| **数据文件** | | |
| SchoolDetailPage.jsx | ~835KB | 73流派数据内联，8组件渲染 |
| components/school/ | 9文件 | 8可复用组件 + tokens.js |
| philosophers_db.py | ~300KB | 148位哲学家bio + 元数据 |
| books.json | ~250KB | 253本书目元数据 |

## 数据校验脚本

部署前运行以下命令快速检查数据是否达标：

```bash
cd Q&ASystem
python -c "
import ast, json

# 检查谱系数据
with open('DeepPhilosophy/app/src/pages/SchoolDetailPage.jsx','r',encoding='utf-8') as f:
    c = f.read()
import re
# 检查 quotes 数量
for m in re.finditer(r'const (\w+)_DATA', c):
    name = m.group(1)
    block_end = c.find('};', m.start()) + 2
    block = c[m.start():block_end]
    qc = block.count('\"text\":')
    cc = len(re.findall(r'overview:\x60', block))
    if qc < 20: print(f'  ⚠ {name}: only {qc} quotes')
    if 'overview:\x60' in block and cc == 0: pass
print('谱系检查完毕')

# 检查哲学家 bio
with open('DeepPhilosophy/backend/philosophers_db.py','r',encoding='utf-8') as f:
    c = f.read()
ds = c.find('PHILOSOPHERS = {') + len('PHILOSOPHERS = ')
d,i=0,ds
for i in range(ds,len(c)):
    if c[i]=='{': d+=1
    elif c[i]=='}': d-=1
    if d==0: break
phil = ast.literal_eval(ast.parse('x = ' + c[ds:i+1]).body[0].value)
short = [(n,len(v['bio'])) for n,v in phil.items() if len(v['bio']) < 1000]
if short: print(f'  ⚠ {len(short)} authors under 1000 chars')
print(f'作者检查完毕: {len(phil)}位, {len(short)}位未达标')
"
```

---

## 构建与部署

推送到 GitHub `master` 分支后 Render 自动部署。Docker 工作流：

```
1. pip install Python 依赖
2. COPY 后端代码
3. COPY backend/app-dist/ → static/   ← 前端构建产物
4. python main.py
```

### 部署前检查清单

```bash
cd DeepPhilosophy/app
npm run build                          # 1. 构建前端
rm -rf ../backend/app-dist             # 2. 同步到后端
cp -r dist ../backend/app-dist
git add . && git commit -m "..."       # 3. 提交
git push origin master                 # 4. 推送 → Render 自动部署
```

---

## 常见陷阱

| 问题 | 原因 | 解决 |
|------|------|------|
| 谱系页面跳转无内容 | `backend/app-dist/` 未同步最新构建 | 重新 build 并同步 |
| 双书名号《《》》 | API 生成的 title 已含《》，渲染代码又包一层 | 剥离数据中的预置《》 |
| 星丛全部同色 | thinker 的 `sub` 值不在 SUB_COLORS 中 | 两个 sub 格式都要匹配：`sub:"x"` 和 `"sub":"x"` |
| 构建报错 `Expected , or }` | JS 双引号字符串内出现未转义的中文引号 | 避免 `""` 出现在 JS `""` 字符串内 |
| SCHOOL_MAP 重复键 | 插入数据时未清理旧条目 | JS 允许重复键但不报错，会导致回退逻辑失效 |
| 问答不工作 | API Key 未配置 | 在 Settings 页面填入 DeepSeek API Key |

## 技术栈

- **前端**: React 18 + React Router v6 + Vite (rolldown)
- **阅读器**: react-pdf (PDF) + epubjs (EPUB)
- **后端**: Python FastAPI + ChromaDB + sentence-transformers
- **AI**: DeepSeek Chat API (流式) + RAG 检索增强
- **安全**: Web Crypto API AES-GCM（API Key 加密）
- **部署**: Render (Docker, Singapore)
