# DeepPhilosophy — 哲学爱好者知识平台

东西方及世界哲学的综合 Web 应用。React + FastAPI + DeepSeek AI，部署于 Render。

**v2.1** — 88 个哲学流派，353 位哲学家，342 本著作，3 个互动游戏。哲学之河博物馆级谱系页。

---

## 目录

1. [快速开始](#快速开始)
2. [项目架构](#项目架构)
3. [数据流](#数据流)
4. [页面与路由](#页面与路由)
5. [关键文件](#关键文件)
6. [如何新增内容](#如何新增内容)
7. [脚本工具](#脚本工具)
8. [数据标准](#数据标准)
9. [标签系统](#标签系统)
10. [部署](#部署)
11. [常见问题](#常见问题)
12. [经验教训](#经验教训)

---

## 快速开始

```bash
# 1. 克隆项目
git clone git@github.com:wqx-txdsyl/DeepPhilosophy.git
cd DeepPhilosophy

# 2. 安装前端依赖
cd app
npm install

# 3. 启动前端开发服务器
npm run dev                    # http://localhost:5173

# 4. 启动后端（新开终端）
cd ../backend
pip install -r requirements.txt
KNOWLEDGE_DIR=F:/philosophy python main.py   # http://localhost:8000

# 5. 构建生产版本
cd ../app
npm run build                  # 输出到 app/dist/
rm -rf ../backend/app-dist && cp -r dist ../backend/app-dist
```

> **Windows 用户**：后端启动可能遇到 `&` 路径问题。使用 `C:\dp` junction 或 PowerShell。

---

## 项目架构

```
DeepPhilosophy/
├── app/                          # React 前端 (Vite)
│   ├── public/
│   │   └── schools/              # 88 张流派背景图 + JSON 数据
│   ├── src/
│   │   ├── pages/
│   │   │   ├── HomePage.jsx                  # 首页：世界地图 + 金句 + 时间轴
│   │   │   ├── GenealogyPage.jsx             # 哲学之河 V2 — 博物馆级谱系页（PRD compliant）
│   │   │   ├── SchoolDetailPage.jsx          # 流派详情页（88 流派数据内联）
│   │   │   ├── WorldPhilosophiesPage.jsx     # 世界哲学 24 流派
│   │   │   ├── WesternPhilosophiesPage.jsx   # 西方哲学 40 流派
│   │   │   ├── EasternPhilosophiesPage.jsx   # 东方哲学 24 流派
│   │   │   ├── BooksPage.jsx / BookDetailPage.jsx / ReaderPage.jsx
│   │   │   ├── AuthorsPage.jsx / AuthorDetailPage.jsx
│   │   │   ├── QAPage.jsx
│   │   │   ├── GamesPage.jsx / AnswerBookPage.jsx
│   │   │   ├── PHTIPage.jsx / PHTISillyPage.jsx
│   │   │   ├── ProfilePage.jsx / SettingsPage.jsx
│   │   ├── components/
│   │   │   ├── school/           # 流派详情页 8 组件
│   │   │   │   ├── HeroSection / OverviewSection / ConstellationMap
│   │   │   │   ├── TimelineSection / GlossaryCloud / QuotesGallery
│   │   │   │   ├── WorksList / EpilogueSection / tokens.js
│   │   │   ├── WorldMap.jsx      # 首页世界地图（25 热点+金色脉冲）
│   │   │   └── PhilosophyTimeline.jsx  # 三列时间轴
│   │   ├── data/
│   │   │   ├── dailyQuotes.js    # 665 条金句
│   │   │   ├── answer_book.json  # 161 条答案之书
│   │   │   ├── phti_questions.json / phti_silly_questions.json
│   │   │   ├── phti_types.json / phti_original_types.json
│   │   │   └── userData.js / crypto.js
│   │   ├── App.jsx / App.css / main.jsx
│   ├── gen_inline_schools.py     # JSON → JS DATA 内联生成器
│   ├── fix_school_page.py        # DATA 插入 SchoolDetailPage 脚本
│   ├── build_timeline.py         # 时间轴数据分析
│   └── vite.config.js
│
├── backend/                      # FastAPI 后端
│   ├── main.py                   # API 路由（书籍/作者/问答/用户/同步）
│   ├── auth.py                   # 用户认证（SQLite + GitHub Release 备份）
│   ├── config.py                 # 配置（API Key / 路径 / 存储后端）
│   ├── philosophers_db.py        # 哲学家数据库（JSON 加载，353 位）
│   ├── modules/                  # RAG 模块
│   │   ├── document_loader.py / text_processor.py
│   │   ├── embedding.py / vector_store.py / rag_chain.py
│   │   └── llm_client.py / ocr_engine.py
│   ├── data/
│   │   ├── philosophers.json     # 哲学家数据（JSON，353 位）
│   │   ├── name_aliases.json     # 姓名别名（57 条）
│   │   ├── book_summaries.json   # 342 本书籍摘要
│   │   ├── books_cache.json      # 书籍关键词缓存
│   │   ├── answer_book.json      # 答案之书（161 条）
│   │   ├── phti_questions.json   # PHTI 题库（496 题）
│   │   ├── school_*.json         # 新流派 JSON 数据
│   │   └── users.db              # 用户数据库（运行时生成）
│   ├── build_*.py / fill_*.py / fix_*.py  # 构建/修复脚本
│   ├── Dockerfile
│   └── requirements.txt
│
├── PHTI.csv                      # 16 种沙雕哲学家（答案之书版）
├── DeepPhilosophy_Timeline_V2_PRD.md  # 哲学之河 V2 博物馆设计规范（203条）
├── render.yaml                   # Render 部署配置
├── 流派列表.csv                   # 88流派完整列表
└── README.md

图片资源:
F:/philosophy/jpg/                # 88张流派背景图 + 世界地图等
F:/philosophy/jpg/gene/           # 博物馆环境素材（纸纹/古地图/金粒/时代插图/文明剪影）
```

---

## 数据流

### 流派详情页
```
school_*.json (backend/data/)
  → gen_inline_schools.py 读取
  → 生成 _new_schools_data.jsx (export const XXX_DATA = {...})
  → fix_school_page.py 粘贴进 SchoolDetailPage.jsx
  → Vite 编译进 JS bundle
  → 浏览器直接渲染（无网络请求）
```

### 哲学家/哲人页
```
philosophers.json (backend/data/)
  → philosophers_db.py 启动时加载
  → main.py list_all_authors() 组装作者列表
  → GET /api/authors 返回 JSON
  → AuthorsPage.jsx 前端渲染 + 客户端筛选
```

### 书籍
```
KNOWLEDGE_DIR (F:/philosophy/)
  → main.py scan_books() 扫描 .pdf/.epub/.txt
  → 5 分钟内存缓存
  → GET /api/books 返回 JSON
```

---

## 页面与路由

| 路由 | 页面 | 说明 |
|------|------|------|
| `/` | HomePage | Hero + 世界地图 + 每日金句 + 三列时间轴 |
| `/genealogy` | GenealogyPage | 哲学之河（河流骨架+博物馆卡片） |
| `/school/:name` | SchoolDetailPage | 流派详情（星丛+辞海+金句+时间轴） |
| `/western-philosophies` | WesternPhilosophiesPage | 西方 40 流派 |
| `/eastern-philosophies` | EasternPhilosophiesPage | 东方 24 流派 |
| `/world-philosophies` | WorldPhilosophiesPage | 世界 24 流派 |
| `/books` `/book/:id` `/reader/:id` | 书籍 | 浏览/详情/阅读 |
| `/authors` `/author/:name` | 哲人 | 列表/详情（353 位） |
| `/qa` | QAPage | AI 哲学问答（流式） |
| `/games` `/games/answer-book` `/games/phti` `/games/phti-silly` | 游戏 | 答案之书/PHTI/PHTI沙雕版 |
| `/profile` `/settings` | 用户 | 登录/设置 |

---

## 关键文件

| 文件 | 大小 | 用途 |
|------|------|------|
| `app/src/pages/SchoolDetailPage.jsx` | ~850KB | 88 流派的所有 DATA 内联（最大的文件） |
| `backend/data/philosophers.json` | ~500KB | 353 位哲学家数据 |
| `backend/main.py` | ~1850 行 | API 路由 + 标签系统 |
| `app/src/components/WorldMap.jsx` | | 首页世界地图（25 热点） |
| `app/src/components/PhilosophyTimeline.jsx` | | 三列时间轴 |
| `app/src/pages/GenealogyPage.jsx` | | 哲学之河谱系页 |
| `app/gen_inline_schools.py` | | JSON→JS DATA 转换器 |
| `backend/auth.py` | | 用户认证（SQLite+GitHub备份） |

---

## 如何新增内容

### 新增一个哲学流派

```bash
# 1. 创建流派 JSON 数据
cd backend
# 手动编写或用 AI 生成：参考 build_world_schools.py

# 2. 保存 JSON 到两个位置
cp data/school_新流派.json ../app/public/schools/

# 3. 复制背景图到 public/schools/（同名 PNG）

# 4. 重新生成内联 DATA 并构建
cd ../app
python gen_inline_schools.py    # 重新生成 _new_schools_data.jsx
# 编辑 fix_school_page.py 添加新流派到 SCHOOL_MAP
npm run build

# 5. 同步到后端
rm -rf ../backend/app-dist && cp -r dist ../backend/app-dist

# 6. 更新以下文件中的计数：
#    - HomePage.jsx (流派总数)
#    - SettingsPage.jsx (关于页)
#    - WorldPhilosophiesPage.jsx (如果是世界流派)
#    - WorldMap.jsx (如果是世界流派，添加地图热点)
#    - PhilosophyTimeline.jsx (添加时间轴条目)
#    - GenealogyPage.jsx (谱系页计数)
```

### 新增一个哲学家

```bash
# 直接编辑 backend/data/philosophers.json
# 格式：{"名字": {"era":"年代","country":"国家","school":"流派","bio":"简介","wiki_url":"链接"}}
# 别名添加到 backend/data/name_aliases.json
```

---

## 脚本工具

| 脚本 | 用途 |
|------|------|
| `app/gen_inline_schools.py` | 读取 `public/schools/school_*.json` → 生成 JS DATA 变量 |
| `app/fix_school_page.py` | 将生成的 DATA 粘贴进 SchoolDetailPage.jsx |
| `backend/rebuild_tags.py` | 规范化 philosophers.json 中的流派/国家标签 |
| `backend/build_world_schools.py` | AI 批量生成世界哲学流派 JSON |
| `backend/build_answer_book.py` | AI 筛选金句+生成解释 |
| `backend/build_phti_questions.py` | AI 生成 PHTI 题库 |
| `backend/fill_*.py` | AI 补全哲学家 bio |
| `backend/fix_stars.py` | 从 SchoolDetailPage 提取星丛名字→匹配哲学家DB |

### 构建命令

```bash
# 前端
cd app && npm run build

# 同步到后端
rm -rf ../backend/app-dist && cp -r dist ../backend/app-dist

# 提交
git add app/src backend/data backend/app-dist
git commit -m "..."
git push
```

---

## 数据标准

| 模块 | 字段 | 最低标准 |
|------|------|---------|
| 📚 书籍 | 摘要 | ≥300字 |
| ✒️ 哲人 | bio | ≥1000字 |
| 🧬 流派 | overview | ≥500字 |
| 🧬 流派 | conclusion | ≥500字 |
| 🧬 流派 | quotes | ≥20条 |
| 🧬 流派 | cihai | ≥20条 |
| 🧬 流派 | timeline | ≥8条 |
| 🧬 流派 | thinkers | ≥8位 |

### 数据格式（极易出错！）

```javascript
// ✅ 正确 — cihai/quotes/works 每元素是对象
cihai: [{word:"术语", def:"定义", source:"出处"}, ...]
quotes: [{text:"引文", author:"作者", exp:"阐释"}, ...]
works: [{title:"书名", author:"作者", era:"年代", desc:"简介"}, ...]

// ❌ 错误 — 字符串数组会导致页面崩溃
cihai: ['术语1', '术语2', ...]           // GlossaryCloud 调用 item.word.split() 崩溃
quotes: ['引文1', '引文2', ...]          // QuotesGallery 访问 q.text 崩溃
```

---

## 标签系统

标签经过三轮重构，前后端必须保持同步：

### 规范化规则
1. **相近合并**：`儒家创始人`→`儒家`，`斯多葛派`→`古希腊哲学`
2. **连写拆分**：`存在主义女性主义`→`存在主义` + `女性主义`
3. **多世纪覆盖**：生卒年跨越多世纪的人物在所有世纪筛选器中都出现
4. **今国名**：`普鲁士`→`德国`，`俄国`→`俄罗斯`，各朝代→`中国`
5. **多国支持**：移居者同时出现在两个国家筛选中

### 同步点
- `backend/data/philosophers.json` — 源数据（已规范化）
- `backend/main.py` `_normalize_tag()` — 后端筛选
- `app/src/pages/AuthorsPage.jsx` `normMap` — 前端筛选

> ⚠️ **修改标签时必须三处同步更新！**

---

## 部署

### Render（生产环境）
1. 推送到 `master` 分支 → Render 自动部署
2. Dockerfile 位置：`backend/Dockerfile`
3. 环境变量（在 Render Dashboard 设置）：
   - `DEEPSEEK_API_KEY` — AI 问答
   - `GITHUB_TOKEN` — 用户数据备份到 GitHub Release
   - `USE_GITHUB=true` — 书籍从 GitHub Release 加载

### 用户数据持久化
- 用户 DB（SQLite）通过 GitHub Release 备份/恢复（免费层无 Disk）
- 前端 localStorage 合并策略保护本地数据不被云端空数据覆盖

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 新流派打开白屏/空页 | DATA 未正确内联到 SchoolDetailPage | 运行 gen_inline_schools.py + 检查 SCHOOL_MAP |
| 标签筛选无效 | 前后端 normalize 不同步 | 三处同步更新 MERGE MAP |
| 详情页图片不显示 | bg 路径后缀错误（.jpg vs .png） | 检查实际文件后缀 |
| 双书名号 | JSON title 带《》，WorksList 又包一层 | `work.title.replace(/^《\|》$/g, '')` |
| `const XXX_DATA` 重复声明 | gen+fix 脚本重复插入 | 插入前检查目标字符串是否存在 |
| SPA 子路径白屏 | vite.config.js `base: './'` | 改为 `base: '/'` |
| 后台 JSON 损坏 | 多进程并发写入同一文件 | 使用单进程 + JSON 中间格式 |
| `influence: "9"` (字符串) | gen 脚本输出未做类型转换 | 生成后用 `influence: "9"`→`influence: 9` 修正 |
| git push 被拒 | 敏感文件（.env, oss_upload.py）被提交 | `.gitignore` 提前配置 |

---

## 经验教训

1. **JS 模块导入**：`import * as X from file` 要求 file 中 `export const`，仅 `const` 不可导入
2. **React Hooks 顺序**：`useState`/`useEffect` 必须在所有变量引用之前声明
3. **正则边界**：CE 年份匹配需要 `(?<![前\d])` 负向前瞻，否则 BCE 年份被误匹配
4. **并发写入**：两个 Python 进程同时写同一个 JSON → 文件损坏。始终单进程操作
5. **脚本幂等性**：`fix_school_page.py` 多次运行会重复插入 DATA。加入去重检查
6. **Git LFS**：大 PNG 文件用 `GIT_LFS_SKIP_PUSH=1` 绕过 LFS 推送
7. **`git add -A` 危险**：会带入临时文件和敏感凭据。始终精确 `git add <specific files>`
8. **标签同步**：前端 `normMap` 和后端 `_normalize_tag` 是同一份数据的两个副本——极易不同步。理想方案是共享 JSON 配置

---

## 技术栈

- **前端**: React 18 + React Router v6 + Vite 8
- **阅读器**: react-pdf + epubjs
- **后端**: Python FastAPI + SQLite
- **AI**: DeepSeek Chat API (流式 + RAG 检索增强)
- **部署**: Render (Docker, Singapore)
- **存储**: GitHub Release (书籍 + 用户DB备份)
