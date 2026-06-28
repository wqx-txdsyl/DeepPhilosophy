# DeepPhilosophy — 哲学爱好者知识平台

东西方及世界哲学的综合Web应用，五个模块：首页、书籍、作者、谱系、问答。React + FastAPI，部署于 Render。

## 数据质量标准（强制执行）

| 模块 | 字段 | 最低标准 |
|------|------|---------|
| 📚 书籍 | 摘要 | ≥300字 |
| ✒️ 作者 | bio | ≥1000字 |
| 🧬 谱系 | overview | ≥500字 |
| 🧬 谱系 | conclusion | ≥500字 |
| 🧬 谱系 | quotes | ≥20条 |
| 🧬 谱系 | cihai | ≥20条 |

---

## 项目结构

```
Q&ASystem/
├── _gen_east.py              # 东方学派数据生成器（24学派）
├── _gen_west.py              # 西方学派数据生成器（43学派）
├── _gen_world.py             # 世界哲学数据生成器（9学派）
└── DeepPhilosophy/
    ├── app/                  # React 前端 (Vite)
    │   └── src/
    │       ├── pages/
    │       │   ├── HomePage.jsx              # 首页 Landing（Hero+金句+三入口+数字+时间轴）
    │       │   ├── GenealogyPage.jsx         # 谱系时间轴（双列东西方）
    │       │   ├── SchoolDetailPage.jsx      # 流派详情容器（~850KB，76学派数据内联）
    │       │   ├── WorldPhilosophiesPage.jsx # 世界哲学9流派卡片
    │       │   ├── WesternPhilosophiesPage.jsx # 西方哲学43流派卡片
    │       │   ├── EasternPhilosophiesPage.jsx # 东方哲学24流派卡片
    │       │   ├── BooksPage.jsx / BookDetailPage.jsx / ReaderPage.jsx
    │       │   ├── AuthorsPage.jsx / AuthorDetailPage.jsx
    │       │   ├── QAPage.jsx / ProfilePage.jsx / SettingsPage.jsx
    │       ├── components/school/           # 谱系详情页组件库（8组件+tokens）
    │       │   ├── tokens.js                # 设计token
    │       │   ├── HeroSection / OverviewSection / ConstellationMap
    │       │   ├── TimelineSection / GlossaryCloud / QuotesGallery
    │       │   ├── WorksList / EpilogueSection
    │       ├── data/
    │       │   ├── dailyQuotes.js           # 665条每日金句
    │       │   ├── data.js / userData.js / crypto.js
    │       │   └── assets/books.json        # 305本书目
    │       ├── App.jsx / App.css
    ├── backend/               # FastAPI 后端
    │   ├── main.py            # API路由 + AI代理
    │   ├── config.py          # 配置（自动读取_gen_east.py或环境变量）
    │   ├── philosophers_db.py # 140位哲学家数据
    │   ├── Dockerfile / requirements.txt
    │   └── app-dist/          # 前端构建产物
    └── render.yaml            # Render部署配置
```

---

## 页面路由

| 路由 | 页面 | 说明 |
|------|------|------|
| `/` | HomePage | 首页：Hero + 每日金句 + 三入口 + 数字 + 时间轴 |
| `/genealogy` | GenealogyPage | 东西方哲学谱系双列时间轴 |
| `/school/:name` | SchoolDetailPage | 流派详情（星丛+辞海+金句+著作+时间轴+结语） |
| `/western-philosophies` | WesternPhilosophiesPage | 西方43流派概览卡片 |
| `/eastern-philosophies` | EasternPhilosophiesPage | 东方24流派概览卡片 |
| `/world-philosophies` | WorldPhilosophiesPage | 世界9流派概览卡片 |
| `/books` `/book/:id` `/reader/:id` | 书籍 | 浏览/详情/阅读 |
| `/authors` `/author/:name` | 作者 | 列表/详情（维基+百度百科链接） |
| `/qa` | QAPage | AI哲学问答（RAG + DeepSeek流式） |
| `/profile` `/settings` | 用户 | 个人中心/API配置 |

---

## 谱系组件架构

```
SchoolDetailPage (数据容器 + 星丛坐标计算)
  ├── HeroSection        ← name, subtitle, quote, quoteAuthor, heroImage, englishName
  ├── OverviewSection    ← overview, subSchools[]
  ├── ConstellationMap   ← thinkers[], relations[], SUB_COLORS
  ├── TimelineSection    ← timeline[]
  ├── GlossaryCloud      ← cihai[]
  ├── QuotesGallery      ← quotes[]
  ├── WorksList          ← works[]
  └── EpilogueSection    ← conclusion, closingQuote
```

所有组件通过 props 接收数据，76 学派共用。设计 tokens: `components/school/tokens.js`

---

## 数据统计

