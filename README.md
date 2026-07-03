# DeepPhilosophy — 哲学爱好者知识平台

东西方及世界哲学的综合 Web 应用。React + FastAPI + DeepSeek AI，部署于 Render。

**v2.5** — 96 流派，353+ 哲人，305 著作，31 国别，Editorial Layout 谱系图录。

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
9. [书籍排序与标签系统](#书籍排序与标签系统)
10. [AI 问答与伴读](#ai-问答与伴读)
11. [部署](#部署)
12. [常见问题](#常见问题)
13. [经验教训](#经验教训)

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
│   │   └── schools/              # 96 张流派背景图 + JSON 数据
│   │   └── gene/                 # 博物馆素材库（region/era/symbol/landmark/terrain/textures）
│   ├── src/
│   │   ├── pages/
│   │   │   ├── HomePage.jsx                  # 首页：世界地图 + 金句 + 时间轴
│   │   │   ├── GenealogyPage.jsx             # 哲学之河 V2 — 博物馆级谱系页
│   │   │   ├── SchoolDetailPage.jsx          # 流派详情页（96 流派数据内联）
│   │   │   ├── WorldPhilosophiesPage.jsx     # 世界哲学 31 流派
│   │   │   ├── WesternPhilosophiesPage.jsx   # 西方哲学 41 流派
│   │   │   ├── EasternPhilosophiesPage.jsx   # 东方哲学 24 流派
│   │   │   ├── BooksPage.jsx / BookDetailPage.jsx / ReaderPage.jsx
│   │   │   ├── AuthorsPage.jsx / AuthorDetailPage.jsx
│   │   │   ├── QAPage.jsx
│   │   │   ├── GamesPage.jsx / AnswerBookPage.jsx
│   │   │   ├── PHTIPage.jsx / PHTISillyPage.jsx
│   │   │   ├── ProfilePage.jsx / SettingsPage.jsx
│   │   ├── components/
│   │   │   ├── ErrorBoundary.jsx             # 全局错误捕获
│   │   │   ├── WorldMap.jsx                  # 首页世界地图（45+ 热点+金色脉冲）
│   │   │   ├── PhilosophyTimeline.jsx        # 三列时间轴
│   │   │   └── school/                       # 流派详情页 8 组件
│   │   │       ├── HeroSection / OverviewSection / ConstellationMap
│   │   │       ├── TimelineSection / GlossaryCloud / QuotesGallery
│   │   │       ├── WorksList / EpilogueSection / tokens.js
│   │   ├── data/
│   │   │   ├── dailyQuotes.js    # 665 条金句
│   │   │   ├── answer_book.json  # 161 条答案之书
│   │   │   ├── phti_questions.json / phti_silly_questions.json
│   │   │   ├── phti_types.json / phti_original_types.json
│   │   │   └── userData.js / crypto.js
│   │   ├── App.jsx / App.css / main.jsx
│   ├── gen_inline_schools.py
│   ├── fix_school_page.py
│   └── vite.config.js
│
├── backend/                      # FastAPI 后端
│   ├── main.py                   # API 路由（书籍/作者/问答/用户/同步），~1900 行
│   ├── auth.py                   # 用户认证（SQLite + GitHub Release 备份）
│   ├── config.py                 # 配置（API Key / 路径 / R2 存储）
│   ├── philosophers_db.py        # 哲学家数据库（JSON 加载，353 位）
│   ├── modules/                  # RAG 模块
│   │   ├── document_loader.py / text_processor.py
│   │   ├── embedding.py / vector_store.py / rag_chain.py
│   │   └── llm_client.py / ocr_engine.py
│   ├── data/
│   │   ├── philosophers.json     # 哲学家数据（JSON，353 位）
│   │   ├── name_aliases.json     # 姓名别名（57 条）
│   │   ├── book_summaries.json   # 书籍摘要缓存（`书名||作者` 键）
│   │   ├── books_cache.json      # 书籍关键词缓存
│   │   ├── answer_book.json      # 答案之书（161 条）
│   │   ├── phti_questions.json   # PHTI 题库（496 题）
│   │   ├── school_*.json         # 流派 JSON 数据
│   │   └── users.db              # 用户数据库（运行时生成）
│   ├── build_*.py / fill_*.py / fix_*.py  # 构建/修复脚本
│   ├── Dockerfile
│   └── requirements.txt
│
├── render.yaml                   # Render 部署配置
└── README.md                     # 本文件
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
KNOWLEDGE_DIR (F:/philosophy/) 或 R2 云存储
  → main.py scan_books() 扫描 .pdf/.epub/.txt
  → 5 分钟内存缓存
  → GET /api/books 返回 JSON（含标签+摘要）
```

---

## 页面与路由

| 路由 | 页面 | 说明 |
|------|------|------|
| `/` | HomePage | Hero + 世界地图 + 每日金句 + 三列时间轴 |
| `/genealogy` | GenealogyPage | 哲学之河（博物馆级谱系图录） |
| `/school/:name` | SchoolDetailPage | 流派详情（星丛+辞海+金句+时间轴） |
| `/western-philosophies` | WesternPhilosophiesPage | 西方 41 流派 |
| `/eastern-philosophies` | EasternPhilosophiesPage | 东方 24 流派 |
| `/world-philosophies` | WorldPhilosophiesPage | 世界 31 流派 |
| `/books` `/book/:id` `/reader/:id` | 书籍 | 浏览/详情/阅读 |
| `/authors` `/author/:name` | 哲人 | 列表/详情（353 位） |
| `/qa` | QAPage | AI 哲学问答（流式） |
| `/games` `/games/answer-book` `/games/phti` `/games/phti-silly` | 游戏 | 答案之书/PHTI/PHTI沙雕版 |
| `/profile` `/settings` | 用户 | 登录/设置 |

---

## 关键文件

| 文件 | 大小 | 用途 |
|------|------|------|
| `app/src/pages/SchoolDetailPage.jsx` | ~850KB | 96 流派 DATA 内联（最大文件） |
| `backend/data/philosophers.json` | ~500KB | 353 位哲学家数据 |
| `backend/main.py` | ~1900 行 | API 路由 + 标签系统 + 扫描 |
| `app/src/components/WorldMap.jsx` | | 世界地图（45+ 热点） |
| `app/src/components/PhilosophyTimeline.jsx` | | 三列时间轴 |
| `app/src/pages/GenealogyPage.jsx` | ~800 行 | 哲学之河谱系页 |
| `app/gen_inline_schools.py` | | JSON→JS DATA 转换器 |
| `backend/auth.py` | | 用户认证（SQLite+GitHub备份） |
| `backend/data/book_summaries.json` | | 书籍摘要+标签缓存 |
| `backend/generate_tags_summaries.py` | | DeepSeek API 批量生成工具 |

---

## 如何新增内容

### 新增一个哲学流派

```bash
# 1. 创建流派 JSON 数据
cd backend
# 参考 build_world_schools.py 用 AI 批量生成

# 2. 保存 JSON 到两个位置
cp data/school_新流派.json ../app/public/schools/

# 3. 复制背景图到 public/schools/（同名 JPG）

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

### 新增一本书

```bash
# 1. 将书放到正确路径：F:/philosophy/{东方/西方}/{作者}/{书名}.{pdf/epub}
# 2. 如果替换 TXT 占位，删除同名 .txt 文件
# 3. 运行摘要/标签生成：
cd backend && KNOWLEDGE_DIR=F:/philosophy python generate_tags_summaries.py
# 4. 后端自动感知新文件（每次请求重新扫描）
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
| `backend/generate_tags_summaries.py` | DeepSeek API 批量生成书籍标签+摘要 |
| `backend/fix_duplicates.py` | 修复同名不同作者的书摘要覆盖问题 |
| `backend/fill_*.py` | AI 补全哲学家 bio |

### 构建命令

```bash
# 前端
cd app && npm run build

# 同步到后端 Docker 构建源
rm -rf ../backend/app-dist && cp -r dist ../backend/app-dist

# 提交（精确指定，不要 git add -A）
git add app/src backend/data backend/app-dist
git commit -m "..."
git push
```

---

## 数据标准

### 最低质量标准

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

### 流派 JSON 字段清单

每个 `school_*.json` 文件需包含以下字段（全部必填）：

```json
{
  "name": "流派名称",
  "overview": "概述（≥500字）",
  "conclusion": "结语（≥500字）",
  "cihai": [{"word": "术语", "def": "定义", "source": "出处"}],
  "quotes": [{"text": "引文", "author": "作者", "exp": "阐释"}],
  "timeline": [{"event": "事件", "year": "年份", "detail": "详情"}],
  "thinkers": [{"name": "哲学家", "years": "生卒年", "contribution": "贡献"}],
  "works": [{"title": "书名", "author": "作者", "era": "年代", "desc": "简介"}],
  "tags": ["标签1", "标签2"],
  "bg": "背景图文件名.jpg"
}
```

---

## 书籍排序与标签系统

### 书籍排序方法

按东西方分组，每组内部按哲学家**出生年份**升序：

1. 每组第一个固定为「合集&概述」
2. 其余哲学家按出生年份升序（古希腊→中世纪→近代→现代→当代）
3. 年代来源优先级：**philosophers_db.py 内置数据 → 百度百科爬虫 → AI/上网检索**
4. 未知年代的哲学家排在最末

排序实现位于 `backend/main.py:_author_sort_key()`，从 `philosophers_db.py` 的 `era` 字段提取年份：
- `约公元前624-前546年` → 解析为 -624
- `1770-1831年` → 解析为 1770
- 含"公元前/前"前缀的年份取反，确保公元前早于公元后
- 无年份信息的返回 9999（排最后）

### 书籍扫描 (scan_books)

1. `os.walk(KNOWLEDGE_DIR)` 遍历 `region/author/title.ext` 结构
2. 过滤扩展名：`.pdf / .epub / .txt / .md`
3. 从路径解析 region、author、title（`Path(f).stem`）
4. `###合集&概述###` → 清洗为 `合集&概述`
5. 空目录补 `status=pending` 占位条目

**文件名→显示标题修正：** `TITLE_FIXES` 字典：
```python
TITLE_FIXES = {"SZ": "S/Z"}  # 文件名不能含 /
```

### 书籍标签与简介生成

**优先级：**
1. **内置缓存** — `backend/data/book_summaries.json`（AI 生成，优先使用）
2. **AI 生成** — DeepSeek API（`generate_tags_summaries.py` 批量调用）
3. **上网检索** — 百度百科等（暂未实现批量，仅 AuthorDetailPage 详情页用）
4. **兜底模板** — 绝对不用，一旦发现需立即替换

**标签规范：**
- 每个标签为短关键词，用于前端筛选分类
- 必须是公认的哲学流派/学派名称：`古希腊哲学`、`存在主义`、`德国古典哲学`、`伦理学`……
- 每本书 2-5 个标签

**缓存格式：** `book_summaries.json` 使用 `{书名}||{作者}` 复合键：
```json
{
  "论语||孔子": {
    "summary": "《论语》是孔子及其弟子的语录集…",
    "tags": ["儒家", "伦理学", "政治哲学", "教育哲学"]
  }
}
```
**必须包含作者名**：同名不同作者的书各自独立存储。

**批量生成流程：**
```bash
cd backend && KNOWLEDGE_DIR=F:/philosophy python generate_tags_summaries.py
```
分两阶段：
1. **Phase 1** — 有真实摘要但缺标签的，AI 从摘要提取标签（快）
2. **Phase 2** — 模板/空白摘要的，AI 生成完整简介+标签（慢）

每 5-10 本自动保存，可中断续跑。

### 标签规范化系统

标签经过三轮重构，前后端必须保持同步：

**规范化规则：**
1. **相近合并**：`儒家创始人`→`儒家`，`斯多葛派`→`古希腊哲学`
2. **连写拆分**：`存在主义女性主义`→`存在主义` + `女性主义`
3. **多世纪覆盖**：生卒年跨越多世纪的人物在所有世纪筛选器中都出现
4. **今国名**：`普鲁士`→`德国`，`俄国`→`俄罗斯`，各朝代→`中国`
5. **多国支持**：移居者同时出现在两个国家筛选中

**同步点（三处）：**
- `backend/data/philosophers.json` — 源数据（已规范化）
- `backend/main.py` `_normalize_tag()` — 后端筛选
- `app/src/pages/AuthorsPage.jsx` `normMap` — 前端筛选

> ⚠️ **修改标签时必须三处同步更新！**

---

## AI 问答与伴读

### QAPage 问答页
- 流式调用 DeepSeek API，逐字输出
- 90 秒硬超时保护，防止无限 loading
- 聊天历史本地自动保存 + 云端同步（`userData.js`）
- 思考阶段轮播动画（检索→分析→深度思考→组织回答）
- 自动滚动到底部（哨兵 div + `scrollIntoView`）

### ReaderPage AI 伴读
- 预设阅读上下文（书名/作者/页码/哲学传统）
- 流式输出，支持多轮对话
- 自动滚动跟随输出
- 侧边栏面板，与批注共享空间（互斥显示）

---

## 部署

### Render（生产环境）

1. 推送到 `master` 分支 → Render 自动部署
2. Dockerfile 位置：`backend/Dockerfile`
3. Docker 构建源：`backend/app-dist/` → 容器内 `./static/`
4. 环境变量（在 Render Dashboard 设置）：
   - `DEEPSEEK_API_KEY` — AI 问答
   - `GITHUB_TOKEN` — 用户数据备份到 GitHub Release
   - `USE_GITHUB=true` — 书籍从 GitHub Release 加载

### Render 配置文件

```yaml
# render.yaml
services:
  - type: web
    name: deephilosophy-api
    env: docker
    repo: https://github.com/wqx-txdsyl/DeepPhilosophy
    branch: master
    region: singapore
    plan: free
    dockerfilePath: ./backend/Dockerfile
    envVars:
      - key: PYTHON_VERSION
        value: 3.11
      - key: PORT
        value: 8000
      - key: USE_GITHUB
        value: true
```

### Cloudflare R2 云存储（可选）

> 如果没有 R2，书籍直接从 GitHub Release 加载（`USE_GITHUB=true`）。以下为可选升级。

**原理：**
```
手机/浏览器 → https://deepphilosophy.onrender.com (Render)
                  ├── /api/books, /api/authors → Render 本地计算
                  ├── /api/books/{id}/file → R2 预签名 URL（1h 有效）
                  └── 摘要/标签缓存 → Render 盘内
```

**步骤：**

1. 在 Cloudflare Dashboard 创建 R2 存储桶 `deepphilosophy-books`
2. 创建 API Token（Object Read & Write，仅限该桶）
3. 上传书籍：
```bash
aws s3 sync F:/philosophy s3://deepphilosophy-books/books/ \
  --endpoint-url https://<账户ID>.r2.cloudflarestorage.com
```
4. 在 Render Dashboard 设置环境变量：
   - `USE_R2=true`
   - `R2_ACCESS_KEY` / `R2_SECRET_KEY` / `R2_ENDPOINT` / `R2_BUCKET`
5. 重新部署

**费用：** 全部在免费额度内（R2 10GB 存储 / Render 750h）。

### 前端连接

Android / Web App 设置中，API 地址填 Render 地址：
```
VITE_API_URL=https://deepphilosophy.onrender.com
```

### 本地开发 vs 云端

```bash
# 本地开发（读本地文件）
cd backend && KNOWLEDGE_DIR=F:/philosophy python main.py

# 测试 R2 模式（本地模拟云端）
USE_R2=true R2_ACCESS_KEY=xxx R2_SECRET_KEY=xxx R2_ENDPOINT=xxx python main.py

# 测试 GitHub 模式
USE_GITHUB=true python main.py
```

### 用户数据持久化

- 用户 DB（SQLite）通过 GitHub Release 备份/恢复（Render 免费层无持久磁盘）
- 前端 localStorage 合并策略保护本地数据不被云端空数据覆盖
- 退出登录时自动清除本地历史

---

## 数量限制与约束

| 项目 | 当前值 | 说明 |
|------|--------|------|
| 哲学流派 | 96 | 西方 41 / 东方 24 / 世界 31 |
| 哲学家 | 353+ | `philosophers.json`，持续增长 |
| 著作 | 305 | PDF/EPUB 实体 + TXT 占位 |
| 国别 | 31 | 世界哲学地图覆盖 |
| 每日金句 | 665 条 | `dailyQuotes.js` |
| 答案之书 | 161 条 | `answer_book.json` |
| PHTI 题库 | 496 题 | `phti_questions.json` |
| 用户聊天历史 | 最多 500 条 | localStorage 限制 |
| 阅读历史 | 最多 100 条 | localStorage 限制 |
| 书籍标签 | 2-5 个/本 | 规范化流派名称 |
| cihai/流派 | ≥20 条 | 术语词典 |
| quotes/流派 | ≥20 条 | 名家金句 |
| timeline/流派 | ≥8 条 | 时间轴事件 |
| thinkers/流派 | ≥8 位 | 代表人物 |
| 流派概述 | ≥500 字 | overview + conclusion |
| 书籍摘要 | ≥300 字 | AI 生成 |
| 哲人 bio | ≥1000 字 | AI 补全 |
| 标签归一化同步点 | 3 处 | philosophers.json + main.py + AuthorsPage.jsx |
| 前端流派内联包 | ~850KB | SchoolDetailPage.jsx |
| 哲学家数据 | ~500KB | `philosophers.json` |
| API 路由 | ~1900 行 | `backend/main.py` |

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
| 部署后无变化 | 前端构建产物未复制到 `app-dist/` | Dockerfile 从 `backend/app-dist/` 构建，不是 `backend/static/` |
| 同名书摘要覆盖 | `书名` 单键冲突 | 改用 `书名\|\|作者` 复合键 |
| 模板兜底摘要残留 | 含 `"的著作，TXT格式"` 等机械拼接 | 发现即清理，运行 generate_tags_summaries.py |
| AI 问答无限 loading | 流式连接 hang 住 | 90s 硬超时自动中断 |
| EPUB 版权书可下载 | 版权期内的书误放 | 不可下载 20 世纪版权期内著作（移到大文件存储或不公开） |

---

## 经验教训

1. **`git add -A` 危险**：会带入临时文件和敏感凭据。始终精确 `git add <specific files>`
2. **部署路径**：Dockerfile `COPY app-dist/ ./static/` — 构建产物必须放在 `backend/app-dist/`
3. **JS 模块导入**：`import * as X from file` 要求 file 中 `export const`，仅 `const` 不可导入
4. **React Hooks 顺序**：`useState`/`useEffect` 必须在所有变量引用之前声明
5. **正则边界**：CE 年份匹配需要 `(?<![前\d])` 负向前瞻，否则 BCE 年份被误匹配
6. **并发写入**：两个 Python 进程同时写同一个 JSON → 文件损坏。始终单进程操作
7. **脚本幂等性**：`fix_school_page.py` 多次运行会重复插入 DATA。加入去重检查
8. **Git LFS**：大 PNG 文件用 `GIT_LFS_SKIP_PUSH=1` 绕过 LFS 推送
9. **标签同步**：前端 `normMap` 和后端 `_normalize_tag` 是同一份数据的两个副本——极易不同步。理想方案是共享 JSON 配置
10. **数据类型**：`cihai`/`quotes`/`works` 必须是对象数组而非字符串数组，否则页面崩溃
11. **同名书处理**：摘要缓存键必须含作者名（`书名||作者`），否则同名书互相覆盖
12. **流式超时**：AI 流式 API 需硬超时保护，连接 hang 住会导致无限 loading
13. **暗色模式**：inline style 硬编码颜色值不随 CSS 变量切换，应全部改用 `var(--xxx)`
14. **UserData 数据类型**：云端同步时 `sources` 被序列化为字符串，前端渲染需 `Array.isArray` 守卫

---

## 新增流派完整教程

> ⚠️ **血泪教训：必须严格按此流程，跳过任何一步都会导致白屏崩溃。**

### 前置要求

流派 JSON 必须包含以下全部字段（缺一不可）：

```json
{
  "name": "流派名",
  "subtitle": "简短描述",
  "overview": "概述（≥500字）",
  "conclusion": "结语（≥500字）",
  "quote": "标题下名言",
  "quoteAuthor": "名言作者",
  "closingQuote": "结语名言（含作者，格式：'名言——作者'）",
  "timeline": [{"year":"年份","event":"事件","detail":"详情","type":"event|era|person|book|idea|birth"}],
  "thinkers": [{"name":"姓名","sub":"下属流派","era":"年代","influence":8,"key":"核心概念","works":["著作1","著作2"]}],
  "relations": [{"from":"思想者A","to":"思想者B","label":"关系描述"}],
  "cihai": [{"word":"术语","def":"定义","source":"出处"}],
  "quotes": [{"text":"引文","author":"作者","exp":"阐释"}],
  "works": [{"title":"书名","author":"作者","era":"年代","desc":"简介"}],
  "meta": {"中文名":"流派名","英文名":"English Name"},
  "region": "世界",
  "bg": "url(/schools/english-name.jpg)",
  "sub_schools": {"子流派key":{"name":"子流派名","desc":"描述"}}
}
```

### 步骤 1：准备数据

```bash
# 1.1 在 backend/data/ 创建 school_新流派.json（严格按上述格式）
# 1.2 准备背景图：app/public/schools/english-name.jpg（≤2MB，必须纯英文文件名）
# 1.3 生成缩略图：app/public/schools/thumb/english-name.jpg（200×280）
```

### 步骤 2：生成内联 DATA 并注入 SchoolDetailPage

```bash
cd app

# 2.1 从 JSON 生成 _new_schools_data.jsx
python gen_inline_schools.py

# 2.2 注入到 SchoolDetailPage.jsx（自动添加 SCHOOL_MAP 条目 + ENG_NAMES + DATA 常量）
python fix_school_page.py

# ⚠️ 如果 fix_school_page.py 创建了重复条目，手动清理 SchoolDetailPage.jsx，
#    然后用 scripts/build_6_schools.py 手动注入（参考该脚本的逻辑）
```

### 步骤 3：更新谱系页和地图

```bash
# 3.1 GenealogyPage.jsx — ALL_SCHOOLS 数组添加条目
# 3.2 PhilosophyTimeline.jsx — ALL_SCHOOLS 数组添加条目
# 3.3 WorldMap.jsx — REGIONS 数组添加地图热点坐标
# 3.4 WorldPhilosophiesPage.jsx — WORLD_PHILOSOPHIES 数组添加条目
# 3.5 HomePage.jsx — 更新流派总数
# 3.6 GenealogyPage.jsx — 更新页脚流派总数（一百零二个）
# 3.7 SettingsPage.jsx — 更新关于页数量
# 3.8 GenealogyPage.jsx — IMG_MAP 添加图片文件名映射
```

### 步骤 4：构建部署

```bash
npm run build
rm -rf ../backend/app-dist ../backend/static
cp -r dist ../backend/app-dist
cp -r dist ../backend/static
# 确保 JPG 图片在 backend/app-dist/schools/ 下
git add <specific files>
git commit -m "feat: 新增XXX流派"
git push  # Render 自动部署
```

---

## 新增流派常见致命错误

| # | 错误 | 后果 | 正确做法 |
|---|------|------|---------|
| 1 | **DATA const 放在 SCHOOL_MAP 之后** | `Cannot access 'X' before initialization` 白屏 | DATA const 必须定义在 SCHOOL_MAP 引用之前 |
| 2 | **图片用中文文件名** | 浏览器 URL 编码与服务器不匹配 → 404 | 统一用英文文件名，GenealogyPage 加 IMG_MAP |
| 3 | **`works` 字段缺失或为字符串** | `Cannot read properties of undefined (reading 'map')` | `works` 必须是数组 |
| 4 | **`thinkers` 为空数组** | 星座图 `sorted[0].name` 崩溃 | 至少有一个 thinker |
| 5 | **`relations` 的 from/to 不匹配 thinkers** | 星座图连线异常 | from/to 必须是 thinkers 中存在的 name |
| 6 | **JSON 缺少 `closingQuote`** | 结语后无名言 | 取 quotes 最后一条附加作者 |
| 7 | **bg 路径用 `.png`** | 图片不显示 | PNG 太大不提交 git，用 JPG |
| 8 | **单个引号 `'` 未转义** | JS 语法错误 | 用 `json.dumps` 自动转义，不要手写 |
| 9 | **`influence` 为字符串 `"7"`** | 星座图大小异常 | 必须是数字 `7` |
| 10 | **SCHOOL_MAP 缺少 `};` 闭合** | 后续 const 被吞进对象字面量 | 检查所有 `{ }` 配对 |
| 11 | **用 `_json` 动态加载代替内联** | 先显示"正在构建中"，网络失败则永远不显示 | 流派 DATA 必须内联到 JS bundle |
| 12 | **忘更新 ENG_NAMES** | 详情页显示 "PHILOSOPHICAL SCHOOL" | 中文名→英文大写名的映射 |
| 13 | **忘更新 GenealogyPage 的 IMG_MAP** | 谱系页图片 404 | 中文流派名→英文文件名的映射 |
| 14 | **`cp -r dist backend/app-dist` 覆盖而非替换** | 旧文件残留 | 先 `rm -rf backend/app-dist` 再 copy |
| 15 | **`git add .` 提交敏感文件** | API Key 泄露 | 精确 `git add <specific files>` |

---

## 经验教训（新增流派专项）

15. **DATA 定义顺序致命**：JavaScript `const` 不提升初始化。SCHOOL_MAP 引用的 DATA const 必须在 SCHOOL_MAP 之前定义，否则 TDZ 报错 `Cannot access before initialization`，页面直接白屏。
16. **图片文件名禁止中文**：浏览器对 CSS `url()` 中的中文进行百分号编码后，与服务器文件系统的编码不一致，导致 404。全部图片使用 ASCII 文件名，通过 IMG_MAP 映射。
17. **流派数据必须内联**：`_json` 动态加载依赖网络，会先闪"正在构建中"再加载，且网络失败时永远卡住。所有流派 DATA 应内联到 JS bundle，与已有 96 个流派保持一致。
18. **`fix_school_page.py` 有去重 bug**：多次运行会重复插入已有 DATA，导致 `Identifier already declared`。运行前确保目标文件干净。
19. **用 `json.dumps` 生成 JS 代码**：手动拼接字符串极易出现引号未转义、`\n` 被当作换行等问题。Python 脚本中用 `json.dumps(s, ensure_ascii=False)` 安全编码。
20. **本地先测再推送**：`npm run build` 通过不代表运行时无错。`npx vite preview` 启动预览服务器，在浏览器 F12 看 Console 报错，确认无红字再 git push。

---

## AI 工具与 Skill

项目内置 3 个 Claude Code Skill（`.claude/skills/`），可直接用自然语言调用：

| Skill | 功能 | 用法示例 |
|-------|------|---------|
| `agnes-image` | Agnes API 文生图 + 图像理解 | "用 Agnes 生成一张萨满哲学的插图" |
| `icon-gen` | emoji → AI 分析 → 生成透明背景图标 | "把 🔥 生成图标" |
| `school-bg-gen` | AI 学习现有流派背景图风格 → 按需生成新图 | "给萨满哲学生成背景图" |

### 使用流程

```bash
# 图标生成
cd scripts && python gen_icon_from_emoji.py "🔥"

# 流派背景
python gen_school_bg.py "萨满哲学"
```

### 本地文生图工具

浏览器打开 `scripts/img_gen.html`，输入 prompt 和尺寸即可生成图片。API Key 已预填在密码框中。

---

### 一键新增流派脚本

```bash
cd scripts && python add_school.py "流派名"
```

自动完成全部 7 步：数据处理 → 图片改名 → 内联 DATA → 谱系 → 地图 AI 定位 → 计数更新。详见 `.claude/skills/add-school.md`。

### 血泪教训速查（新增流派必读）

| # | 致命错误 | 后果 | 正确做法 |
|---|---------|------|---------|
| 1 | **DATA const 放在 SCHOOL_MAP 之后** | TDZ 崩溃 `Cannot access before initialization` | const 必须在引用之前 |
| 2 | **图片中文文件名** | Render 返回 404 | 统一英文名 + IMG_MAP 映射 |
| 3 | **SYNTAX_ERROR: `}` 未闭合** | const 被吞进对象 | Python 脚本插入后检查 `{` `}` 配对 |
| 4 | **`git add .`** | API Key 泄露 | 精确 `git add <specific files>` |
| 5 | **没复制 `backend/app-dist`** | Docker 镜像无新文件 | 每次 build 后 `rm -rf && cp -r` |
| 6 | **Dockerfile 缺 `COPY`** | `ModuleNotFoundError` | 新增 .py 文件必须加到 Dockerfile |
| 7 | **引号内嵌未转义** | JS 解析崩溃 | 用 `json.dumps` 安全编码 |
| 8 | **缩略图缺失** | 谱系页模糊图永不升级 | 生成 JPG 同时生成 200×280 thumb |

---

## 技术栈

- **前端**: React 19 + React Router v6 + Vite 8
- **阅读器**: react-pdf + epubjs（PDF/EPUB/TXT）
- **后端**: Python FastAPI + SQLite
- **AI**: DeepSeek Chat API（流式 + RAG 检索增强）
- **嵌入模型**: BAAI/bge-small-zh-v1.5（主）/ jieba TF-IDF（回退）
- **向量数据库**: ChromaDB
- **OCR**: PaddleOCR（中文扫描件）
- **部署**: Render (Docker, Singapore)，自动检测 master 分支推送
- **存储**: GitHub Release（书籍 + 用户DB备份）/ 阿里云 OSS / Cloudflare R2（可选）
