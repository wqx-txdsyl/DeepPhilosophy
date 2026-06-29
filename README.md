# DeepPhilosophy — 哲学爱好者知识平台

东西方及世界哲学的综合Web应用。React + FastAPI，部署于 Render。v2.0

## 数据质量标准（强制执行）

| 模块 | 字段 | 最低标准 |
|------|------|---------|
| 📚 书籍 | 摘要 | ≥300字 |
| ✒️ 哲人 | bio | ≥1000字 |
| 🧬 谱系 | overview | ≥500字 |
| 🧬 谱系 | conclusion | ≥500字 |
| 🧬 谱系 | quotes | ≥20条 |
| 🧬 谱系 | cihai | ≥20条 |

---

## 数据统计

| 类别 | 数量 | 说明 |
|------|------|------|
| 西方哲学流派 | 40 | 教父哲学→技术哲学（古希腊+斯多葛+怀疑论移入世界） |
| 东方哲学流派 | 24 | 先秦→当代 |
| 世界哲学流派 | 24 | 古希腊/古埃及/美索不达米亚/印度/犹太/波斯/伊斯兰/阿拉伯/西藏/非洲/拉美/玛雅/阿兹特克/东南亚/韩国/北欧/东欧/北美/蒙古中亚/澳洲/印加/前苏格拉底/伊壁鸠鲁学派/犬儒学派/新柏拉图主义 |
| **流派合计** | **88** | |
| 哲学著作 | 342 | PDF/EPUB/TXT |
| 哲学家 | 353 | 含星丛全量覆盖，JSON存储 |
| 每日金句 | 665 | |
| 游戏 | 3 | 答案之书 / PHTI / PHTI沙雕版 |

---

## 关键架构决策

### philosophers_db → JSON
哲学家数据库从 1MB Python dict 转为 JSON 文件加载，避免 Python 字符串转义问题。`philosophers_db.py` → `data/philosophers.json`

### SchoolDetailPage — inline DATA
流派详情数据直接内联编译进 JS bundle（无动态 fetch），与 76 个老流派保持一致的渲染方式。生成脚本：`app/gen_inline_schools.py`

### 标签系统
哲学家标签（流派/时代/国家）经过三轮重构：
1. 后端 `_normalize_tag` + 前端 `normMap` 双端同步
2. `philosophers.json` 中直接规范化标签（215处合并）
3. 国家名今名化（普鲁士→德国等14个映射）
4. 跨世纪覆盖（`_era_to_centuries` 返回生卒年间所有世纪）

### 世界哲学流派构建
10个新流派通过 AI 批量生成 school JSON → gen_inline_schools.py 转为 JS DATA → 内联进 SchoolDetailPage。数据标准：overview≥800字, conclusion≥500字, quotes≥20条, cihai≥20条, timeline≥8条, thinkers≥8位。

---

## 部署

推送到 GitHub `master` 分支，Render 自动部署。Dockerfile 使用 `backend/app-dist/` 作为静态文件。

Render 环境变量：`DEEPSEEK_API_KEY`, `GITHUB_TOKEN`

---

## ⚠️ 经验教训

| 错误 | 根因 | 教训 |
|------|------|------|
| 新流派白屏 | `import * as X from file` 但忘记 `export` | JS模块必须先export才能import |
| 多次重复声明DATA | fix_school_page.py 插入点重复 | 脚本幂等性检查 |
| 详情页全崩 | `useState` 在 `const data = dynamicData` 之后声明 | Hooks 必须在所有变量引用之前 |
| 标签筛选全0人 | `_era_to_centuries` CE正则匹配了BCE年份 | 负向前瞻必须完整 |
| `influence: "9"` | gen脚本输出字符串非数字 | 数据生成后必须类型检查 |
| 双书名号 | JSON title自带《》，WorksList又包一层 | 组件加 `.replace()` 防御 |
| 后台JSON写坏 | 并发进程同时写同一文件 | 加工单进程+JSON中间格式 |
| `bg:.jpg`但文件是`.png` | 统一后缀疏忽 | 构建前校验文件存在性 |
| 标签无效 | 前后端 normalize 不同步 | 标签统一从JSON规范化，前后端共享同一MERGE MAP |
| git push被阻 | `git add -A` 带入敏感文件 | `.gitignore` 必须提前配置 |
| `const`重复声明 | Python脚本多次插入同一段DATA | 插入前检查目标字符串是否已存在 |

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