| 类别 | 数量 | 说明 |
|------|------|------|
| 西方哲学流派 | 43 | 古希腊→后现代 |
| 东方哲学流派 | 24 | 先秦→当代 |
| 世界哲学流派 | 9 | 印度/日本/伊斯兰/阿拉伯/非洲/犹太/波斯/拉美/东南亚 |
| **流派合计** | **76** | |
| 哲学著作 | 305 | PDF/EPUB/TXT |
| 哲学家 | 140 | 每人1000+字思想剖析 |
| 每日金句 | 665 | 76流派金句去重汇合 |
| 背景图片 | 77 | 43西哲+24东哲+9世界+1总览 |

---

## 快速开始

```bash
cd DeepPhilosophy/app
npm install
npm run dev           # Vite → http://localhost:5173
npm run build         # 构建到 app/dist/

# 同步到后端
rm -rf ../backend/app-dist && cp -r dist ../backend/app-dist
```

---

## 生成器

```bash
cd Q&ASystem
python _gen_east.py    # 东方
python _gen_west.py    # 西方
python _gen_world.py   # 世界
```

---

## ⚠️ 数据格式强制规范（新增流派必读）

**这是最容易出错的环节。API返回的数据格式必须严格校验！**

| 字段 | 正确格式 | 错误格式（会崩溃！） |
|------|---------|-------------------|
| `cihai` | `[{word:"术语", def:"定义", source:"出处"}, ...]` | `['术语1', '术语2', ...]` ← 字符串数组！|
| `quotes` | `[{text:"引文", author:"作者", exp:"阐释"}, ...]` | `['引文1', '引文2', ...]` ← 字符串数组！|
| `works` | `[{title:"书名", author:"作者", era:"年代", desc:"简介"}, ...]` | `['书名1', '书名2', ...]` ← 字符串数组！|
| `thinkers[].works` | `['著作1', '著作2']` ← 这里是字符串数组OK | — |
| `timeline` | `[{year:"年份", event:"事件", detail:"描述", type:"birth/book/idea/event"}, ...]` | — |

**核心规则：CIHAI/Quotes/Works 三个顶层数组的每个元素必须是对象，绝不能是裸字符串。**

原因：`GlossaryCloud` 访问 `item.word.split('')`，`QuotesGallery` 访问 `q.text`，`WorksList` 访问 `work.title` —— 如果是字符串会直接崩溃。

**生成器校验代码：**
```python
# 生成后立即检查
import json
data = json.loads(api_response)
assert isinstance(data['cihai'][0], dict), "CIHAI 必须是对象数组！"
assert isinstance(data['quotes'][0], dict), "Quotes 必须是对象数组！"  
assert isinstance(data['works'][0], dict), "Works 必须是对象数组！"
```

---

## 新增流派步骤

1. 运行对应生成器或手动在 `SchoolDetailPage.jsx` 中 `function SchoolDetailPage()` 前添加 `XXX_DATA` / `XXX_CIHAI` / `XXX_SUB_SCHOOLS`。**添加后必须校验上述格式！**
2. 在 `SCHOOL_MAP` 中注册
3. 在 `GenealogyPage.jsx` 时间轴和描述中添加条目
4. 在对应 Overview 页面（Western/Eastern/WorldPhilosophiesPage）添加卡片
5. 同步背景图到 `app/public/schools/`

---

## 部署

推送到 GitHub `master` 分支，Render 自动部署。Dockerfile 使用 `backend/app-dist/` 作为静态文件。

Render 环境变量：`DEEPSEEK_API_KEY` — 问答代理使用，本地自动从 `_gen_east.py` 读取。

---

## 常见陷阱

| 问题 | 解决 |
|------|------|
| 页面跳转无内容 | `backend/app-dist/` 未同步 |
| 双书名号 | API生成title预置《》，渲染又包一层 → 剥离 |
| 星丛同色 | sub值未进SUB_COLORS → 两种格式都要匹配 |
| 详情页空白+Cannot read properties of undefined (reading 'split') | CIHAI/quotes/works 是字符串数组而非对象数组 |
| 构建报错 | JS字符串内中文引号冲突 → 避免或转义 |
| 哲学家bio不换行 | `whiteSpace: pre-line` |
| Render部署失败 | philosophers_db.py换行未转义 → `\n`→`\\n` |
| 图片太大 | 压缩至≤500KB，1600px宽 |
| git push被拒 | 不要`git add .`，敏感文件（.env.oss, oss_upload.py）勿提交 |

---

## 技术栈

- **前端**: React 18 + React Router v6 + Vite
- **阅读器**: react-pdf + epubjs
- **后端**: Python FastAPI + ChromaDB
- **AI**: DeepSeek Chat API（流式 + RAG检索增强）
- **部署**: Render (Docker, Singapore)
