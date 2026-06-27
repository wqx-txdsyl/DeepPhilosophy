# DeepPhilosophy — 哲学谱系 Web 应用

一个展示东西方及世界哲学流派谱系、详情、著作和金句的单页应用（React + FastAPI），部署于 Render。

## 项目结构

```
DeepPhilosophy/
├── app/                          # React 前端 (Vite)
│   └── src/
│       ├── pages/
│       │   ├── GenealogyPage.jsx        # 谱系总览页（东西方时间轴）
│       │   ├── SchoolDetailPage.jsx     # 流派详情页（~850KB，所有数据内联）
│       │   └── WorldPhilosophiesPage.jsx # 世界哲学概览页（卡片网格）
│       ├── App.jsx                      # 路由配置
│       └── App.css                      # 全局样式变量（--ink, --text-dim 等）
├── backend/                      # FastAPI 后端
│   ├── main.py                   # API + 静态文件服务
│   ├── Dockerfile                # Render 部署镜像
│   └── app-dist/                 # 前端构建产物（Docker 从此复制到 static/）
├── render.yaml                   # Render 部署配置
└── README.md
```

根目录的辅助脚本（在 `../Q&ASystem/` 下）：
- `_gen_east3.py` — 东方学派数据生成器（调用 DeepSeek API）
- `_gen_world.py` — 世界哲学数据生成器（调用 DeepSeek API）

## 快速开始

```bash
# 前端开发
cd app
npm install
npm run dev          # Vite 开发服务器 → http://localhost:5173

# 前端构建
npm run build        # 产物输出到 app/dist/

# 预览构建结果
npx vite preview

# 同步构建产物到后端（Render 部署前必须）
rm -rf ../backend/app-dist && cp -r dist ../backend/app-dist
```

## 页面路由

| 路由 | 页面 | 说明 |
|------|------|------|
| `/` 或 `/genealogy` | GenealogyPage | 东西方哲学谱系双列时间轴 |
| `/school/:name` | SchoolDetailPage | 流派详情（星丛、辞海、金句、著作、时间轴） |
| `/world-philosophies` | WorldPhilosophiesPage | 世界9大哲学传统概览卡片 |
| `/books`, `/authors`, `/qa`, `/profile` | 其他功能页 | 书籍、作者、问答、个人 |

## 数据架构

### SchoolDetailPage.jsx 数据格式

所有流派数据直接内联在 `app/src/pages/SchoolDetailPage.jsx` 中（~850KB），每个流派有三个 JS 常量：

```js
// 主数据（约20个字段）
const XXX_DATA = {
  name: "流派名",
  quote: "代表性引语",
  quoteAuthor: "引语作者",
  subtitle: "一行概括",
  overview: `多段落概述（400-800字）`,
  thinkers: [{name, sub, era, influence, key, works: ["著作1","著作2"]}],  // 5-7位
  relations: [{from, to, type}],   // 继承/师生/影响/批判/友谊/对立
  timeline: [{year, event, detail, type}],  // 12-20个事件，type: birth/death/book/idea/event
  conclusion: `多段落总结（300-600字）`,
  works: [{title, author, era, desc}],      // 6-8部代表著作
  quotes: [{text, author, exp}],             // 18-20条金句
  closingQuote: "结尾引文 —— 作者"
};

// 辞海（术语表）
const XXX_CIHAI = [{word, def, source}];  // 20+条目

// 下属流派
const XXX_SUB_SCHOOLS = [{name, era, desc}];  // 2-4个子流派
```

### 数据注册（SCHOOL_MAP）

在 `SchoolDetailPage.jsx` 底部 `function SchoolDetailPage()` 内部：

```js
const SCHOOL_MAP = {
  '流派名': { data: XXX_DATA, sub: XXX_SUB_SCHOOLS, ci: XXX_CIHAI, bg: 'url(/schools/greek.jpg)' },
  // ...
};
```

### 星丛颜色（SUB_COLORS）

在 `SchoolDetailPage.jsx` 顶部有一个 `const SUB_COLORS = {...}` 对象，将 `t.sub` 值映射到颜色。**每新增一个 thinker sub 值都需要在此添加颜色条目**，否则星丛节点将全部显示为默认土黄色。

## 新增流派指南

### 手动添加

1. 在 `SchoolDetailPage.jsx` 中 `function SchoolDetailPage()` **之前**添加 `XXX_DATA`、`XXX_CIHAI`、`XXX_SUB_SCHOOLS` 三个常量
2. 在 `SCHOOL_MAP` 中注册
3. 在 `SUB_COLORS` 中为每个 thinker 的 `sub` 值添加颜色
4. 在 `GenealogyPage.jsx` 的时间轴中引用（如果需要）

### 使用生成器批量生成

```bash
cd ../Q&ASystem
python _gen_world.py    # 生成世界哲学数据
python _gen_east3.py    # 生成东方哲学数据
```

生成器通过 DeepSeek API 自动生成 overview/conclusion/thinkers/cihai/quotes/works/timeline。

## 构建与部署

### Render 自动部署

推送到 GitHub `master` 分支后 Render 自动部署。Dockerfile 工作流：

```
1. 安装 Python 依赖
2. 复制后端代码
3. 复制 backend/app-dist/ 到 static/     ← 前端构建产物
4. 启动 python main.py
```

### 部署前检查清单

```bash
# 1. 构建前端
cd app && npm run build

# 2. 检查构建无报错，产物在 app/dist/

# 3. 同步到后端
rm -rf ../backend/app-dist && cp -r dist ../backend/app-dist

# 4. 提交并推送
git add app/src/pages/SchoolDetailPage.jsx backend/app-dist
git commit -m "描述改动"
git push origin master
```

## 常见陷阱

| 问题 | 原因 | 解决 |
|------|------|------|
| 页面跳转无内容 | `backend/app-dist/` 未同步最新构建 | 重新 `npm run build` 并同步 |
| 双书名号《《》》 | API 生成的 title 已含《》，渲染代码又包了一层 | 在数据中剥离预置《》 |
| 星丛全部同色 | thinker 的 `sub` 值不在 SUB_COLORS 中 | 在 SUB_COLORS 中添加该 sub 的映射 |
| 构建报错 `Expected , or }` | JS 字符串内出现未转义的 ASCII 双引号 | 避免在双引号字符串内使用中文引号 `""`，改用无引号或转义 |
| SCHOOL_MAP 重复键 | 插入数据时未清理旧条目 | JS 对象重复键不报错但会导致回退逻辑失效 |

## 数据统计

| 类别 | 流派数 | 数据完整性 |
|------|--------|-----------|
| 西方哲学 | 43 | quote/subtitle/thinkers/relations/cihai(20+)/quotes(18+)/timeline 全部完整 |
| 东方哲学 | 22 | 同上，overview/conclusion/sub_schools 均已补齐 |
| 世界哲学 | 8 | 印度/日本/伊斯兰阿拉伯/非洲/犹太/波斯/拉美/东南亚，数据通过 API 生成 |
| **合计** | **73** | |

## 技术栈

- **前端**: React 18 + React Router v6 + Vite (rolldown)
- **后端**: Python FastAPI + ChromaDB + sentence-transformers
- **部署**: Render (Docker, Singapore region, free plan)
- **数据生成**: DeepSeek API
